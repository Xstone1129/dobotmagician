"""Generate rear-pick, turn, and opposite-side-place demonstrations for the full arm."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator


HOME = np.array([0.10, 0.00, 0.20])
# These stations lie on a reachable 0.15 m ring around the Dobot base.
# The previous rear point was outside the model's negative-x IK workspace.
REAR_PICK = np.array([0.039723, -0.086036, 0.030])
OPPOSITE_PLACE = np.array([0.080000, 0.160000, 0.030])
LIFT_Z = 0.18
ARM_BASE_XY = np.array([-0.08315, 0.0])


def _turn_arc(pick: np.ndarray, place: np.ndarray, n_points: int = 13) -> np.ndarray:
    """Return a lifted, shortest circular arc about the Dobot base."""

    pick_vector = pick[:2] - ARM_BASE_XY
    place_vector = place[:2] - ARM_BASE_XY
    radius = float(np.linalg.norm(pick_vector))
    if radius < 1e-6:
        raise ValueError("Pick position is too close to the arm base for a turn arc.")
    pick_angle = float(np.arctan2(pick_vector[1], pick_vector[0]))
    place_angle = float(np.arctan2(place_vector[1], place_vector[0]))
    angle_delta = (place_angle - pick_angle + np.pi) % (2.0 * np.pi) - np.pi
    angles = np.linspace(pick_angle, pick_angle + angle_delta, n_points)
    arc = np.column_stack(
        [
            ARM_BASE_XY[0] + radius * np.cos(angles),
            ARM_BASE_XY[1] + radius * np.sin(angles),
            np.full(n_points, LIFT_Z),
        ]
    )
    return arc


def build_demo(
    rng: np.random.Generator, n_steps: int = 180, noise_std: float = 0.0015
) -> np.ndarray:
    """Build one demo with Gaussian measurement noise on Cartesian coordinates."""
    if noise_std < 0:
        raise ValueError("noise_std must be non-negative")
    xy_noise = rng.uniform(-0.007, 0.007, size=2)
    pick = REAR_PICK + np.array([xy_noise[0], xy_noise[1], 0.0])
    place = OPPOSITE_PLACE + np.array([-xy_noise[1], xy_noise[0], 0.0])
    # Lift the picked block, rotate around the base on a real circular arc,
    # then move radially to the place station before releasing it.
    turn_arc = _turn_arc(pick, place)
    waypoints = np.vstack(
        [
            HOME,
            [pick[0], pick[1], LIFT_Z],
            pick,
            pick,
            [pick[0], pick[1], LIFT_Z],
            turn_arc[1:],
            [place[0], place[1], LIFT_Z],
            place,
            place,
            [place[0], place[1], LIFT_Z],
            HOME,
        ]
    )
    vacuum = np.array(
        [0, 0, 0, 1, 1] + [1] * (len(turn_arc) - 1) + [1, 1, 0, 0, 0],
        dtype=float,
    )
    source_phase = np.linspace(0.0, 1.0, len(waypoints))
    phase = np.linspace(0.0, 1.0, n_steps)
    # PCHIP keeps every coordinate inside the waypoint envelope. A natural
    # cubic spline overshoots near the rear station and can leave the Dobot's
    # joint-limited workspace even when all waypoints are reachable.
    xyz = PchipInterpolator(source_phase, waypoints, axis=0)(phase)
    signal = np.clip(PchipInterpolator(source_phase, vacuum)(phase), 0.0, 1.0)
    time = np.linspace(0.0, (n_steps - 1) * 0.04, n_steps)
    noisy_xyz = xyz + rng.normal(0.0, noise_std, size=xyz.shape)
    noisy_xyz[0] = HOME
    noisy_xyz[-1] = HOME
    return np.column_stack([time, noisy_xyz, signal])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate full Dobot suction turn demonstrations.")
    parser.add_argument("--output-dir", default="data/demos_suction_turn")
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--seed", type=int, default=57)
    parser.add_argument("--noise-std", type=float, default=0.0015, help="Cartesian Gaussian noise (m).")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for path in output.glob("demo_*.csv"):
        path.unlink()
    rng = np.random.default_rng(args.seed)
    for index in range(1, args.count + 1):
        with (output / f"demo_{index:02d}.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, lineterminator="\n")
            writer.writerow(["t", "x", "y", "z", "gripper"])
            writer.writerows(build_demo(rng, noise_std=args.noise_std))
    print(f"Saved {args.count} noisy demos (std={args.noise_std:g} m) to {output.resolve()}")


if __name__ == "__main__":
    main()
