"""Generate rear-pick, turn, and opposite-side-place demonstrations for the full arm."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline


HOME = np.array([0.10, 0.00, 0.20])
REAR_PICK = np.array([-0.20, -0.14, 0.030])
OPPOSITE_PLACE = np.array([0.08, 0.16, 0.030])
LIFT_Z = 0.18


def build_demo(rng: np.random.Generator, n_steps: int = 180) -> np.ndarray:
    xy_noise = rng.uniform(-0.007, 0.007, size=2)
    pick = REAR_PICK + np.array([xy_noise[0], xy_noise[1], 0.0])
    place = OPPOSITE_PLACE + np.array([-xy_noise[1], xy_noise[0], 0.0])
    # Lifting at the rear then passing over the base makes the turn visible and
    # keeps the target above the table while it changes sides.
    waypoints = np.array(
        [
            HOME,
            [pick[0], pick[1], LIFT_Z],
            pick,
            pick,
            [pick[0], pick[1], LIFT_Z],
            [-0.02, 0.02, LIFT_Z + 0.025],
            [place[0], place[1], LIFT_Z],
            place,
            place,
            [place[0], place[1], LIFT_Z],
            HOME,
        ]
    )
    vacuum = np.array([0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0], dtype=float)
    source_phase = np.linspace(0.0, 1.0, len(waypoints))
    phase = np.linspace(0.0, 1.0, n_steps)
    xyz = CubicSpline(source_phase, waypoints, axis=0, bc_type="natural")(phase)
    signal = np.clip(CubicSpline(source_phase, vacuum, bc_type="natural")(phase), 0.0, 1.0)
    time = np.linspace(0.0, (n_steps - 1) * 0.04, n_steps)
    return np.column_stack([time, xyz, signal])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate full Dobot suction turn demonstrations.")
    parser.add_argument("--output-dir", default="data/demos_suction_turn")
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--seed", type=int, default=57)
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for path in output.glob("demo_*.csv"):
        path.unlink()
    rng = np.random.default_rng(args.seed)
    for index in range(1, args.count + 1):
        with (output / f"demo_{index:02d}.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["t", "x", "y", "z", "gripper"])
            writer.writerows(build_demo(rng))
    print(f"Saved {args.count} rear-pick / turn / opposite-place demos to {output.resolve()}")


if __name__ == "__main__":
    main()
