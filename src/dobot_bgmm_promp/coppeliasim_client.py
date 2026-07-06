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
    block_path: str | None = None
    block_local_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
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
        self.block = None

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
        carrying_block = False
        release_done = False

        for i in range(len(cartesian)):
            self.sim.setObjectPosition(self.target, cartesian[i].tolist(), -1)
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
            place_position = self.config.place_positions[self.config.place_index - 1]
        else:
            place_position = (float(fallback_position[0]), float(fallback_position[1]), 0.006)
        self.sim.setObjectPosition(self.block, list(place_position), -1)
