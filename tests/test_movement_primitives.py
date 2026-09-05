import numpy as np
import pytest

from dobot_algorithms.evaluation import evaluate_reference_trajectory, format_trajectory_metrics
from dobot_algorithms.movement_primitives import (
    GMMGMRDMP,
    BGMMGMRProMP,
    GMMGMRSegmentedDMP,
    IncGMMGMRDMP,
)
from dobot_algorithms.primitives.dmp import DiscreteDMP


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


def test_position_metric_does_not_mix_in_gripper_units():
    demo = np.zeros((20, 4))
    prediction = demo.copy()
    prediction[:, 3] = 1.0
    metrics = evaluate_reference_trajectory([demo], prediction)
    assert metrics.position_rmse == 0.0
    assert metrics.rmse[3] == 1.0


def test_closed_dmp_tracks_shape_and_responds_to_forcing_weights():
    phase = np.linspace(0.0, 1.0, 180)
    reference = np.column_stack([0.1 + 0.03 * np.sin(2 * np.pi * phase), phase])
    model = DiscreteDMP(n_time_steps=180, n_basis=50, alpha_s=1.0).fit([reference])
    rollout = model.dynamic_rollout()
    assert np.sqrt(np.mean((rollout[:, 0] - reference[:, 0]) ** 2)) < 0.003
    model.weights_[:] = 0
    assert np.max(np.abs(model.dynamic_rollout()[:, 0] - rollout[:, 0])) > 0.02


def test_promp_constrained_reconstruction_preserves_endpoints():
    demos, _ = _palletizing_demos()
    model = BGMMGMRProMP(
        n_time_steps=80, n_components=3, random_state=1,
        promp_basis=25, promp_constrain_endpoints=True,
    ).fit(demos)
    np.testing.assert_allclose(model.mean_trajectory()[[0, -1]], demos[0][[0, -1]], atol=1e-10)
