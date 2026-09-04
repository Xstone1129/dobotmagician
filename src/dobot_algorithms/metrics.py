from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dobot_algorithms.model_selection import normalize_demo


@dataclass(frozen=True)
class TrajectoryMetrics:
    """Per-dimension reconstruction metrics against the demonstration set."""

    pearson: np.ndarray
    rmse: np.ndarray

    @property
    def mean_pearson(self) -> float:
        return float(np.nanmean(self.pearson))

    @property
    def mean_rmse(self) -> float:
        return float(np.mean(self.rmse))


def evaluate_reference_trajectory(
    demos: list[np.ndarray],
    reference: np.ndarray,
) -> TrajectoryMetrics:
    """Compare a generated trajectory with each demo after temporal normalization."""

    if not demos:
        raise ValueError("At least one demonstration is required for evaluation.")

    reference = np.asarray(reference, dtype=float)
    if reference.ndim != 2:
        raise ValueError("Reference trajectory must be shaped [time, dimension].")

    normalized = [normalize_demo(demo, reference.shape[0]) for demo in demos]
    if any(demo.shape[1] != reference.shape[1] for demo in normalized):
        raise ValueError("Demonstrations and reference trajectory must have the same dimensions.")

    pearson_values = []
    rmse_values = []
    for demo in normalized:
        pearson_values.append(_pearson_by_dimension(demo, reference))
        rmse_values.append(np.sqrt(np.mean((demo - reference) ** 2, axis=0)))

    return TrajectoryMetrics(
        pearson=_nanmean_by_dimension(np.vstack(pearson_values)),
        rmse=np.mean(np.vstack(rmse_values), axis=0),
    )


def format_trajectory_metrics(label: str, metrics: TrajectoryMetrics) -> str:
    dim_labels = ["X", "Y", "Z", "Gripper"]
    dim_labels.extend(f"D{i + 1}" for i in range(max(0, len(metrics.rmse) - len(dim_labels))))
    dim_labels = dim_labels[: len(metrics.rmse)]

    pearson = ", ".join(
        f"{dim}={_format_float(value)}" for dim, value in zip(dim_labels, metrics.pearson)
    )
    rmse = ", ".join(f"{dim}={value:.4f}" for dim, value in zip(dim_labels, metrics.rmse))
    return (
        f"{label} trajectory metrics:\n"
        f"  Pearson: {pearson} (mean={metrics.mean_pearson:.4f})\n"
        f"  RMSE: {rmse} (mean={metrics.mean_rmse:.4f})"
    )


def _pearson_by_dimension(actual: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    values = []
    for dim in range(actual.shape[1]):
        a = actual[:, dim]
        p = predicted[:, dim]
        if np.std(a) < 1e-12 or np.std(p) < 1e-12:
            values.append(np.nan)
        else:
            values.append(float(np.corrcoef(a, p)[0, 1]))
    return np.asarray(values, dtype=float)


def _nanmean_by_dimension(values: np.ndarray) -> np.ndarray:
    means = []
    for dim in range(values.shape[1]):
        finite = values[:, dim][~np.isnan(values[:, dim])]
        means.append(float(np.mean(finite)) if finite.size else np.nan)
    return np.asarray(means, dtype=float)


def _format_float(value: float) -> str:
    if np.isnan(value):
        return "nan"
    return f"{value:.4f}"
