from __future__ import annotations

import argparse
import csv
from collections.abc import Callable
from pathlib import Path

import numpy as np

from dobot_algorithms.movement_primitives import (
    BGMMGMRProMP,
    GMMGMRDMP,
    GMMGMRSegmentedDMP,
    IncGMMGMRDMP,
)
from dobot_algorithms.data_io import load_config, load_demonstrations, project_path, save_model
from dobot_algorithms.evaluation import evaluate_reference_trajectory, format_trajectory_metrics
from dobot_algorithms.trajectory_selection import normalize_demo
from dobot_algorithms.visualization import (
    plot_gmm_components,
    plot_gmm_comparison,
    plot_gmr_regression,
    plot_model_comparison,
    plot_trajectories,
)


ALGORITHM_BUILDERS: dict[str, tuple[str, Callable[..., object]]] = {
    "gmm_gmr_dmp": ("GMM+GMR+DMP", GMMGMRDMP),
    "inc_gmm_gmr_dmp": ("Inc-GMM+GMR+DMP", IncGMMGMRDMP),
    "gmm_gmr_segmented_dmp": ("GMM+GMR+Segmented DMP", GMMGMRSegmentedDMP),
    "bgmm_gmr_promp": ("BGMM+GMR+ProMP", BGMMGMRProMP),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Learn GMM/GMR movement primitive models.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument(
        "--algorithm",
        choices=[*ALGORITHM_BUILDERS, "compare"],
        help="Override model.algorithm without editing the YAML configuration.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    demos = load_demonstrations(
        config["data"]["demos_dir"],
        time_column=config["data"]["time_column"],
        coordinate_columns=config["data"]["coordinate_columns"],
        gripper_column=config["data"].get("gripper_column"),
    )

    algorithm = args.algorithm or config["model"].get("algorithm", "compare")
    if algorithm != "compare" and algorithm not in ALGORITHM_BUILDERS:
        options = ", ".join([*ALGORITHM_BUILDERS, "compare"])
        raise ValueError(f"model.algorithm must be one of: {options}")

    algorithm_names = list(ALGORITHM_BUILDERS) if algorithm == "compare" else [algorithm]
    trained_models = {}
    metric_rows = []
    stage_metric_rows = []
    gmm_mixtures = {}
    gmr_trajectories = {}
    plot_config = config.get("plot", {})

    for algorithm_name in algorithm_names:
        label, builder = ALGORITHM_BUILDERS[algorithm_name]
        model_config = config[algorithm_name]
        model = builder(**model_config.get("params", {})).fit(demos)
        save_model(model, model_config["output_path"])
        trained_models[algorithm_name] = model
        gmm_mixtures[label] = model.mixture_parameters()
        gmr_trajectories[label] = model.gmr_trajectory_.copy()

        samples = model.sample_trajectories(min(8, len(demos)))
        output_path = model_config.get(
            "plot_output_path",
            plot_config.get(f"{algorithm_name}_output_path", plot_config.get("output_path")),
        )
        plot_trajectories(
            demos,
            model.mean_trajectory(),
            samples,
            project_path(output_path),
            title=f"{label}: demonstrations vs learned trajectory",
        )
        _save_intermediate_figures(
            model,
            demos,
            algorithm_name,
            label,
            project_path(plot_config.get("intermediate_output_dir", "models/intermediate")),
        )
        print(f"Saved {label} model: {model_config['output_path']}")
        print(f"Saved {label} plot: {output_path}")
        metrics = evaluate_reference_trajectory(demos, model.mean_trajectory())
        gmr_metrics = evaluate_reference_trajectory(demos, model.gmr_trajectory_)
        stage_metric_rows.append(_stage_metrics_row(algorithm_name, label, "GMR", gmr_metrics))
        stage_metric_rows.append(_stage_metrics_row(algorithm_name, label, "Primitive", metrics))
        print(format_trajectory_metrics(f"{label} mean", metrics))
        metric_rows.append(
            _metrics_row(
                algorithm_name=algorithm_name,
                label=label,
                metrics=metrics,
                model_path=model_config["output_path"],
                plot_path=output_path,
            )
        )

    if algorithm == "compare":
        place_positions = config.get("plot", {}).get("place_positions", [[0.08, 0.16, 0.03]])
        comparison = {
            label: model.trajectory_for_place(1, place_positions)
            for label, model in trained_models.items()
        }
        output_path = plot_config.get("comparison_output_path", "models/trajectory_comparison.png")
        plot_model_comparison(
            demos,
            comparison,
            project_path(output_path),
            title="Four GMM-GMR movement primitive algorithms",
        )
        print(f"Saved comparison plot: {output_path}")
        points = np.vstack([np.column_stack([np.linspace(0.0, 1.0, len(demo)), demo]) for demo in demos])
        plot_gmm_comparison(
            points, gmm_mixtures,
            project_path(plot_config.get("gmm_comparison_output_path", "models/gmm_comparison.png")),
        )
        plot_model_comparison(
            demos, gmr_trajectories,
            project_path(plot_config.get("gmr_comparison_output_path", "models/gmr_comparison.png")),
            title="GMR regression comparison",
        )

    csv_path = project_path("models/algorithm_metrics.csv")
    md_path = project_path("models/algorithm_metrics.md")
    _write_metric_tables(metric_rows, csv_path, md_path)
    _write_stage_metric_tables(
        stage_metric_rows,
        project_path(plot_config.get("stage_metrics_csv", "models/stage_metrics.csv")),
        project_path(plot_config.get("stage_metrics_md", "models/stage_metrics.md")),
    )
    print(f"Saved metrics table: {csv_path}")
    print(f"Saved metrics summary: {md_path}")


def _metrics_row(
    *,
    algorithm_name: str,
    label: str,
    metrics,
    model_path: str,
    plot_path: str,
) -> dict[str, str]:
    dim_names = ["X", "Y", "Z", "Gripper"]
    row = {
        "Algorithm ID": algorithm_name,
        "Algorithm": label,
        "Pearson Mean": _format_number(metrics.mean_pearson),
        "RMSE Mean": _format_number(metrics.mean_rmse),
        "Model File": model_path,
        "Trajectory Plot": plot_path,
    }
    for index, dim in enumerate(dim_names):
        row[f"Pearson {dim}"] = _format_number(metrics.pearson[index])
        row[f"RMSE {dim}"] = _format_number(metrics.rmse[index])
    return row


def _stage_metrics_row(algorithm_name: str, label: str, stage: str, metrics) -> dict[str, str]:
    row = _metrics_row(
        algorithm_name=algorithm_name, label=label, metrics=metrics,
        model_path="", plot_path="",
    )
    row["Stage"] = stage
    return row


def _write_stage_metric_tables(rows: list[dict[str, str]], csv_path: Path, md_path: Path) -> None:
    if not rows:
        return
    fieldnames = ["Stage", "Algorithm ID", "Algorithm", "Pearson Mean", "RMSE Mean",
                  "Pearson X", "Pearson Y", "Pearson Z", "Pearson Gripper",
                  "RMSE X", "RMSE Y", "RMSE Z", "RMSE Gripper", "Model File", "Trajectory Plot"]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# Stage Metrics", "", "| Stage | Algorithm | Pearson Mean | RMSE Mean |", "|---|---|---:|---:|"]
    lines.extend(f"| {r['Stage']} | {r['Algorithm']} | {r['Pearson Mean']} | {r['RMSE Mean']} |" for r in rows)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _save_intermediate_figures(model, demos, algorithm_name: str, label: str, output_dir: Path) -> None:
    """Persist the observable GMM and GMR stages, not only the final primitive."""

    if model.gmr_trajectory_ is None:
        return
    means, covariances, weights = model.mixture_parameters()
    n_steps = model.gmr_trajectory_.shape[0]
    phase = np.linspace(0.0, 1.0, n_steps)
    normalized = [normalize_demo(demo, n_steps) for demo in demos]
    points = np.vstack([np.column_stack([phase, demo]) for demo in normalized])
    plot_gmm_components(
        points,
        means,
        covariances,
        weights,
        output_dir / f"{algorithm_name}_gmm.png",
        title=f"{label}: fitted GMM components before GMR",
    )
    plot_gmr_regression(
        demos,
        model.gmr_trajectory_,
        output_dir / f"{algorithm_name}_gmr.png",
        title=f"{label}: GMR conditional mean before movement primitive",
    )


def _write_metric_tables(rows: list[dict[str, str]], csv_path: Path, md_path: Path) -> None:
    if not rows:
        return

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Algorithm ID",
        "Algorithm",
        "Pearson X",
        "Pearson Y",
        "Pearson Z",
        "Pearson Gripper",
        "Pearson Mean",
        "RMSE X",
        "RMSE Y",
        "RMSE Z",
        "RMSE Gripper",
        "RMSE Mean",
        "Model File",
        "Trajectory Plot",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Algorithm Metrics",
        "",
        "| Algorithm | Pearson Mean | RMSE Mean | Pearson X | Pearson Y | Pearson Z | Pearson Gripper | RMSE X | RMSE Y | RMSE Z | RMSE Gripper |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {Algorithm} | {Pearson Mean} | {RMSE Mean} | {Pearson X} | {Pearson Y} | "
            "{Pearson Z} | {Pearson Gripper} | {RMSE X} | {RMSE Y} | {RMSE Z} | "
            "{RMSE Gripper} |".format(**row)
        )
    lines.extend(
        [
            "",
            "Generated by `python -m dobot_algorithms.scripts.train_models --config configs/default.yaml`.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def _format_number(value: float) -> str:
    return "nan" if value != value else f"{value:.4f}"


if __name__ == "__main__":
    main()
