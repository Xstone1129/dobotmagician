from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import json
from pathlib import Path

from dobot_bgmm_promp.io import load_config, project_path


def required_object_paths(config: dict) -> dict[str, str]:
    sim = config["coppeliasim"]
    paths = {
        "GripperBase": sim["target_path"],
        "GripCenter": sim["tip_path"],
        "GripperJawLeftJoint": sim["left_gripper_joint_path"],
        "GripperJawRightJoint": sim["right_gripper_joint_path"],
        "PalletBlock": sim["block_path"],
        "PickPoint": "/PickPoint",
        "Floor": "/Floor",
    }
    for index, _ in enumerate(sim["place_positions"], start=1):
        paths[f"Place_{index:02d}"] = f"/Place_{index:02d}"
    return paths


def collect_object_inventory(sim, paths: Mapping[str, str]) -> list[dict]:
    inventory = []
    for expected_alias, object_path in paths.items():
        try:
            handle = sim.getObject(object_path)
            inventory.append(
                {
                    "expected_alias": expected_alias,
                    "configured_path": object_path,
                    "found": True,
                    "actual_alias": str(sim.getObjectAlias(handle)).lstrip("/"),
                    "world_position": [float(value) for value in sim.getObjectPosition(handle, -1)],
                }
            )
        except Exception as exc:
            inventory.append(
                {
                    "expected_alias": expected_alias,
                    "configured_path": object_path,
                    "found": False,
                    "error_type": type(exc).__name__,
                }
            )
    return inventory


def connect_read_only(config: dict):
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient

    sim_config = config["coppeliasim"]
    client = RemoteAPIClient(host=sim_config["host"], port=int(sim_config["port"]))
    return client.require("sim")


def export_inventory(config_path: str | Path, output_path: str | Path) -> dict:
    config = load_config(config_path)
    objects = collect_object_inventory(connect_read_only(config), required_object_paths(config))
    payload = {
        "capture_mode": "read-only Remote API object lookup",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "host": config["coppeliasim"]["host"],
        "port": int(config["coppeliasim"]["port"]),
        "objects": objects,
    }
    output = project_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a read-only CoppeliaSim object inventory.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--output", default="reports/evidence/coppeliasim/object-inventory.json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = export_inventory(args.config, args.output)
    missing = [item["expected_alias"] for item in payload["objects"] if not item["found"]]
    if missing:
        print("Missing required objects: " + ", ".join(missing))
        return 2
    print(f"Exported read-only inventory: {project_path(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
