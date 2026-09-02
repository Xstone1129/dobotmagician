from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from dobot_bgmm_promp.report_figures import (
    collect_report_facts,
    compose_scene_evidence,
    render_algorithm_structures,
    render_playback_state_machine,
    render_project_data_flow,
    update_asset_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate traceable report evidence figures.")
    parser.add_argument("--font-path")
    parser.add_argument("--manifest", default="reports/figures/manifest.json")
    subparsers = parser.add_subparsers(dest="command", required=True)
    diagrams = subparsers.add_parser("diagrams")
    diagrams.add_argument("--config", default="configs/default.yaml")
    diagrams.add_argument("--output-dir", default="reports/figures")
    scene = subparsers.add_parser("scene")
    scene.add_argument("--scene-image", required=True)
    scene.add_argument("--inventory", required=True)
    scene.add_argument("--output", default="reports/figures/figure-2-2-coppeliasim-scene-and-objects.png")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    records = []
    if args.command == "diagrams":
        facts = collect_report_facts(args.config)
        output_dir = Path(args.output_dir)
        records.extend(render_project_data_flow(facts, output_dir / "figure-2-1-project-data-flow", font_path=args.font_path))
        records.extend(render_playback_state_machine(facts, output_dir / "figure-2-3-playback-state-machine", font_path=args.font_path))
        records.extend(render_algorithm_structures(facts, output_dir / "figure-3-1-algorithm-structures", font_path=args.font_path))
    else:
        records.append(compose_scene_evidence(args.scene_image, args.inventory, args.output, font_path=args.font_path))
    update_asset_manifest(records, args.manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
