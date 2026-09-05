"""Tune on demonstration-level folds; keep the last two demos out of selection."""
from __future__ import annotations

import argparse
import itertools
import json
import warnings
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning

from dobot_algorithms.data_io import load_config, load_demonstrations
from dobot_algorithms.scripts.train_models import ALGORITHM_BUILDERS
from dobot_algorithms.trajectory_selection import normalize_demo


def tracking_metrics(demos, trajectory):
    stack = np.stack([normalize_demo(d, len(trajectory)) for d in demos])
    error = trajectory[None] - stack
    low = stack[:, :, 2] <= 0.05
    endpoint = np.linalg.norm(error[:, [0, -1], :3], axis=2)
    xyz = float(np.sqrt(np.mean(error[:, :, :3] ** 2)))
    contact = float(np.sqrt(np.mean(error[:, :, :3][low] ** 2))) if low.any() else xyz
    return {
        "xyz_rmse_mm": xyz * 1000,
        "z_rmse_mm": float(np.sqrt(np.mean(error[:, :, 2] ** 2))) * 1000,
        "contact_xyz_rmse_mm": contact * 1000,
        "endpoint_max_mm": float(endpoint.max()) * 1000,
        "gripper_rmse": float(np.sqrt(np.mean(error[:, :, 3] ** 2))),
        "score_mm": (xyz + 0.5 * contact + 0.25 * endpoint.max()) * 1000,
    }


def candidates(key, base):
    common = dict(base, mixture_max_iter=1000, mixture_n_init=2)
    if key == "bgmm_gmr_promp":
        for components, prior, basis_width in itertools.product(
            [8, 12, 20, 32], [0.01, 0.1], [(50, 0.02), (80, 0.012)]
        ):
            yield dict(common, n_components=components,
                       bgmm_mean_precision_prior=0.001,
                       bgmm_covariance_prior_scale=prior,
                       promp_basis=basis_width[0], promp_basis_width=basis_width[1],
                       promp_constrain_endpoints=True)
    elif key == "inc_gmm_gmr_dmp":
        for lam, basis in itertools.product([0.05, 0.15, 0.5, 1.5, 5.0], [80, 140]):
            yield dict(common, inc_lam=lam, dmp_basis=basis, dmp_alpha_s=1.0,
                       dmp_alpha_z=50.0, dmp_beta_z=12.5)
    elif key == "gmm_gmr_segmented_dmp":
        for components, segments, basis in itertools.product([12, 24, 40], [2, 4, 6], [25, 50]):
            yield dict(common, n_components=components, n_segments=segments,
                       dmp_basis=basis, dmp_alpha_s=1.0,
                       dmp_alpha_z=50.0, dmp_beta_z=12.5)
    else:
        for components, basis in itertools.product([8, 12, 24, 40, 60], [80, 140]):
            yield dict(common, n_components=components, dmp_basis=basis,
                       dmp_alpha_s=1.0, dmp_alpha_z=50.0, dmp_beta_z=12.5)


def fit(builder, params, demos):
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model = builder(**params).fit(demos)
    if not np.isfinite(model.mean_trajectory()).all():
        raise ValueError("Non-finite trajectory")
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/suction_arm.yaml")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    demos = load_demonstrations(**config["data"])
    if len(demos) < 8:
        raise ValueError("Need at least eight demonstrations for this split")
    development, held_out = demos[:-2], demos[-2:]
    folds = np.array_split(np.arange(len(development)), 3)
    report = {
        "config": args.config,
        "selection": "Three folds on all but the last two CSVs; last two are held out.",
        "objective": "XYZ RMSE + 0.5 * low-height XYZ RMSE + 0.25 * max endpoint error; all mm.",
        "gripper_limit": 0.12,
        "algorithms": {},
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    for key, (_, builder) in ALGORITHM_BUILDERS.items():
        rows = []
        for index, params in enumerate(candidates(key, config[key]["params"])):
            try:
                metrics = []
                for validation_ids in folds:
                    train = [d for i, d in enumerate(development) if i not in validation_ids]
                    validation = [development[i] for i in validation_ids]
                    model = fit(builder, params, train)
                    metrics.append(tracking_metrics(validation, model.mean_trajectory()))
                average = {name: float(np.mean([m[name] for m in metrics])) for name in metrics[0]}
                eligible = max(m["gripper_rmse"] for m in metrics) <= report["gripper_limit"]
                rows.append({"params": params, "cv": average, "eligible": eligible})
                print(key, index, "score_mm", round(average["score_mm"], 3),
                      "gripper", round(average["gripper_rmse"], 4), "eligible", eligible, flush=True)
            except (ValueError, np.linalg.LinAlgError, ConvergenceWarning) as error:
                print(key, index, type(error).__name__, str(error), flush=True)
        eligible = [row for row in rows if row["eligible"]]
        if not eligible:
            raise RuntimeError(f"No converged candidate meets the gripper threshold for {key}")
        best = min(eligible, key=lambda row: row["cv"]["score_mm"])
        model = fit(builder, best["params"], development)
        best["held_out"] = tracking_metrics(held_out, model.mean_trajectory())
        report["algorithms"][key] = {"best": best, "candidates": rows}
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("SELECTED", key, json.dumps(best), flush=True)


if __name__ == "__main__":
    main()
