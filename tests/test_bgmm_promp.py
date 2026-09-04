import numpy as np
import pytest

from dobot_algorithms.gmr_primitives import (
    BGMMGMRProMP,
    GMMGMRDMP,
    GMMGMRSegmentedDMP,
    IncGMMGMRDMP,
)
from dobot_algorithms.metrics import evaluate_reference_trajectory, format_trajectory_metrics


def _palletizing_demos():
    phase = np.linspace(0.0, 1.0, 80)
    demos = []
    places = [[0.34, -0.16, 0.006]]
    px, py, pz = places[0]
    for offset in [0.0, 0.002, -0.0015, 0.001]:
        x = np.interp(phase, [0.0, 0.5, 0.75, 1.0], [0.0, 0.2, px + offset, 0.0])
        y = np.interp(phase, [0.0, 0.5, 0.75, 1.0], [0.0, -0.16, py + offset, 0.0])
        z = np.interp(phase, [0.0, 0.5, 0.75, 1.0], [0.15, 0.006, pz, 0.15])
        gripper = np.interp(phase, [0.0, 0.45, 0.65, 0.8, 1.0], [0.0, 1.0, 1.0, 0.0, 0.0])
        demos.append(np.column_stack([x, y, z, gripper]))
    return demos, places


@pytest.mark.parametrize(
    "model_cls,kwargs",
    [
        (GMMGMRDMP, {"n_time_steps": 60, "n_components": 3, "dmp_basis": 12, "random_state": 1}),
        (IncGMMGMRDMP, {"n_time_steps": 60, "inc_lam": 0.5, "dmp_basis": 12}),
        (
            GMMGMRSegmentedDMP,
            {"n_time_steps": 60, "n_components": 3, "dmp_basis": 12, "n_segments": 3, "random_state": 1},
        ),
        (
            BGMMGMRProMP,
            {"n_time_steps": 60, "n_components": 3, "promp_basis": 12, "random_state": 1},
        ),
    ],
)
def test_gmr_primitive_models_fit_and_return_4d_trajectory(model_cls, kwargs):
    demos, places = _palletizing_demos()

    model = model_cls(**kwargs).fit(demos)

    mean = model.mean_trajectory()
    samples = model.sample_trajectories(2)
    trajectory = model.trajectory_for_place(1, places)

    assert mean.shape == (60, 4)
    assert samples.shape == (2, 60, 4)
    assert trajectory.shape == (60, 4)
    assert np.isfinite(mean).all()
    assert np.logical_and(mean[:, 3] >= 0.0, mean[:, 3] <= 1.0).all()


def test_trajectory_metrics_handle_constant_dimensions():
    phase = np.linspace(0.0, 1.0, 20)
    demos = [
        np.column_stack([phase, phase**2, np.ones_like(phase)]),
        np.column_stack([phase, phase**2 + 0.01, np.ones_like(phase)]),
    ]
    reference = np.column_stack([phase, phase**2, np.ones_like(phase)])

    metrics = evaluate_reference_trajectory(demos, reference)
    summary = format_trajectory_metrics("Test", metrics)

    assert metrics.pearson.shape == (3,)
    assert metrics.rmse.shape == (3,)
    assert metrics.pearson[0] > 0.99
    assert np.isnan(metrics.pearson[2])
    assert "Pearson" in summary
    assert "RMSE" in summary
