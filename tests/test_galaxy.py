"""Tests for the spiral galaxy."""

import numpy as np
import pytest

from theblackhole.config import GALAXY_ROTATION_SPEED
from theblackhole.galaxy import Galaxy, rotation_speed


def test_rotation_curve_is_flat_far_from_the_core():
    assert rotation_speed(np.array([0.0]))[0] == 0
    far = rotation_speed(np.array([1500.0, 2000.0]))
    assert far == pytest.approx([GALAXY_ROTATION_SPEED] * 2, rel=0.01)


def test_stars_keep_their_orbit_radius():
    galaxy = Galaxy(count=300)
    start = np.linalg.norm(galaxy.positions, axis=1)
    for _ in range(600):
        galaxy.step(1 / 60)
    assert np.linalg.norm(galaxy.positions, axis=1) == pytest.approx(start, rel=0.02)


def test_inner_stars_go_round_faster_so_the_arms_wind_up():
    galaxy = Galaxy(count=2000)
    radius = np.linalg.norm(galaxy.positions[:, [0, 2]], axis=1)
    angular_speed = rotation_speed(radius) / radius
    inner, outer = angular_speed[radius < 400].mean(), angular_speed[radius > 1500].mean()
    assert inner > 3 * outer
