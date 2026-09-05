from __future__ import annotations

import copy
from itertools import pairwise
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("rclpy")

from dobot_algorithms.scripts import play_algorithm as player


def _build(monkeypatch, joints: np.ndarray, **overrides):
    trajectory = np.zeros((len(joints), 3))
    trajectory[:, 0] = np.arange(len(joints))
    monkeypatch.setattr(
        player,
        "inverse_kinematics",
        lambda x, y, z, *, vertical_tool: joints[int(x)],
    )
    options = {
        "speed": 1.0,
        "sample_period": 0.08,
        "lead_in": 2.0,
        "max_waypoints": None,
        "vertical_tail_fraction": 1.0,
    }
    options.update(overrides)
    message, skipped = player.build_joint_trajectory(trajectory, **options)
    assert skipped == []
    return message


def _times(message) -> np.ndarray:
    return np.array(
        [point.time_from_start.sec + point.time_from_start.nanosec * 1e-9 for point in message.points]
    )


@pytest.mark.parametrize("speed", [0.5, 1.0, 2.0])
def test_distant_first_point_respects_joint_speed_cap(monkeypatch, speed: float) -> None:
    joints = np.tile(player.HOME_JOINTS, (2, 1))
    joints[:, 0] = [2.4, 2.41]
    message = _build(monkeypatch, joints, speed=speed)
    times = _times(message)
    positions = np.array([point.positions for point in message.points])
    limit = 0.8 * min(speed, 1.0)

    np.testing.assert_array_equal(positions[0], player.HOME_JOINTS)
    np.testing.assert_array_equal(positions[1:], joints)
    assert times[0] == pytest.approx(2.0 / speed)
    assert times[1] - times[0] == pytest.approx(2.4 / limit)
    assert np.all(np.abs(np.diff(positions, axis=0)) / np.diff(times)[:, None] <= limit + 1e-9)


def test_abrupt_interior_joint_change_is_retimed(monkeypatch) -> None:
    joints = np.tile(player.HOME_JOINTS, (3, 1))
    joints[:, 0] = [0.01, 1.61, 1.62]
    message = _build(monkeypatch, joints)

    np.testing.assert_allclose(np.diff(_times(message)), [0.08, 2.0, 0.08])
    np.testing.assert_array_equal([point.positions for point in message.points[1:]], joints)


@pytest.mark.parametrize("max_waypoints", [None, 3])
def test_nominal_sample_schedule_preserves_downsampled_gaps(monkeypatch, max_waypoints) -> None:
    joints = np.tile(player.HOME_JOINTS, (7, 1))
    joints[:, 0] = 0.01 * np.arange(1, 8)
    message = _build(monkeypatch, joints, sample_period=0.1, max_waypoints=max_waypoints)
    selected = np.arange(7) if max_waypoints is None else np.array([0, 3, 6])

    np.testing.assert_allclose(_times(message), np.r_[2.0, 2.0 + (selected + 1) * 0.1])
    np.testing.assert_array_equal(message.points[0].positions, player.HOME_JOINTS)
    np.testing.assert_array_equal([point.positions for point in message.points[1:]], joints[selected])


@pytest.mark.parametrize("max_joint_speed", [np.nan, 0.0, 3.16])
def test_invalid_joint_speed_limit_is_rejected(monkeypatch, max_joint_speed: float) -> None:
    joints = np.tile(player.HOME_JOINTS, (2, 1))
    with pytest.raises(ValueError, match="max_joint_speed"):
        _build(monkeypatch, joints, max_joint_speed=max_joint_speed)


@pytest.mark.parametrize("max_waypoints", [2, 3])
def test_downsampling_preserves_suction_enable_and_release(max_waypoints: int) -> None:
    trajectory = np.zeros((8, 4))
    trajectory[2:5, 3] = 1.0

    indices = player.playback_indices(trajectory, max_waypoints)

    assert {0, 2, 5, 7}.issubset(indices)
    assert np.all(np.diff(indices) > 0)
    commands = trajectory[indices, 3] >= 0.5
    assert commands.tolist().count(True) >= 1
    np.testing.assert_array_equal(np.diff(commands.astype(int))[np.diff(commands.astype(int)) != 0], [1, -1])


