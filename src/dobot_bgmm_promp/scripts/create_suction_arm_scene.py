"""Build a full Dobot Magician suction-cup scene without replacing the gripper demo."""

from __future__ import annotations

import argparse
import math
import subprocess
import time
from pathlib import Path

from dobot_bgmm_promp.io import load_config, project_path


COPPELIASIM_EXE = r"C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu\coppeliaSim.exe"
SOURCE_SCENE = r"C:\Users\Administrator\Desktop\dobotmagician.before_ik_backup.ttt"
SUCTION_MODEL = r"C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu\models\components\grippers\suction pad.ttm"
OUTPUT_SCENE = "scenes/dobot_magician_suction.ttt"

FOLLOW_SCRIPT = r'''
function sysCall_init()
    target=sim.getObject('/target')
    j1=sim.getObject('/magician_joint_1')
    j2=sim.getObject('/magician_joint_2')
    j3=sim.getObject('/magician_joint_3')
    j4=sim.getObject('/magician_joint_4')
end

function sysCall_actuation()
    p=sim.getObjectPosition(target,-1)
    dx=p[1]+0.08315
    dy=p[2]
    dz=p[3]-0.13155
    radius=math.sqrt(dx*dx+dy*dy)
    sim.setJointPosition(j1, math.atan2(dy,dx))
    sim.setJointPosition(j2, math.max(-1.25, math.min(1.25,(radius-0.20)*7.0)))
    sim.setJointPosition(j3, math.max(-1.25, math.min(1.25,(dz-(-0.02))*8.0)))
    sim.setJointPosition(j4, 0)
end
'''


def _set_alias(sim, handle: int, alias: str) -> None:
    sim.setObjectAlias(handle, alias)


def _box(sim, alias: str, size: list[float], pos: list[float], color: list[float]) -> int:
    handle = sim.createPrimitiveShape(sim.primitiveshape_cuboid, size)
    _set_alias(sim, handle, alias)
    sim.setObjectPosition(handle, pos, sim.handle_world)
    sim.setShapeColor(handle, "", sim.colorcomponent_ambient_diffuse, color)
    return handle


def _marker(sim, alias: str, pos: list[float], color: list[float]) -> int:
    handle = sim.createPrimitiveShape(sim.primitiveshape_cylinder, [0.018, 0.018, 0.003])
    _set_alias(sim, handle, alias)
    sim.setObjectPosition(handle, [pos[0], pos[1], 0.0015], sim.handle_world)
    sim.setShapeColor(handle, "", sim.colorcomponent_ambient_diffuse, color)
    return handle


def _set_overview_camera(sim) -> None:
    """Aim the saved scene camera at the complete pick-and-place workspace."""

    camera = sim.getObject("/DefaultCamera")
    position = [1.10, -1.45, 1.05]
    focus = [-0.02, 0.08, 0.08]
    forward = [focus[index] - position[index] for index in range(3)]
    length = math.sqrt(sum(value * value for value in forward))
    forward = [value / length for value in forward]
    # CoppeliaSim camera looks along local +Z. Construct X/Y axes around it.
    right = [-forward[1], forward[0], 0.0]
    right_length = math.hypot(right[0], right[1])
    right = [value / right_length for value in right]
    up = [
        forward[1] * right[2] - forward[2] * right[1],
        forward[2] * right[0] - forward[0] * right[2],
        forward[0] * right[1] - forward[1] * right[0],
    ]
    sim.setObjectMatrix(
        camera,
        [
            right[0], up[0], forward[0], position[0],
            right[1], up[1], forward[1], position[1],
            right[2], up[2], forward[2], position[2],
        ],
        sim.handle_world,
    )


def _wait_for_sim() -> object:
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient

    last_error: Exception | None = None
    for _ in range(30):
        try:
            return RemoteAPIClient().require("sim")
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError("Could not connect to CoppeliaSim ZeroMQ remote API.") from last_error


