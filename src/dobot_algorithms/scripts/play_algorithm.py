"""Play one learned Cartesian trajectory on the ROS 2 Dobot controller.

The selected model can come from the config's ``active_algorithm`` entry or be
overridden on the command line, so the same runtime path works for all four
learned models.
"""
from __future__ import annotations

import argparse
import copy
import signal
import subprocess
import time
from contextlib import suppress
from dataclasses import dataclass

import numpy as np
import rclpy
from action_msgs.msg import GoalStatus
from control_msgs.action import FollowJointTrajectory
from dobot_magician_ros.kinematics import inverse_kinematics
from rclpy.action import ActionClient
from rclpy.clock import Clock, ClockType
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import String
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from dobot_algorithms.data_io import load_config, load_model

ALGORITHMS = ("gmm_gmr_dmp", "inc_gmm_gmr_dmp", "gmm_gmr_segmented_dmp", "bgmm_gmr_promp")
DEFAULT_SAMPLE_PERIOD = 0.08
DEFAULT_LEAD_IN = 2.0
DEFAULT_MAX_JOINT_SPEED = 0.8
HOME_JOINTS = (0.0, 0.05, 0.05, 0.0)


def resolve_algorithm(config: dict, override: str | None) -> str:
    model_config = config.get("model", {})
    algorithm = (
        override
        or model_config.get("active_algorithm")
        or model_config.get("algorithm", "gmm_gmr_dmp")
    )
    if algorithm == "compare":
        algorithm = model_config.get("active_algorithm") or "gmm_gmr_dmp"
    if algorithm not in ALGORITHMS:
        options = ", ".join(ALGORITHMS)
        raise ValueError(f"Algorithm must be one of: {options}")
    return algorithm


def sample_indices(n_points: int, max_waypoints: int | None) -> np.ndarray:
    if n_points < 2:
        raise ValueError("The learned trajectory must contain at least two waypoints")
    if max_waypoints is None or max_waypoints <= 0 or max_waypoints >= n_points:
        return np.arange(n_points, dtype=int)
    indices = np.linspace(0, n_points - 1, max_waypoints).round().astype(int)
    return np.unique(indices)


def playback_indices(trajectory: np.ndarray, max_waypoints: int | None) -> np.ndarray:
    indices = sample_indices(len(trajectory), max_waypoints)
    if trajectory.shape[1] >= 4:
        if not np.isfinite(trajectory[:, 3]).all():
            raise ValueError("Suction commands must be finite")
        enabled = trajectory[:, 3] >= 0.5
        changes = np.flatnonzero(enabled[1:] != enabled[:-1]) + 1
        indices = np.union1d(indices, changes)
    return indices


def build_joint_trajectory(
    trajectory: np.ndarray,
    *,
    speed: float,
    sample_period: float,
    lead_in: float,
    max_waypoints: int | None,
    vertical_tail_fraction: float,
    max_joint_speed: float = DEFAULT_MAX_JOINT_SPEED,
) -> tuple[JointTrajectory, list[int]]:
    if trajectory.ndim != 2 or trajectory.shape[1] < 3:
        raise ValueError("The learned trajectory must contain X, Y and Z columns")
    if not np.isfinite(max_joint_speed) or not 0 < max_joint_speed <= 3.15:
        raise ValueError("max_joint_speed must be positive and at most the URDF limit of 3.15 rad/s")
    if not np.isfinite(speed) or speed <= 0:
        raise ValueError("speed must be finite and positive")
    speed = max(float(speed), 0.1)
    sample_period = max(float(sample_period), 1e-3)
    lead_in = max(float(lead_in), 0.0)
    indices = playback_indices(trajectory, max_waypoints)
    vertical_tail_fraction = min(max(float(vertical_tail_fraction), 0.0), 1.0)
    vertical_start = round(len(trajectory) * (1.0 - vertical_tail_fraction))
    msg = JointTrajectory(joint_names=["joint_1", "joint_2", "joint_3", "joint_4"])
    skipped: list[int] = []
    reachable = 0
    home_point = JointTrajectoryPoint(positions=list(HOME_JOINTS))
    lead_in_time = lead_in / speed
    home_point.time_from_start.sec = int(lead_in_time)
    home_point.time_from_start.nanosec = round((lead_in_time - home_point.time_from_start.sec) * 1e9)
    if home_point.time_from_start.nanosec >= 1_000_000_000:
        home_point.time_from_start.sec += 1
        home_point.time_from_start.nanosec -= 1_000_000_000
    msg.points.append(home_point)
    elapsed = lead_in_time
    previous_index = -1
    previous_joints = np.asarray(HOME_JOINTS)
    joint_speed_limit = max_joint_speed * min(speed, 1.0)
    for row_index in indices:
        try:
            joints = inverse_kinematics(
                *trajectory[row_index, :3],
                vertical_tool=int(row_index) >= vertical_start,
            )
        except ValueError:
            skipped.append(int(row_index))
            continue
        reachable += 1
        point = JointTrajectoryPoint(positions=list(joints))
        # Include HOME -> pick in retiming; a distant first point is not one sample away.
        nominal_duration = (int(row_index) - previous_index) * sample_period / speed
        motion_duration = (
            float(np.max(np.abs(np.asarray(joints) - previous_joints))) / joint_speed_limit
        )
        elapsed += max(nominal_duration, motion_duration)
        point.time_from_start.sec = int(elapsed)
        point.time_from_start.nanosec = round((elapsed - point.time_from_start.sec) * 1e9)
        if point.time_from_start.nanosec >= 1_000_000_000:
            point.time_from_start.sec += 1
            point.time_from_start.nanosec -= 1_000_000_000
        msg.points.append(point)
        previous_index = int(row_index)
        previous_joints = np.asarray(joints)
    if reachable == 0:
        raise ValueError("The learned trajectory did not contain any reachable waypoints")
    return msg, skipped


