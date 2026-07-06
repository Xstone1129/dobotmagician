from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


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
