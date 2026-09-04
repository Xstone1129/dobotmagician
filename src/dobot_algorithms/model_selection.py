from __future__ import annotations

import numpy as np


DEFAULT_PLACE_POSITIONS: tuple[tuple[float, float, float], ...] = (
    (0.34, -0.16, 0.006),
)


def normalize_demo(demo: np.ndarray, n_time_steps: int) -> np.ndarray:
    demo = np.asarray(demo, dtype=float)
    if demo.ndim != 2:
        raise ValueError("Each demonstration must be a 2D array shaped [time, dimension].")
    if demo.shape[0] < 2:
        raise ValueError("Each demonstration needs at least two time steps.")
    if demo.shape[0] == n_time_steps:
        return demo

    old_phase = np.linspace(0.0, 1.0, demo.shape[0])
    new_phase = np.linspace(0.0, 1.0, n_time_steps)
    return np.column_stack([np.interp(new_phase, old_phase, demo[:, dim]) for dim in range(demo.shape[1])])


def placement_feature(trajectory: np.ndarray) -> np.ndarray:
    trajectory = np.asarray(trajectory, dtype=float)
    if trajectory.ndim != 2 or trajectory.shape[1] < 2:
        raise ValueError("Trajectory must be shaped [time, dimension] with at least x,y.")

    if trajectory.shape[1] >= 4:
        phase = np.linspace(0.0, 1.0, len(trajectory))
        gripper = trajectory[:, 3]
        place_mask = (phase > 0.45) & (gripper < 0.55)
        if place_mask.any():
            return trajectory[place_mask][0, :2].copy()

    index = int(0.7 * (len(trajectory) - 1))
    return trajectory[index, :2].copy()


def select_trajectory_for_place(
    trajectories: np.ndarray,
    place_index: int,
    place_positions: list[list[float]] | tuple[tuple[float, float, float], ...],
) -> np.ndarray:
    if not 1 <= place_index <= len(place_positions):
        raise ValueError(f"place_index must be between 1 and {len(place_positions)}.")

    target_xy = np.asarray(place_positions[place_index - 1][:2], dtype=float)
    best_trajectory = None
    best_distance = float("inf")

    for trajectory in np.asarray(trajectories, dtype=float):
        candidate = placement_feature(trajectory)
        distance = float(np.linalg.norm(candidate - target_xy))
        if distance < best_distance:
            best_distance = distance
            best_trajectory = trajectory

    if best_trajectory is None:
        raise RuntimeError("No trajectory candidates are available.")
    return np.asarray(best_trajectory, dtype=float)
