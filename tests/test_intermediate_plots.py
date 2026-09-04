from pathlib import Path

import numpy as np

from dobot_algorithms.plotting import plot_gmm_components, plot_gmr_regression


def test_intermediate_gmm_and_gmr_plots_are_saved(tmp_path: Path) -> None:
    phase = np.linspace(0.0, 1.0, 12)
    demo = np.column_stack([phase, phase**2, 0.1 + phase, phase])
    points = np.vstack([np.column_stack([phase, demo]), np.column_stack([phase, demo + 0.001])])
    means = np.array([[0.25, 0.25, 0.06, 0.25], [0.75, 0.75, 0.16, 0.75]])
    covariances = np.tile(np.eye(4)[None, :, :] * 0.01, (2, 1, 1))
    gmm_path = tmp_path / "gmm.png"
    gmr_path = tmp_path / "gmr.png"

    plot_gmm_components(points, means, covariances, np.array([0.5, 0.5]), gmm_path, title="GMM")
    plot_gmr_regression([demo], demo, gmr_path, title="GMR")

    assert gmm_path.exists() and gmm_path.stat().st_size > 1000
    assert gmr_path.exists() and gmr_path.stat().st_size > 1000