@dataclass
class PlaybackStage:
    trajectory: JointTrajectory
    suction_after: bool | None


def build_playback_stages(
    trajectory: np.ndarray, message: JointTrajectory, indices: np.ndarray
) -> list[PlaybackStage]:
    """Stop at each vacuum transition so contact/release can be confirmed before moving."""
    if len(message.points) != len(indices) + 1:
        raise ValueError("Cannot execute suction transitions on an incomplete joint trajectory")
    boundaries: list[tuple[int, bool | None]] = []
    enabled = False
    if trajectory.shape[1] >= 4:
        for point_index, row_index in enumerate(indices, start=1):
            command = bool(trajectory[row_index, 3] >= 0.5)
            if command != enabled:
                boundaries.append((point_index, command))
                enabled = command
    last = len(message.points) - 1
    if not boundaries or boundaries[-1][0] != last:
        boundaries.append((last, False if enabled else None))
    elif enabled:
        raise ValueError("The final trajectory point must release the suction cup")
    stages = []
    start = 0
    offset_ns = 0
    for end, command in boundaries:
        stage = JointTrajectory(joint_names=list(message.joint_names))
        for point in message.points[start:end + 1]:
            local = copy.deepcopy(point)
            stamp = point.time_from_start
            local_ns = stamp.sec * 1_000_000_000 + stamp.nanosec - offset_ns
            local.time_from_start.sec, local.time_from_start.nanosec = divmod(local_ns, 1_000_000_000)
            stage.points.append(local)
        stages.append(PlaybackStage(stage, command))
        start = end
        stamp = message.points[end].time_from_start
        offset_ns = stamp.sec * 1_000_000_000 + stamp.nanosec
    return stages