def _make_kinematic_subtree(sim, root: int) -> None:
    """Prevent physics from detaching visual components during simulation."""

    for handle in sim.getObjectsInTree(root):
        if sim.getObjectType(handle) == sim.object_shape_type:
            sim.setObjectInt32Param(handle, sim.shapeintparam_static, 1)
            sim.setObjectInt32Param(handle, sim.shapeintparam_respondable, 0)


def _attach_follow_script(sim) -> None:
    """Attach the one authoritative target-follow controller."""

    script = sim.createScript(sim.scripttype_simulation, FOLLOW_SCRIPT, 0, "lua")
    _set_alias(sim, script, "DobotTargetFollow")
    sim.setObjectParent(script, sim.getObject("/magician_root_link_visual"), False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a full Dobot Magician suction-cup scene.")
    parser.add_argument("--config", default="configs/suction_arm.yaml")
    parser.add_argument("--coppeliasim", default=COPPELIASIM_EXE)
    parser.add_argument("--source-scene", default=SOURCE_SCENE)
    parser.add_argument("--suction-model", default=SUCTION_MODEL)
    parser.add_argument("--output", default=OUTPUT_SCENE)
    args = parser.parse_args()

    config = load_config(args.config)
    scene = config.get("scene", {})
    sim_config = config["coppeliasim"]
    source = Path(scene.get("source_scene", args.source_scene))
    suction_model = Path(scene.get("suction_model", args.suction_model))
    output = project_path(scene.get("output", args.output))
    if not source.exists() or not suction_model.exists():
        raise FileNotFoundError("The Dobot source scene or CoppeliaSim suction-pad model is missing.")

    proc = subprocess.Popen([scene.get("coppeliasim", args.coppeliasim), str(source)])
    try:
        sim = _wait_for_sim()
        time.sleep(1)
        old_tip = sim.getObject("/tip")
        _make_kinematic_subtree(sim, sim.getObject("/magician_root_link_visual"))
        # Keep `tip`: the source scene's IK script drives the joint chain through
        # it. Removing the gripper subtree also removes that IK endpoint, which
        # is why a detached cup can appear to fly while the arm stays still.
        gripper_root = sim.getObject("/magician_link_gripper_core_respondable")
        for handle in sim.getObjectsInTree(gripper_root):
            if sim.getObjectType(handle) == sim.object_shape_type:
                sim.setObjectInt32Param(handle, sim.objintparam_visibility_layer, 0)
        suction = sim.loadModel(str(suction_model))
        _set_alias(sim, suction, "SuctionCup")
        sim.setObjectParent(suction, old_tip, False)
        sim.setObjectPosition(suction, [0.0, 0.0, 0.0], old_tip)
        sim.setObjectOrientation(suction, [0.0, 0.0, 0.0], old_tip)
        # The supplied suction-pad model is a dynamic assembly. It must be
        # kinematic when mounted on the Dobot tip, otherwise physics detaches
        # it as soon as the simulation starts.
        _make_kinematic_subtree(sim, suction)
        suction_tip = sim.getObject("/SuctionCup/Link")
        _set_alias(sim, suction_tip, "SuctionTip")
        _attach_follow_script(sim)

        pick = list(sim_config["pick_position"])
        place = list(sim_config["place_positions"][0])
        _box(sim, "Worktable", [0.72, 0.62, 0.04], [-0.05, 0.0, -0.02], [0.74, 0.76, 0.78])
        _box(sim, "RearPickStation", [0.082, 0.082, 0.012], [pick[0], pick[1], 0.006], [0.18, 0.42, 0.92])
        _box(sim, "OppositePlaceTray", [0.092, 0.092, 0.012], [place[0], place[1], 0.006], [0.16, 0.70, 0.34])
        _box(sim, "PalletBlock", [0.024, 0.024, 0.018], [pick[0], pick[1], 0.021], [0.92, 0.12, 0.08])
        _marker(sim, "RearPickPoint", pick, [0.12, 0.35, 0.92])
        _marker(sim, "OppositePlacePoint", place, [0.12, 0.68, 0.28])
        _set_overview_camera(sim)
        output.parent.mkdir(parents=True, exist_ok=True)
        sim.saveScene(str(output))
        print(f"Saved full Dobot suction scene: {output}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
