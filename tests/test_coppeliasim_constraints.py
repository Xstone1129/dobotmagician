from __future__ import annotations

import numpy as np

from dobot_bgmm_promp.coppeliasim_client import CoppeliaConfig, CoppeliaDobotClient


def _client() -> CoppeliaDobotClient:
    return CoppeliaDobotClient(
        CoppeliaConfig(
            arm_base_position=(-0.08315, 0.0, 0.13155),
            pick_position=(-0.20, -0.14, 0.030),
            place_positions=((0.08, 0.16, 0.030),),
            place_index=1,
            workspace_max_radius=0.27,
            workspace_z_bounds=(0.030, 0.32),
            base_exclusion_radius=0.105,
            base_clearance_z=0.245,
        )
    )


def test_constraint_lifts_points_inside_base_and_clips_reach() -> None:
    client = _client()
    points = np.array(
        [
            [-0.08315, 0.0, 0.03],
            [0.40, 0.0, 0.01],
        ]
    )

    constrained = client._constrain_cartesian(points)

    assert constrained[0, 2] == 0.245
    assert np.linalg.norm(constrained[1, :2] - np.array([-0.08315, 0.0])) == 0.27
    assert constrained[:, 2].min() >= 0.030


def test_event_retargeting_hits_configured_pick_and_place() -> None:
    client = _client()
    points = np.zeros((6, 3))
    gripper = np.array([0.0, 0.7, 1.0, 1.0, 0.2, 0.0])

    retargeted = client._retarget_events(
        points,
        gripper,
        np.array(client.config.pick_position),
        np.array(client.config.place_positions[0]),
    )

    assert np.allclose(retargeted[1], client.config.pick_position)
    assert np.allclose(retargeted[4], client.config.place_positions[0])
