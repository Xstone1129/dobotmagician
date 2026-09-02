from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from dobot_bgmm_promp.report_figures import (
    collect_report_facts,
    compose_scene_evidence,
    render_algorithm_structures,
    render_playback_state_machine,
    render_project_data_flow,
    update_asset_manifest,
)


def test_default_report_facts_match_current_repository() -> None:
    facts = collect_report_facts("configs/default.yaml")

    assert facts.demo_count == 8
    assert facts.normalized_steps == 150
    assert facts.data_columns == ("x", "y", "z", "gripper")
    assert [item.algorithm_id for item in facts.algorithms] == [
        "gmm_gmr_dmp",
        "inc_gmm_gmr_dmp",
        "gmm_gmr_segmented_dmp",
        "bgmm_gmr_promp",
    ]
    segmented = facts.algorithms[2]
    assert segmented.segment_sizes == (38, 38, 37, 37)
    assert facts.playback.active_algorithm == "bgmm_gmr_promp"
    assert facts.playback.pickup_threshold == pytest.approx(0.65)
    assert facts.playback.release_threshold == pytest.approx(0.35)
    assert facts.playback.endpoint_label == "播放至模型轨迹末端"


def test_diagrams_render_traceable_png_svg_and_manifest(tmp_path: Path) -> None:
    facts = collect_report_facts("configs/default.yaml")
    records = []
    records.extend(render_project_data_flow(facts, tmp_path / "figure-2-1"))
    records.extend(render_playback_state_machine(facts, tmp_path / "figure-2-3"))
    records.extend(render_algorithm_structures(facts, tmp_path / "figure-3-1"))
    update_asset_manifest(records, tmp_path / "manifest.json")

    assert len(records) == 6
    for record in records[::2]:
        assert Path(record.output.path).exists()
        assert record.width_px is not None and record.width_px >= 1654
        assert record.height_px is not None and record.height_px > 600
        assert record.dpi_x == pytest.approx(300, abs=1)
        assert record.source_files
        assert record.source_symbols
    svg_text = (tmp_path / "figure-2-3.svg").read_text(encoding="utf-8")
    assert "播放至模型轨迹末端" in svg_text
    assert "返回 HOME" not in svg_text
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert {item["figure_id"] for item in manifest["assets"]} == {"2-1", "2-3", "3-1"}


def test_scene_composition_requires_real_image_and_complete_inventory(tmp_path: Path) -> None:
    scene = tmp_path / "scene.png"
    Image.new("RGB", (1600, 900), "#dde7ef").save(scene)
    inventory = tmp_path / "inventory.json"
    names = (
        "GripperBase",
        "GripCenter",
        "GripperJawLeftJoint",
        "GripperJawRightJoint",
        "PalletBlock",
        "PickPoint",
        "Place_01",
        "Floor",
    )
    inventory.write_text(
        json.dumps(
            {
                "capture_mode": "read-only Remote API object lookup",
                "objects": [
                    {
                        "expected_alias": name,
                        "configured_path": f"/{name}",
                        "found": True,
                        "actual_alias": name,
                        "world_position": [0.0, 0.0, 0.0],
                    }
                    for name in names
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    record = compose_scene_evidence(scene, inventory, tmp_path / "figure-2-2.png")
    assert record.figure_id == "2-2"
    assert record.width_px is not None and record.width_px >= 1654
    assert record.dpi_x == pytest.approx(300, abs=1)

    payload = json.loads(inventory.read_text(encoding="utf-8"))
    payload["objects"][0]["found"] = False
    inventory.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required"):
        compose_scene_evidence(scene, inventory, tmp_path / "rejected.png")