class AlgorithmPlayer(Node):
    def __init__(
        self,
        algorithm: str,
        config: dict,
        speed: float,
        sample_period: float,
        lead_in: float,
        max_waypoints: int | None,
        startup_delay: float,
        vertical_tail_fraction: float,
        max_joint_speed: float = DEFAULT_MAX_JOINT_SPEED,
    ) -> None:
        super().__init__("algorithm_player", parameter_overrides=[
            Parameter("use_sim_time", value=True),
        ])
        self.client = ActionClient(
            self, FollowJointTrajectory, "/arm_controller/follow_joint_trajectory"
        )
        self.create_subscription(String, "/dobot_magician/suction_state", self.on_suction_state, 10)
        self.algorithm = algorithm
        path = config[algorithm]["output_path"]
        model = load_model(path)
        trajectory = np.asarray(model.mean_trajectory(), dtype=float)
        self.msg, skipped = build_joint_trajectory(
            trajectory,
            speed=speed,
            sample_period=sample_period,
            lead_in=lead_in,
            max_waypoints=max_waypoints,
            vertical_tail_fraction=vertical_tail_fraction,
            max_joint_speed=max_joint_speed,
        )
        if skipped:
            raise ValueError(
                f"Refusing incomplete {self.algorithm}: {len(skipped)} unreachable points {skipped[:8]}"
            )
        self.stages = build_playback_stages(
            trajectory, self.msg, playback_indices(trajectory, max_waypoints)
        )
        self.stage_index = 0
        self.suction_state = None
        self.suction_sequence = 0
        self.suction_enabled = False
        self.wait_state = None
        self.wait_sequence = 0
        self.wait_deadline = 0
        self.goal_handle = None
        self.goal_future = None
        self.result_future = None
        self.started = False
        self.finished = False
        self.exit_code = 0
        self.started_at = time.monotonic()
        self.progress_deadline = self.started_at + 60
        self.last_feedback_time = 0
        self.startup_delay = max(float(startup_delay), 0.0)
        self.timer = self.create_timer(0.05, self.tick)
        self.wall_clock = Clock(clock_type=ClockType.STEADY_TIME)
        self.watchdog = self.create_timer(0.2, self.check_watchdog, clock=self.wall_clock)

    def on_suction_state(self, message: String) -> None:
        self.suction_state = message.data
        self.suction_sequence += 1

    def set_suction(self, enabled: bool) -> None:
        if enabled:
            self.suction_enabled = True
        subprocess.run(
            ["gz", "topic", "-t", "/dobot_magician/suction/enable",
             "-m", "gz.msgs.Boolean", "-p", f"data: {str(enabled).lower()}"],
            check=True, timeout=5.0, capture_output=True,
        )
        self.suction_enabled = enabled

    def wait_for_suction(self, enabled: bool) -> None:
        self.wait_sequence = self.suction_sequence
        self.wait_state = "attached" if enabled else "detached"
        self.set_suction(enabled)
        self.wait_deadline = self.get_clock().now().nanoseconds + 3_000_000_000
        self.progress_deadline = time.monotonic() + 45

    def tick(self) -> None:
        if self.finished:
            return
        if not self.started:
            if (time.monotonic() - self.started_at < self.startup_delay
                    or not self.client.server_is_ready() or self.suction_state is None):
                return
            self.started = True
            duration = self.msg.points[-1].time_from_start
            self.get_logger().info(
                f"Playing {self.algorithm} with {len(self.msg.points)} waypoints in "
                f"{len(self.stages)} stages; motion duration "
                f"{duration.sec + duration.nanosec * 1e-9:.2f} s"
            )
            self.wait_for_suction(False)
        elif self.wait_state is not None:
            if self.suction_sequence > self.wait_sequence and self.suction_state == self.wait_state:
                self.get_logger().info(f"Suction confirmed: {self.wait_state}")
                self.wait_state = None
                self.send_stage()
            elif self.get_clock().now().nanoseconds > self.wait_deadline:
                self.finish(f"Timed out waiting for suction {self.wait_state}; stopped before next stage")

    def send_stage(self) -> None:
        if self.stage_index == len(self.stages):
            self.finish()
            return
        stage = self.stages[self.stage_index]
        self.progress_deadline = time.monotonic() + 45
        goal = FollowJointTrajectory.Goal(trajectory=stage.trajectory)
        self.get_logger().info(
            f"Moving stage {self.stage_index + 1}/{len(self.stages)}"
        )
        self.goal_future = self.client.send_goal_async(goal, feedback_callback=self.on_feedback)
        self.goal_future.add_done_callback(self.on_goal)

    def on_feedback(self, feedback) -> None:
        stamp = feedback.feedback.header.stamp
        now = stamp.sec * 1_000_000_000 + stamp.nanosec
        if now > self.last_feedback_time:
            self.last_feedback_time = now
            self.progress_deadline = time.monotonic() + 45

    def on_goal(self, future) -> None:
        handle = future.result()
        self.goal_future = None
        if not handle.accepted:
            self.finish("Trajectory controller rejected the stage")
            return
        self.goal_handle = handle
        self.result_future = handle.get_result_async()
        if not self.finished:
            self.result_future.add_done_callback(self.on_result)

    def on_result(self, future) -> None:
        if self.finished:
            return
        response = future.result()
        self.goal_handle = None
        if (response.status != GoalStatus.STATUS_SUCCEEDED
                or response.result.error_code != FollowJointTrajectory.Result.SUCCESSFUL):
            self.finish(f"Trajectory failed: {response.result.error_string} (status {response.status})")
            return
        stage = self.stages[self.stage_index]
        self.stage_index += 1
        if stage.suction_after is not None:
            self.wait_for_suction(stage.suction_after)
        else:
            self.send_stage()

    def check_watchdog(self) -> None:
        if not self.finished and time.monotonic() > self.progress_deadline:
            self.finish(
                f"No simulation/controller progress: started={self.started}, "
                f"sim_time={self.get_clock().now().nanoseconds * 1e-9:.3f}, "
                f"action_ready={self.client.server_is_ready()}, suction={self.suction_state}"
            )

    def stop(self) -> None:
        self.finished = True
        self.timer.cancel()
        self.watchdog.cancel()
        # This runs outside callbacks, with the ROS context alive until cancellation completes.
        if self.goal_future is not None:
            pending = self.goal_future
            rclpy.spin_until_future_complete(self, pending, timeout_sec=3.0)
            if not pending.done():
                raise RuntimeError("Cannot confirm pending trajectory status; suction kept enabled")
            handle = pending.result()
            if handle.accepted and self.goal_handle is None:
                self.goal_handle = handle
                self.result_future = handle.get_result_async()
        if self.goal_handle is not None:
            if not rclpy.ok():
                raise RuntimeError("ROS stopped before trajectory cancellation; suction kept enabled")
            cancellation = self.goal_handle.cancel_goal_async()
            rclpy.spin_until_future_complete(self, cancellation, timeout_sec=3.0)
            result = self.result_future or self.goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result, timeout_sec=3.0)
            terminal = (GoalStatus.STATUS_CANCELED, GoalStatus.STATUS_ABORTED, GoalStatus.STATUS_SUCCEEDED)
            if not result.done() or result.result().status not in terminal:
                raise RuntimeError("Cannot confirm controller stop; suction kept enabled")
            self.goal_handle = None
            self.get_logger().info("Controller stopped before disabling suction.")
        if self.suction_enabled:
            self.set_suction(False)

    def finish(self, error: str | None = None) -> None:
        if self.finished:
            return
        self.finished = True
        self.exit_code = 1 if error else 0
        if error:
            self.get_logger().error(error)
        else:
            self.get_logger().info("Learned trajectory complete; suction released.")
        self.timer.cancel()
        self.watchdog.cancel()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algorithm", choices=[*ALGORITHMS, "compare"])
    parser.add_argument("--config", default="configs/suction_arm.yaml")
    parser.add_argument(
        "--speed", type=float, default=1.0, help="trajectory playback speed multiplier"
    )
    parser.add_argument(
        "--sample-period",
        type=float,
        default=DEFAULT_SAMPLE_PERIOD,
        help="sample spacing in seconds before speed scaling",
    )
    parser.add_argument(
        "--lead-in",
        type=float,
        default=DEFAULT_LEAD_IN,
        help="seconds to hold the home posture before the learned trajectory",
    )
    parser.add_argument(
        "--max-joint-speed",
        type=float,
        default=DEFAULT_MAX_JOINT_SPEED,
        help="joint speed cap in rad/s, further reduced when --speed is below 1",
    )
    parser.add_argument(
        "--max-waypoints",
        type=int,
        default=None,
        help="optional waypoint cap for downsampling the learned trajectory",
    )
    parser.add_argument(
        "--startup-delay",
        type=float,
        default=8.0,
        help="minimum startup wait before checking controller and suction readiness",
    )
    parser.add_argument(
        "--vertical-tail-fraction",
        type=float,
        default=1.0,
        help="final fraction of the learned path that keeps the suction cup vertical",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    algorithm = resolve_algorithm(config, args.algorithm)
    max_waypoints = None if args.max_waypoints is None or args.max_waypoints <= 0 else args.max_waypoints
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    previous_handlers = {
        sig: signal.signal(sig, signal.default_int_handler) for sig in (signal.SIGINT, signal.SIGTERM)
    }
    node = None
    exit_code = 0
    try:
        node = AlgorithmPlayer(
            algorithm,
            config,
            args.speed,
            args.sample_period,
            args.lead_in,
            max_waypoints,
            args.startup_delay,
            args.vertical_tail_fraction,
            args.max_joint_speed,
        )
        while rclpy.ok() and not node.finished:
            rclpy.spin_once(node)
    except KeyboardInterrupt:
        exit_code = 130
    except ExternalShutdownException:
        exit_code = 1
    except Exception as error:
        exit_code = 1
        if node is None:
            raise
        node.get_logger().error(f"Playback failed: {error}")
    finally:
        # Ignore repeated launch signals while cancelling the controller and releasing the cup.
        for sig in previous_handlers:
            signal.signal(sig, signal.SIG_IGN)
        try:
            if node is not None:
                try:
                    node.stop()
                except (OSError, subprocess.SubprocessError, RuntimeError) as error:
                    exit_code = 1
                    node.get_logger().error(f"Playback cleanup failed: {error}")
                exit_code = max(exit_code, node.exit_code)
                node.destroy_node()
        finally:
            with suppress(ExternalShutdownException):
                rclpy.try_shutdown()
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
