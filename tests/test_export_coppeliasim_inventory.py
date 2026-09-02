from __future__ import annotations

from dobot_bgmm_promp.scripts.export_coppeliasim_inventory import (
    collect_object_inventory,
    required_object_paths,
)


class FakeReadOnlySim:
    def __init__(self) -> None:
        self.paths = {"/GripperBase": 1, "/Floor": 2}
        self.aliases = {1: "GripperBase", 2: "Floor"}
        self.positions = {1: [0.0, 0.0, 0.15], 2: [0.2, -0.12, -0.002]}

    def getObject(self, path: str) -> int:
        return self.paths[path]

    def getObjectAlias(self, handle: int) -> str:
        return self.aliases[handle]

    def getObjectPosition(self, handle: int, relative_to: int) -> list[float]:
        assert relative_to == -1
        return self.positions[handle]


def test_inventory_collection_uses_read_methods_only() -> None:
    inventory = collect_object_inventory(
        FakeReadOnlySim(),
        {"GripperBase": "/GripperBase", "Floor": "/Floor", "Missing": "/Missing"},
    )

    assert inventory[0]["actual_alias"] == "GripperBase"
    assert inventory[1]["world_position"] == [0.2, -0.12, -0.002]
    assert inventory[2]["found"] is False


def test_required_paths_include_every_report_object() -> None:
    paths = required_object_paths(
        {
            "coppeliasim": {
                "target_path": "/GripperBase",
                "tip_path": "/GripperBase/GripCenter",
                "left_gripper_joint_path": "/left",
                "right_gripper_joint_path": "/right",
                "block_path": "/PalletBlock",
                "place_positions": [[0.34, -0.16, 0.006]],
            }
        }
    )

    assert tuple(paths) == (
        "GripperBase",
        "GripCenter",
        "GripperJawLeftJoint",
        "GripperJawRightJoint",
        "PalletBlock",
        "PickPoint",
        "Floor",
        "Place_01",
    )
