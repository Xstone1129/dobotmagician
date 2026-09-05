from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

from dobot_algorithms.scripts import generate_suction_demos as generator


def test_stations_match_current_scene_centers_and_contact_heights() -> None:
    pick, place = generator.load_stations()

    np.testing.assert_allclose(pick, [0.18, -0.15, 0.0255])
    np.testing.assert_allclose(place, [0.08, 0.16, 0.0270])
    np.testing.assert_array_equal(generator.ARM_BASE_XY, np.zeros(2))


def test_stations_follow_world_centers_and_object_dimensions(tmp_path: Path) -> None:
    world = ET.parse(generator.DEFAULT_WORLD)
    pick = world.find(".//model[@name='pick_box']")
    place = world.find(".//model[@name='place_table']")
    assert pick is not None and place is not None
    pick.find("pose").text = "0.17 -0.14 0.02 0 0 0"
    pick.find("link/collision/geometry/box/size").text = "0.02 0.02 0.04"
    place.find("pose").text = "0.09 0.15 0.005 0 0 0"
    place.find("link/collision/geometry/box/size").text = "0.1 0.1 0.008"
    world_path = tmp_path / "shifted_stations.sdf"
    world.write(world_path, encoding="utf-8")

    actual_pick, actual_place = generator.load_stations(world_path=world_path)
    np.testing.assert_allclose(actual_pick, [0.17, -0.14, 0.0455])
    np.testing.assert_allclose(actual_place, [0.09, 0.15, 0.0545])
    demo = generator.build_demo(np.random.default_rng(57), world_path=world_path)
    np.testing.assert_array_equal(demo[0, 1:4], actual_pick)
    np.testing.assert_array_equal(demo[-1, 1:4], actual_place)


@pytest.mark.parametrize(
    ("press_depth", "pick_z", "place_z"),
    [(0.0, 0.026, 0.0275), (0.001, 0.025, 0.0265)],
)
def test_press_depth_lowers_both_contacts_without_moving_centers(
    press_depth: float, pick_z: float, place_z: float,
) -> None:
    pick, place = generator.load_stations(press_depth=press_depth)
    demo = generator.build_demo(np.random.default_rng(57), press_depth=press_depth)

    np.testing.assert_allclose(pick, [0.18, -0.15, pick_z])
    np.testing.assert_allclose(place, [0.08, 0.16, place_z])
    np.testing.assert_array_equal(demo[0, 1:4], pick)
    np.testing.assert_array_equal(demo[-1, 1:4], place)


@pytest.mark.parametrize("press_depth", [-0.0001, 0.0011, np.nan, np.inf])
def test_invalid_press_depth_is_rejected(press_depth: float) -> None:
    with pytest.raises(ValueError, match="press_depth"):
        generator.load_stations(press_depth=press_depth)
    with pytest.raises(ValueError, match="press_depth"):
        generator.build_demo(np.random.default_rng(57), press_depth=press_depth)


def test_turn_arc_sweeps_around_current_base_at_constant_radius() -> None:
    pick, place = generator.load_stations()
    arc = generator._turn_arc(pick, place)
    radius = np.linalg.norm(arc[:, :2] - generator.ARM_BASE_XY, axis=1)
    angles = np.unwrap(np.arctan2(arc[:, 1], arc[:, 0]))

    np.testing.assert_allclose(radius, np.linalg.norm(pick[:2]))
    np.testing.assert_allclose(arc[0, :2], pick[:2])
    np.testing.assert_allclose(arc[-1, :2] / radius[-1], place[:2] / np.linalg.norm(place[:2]))
    np.testing.assert_allclose(arc[:, 2], generator.LIFT_Z)
    assert abs(angles[-1] - angles[0]) > 1.0


@pytest.mark.parametrize("seed", [57, 91])
def test_contact_periods_stay_at_station_centers_despite_noise(seed: int) -> None:
    pick, place = generator.load_stations()
    demo = generator.build_demo(np.random.default_rng(seed))
    xyz, vacuum = demo[:, 1:4], demo[:, 4]
    at_pick = np.all(np.isclose(xyz, pick, atol=1e-12, rtol=0), axis=1)
    at_place = np.all(np.isclose(xyz, place, atol=1e-12, rtol=0), axis=1)

    assert demo.shape == (180, 5)
    assert np.isfinite(demo).all()
    assert np.all(np.diff(demo[:, 0]) > 0)
    np.testing.assert_array_equal(xyz[0], pick)
    np.testing.assert_array_equal(xyz[-1], place)
    np.testing.assert_array_equal(vacuum[[0, -1]], [0, 0])
    assert at_pick.sum() >= 2
    assert at_place.sum() >= 2
    assert np.any(vacuum[at_pick] > 0.8)
    assert np.any(vacuum[at_place] > 0.8)
    assert np.all((0 <= vacuum) & (vacuum <= 1))
    lifted = (xyz[:, 2] > 0.08) & (vacuum > 0.8)
    assert lifted.sum() > 20
    assert xyz[:, 2].max() < 0.11


@pytest.mark.parametrize("noise_std", [-0.001, np.nan, np.inf])
def test_invalid_measurement_noise_is_rejected(noise_std: float) -> None:
    with pytest.raises(ValueError, match="noise_std"):
        generator.build_demo(np.random.default_rng(57), noise_std=noise_std)


def test_lift_below_contact_stations_is_rejected() -> None:
    with pytest.raises(ValueError, match="lift"):
        generator.build_demo(np.random.default_rng(57), lift_z=0.02)


def test_generated_demo_is_reachable_with_vertical_cup(pytestconfig, monkeypatch) -> None:
    ros_python = Path(pytestconfig.rootpath) / "ros2_ws/src/dobot_magician_ros"
    monkeypatch.syspath_prepend(str(ros_python))
    demo = generator.build_demo(np.random.default_rng(57))

    generator.validate_reachability([demo])


def test_failed_validation_preserves_existing_demonstrations(tmp_path: Path, monkeypatch) -> None:
    existing = tmp_path / "demo_01.csv"
    previous = b"t,x,y,z,gripper\n0,0.18,-0.15,0.026,0\n"
    existing.write_bytes(previous)

    def reject_demo(demos) -> None:
        assert len(demos) == 2
        raise ValueError("demo 2 point 17 is unreachable")

    monkeypatch.setattr(generator, "validate_reachability", reject_demo)
    monkeypatch.setattr(
        sys, "argv", ["generate_suction_demos", "--output-dir", str(tmp_path), "--count", "2"]
    )
    with pytest.raises(ValueError, match="demo 2 point 17"):
        generator.main()

    assert existing.read_bytes() == previous
    assert sorted(path.name for path in tmp_path.iterdir()) == ["demo_01.csv"]
