from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path

from dobot_bgmm_promp.io import load_config, project_path


COPPELIASIM_EXE = r"C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu\coppeliaSim.exe"
SOURCE_SCENE = r"C:\Users\Administrator\Desktop\dobotmagician.before_ik_backup.ttt"
OUTPUT_SCENE = "scenes/gripper_palletizing.ttt"

# Relative to the imported Dobot gripper core, the useful grasp point is not the
# whole jaw bounding-box center. It is lower, between the two finger tips.
GRIP_POINT_OFFSET = [0.0, 0.0069068439901838405, -0.070]

HOME = [0.0, 0.0, 0.15]
PICK = [0.20, -0.16, 0.006]
PLACE_POSITIONS = [
    [0.34, -0.16, 0.006],
]

VIEW_OBJECT_ALIASES = {
    "DefaultCamera",
    "XYZCameraProxy",
    "DefaultLights",
    "XViewCamera",
    "YViewCamera",
    "ZViewCamera",
    "NXViewCamera",
    "NYViewCamera",
    "NZViewCamera",
    "LightA",
    "LightB",
    "LightC",
    "LightD",
}


def _set_alias(sim, handle: int, alias: str) -> None:
    sim.setObjectAlias(handle, alias)


def _make_box(sim, alias: str, size: list[float], pos: list[float], color: list[float]) -> int:
    handle = sim.createPrimitiveShape(sim.primitiveshape_cuboid, size)
    _set_alias(sim, handle, alias)
    sim.setObjectPosition(handle, pos, sim.handle_world)
    sim.setShapeColor(handle, "", sim.colorcomponent_ambient_diffuse, color)
    return handle


def _make_marker(sim, alias: str, pos: list[float], color: list[float]) -> int:
    handle = sim.createPrimitiveShape(sim.primitiveshape_cylinder, [0.012, 0.012, 0.002])
    _set_alias(sim, handle, alias)
    sim.setObjectPosition(handle, [pos[0], pos[1], 0.001], sim.handle_world)
    sim.setShapeColor(handle, "", sim.colorcomponent_ambient_diffuse, color)
    return handle


def _wait_for_sim() -> object:
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient

    last_error: Exception | None = None
    for _ in range(30):
        try:
            client = RemoteAPIClient()
            return client.require("sim")
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError("Could not connect to CoppeliaSim ZeroMQ remote API.") from last_error


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the simplified gripper palletizing scene.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--coppeliasim", default=COPPELIASIM_EXE)
    parser.add_argument("--source-scene", default=SOURCE_SCENE)
    parser.add_argument("--output", default=OUTPUT_SCENE)
    args = parser.parse_args()

    config = load_config(args.config)
    scene_config = config.get("scene", {})
    coppeliasim = config.get("coppeliasim", {})
    pick_position = list(coppeliasim.get("pick_position", PICK))
    place_positions = [list(position) for position in coppeliasim.get("place_positions", PLACE_POSITIONS)]
    coppeliasim_exe = scene_config.get("coppeliasim", args.coppeliasim)
    source_scene_arg = scene_config.get("source_scene", args.source_scene)
    output_scene_arg = scene_config.get("output", args.output)

    source_scene = Path(source_scene_arg)
    if not source_scene.exists():
        raise FileNotFoundError(f"Source scene not found: {source_scene}")

    output_scene = project_path(output_scene_arg)
    output_scene.parent.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen(
        [coppeliasim_exe, str(source_scene)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        sim = _wait_for_sim()
        time.sleep(2)

        gripper_core = sim.getObject("/magician_link_gripper_core_respondable")
        tip = sim.getObject("/magician_link_gripper_core_respondable/magician_link_gripper_core_visual/tip")
        left_joint = sim.getObject("/magician_link_gripper_core_respondable/magician_joint_prismatic_l")
        right_joint = sim.getObject("/magician_link_gripper_core_respondable/magician_joint_prismatic_r")

        base = sim.createDummy(0.018)
        _set_alias(sim, base, "GripperBase")
        sim.setObjectPosition(base, HOME, sim.handle_world)
        grip_center = sim.createDummy(0.012)
        _set_alias(sim, grip_center, "GripCenter")
        sim.setObjectParent(grip_center, base, False)
        sim.setObjectPosition(grip_center, [0.0, 0.0, 0.0], base)

        sim.setObjectParent(gripper_core, base, False)
        sim.setObjectPosition(
            gripper_core,
            [-GRIP_POINT_OFFSET[0], -GRIP_POINT_OFFSET[1], -GRIP_POINT_OFFSET[2]],
            base,
        )
        sim.setObjectOrientation(gripper_core, [0.0, 0.0, 0.0], base)

        _set_alias(sim, tip, "GripperTip")
        _set_alias(sim, left_joint, "GripperJawLeftJoint")
        _set_alias(sim, right_joint, "GripperJawRightJoint")
        sim.setJointPosition(left_joint, 0.010)
        sim.setJointPosition(right_joint, 0.010)

        keep = set(sim.getObjectsInTree(base))
        for h in sim.getObjectsInTree(sim.handle_scene):
            if sim.getObjectAlias(h) in VIEW_OBJECT_ALIASES:
                keep.add(h)
        remove = [h for h in sim.getObjectsInTree(sim.handle_scene) if h not in keep]
        sim.removeObjects(remove)

        _make_box(sim, "PalletBlock", [0.014, 0.014, 0.012], pick_position, [0.86, 0.28, 0.18])
        _make_marker(sim, "PickPoint", pick_position, [0.1, 0.55, 0.95])
        for i, pos in enumerate(place_positions, start=1):
            _make_marker(sim, f"Place_{i:02d}", pos, [0.15, 0.75, 0.35])

        floor = _make_box(
            sim,
            "Floor",
            [0.46, 0.34, 0.004],
            [0.20, -0.12, -0.002],
            [0.88, 0.88, 0.82],
        )
        try:
            camera = sim.getObject("/DefaultCamera")
            sim.setObjectPosition(camera, [0.42, -0.46, 0.38], sim.handle_world)
            sim.setObjectOrientation(
                camera,
                [-1.842614118577297, -0.24141544042915894, 3.0750563222189684],
                sim.handle_world,
            )
        except Exception:
            pass

        sim.saveScene(str(output_scene))
        print(f"Saved scene: {output_scene}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
