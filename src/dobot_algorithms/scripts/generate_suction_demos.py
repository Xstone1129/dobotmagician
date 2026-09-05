"""Generate scene-aligned pick-to-place demonstrations for the suction cup frame."""

from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

from dobot_algorithms.data_io import project_path

DEFAULT_WORLD = project_path("ros2_ws/src/dobot_magician_ros/worlds/suction_turn.sdf")
DEFAULT_URDF = project_path("ros2_ws/src/dobot_magician_ros/urdf/dobot_magician.urdf.xacro")
LIFT_Z = 0.09
DEFAULT_PRESS_DEPTH = 0.0005
# The rigid suction model accepts at most 1 mm below the box top, without a compliant joint.
MAX_PRESS_DEPTH = 0.001
# simulation.launch.py spawns the fixed robot base at the world origin.
ARM_BASE_XY = np.zeros(2)


def _translation(element: ET.Element) -> np.ndarray:
    pose = element.find("pose")
    if pose is None:
        return np.zeros(3)
    values = np.array([float(value) for value in (pose.text or "").split()])
    if (
        pose.get("relative_to")
        or pose.get("rotation_format", "euler_rpy") != "euler_rpy"
        or values.shape != (6,)
        or not np.isfinite(values).all()
        or not np.allclose(values[3:], 0.0)
    ):
        raise ValueError("Demo stations require axis-aligned boxes with parent-relative poses")
    return values[:3]


def _box_geometry(world: ET.Element, name: str) -> tuple[np.ndarray, np.ndarray]:
    model = world.find(f"./world/model[@name='{name}']")
    link = None if model is None else model.find("link")
    collision = None if link is None else link.find("collision")
    if model is None or link is None or collision is None:
        raise ValueError(f"Missing collision box for scene model {name!r}")
    size = np.array([
        float(value) for value in collision.findtext("geometry/box/size", "").split()
    ])
    if size.shape != (3,) or not np.isfinite(size).all() or np.any(size <= 0):
        raise ValueError(f"Scene model {name!r} must have a positive box size")
    center = _translation(model) + _translation(link) + _translation(collision)
    return center, size


def load_stations(
    world_path: str | Path = DEFAULT_WORLD,
    urdf_path: str | Path = DEFAULT_URDF,
    press_depth: float = DEFAULT_PRESS_DEPTH,
) -> tuple[np.ndarray, np.ndarray]:
    """Read station centers and lower cup-frame contact heights by press_depth (m)."""
    if not np.isfinite(press_depth) or not 0 <= press_depth <= MAX_PRESS_DEPTH:
        raise ValueError(f"press_depth must be finite and between 0 and {MAX_PRESS_DEPTH} m")
    world = ET.parse(project_path(world_path)).getroot()
    pick_center, box_size = _box_geometry(world, "pick_box")
    place_center, table_size = _box_geometry(world, "place_table")
    robot = ET.parse(project_path(urdf_path)).getroot()
    surface_z = robot.findtext("./gazebo/plugin[@name='dobot::SuctionSystem']/surface_z")
    if surface_z is None or not np.isfinite(float(surface_z)) or float(surface_z) >= 0:
        raise ValueError("The URDF suction plugin must define a negative cup surface_z")
    cup_depth = -float(surface_z)
    pick = pick_center.copy()
    pick[2] += box_size[2] / 2 + cup_depth - press_depth
    place = place_center.copy()
    place[2] += table_size[2] / 2 + box_size[2] + cup_depth - press_depth
    return pick, place


def _turn_arc(
    pick: np.ndarray, place: np.ndarray, n_points: int = 13, lift_z: float = LIFT_Z
) -> np.ndarray:
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
            np.full(n_points, lift_z),
        ]
    )
    return arc


