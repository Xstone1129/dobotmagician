from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CoppeliaConfig:
    host: str = "127.0.0.1"
    port: int = 23000
    target_path: str = "/DobotMagician/target"
    tip_path: str | None = None
    gripper_signal: str | None = None
    left_gripper_joint_path: str | None = None
    right_gripper_joint_path: str | None = None
    arm_joint_paths: tuple[str, ...] = ()
    arm_base_position: tuple[float, float, float] = (-0.08315, 0.0, 0.13155)
    block_path: str | None = None
    block_local_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    block_rest_height: float = 0.021
    pick_position: tuple[float, float, float] = (0.20, -0.16, 0.006)
    place_positions: tuple[tuple[float, float, float], ...] = (
        (0.34, -0.16, 0.006),
    )
    place_index: int | None = 1
    gripper_open_position: float = 0.010
    gripper_closed_position: float = 0.000
    pickup_threshold: float = 0.65
    release_threshold: float = 0.35
    release_mode: str = "current_pose"
    playback_dt: float = 0.03
    coordinate_scale: tuple[float, float, float] = (1.0, 1.0, 1.0)
    coordinate_offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
    workspace_max_radius: float | None = None
    workspace_z_bounds: tuple[float, float] | None = None
    base_exclusion_radius: float = 0.11
    base_clearance_z: float = 0.245
    use_scene_ik: bool = False


