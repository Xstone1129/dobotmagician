from __future__ import annotations

import numpy as np

from dobot_algorithms.scripts.generate_suction_turn_demos import (
    ARM_BASE_XY,
    OPPOSITE_PLACE,
    REAR_PICK,
    _turn_arc,
    build_demo,
)


def test_turn_arc_sweeps_around_base_at_constant_radius() -> None:
    arc = _turn_arc(REAR_PICK, OPPOSITE_PLACE)
    radius = np.linalg.norm(arc[:, :2] - ARM_BASE_XY, axis=1)
    angles = np.unwrap(np.arctan2(arc[:, 1], arc[:, 0] - ARM_BASE_XY[0]))

    assert np.allclose(radius, radius[0])
    assert abs(angles[-1] - angles[0]) > 1.0
    assert np.allclose(arc[:, 2], arc[0, 2])


def test_generated_demo_contains_lifted_circular_turn() -> None:
    demo = build_demo(np.random.default_rng(57))
    radius = np.linalg.norm(demo[:, 1:3] - ARM_BASE_XY, axis=1)
    angles = np.unwrap(np.arctan2(demo[:, 2], demo[:, 1] - ARM_BASE_XY[0]))
    lifted = (demo[:, 3] > 0.16) & (demo[:, 4] > 0.8)
    # The lifted phase also contains the final radial move to the place tray;
    # isolate the inner, constant-radius turn before checking circularity.
    turn = lifted & (radius <= np.quantile(radius[lifted], 0.65))

    assert lifted.sum() > 40
    assert turn.sum() > 20
    assert angles[turn][-1] - angles[turn][0] > 1.0
    assert radius[turn].max() - radius[turn].min() < 0.08