def build_demo(
    rng: np.random.Generator,
    n_steps: int = 180,
    noise_std: float = 0.0015,
    *,
    world_path: str | Path = DEFAULT_WORLD,
    urdf_path: str | Path = DEFAULT_URDF,
    lift_z: float = LIFT_Z,
    press_depth: float = DEFAULT_PRESS_DEPTH,
) -> np.ndarray:
    """Start at pick contact, lift and turn, then finish at place contact."""
    if not np.isfinite(noise_std) or noise_std < 0:
        raise ValueError("noise_std must be finite and non-negative")
    if n_steps < 20:
        raise ValueError("n_steps must be at least 20 to retain the pick/place phases")
    pick, place = load_stations(world_path, urdf_path, press_depth=press_depth)
    if not np.isfinite(lift_z) or lift_z <= max(pick[2], place[2]):
        raise ValueError("lift_z must be above both pick and place contact heights")
    turn_arc = _turn_arc(pick, place, lift_z=lift_z)
    waypoints = np.vstack(
        [
            pick,
            pick,
            pick,
            turn_arc,
            [place[0], place[1], lift_z],
            place,
            place,
            place,
        ]
    )
    vacuum = np.array(
        [0, 1, 1] + [1] * len(turn_arc) + [1, 1, 1, 0],
        dtype=float,
    )
    source_phase = np.concatenate([
        [0.0, 0.04, 0.08], np.linspace(0.22, 0.72, len(turn_arc)), [0.80, 0.92, 0.96, 1.0]
    ])
    phase = np.linspace(0.0, 1.0, n_steps)
    xyz = PchipInterpolator(source_phase, waypoints, axis=0)(phase)
    signal = np.clip(PchipInterpolator(source_phase, vacuum)(phase), 0.0, 1.0)
    signal[0] = signal[-1] = 0.0
    time = np.linspace(0.0, (n_steps - 1) * 0.04, n_steps)
    # Keep contact and vertical approach exact; add variation only during transfer.
    noise_window = np.zeros(n_steps)
    transfer = (phase > 0.22) & (phase < 0.80)
    noise_window[transfer] = np.sin(np.pi * (phase[transfer] - 0.22) / 0.58) ** 2
    noisy_xyz = xyz + noise_window[:, None] * rng.normal(0.0, noise_std, size=xyz.shape)
    noisy_xyz[0] = pick
    noisy_xyz[-1] = place
    return np.column_stack([time, noisy_xyz, signal])


def validate_reachability(demos: list[np.ndarray]) -> None:
    """Reject a batch before replacing CSVs if any upright-tool IK fails."""
    try:
        from dobot_magician_ros.kinematics import inverse_kinematics
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Add ros2_ws/src/dobot_magician_ros to PYTHONPATH for the offline IK check"
        ) from error
    for demo_index, demo in enumerate(demos, start=1):
        for point_index, point in enumerate(demo[:, 1:4]):
            try:
                inverse_kinematics(*point, vertical_tool=True)
            except ValueError as error:
                raise ValueError(
                    f"Demo {demo_index}, point {point_index}: upright suction target "
                    f"{point.tolist()} is unreachable; no CSVs were replaced"
                ) from error


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reachable scene-aligned pick/place demos.")
    parser.add_argument("--output-dir", default="data/demos_suction_turn")
    parser.add_argument("--world", type=Path, default=DEFAULT_WORLD)
    parser.add_argument("--urdf", type=Path, default=DEFAULT_URDF)
    parser.add_argument("--lift-z", type=float, default=LIFT_Z, help="Cup-frame transfer height (m).")
    parser.add_argument(
        "--press-depth", type=float, default=DEFAULT_PRESS_DEPTH,
        help="Lower both contact heights by this depth in meters (0 to 0.001; default 0.0005).",
    )
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--seed", type=int, default=57)
    parser.add_argument("--noise-std", type=float, default=0.0015, help="Cartesian Gaussian noise (m).")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    rng = np.random.default_rng(args.seed)
    demos = [
        build_demo(
            rng, noise_std=args.noise_std, world_path=args.world,
            urdf_path=args.urdf, lift_z=args.lift_z, press_depth=args.press_depth,
        )
        for _ in range(args.count)
    ]
    validate_reachability(demos)
    output = project_path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for path in output.glob("demo_*.csv"):
        path.unlink()
    for index, demo in enumerate(demos, start=1):
        with (output / f"demo_{index:02d}.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, lineterminator="\n")
            writer.writerow(["t", "x", "y", "z", "gripper"])
            writer.writerows(demo)
    print(f"Pick cup-frame center: {demos[0][0, 1:4].tolist()} m")
    print(f"Place cup-frame center: {demos[0][-1, 1:4].tolist()} m")
    print(f"Saved {args.count} demos; all {sum(map(len, demos))} points passed upright-tool IK")
    print(f"Output: {output.resolve()}")


if __name__ == "__main__":
    main()