class CoppeliaDobotClient:
    """Small wrapper around the CoppeliaSim ZeroMQ Remote API."""

    def __init__(self, config: CoppeliaConfig) -> None:
        self.config = config
        self.client = None
        self.sim = None
        self.target = None
        self.tip = None
        self.left_gripper_joint = None
        self.right_gripper_joint = None
        self.arm_joints = []
        self.block = None
        self._active_place_position: np.ndarray | None = None

    def connect(self) -> None:
        from coppeliasim_zmqremoteapi_client import RemoteAPIClient

        self.client = RemoteAPIClient(host=self.config.host, port=self.config.port)
        self.sim = self.client.require("sim")
        try:
            self.target = self.sim.getObject(self.config.target_path)
        except Exception as exc:
            raise RuntimeError(
                "CoppeliaSim target object was not found. "
                f"Configured target_path={self.config.target_path!r}. "
                "Open the scene hierarchy, find the dummy/object you want to move, "
                "then set coppeliasim.target_path in configs/default.yaml to its exact alias/path."
            ) from exc
        self.tip = self._get_optional_object(self.config.tip_path) or self.target
        self.left_gripper_joint = self._get_optional_object(self.config.left_gripper_joint_path)
        self.right_gripper_joint = self._get_optional_object(self.config.right_gripper_joint_path)
        self.arm_joints = [self._get_optional_object(path) for path in self.config.arm_joint_paths]
        self.arm_joints = [joint for joint in self.arm_joints if joint is not None]
        self.block = self._get_optional_object(self.config.block_path)

    def start(self) -> None:
        self._require_connection()
        self.sim.startSimulation()

    def stop(self) -> None:
        self._require_connection()
        self.sim.stopSimulation()

    def play_cartesian_trajectory(self, trajectory: np.ndarray) -> None:
        self._require_connection()
        trajectory = np.asarray(trajectory, dtype=float)
        n_cols = trajectory.shape[1]
        if trajectory.ndim != 2 or n_cols not in (3, 4):
            raise ValueError("Cartesian playback expects trajectory shape [time, 3] or [time, 4].")

        if n_cols == 4:
            cartesian = trajectory[:, :3]
            gripper = trajectory[:, 3]
        else:
            cartesian = trajectory
            gripper = None

        scale = np.asarray(self.config.coordinate_scale, dtype=float)
        offset = np.asarray(self.config.coordinate_offset, dtype=float)
        if scale.shape != (3,) or offset.shape != (3,):
            raise ValueError("CoppeliaSim coordinate scale and offset must each contain 3 values.")
        cartesian = cartesian * scale + offset
        place_position = self._selected_place_position(scale, offset)
        pick_position = np.asarray(self.config.pick_position, dtype=float) * scale + offset
        cartesian = self._retarget_events(cartesian, gripper, pick_position, place_position)
        cartesian = self._constrain_cartesian(cartesian)
        self._active_place_position = place_position
        carrying_block = False
        release_done = False

        for i in range(len(cartesian)):
            self.sim.setObjectPosition(self.target, cartesian[i].tolist(), -1)
            if not self.config.use_scene_ik:
                self._drive_arm_fallback(cartesian[i])
            if gripper is not None and self.config.gripper_signal:
                gripper_value = float(np.clip(gripper[i], 0.0, 1.0))
                self.sim.setFloatSignal(self.config.gripper_signal, gripper_value)
                self._set_gripper_joints(gripper_value)
                if self.block is not None:
                    phase = i / max(len(cartesian) - 1, 1)
                    if not carrying_block and gripper_value >= self.config.pickup_threshold:
                        self._attach_block()
                        carrying_block = True
                    elif (
                        carrying_block
                        and not release_done
                        and phase > 0.5
                        and gripper_value <= self.config.release_threshold
                    ):
                        self._release_block(cartesian[i])
                        carrying_block = False
                        release_done = True
            time.sleep(self.config.playback_dt)

    def _selected_place_position(self, scale: np.ndarray, offset: np.ndarray) -> np.ndarray | None:
        if self.config.place_index is None:
            return None
        index = self.config.place_index - 1
        if not 0 <= index < len(self.config.place_positions):
            raise ValueError("place_index does not refer to a configured place position.")
        return np.asarray(self.config.place_positions[index], dtype=float) * scale + offset

    def _retarget_events(
        self,
        cartesian: np.ndarray,
        gripper: np.ndarray | None,
        pick_position: np.ndarray,
        place_position: np.ndarray | None,
    ) -> np.ndarray:
        """Make learned event poses exact without changing the learned timing."""

        result = np.asarray(cartesian, dtype=float).copy()
        if len(result) == 0 or gripper is None:
            return result
        gripper = np.asarray(gripper, dtype=float)
        pick_hits = np.flatnonzero(gripper >= self.config.pickup_threshold)
        if len(pick_hits):
            pick_index = int(pick_hits[0])
            result[pick_index] = pick_position
        if place_position is not None:
            phase = np.linspace(0.0, 1.0, len(result))
            release_hits = np.flatnonzero(
                (phase > 0.5) & (gripper <= self.config.release_threshold)
            )
            if len(release_hits):
                result[int(release_hits[0])] = place_position
        return result

    def _constrain_cartesian(self, cartesian: np.ndarray) -> np.ndarray:
        """Keep playback inside the arm reach and above its physical base."""

        result = np.asarray(cartesian, dtype=float).copy()
        base = np.asarray(self.config.arm_base_position, dtype=float)
        max_radius = self.config.workspace_max_radius
        z_bounds = self.config.workspace_z_bounds
        for point in result:
            if z_bounds is not None:
                point[2] = float(np.clip(point[2], z_bounds[0], z_bounds[1]))
            relative = point[:2] - base[:2]
            radius = float(np.linalg.norm(relative))
            if max_radius is not None and radius > max_radius:
                point[:2] = base[:2] + relative * (max_radius / radius)
                radius = max_radius
            if radius < self.config.base_exclusion_radius and point[2] < self.config.base_clearance_z:
                point[2] = self.config.base_clearance_z
        return result

    def _drive_arm_fallback(self, target: np.ndarray) -> None:
        """Keep the physical four-axis links moving when a scene lacks a live IK task.

        The generated scene also contains a simIK task. This bounded geometric
        fallback makes playback robust when a user opens the scene in a build
        where that add-on is disabled.
        """

        if len(self.arm_joints) < 4:
            return
        base = np.asarray(self.config.arm_base_position, dtype=float)
        relative = np.asarray(target, dtype=float) - base
        radius = float(np.hypot(relative[0], relative[1]))
        angles = (
            float(np.arctan2(relative[1], relative[0])),
            float(np.clip((radius - 0.20) * 7.0, -1.25, 1.25)),
            float(np.clip((relative[2] - 0.11) * 8.0, -1.25, 1.25)),
            0.0,
        )
        angles = (*angles[:3], float(np.clip(-angles[1] - angles[2], -1.5, 1.5)))
        for joint, angle in zip(self.arm_joints, angles):
            self.sim.setJointPosition(joint, angle)

    def _require_connection(self) -> None:
        if self.sim is None or self.target is None:
            raise RuntimeError("Call connect() before controlling CoppeliaSim.")

    def _get_optional_object(self, path: str | None):
        if not path:
            return None
        try:
            return self.sim.getObject(path)
        except Exception:
            return None

    def _set_gripper_joints(self, gripper_value: float) -> None:
        if self.left_gripper_joint is None or self.right_gripper_joint is None:
            return
        open_pos = self.config.gripper_open_position
        closed_pos = self.config.gripper_closed_position
        joint_pos = open_pos + (closed_pos - open_pos) * gripper_value
        self.sim.setJointTargetPosition(self.left_gripper_joint, joint_pos)
        self.sim.setJointTargetPosition(self.right_gripper_joint, joint_pos)

    def _attach_block(self) -> None:
        self.sim.setObjectParent(self.block, self.tip, False)
        self.sim.setObjectPosition(self.block, list(self.config.block_local_position), self.tip)

    def _release_block(self, fallback_position: np.ndarray) -> None:
        self.sim.setObjectParent(self.block, -1, True)
        if self.config.release_mode == "snap_to_place" and self.config.place_index is not None:
            place_position = self._active_place_position
            if place_position is None:
                place_position = np.asarray(
                    self.config.place_positions[self.config.place_index - 1], dtype=float
                )
        else:
            place_position = (
                float(fallback_position[0]),
                float(fallback_position[1]),
                self.config.block_rest_height,
            )
        self.sim.setObjectPosition(self.block, np.asarray(place_position, dtype=float).tolist(), -1)
