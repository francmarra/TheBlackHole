"""Tests for saving and loading scenarios as JSON."""

import json

import numpy as np
import pytest

from theblackhole import scenario
from theblackhole.blackhole import BlackHoleScene
from theblackhole.galaxy import Galaxy
from theblackhole.solar_system import SolarSystem


def round_trip(tmp_path, scene, data):
    path = tmp_path / "save.json"
    scenario.save(path, scene, data, time_scale=4.0)
    document = scenario.load(path)
    assert document["scene"] == scene and document["time_scale"] == 4.0
    return document["data"]


def test_solar_system_continues_exactly_after_loading(tmp_path):
    original = SolarSystem()
    for _ in range(120):
        original.update(1 / 60)
    copy = SolarSystem.from_dict(round_trip(tmp_path, "solar", original.to_dict()))
    for _ in range(120):
        original.update(1 / 60)
        copy.update(1 / 60)
    for a, b in zip(original.planets, copy.planets):
        assert b.position == pytest.approx(a.position)
        assert (b.radius, b.color) == (a.radius, a.color)


def test_black_hole_scene_keeps_rocks_and_captures(tmp_path):
    scene = BlackHoleScene()
    scene.throw_rock((0, 0, -500), (0.3, 0, 1))
    scene.captured = 7
    copy = BlackHoleScene.from_dict(round_trip(tmp_path, "blackhole", scene.to_dict()))
    assert copy.captured == 7 and len(copy.rocks) == 1
    assert copy.rocks[0].velocity == pytest.approx(scene.rocks[0].velocity)
    assert len(copy.gravity.bodies) == 2


def test_galaxy_round_trip(tmp_path):
    galaxy = Galaxy(count=50)
    copy = Galaxy.from_dict(round_trip(tmp_path, "galaxy", galaxy.to_dict()))
    assert np.allclose(copy.positions, galaxy.positions, atol=1e-3)


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        json.dumps({"version": 99, "scene": "solar", "data": {}}),
        json.dumps({"version": 1, "scene": "pacman", "data": {}}),
        json.dumps({"version": 1, "scene": "solar", "data": {}, "time_scale": -1}),
    ],
)
def test_bad_files_are_rejected(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(scenario.ScenarioError):
        scenario.load(path)


@pytest.mark.parametrize(
    "planet",
    [
        {"position": [1, 2], "velocity": [0, 0, 0], "mass": 1, "radius": 5, "color": [1, 2, 3]},
        {"position": [1, 2, "x"], "velocity": [0, 0, 0], "mass": 1, "radius": 5, "color": [1, 2, 3]},
        {"position": [1, 2, 3], "velocity": [0, 0, 0], "mass": -1, "radius": 5, "color": [1, 2, 3]},
        {"position": [1, 2, 3], "velocity": [0, 0, float("nan")], "mass": 1, "radius": 5, "color": [1, 2, 3]},
    ],
)
def test_invalid_values_are_rejected(planet):
    data = {"sun": {"position": [0, 0, 0], "velocity": [0, 0, 0], "mass": 1000}, "planets": [planet]}
    with pytest.raises(scenario.ScenarioError):
        SolarSystem.from_dict(data)
