"""Execute a contact-confirmed pick/place sequence using simulation time."""
import os
import subprocess
import time

import rclpy
from action_msgs.msg import GoalStatus
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from .kinematics import inverse_kinematics


class TrajectoryPlayer(Node):
    def __init__(self):
        super().__init__('trajectory_player', parameter_overrides=[
            Parameter('use_sim_time', value=True)])
        self.client = ActionClient(self, FollowJointTrajectory,
                                   '/arm_controller/follow_joint_trajectory')
        self.create_subscription(String, '/dobot_magician/suction_state',
                                 self.on_suction_state, 10)
        self.suction_state = None
        self.wait_state = None
        self.wait_deadline = 0
        self.exit_code = 0
        self.started = False
        self.finished = False
        self.step = 0
        self.progress_deadline = time.monotonic() + 30
        # Ground top is z=0; the box is 20 mm and the cup extends 6 mm below its frame.
        self.steps = [
            ('approach', (0.18, -0.15, 0.09)),
            ('pick', (0.18, -0.15, 0.0255)),
            ('lift', (0.18, -0.15, 0.09)),
            ('transfer', (0.08, 0.16, 0.09)),
            ('place', (0.08, 0.16, 0.028)),
            ('retreat', (0.08, 0.16, 0.09)),
            ('home', None),
        ]
        self.timer = self.create_timer(0.1, self.tick)
        self.wall_clock = Clock(clock_type=ClockType.STEADY_TIME)
        self.watchdog = self.create_timer(0.2, self.check_watchdog, clock=self.wall_clock)

    def check_watchdog(self):
        if time.monotonic() > self.progress_deadline:
            phase = self.steps[self.step][0] if self.started else 'startup'
            self.finish(f'Wall timeout during {phase}; check simulation clock and controller')

    def made_progress(self):
        self.progress_deadline = time.monotonic() + 45

    def on_suction_state(self, message):
        self.suction_state = message.data

    def set_suction(self, enabled):
        subprocess.run(
            ['gz', 'topic', '-t', '/dobot_magician/suction/enable',
             '-m', 'gz.msgs.Boolean', '-p', f'data: {str(enabled).lower()}'],
            check=True, timeout=5.0, capture_output=True)

    def tick(self):
        if not self.started:
            if not self.client.server_is_ready() or self.suction_state is None:
                return
            self.started = True
            self.set_suction(False)
            self.send_step()
        elif self.wait_state is not None:
            if self.suction_state == self.wait_state:
                self.get_logger().info(f'Suction confirmed: {self.wait_state}')
                self.wait_state = None
                self.made_progress()
                self.send_step()
            elif self.get_clock().now().nanoseconds > self.wait_deadline:
                self.finish(f'Timed out waiting for suction state {self.wait_state}')

    def send_step(self):
        if self.step == len(self.steps):
            self.finish()
            return
        name, point = self.steps[self.step]
        positions = ((0.0, 0.05, 0.05, 0.0) if point is None else
                     inverse_kinematics(*point, vertical_tool=True))
        trajectory = JointTrajectory(joint_names=['joint_1', 'joint_2', 'joint_3', 'joint_4'])
        target = JointTrajectoryPoint(positions=list(positions))
        target.time_from_start.sec = 4
        trajectory.points.append(target)
        goal = FollowJointTrajectory.Goal(trajectory=trajectory)
        self.get_logger().info(f'Moving: {name}')
        self.made_progress()
        self.client.send_goal_async(goal).add_done_callback(self.on_goal)

    def on_goal(self, future):
        handle = future.result()
        if not handle.accepted:
            self.finish('Trajectory controller rejected the goal')
            return
        self.made_progress()
        handle.get_result_async().add_done_callback(self.on_result)

    def on_result(self, future):
        response = future.result()
        if response.status != GoalStatus.STATUS_SUCCEEDED:
            self.finish(f'Trajectory action ended with status {response.status}')
            return
        result = response.result
        if result.error_code != FollowJointTrajectory.Result.SUCCESSFUL:
            self.finish(f'Trajectory failed: {result.error_string}')
            return
        self.made_progress()
        name, _ = self.steps[self.step]
        self.step += 1
        if name == 'approach':
            self.set_suction(True)
        if name in ('pick', 'place'):
            if name == 'place':
                self.set_suction(False)
            self.wait_state = 'attached' if name == 'pick' else 'detached'
            self.wait_deadline = self.get_clock().now().nanoseconds + 2_000_000_000
            return
        self.send_step()

    def finish(self, error=None):
        if self.finished:
            return
        self.finished = True
        self.timer.cancel()
        self.watchdog.cancel()
        self.exit_code = 1 if error else 0
        if error:
            self.get_logger().error(error)
            try:
                self.set_suction(False)
            except (OSError, subprocess.SubprocessError) as command_error:
                self.get_logger().error(f'Could not disable suction: {command_error}')
        else:
            self.get_logger().info('Pick/place complete with attachment and release confirmed.')
        rclpy.try_shutdown()


def main():
    os.environ.pop('FASTRTPS_DEFAULT_PROFILES_FILE', None)
    rclpy.init()
    node = TrajectoryPlayer()
    try:
        rclpy.spin(node)
    except (Exception, KeyboardInterrupt) as error:
        node.finish(f'Execution interrupted: {type(error).__name__}: {error}')
    finally:
        if not node.finished:
            node.finish('ROS execution stopped before pick/place completed')
        node.destroy_node()
        rclpy.try_shutdown()
    raise SystemExit(node.exit_code)
