from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse


def plot_trajectories(
    demos: list[np.ndarray],
    mean_trajectory: np.ndarray,
    samples: np.ndarray | None,
    output_path: str | Path,
    *,
    title: str = "Learned trajectory",
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    dims = mean_trajectory.shape[1]
    dim_names = _dimension_names(dims)
    fig, axes = plt.subplots(dims, 1, figsize=(10, max(3.8, 2.5 * dims)), sharex=True)
    if dims == 1:
        axes = [axes]

    phase = np.linspace(0.0, 1.0, mean_trajectory.shape[0])
    for dim, axis in enumerate(axes):
        for index, demo in enumerate(demos):
            demo_phase = np.linspace(0.0, 1.0, demo.shape[0])
            axis.plot(
                demo_phase,
                demo[:, dim],
                color="0.75",
                linewidth=1,
                label="Demonstrations" if index == 0 else None,
            )
        if samples is not None:
            for index, sample in enumerate(samples):
                axis.plot(
                    phase,
                    sample[:, dim],
                    color="#4c78a8",
                    alpha=0.25,
                    linewidth=1,
                    label="Generated samples" if index == 0 else None,
                )
        axis.plot(phase, mean_trajectory[:, dim], color="#d62728", linewidth=2.2, label="Mean output")
        axis.set_title(dim_names[dim], loc="left", fontsize=10)
        axis.set_ylabel(_dimension_ylabel(dim_names[dim]))
        axis.grid(True, alpha=0.25)

    axes[0].legend(loc="best")
    axes[-1].set_xlabel("normalized time")
    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_model_comparison(
    demos: list[np.ndarray],
    trajectories: dict[str, np.ndarray],
    output_path: str | Path,
    *,
    title: str = "Algorithm comparison",
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    first = next(iter(trajectories.values()))
    dims = first.shape[1]
    dim_names = _dimension_names(dims)
    fig, axes = plt.subplots(dims, 1, figsize=(10, max(3.8, 2.5 * dims)), sharex=True)
    if dims == 1:
        axes = [axes]

    colors = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd"]
    phase = np.linspace(0.0, 1.0, first.shape[0])
    for dim, axis in enumerate(axes):
        for index, demo in enumerate(demos):
            demo_phase = np.linspace(0.0, 1.0, demo.shape[0])
            axis.plot(
                demo_phase,
                demo[:, dim],
                color="0.80",
                linewidth=1,
                label="Demonstrations" if index == 0 else None,
            )
        for (label, trajectory), color in zip(trajectories.items(), colors):
            axis.plot(phase, trajectory[:, dim], color=color, linewidth=2, label=label)
        axis.set_title(dim_names[dim], loc="left", fontsize=10)
        axis.set_ylabel(_dimension_ylabel(dim_names[dim]))
        axis.grid(True, alpha=0.25)

    axes[0].legend(loc="best")
    axes[-1].set_xlabel("normalized time")
    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_gmm_components(
    points: np.ndarray,
    means: np.ndarray,
    covariances: np.ndarray,
    weights: np.ndarray,
    output_path: str | Path,
    *,
    title: str,
) -> None:
    """Save the fitted mixture distribution before GMR or primitive rollout."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    points = np.asarray(points, dtype=float)
    means = np.asarray(means, dtype=float)
    covariances = np.asarray(covariances, dtype=float)
    weights = np.asarray(weights, dtype=float)
    dims = min(3, points.shape[1] - 1)
    fig, axes = plt.subplots(dims, 1, figsize=(10, max(3.8, 2.7 * dims)), sharex=True)
    if dims == 1:
        axes = [axes]
    colors = plt.cm.tab10(np.arange(len(means)) % 10)
    for dim, axis in enumerate(axes, start=1):
        axis.scatter(points[:, 0], points[:, dim], s=5, alpha=0.13, color="#4c566a", label="demo points")
        for index, (mean, covariance, weight) in enumerate(zip(means, covariances, weights)):
            _add_component_ellipse(axis, mean, covariance, dim, colors[index], float(weight))
        axis.set_ylabel(_dimension_ylabel(_dimension_names(points.shape[1] - 1)[dim - 1]))
        axis.grid(True, alpha=0.25)
    axes[0].legend(loc="best", fontsize=8)
    axes[-1].set_xlabel("normalized time")
    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_gmr_regression(
    demos: list[np.ndarray],
    gmr_trajectory: np.ndarray,
    output_path: str | Path,
    *,
    title: str,
) -> None:
    """Save the conditional GMR mean before DMP or ProMP reconstruction."""

    plot_trajectories(demos, gmr_trajectory, None, output_path, title=title)


def plot_gmm_comparison(
    points: np.ndarray,
    mixtures: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]],
    output_path: str | Path,
    *,
    title: str = "GMM layer comparison",
) -> None:
    """Compare fitted mixture component centers for all algorithms."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    dims = min(3, points.shape[1] - 1)
    fig, axes = plt.subplots(dims, 1, figsize=(10, max(3.8, 2.7 * dims)), sharex=True)
    if dims == 1:
        axes = [axes]
    colors = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd"]
    for dim, axis in enumerate(axes, start=1):
        axis.scatter(points[:, 0], points[:, dim], s=5, alpha=0.10, color="0.55", label="demo points")
        for (label, (means, _covariances, _weights)), color in zip(mixtures.items(), colors):
            order = np.argsort(means[:, 0])
            axis.plot(means[order, 0], means[order, dim], "o-", ms=3, lw=1.5, color=color, label=label)
        axis.set_ylabel(_dimension_ylabel(_dimension_names(points.shape[1] - 1)[dim - 1]))
        axis.grid(True, alpha=0.25)
    axes[0].legend(loc="best", fontsize=8)
    axes[-1].set_xlabel("normalized time")
    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(output, dpi=160)
    plt.close(fig)


def _add_component_ellipse(axis, mean, covariance, output_dim: int, color, weight: float) -> None:
    covariance_2d = np.asarray(covariance)[np.ix_([0, output_dim], [0, output_dim])]
    values, vectors = np.linalg.eigh(covariance_2d)
    values = np.maximum(values, 0.0)
    angle = np.degrees(np.arctan2(vectors[1, 1], vectors[0, 1]))
    ellipse = Ellipse(
        xy=(mean[0], mean[output_dim]),
        width=4.0 * np.sqrt(values[0]),
        height=4.0 * np.sqrt(values[1]),
        angle=angle,
        facecolor="none",
        edgecolor=color,
        linewidth=1.3,
        alpha=max(0.25, min(0.9, weight * 4.0)),
    )
    axis.add_patch(ellipse)


def _dimension_names(dims: int) -> list[str]:
    names = ["X position", "Y position", "Z position", "Gripper state"]
    names.extend(f"Dimension {index + 1}" for index in range(max(0, dims - len(names))))
    return names[:dims]


def _dimension_ylabel(name: str) -> str:
    if name == "Gripper state":
        return "open/close"
    if name.endswith("position"):
        return "position"
    return "value"
