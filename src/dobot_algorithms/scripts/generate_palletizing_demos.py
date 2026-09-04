"""Generate synthetic single-place palletizing demonstration data."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline


HOME = (0.0, 0.0, 0.15)
PICK = (0.20, -0.16, 0.02)
PLACE = (0.34, -0.16)
PLACE_Z = 0.02
LIFT_Z = 0.07

N_TIME_STEPS = 150
N_PER_POSE = 5
NOISE_XY = 0.02
NOISE_Z = 0.02


def _waypoints_for_place(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    def jitter(xy: tuple[float, float]) -> tuple[float, float]:
        return (
            xy[0] + rng.uniform(-NOISE_XY, NOISE_XY),
            xy[1] + rng.uniform(-NOISE_XY, NOISE_XY),
        )

    pk = jitter(PICK[:2])
    pl = jitter(PLACE)
    pick_z = PICK[2] + rng.uniform(-NOISE_Z, NOISE_Z)
    place_z = PLACE_Z + rng.uniform(-NOISE_Z, NOISE_Z)
    lift_z = LIFT_Z + rng.uniform(-NOISE_Z, NOISE_Z)

    pos = np.array(
        [
            HOME,
            (pk[0], pk[1], lift_z),
            (pk[0], pk[1], pick_z),
            (pk[0], pk[1], lift_z),
            (pl[0], pl[1], lift_z),
            (pl[0], pl[1], place_z),
            (pl[0], pl[1], lift_z),
            HOME,
        ],
        dtype=float,
    )
    gripper = np.array([0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0], dtype=float)
    return pos, gripper


def _interpolate(pos: np.ndarray, gripper: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    phases = np.linspace(0.0, 1.0, 8)
    target_phases = np.linspace(0.0, 1.0, N_TIME_STEPS)

    interp_pos = CubicSpline(phases, pos, axis=0, bc_type="natural")(target_phases)
    interp_g = CubicSpline(phases, gripper, axis=0, bc_type="natural")(target_phases)
    return interp_pos, np.clip(interp_g, 0.0, 1.0)


def _build_trajectory(rng: np.random.Generator) -> np.ndarray:
    pos, gripper = _waypoints_for_place(rng)
    interp_pos, interp_g = _interpolate(pos, gripper)
    time = np.linspace(0.0, interp_pos.shape[0] * 0.03, interp_pos.shape[0])
    return np.column_stack([time, interp_pos, interp_g])


def _next_demo_path(demos_dir: str | Path) -> Path:
    demos_path = Path(demos_dir)
    demos_path.mkdir(parents=True, exist_ok=True)
    existing = sorted(demos_path.glob("demo_*.csv"))
    max_index = 0
    for path in existing:
        try:
            max_index = max(max_index, int(path.stem.split("_")[-1]))
        except ValueError:
            continue
    return demos_path / f"demo_{max_index + 1:02d}.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate single-place palletizing demos.")
    parser.add_argument("--output-dir", default="data/demos_single_place")
    parser.add_argument(
        "--n-per-pose",
        type=int,
        default=N_PER_POSE,
        help=f"Number of variants for the single place position (default {N_PER_POSE}).",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    total = args.n_per_pose
    print(f"Generating {total} demos for place ({PLACE[0]:.3f}, {PLACE[1]:.3f}) ...")

    first_path = _next_demo_path(args.output_dir)
    start_idx = int(first_path.stem.split("_")[-1])
    for variant in range(args.n_per_pose):
        traj = _build_trajectory(rng)
        out = first_path.parent / f"demo_{start_idx + variant:02d}.csv"
        with out.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["t", "x", "y", "z", "gripper"])
            writer.writerows(traj)
        print(f"  {out.name} -> place ({PLACE[0]:.3f}, {PLACE[1]:.3f})")

    print(f"Done. {total} demos written to {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