def test_suction_stages_preserve_contact_points_and_retimed_intervals(monkeypatch) -> None:
    trajectory = np.zeros((8, 4))
    trajectory[:, 0] = np.arange(8)
    trajectory[2:5, 3] = 1.0
    joints = np.tile(player.HOME_JOINTS, (8, 1))
    joints[:, 0] = [0.01, 0.02, 0.03, 0.04, 1.63, 1.64, 1.65, 1.66]
    monkeypatch.setattr(
        player, "inverse_kinematics", lambda x, y, z, *, vertical_tool: joints[int(x)]
    )
    message, skipped = player.build_joint_trajectory(
        trajectory,
        speed=1.0,
        sample_period=0.1,
        lead_in=2.0,
        max_waypoints=3,
        vertical_tail_fraction=1.0,
    )
    original = copy.deepcopy(message)
    indices = player.playback_indices(trajectory, 3)

    stages = player.build_playback_stages(trajectory, message, indices)

    assert skipped == []
    assert [stage.suction_after for stage in stages] == [True, False, None]
    np.testing.assert_array_equal(stages[0].trajectory.points[-1].positions, joints[2])
    np.testing.assert_array_equal(stages[1].trajectory.points[-1].positions, joints[5])
    np.testing.assert_array_equal(stages[2].trajectory.points[-1].positions, joints[7])
    np.testing.assert_allclose(_times(stages[0].trajectory), [2.0, 2.1, 2.3])
    np.testing.assert_allclose(_times(stages[1].trajectory), [0.0, 2.0, 2.1])
    np.testing.assert_allclose(_times(stages[2].trajectory), [0.0, 0.2])
    for previous, following in pairwise(stages):
        assert previous.trajectory.points[-1].positions == following.trajectory.points[0].positions
        assert _times(following.trajectory)[0] == 0.0
    for stage in stages:
        assert stage.trajectory.joint_names == message.joint_names
        assert np.all(_times(stage.trajectory) >= 0.0)
        assert np.all(np.diff(_times(stage.trajectory)) > 0.0)

    assert message == original
    stages[1].trajectory.points[0].positions[0] = -0.25
    stages[1].trajectory.points[0].time_from_start.sec = 99
    stages[1].trajectory.joint_names[0] = "changed"
    assert message == original
    assert stages[0].trajectory.points[-1].positions[0] == pytest.approx(joints[2, 0])


def test_suction_stages_reject_missing_joint_waypoint(monkeypatch) -> None:
    joints = np.tile(player.HOME_JOINTS, (4, 1))
    message = _build(monkeypatch, joints)
    trajectory = np.zeros((4, 4))
    trajectory[1:3, 3] = 1.0
    message.points.pop(2)

    with pytest.raises(ValueError, match="incomplete joint trajectory"):
        player.build_playback_stages(trajectory, message, np.arange(4))


@pytest.mark.parametrize("expected_state", ["attached", "detached"])
def test_next_stage_requires_fresh_matching_suction_feedback(expected_state: str) -> None:
    sent = []
    fake_player = SimpleNamespace(
        finished=False,
        started=True,
        wait_state=expected_state,
        wait_sequence=10,
        suction_sequence=10,
        suction_state=expected_state,
        wait_deadline=3_000_000_000,
        get_clock=lambda: SimpleNamespace(now=lambda: SimpleNamespace(nanoseconds=1_000_000_000)),
        get_logger=lambda: SimpleNamespace(info=lambda message: None),
        send_stage=lambda: sent.append(True),
    )

    player.AlgorithmPlayer.tick(fake_player)
    assert sent == []
    opposite_state = "detached" if expected_state == "attached" else "attached"
    player.AlgorithmPlayer.on_suction_state(fake_player, SimpleNamespace(data=opposite_state))
    player.AlgorithmPlayer.tick(fake_player)
    assert sent == []

    player.AlgorithmPlayer.on_suction_state(fake_player, SimpleNamespace(data=expected_state))
    player.AlgorithmPlayer.tick(fake_player)
    assert sent == [True]
    assert fake_player.wait_state is None
    player.AlgorithmPlayer.tick(fake_player)
    assert sent == [True]


def test_suction_timeout_stops_before_next_motion() -> None:
    sent = []
    errors = []
    fake_player = SimpleNamespace(
        finished=False,
        started=True,
        wait_state="attached",
        wait_sequence=10,
        suction_sequence=11,
        suction_state="detached",
        wait_deadline=3_000_000_000,
        get_clock=lambda: SimpleNamespace(now=lambda: SimpleNamespace(nanoseconds=3_000_000_001)),
        send_stage=lambda: sent.append(True),
        finish=errors.append,
    )

    player.AlgorithmPlayer.tick(fake_player)

    assert sent == []
    assert len(errors) == 1
    assert "Timed out waiting for suction attached" in errors[0]
