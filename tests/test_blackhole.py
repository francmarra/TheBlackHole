"""Tests for the black hole."""

import pytest

from theblackhole.blackhole import BlackHole, schwarzschild_radius
from theblackhole.config import SHADOW_FACTOR


def test_schwarzschild_radius_formula():
    # Real units: the Sun would have r_s ≈ 2.95 km
    assert schwarzschild_radius(1.989e30, g=6.674e-11, c=2.998e8) == pytest.approx(2954, rel=1e-3)


def test_horizon_grows_linearly_with_mass():
    small, big = BlackHole(mass=1e6), BlackHole(mass=3e6)
    assert big.horizon_radius == pytest.approx(3 * small.horizon_radius)
    assert small.shadow_radius == pytest.approx(SHADOW_FACTOR * small.horizon_radius)


def test_disk_particles_start_inside_the_disk_and_keep_orbiting():
    import numpy as np

    from theblackhole.blackhole import AccretionDisk

    hole = BlackHole()
    disk = AccretionDisk(hole, count=200)
    start_radius = np.linalg.norm(disk.positions[:, [0, 2]], axis=1)
    assert start_radius.min() >= disk.inner - 1e-9 and start_radius.max() <= disk.outer + 1e-9
    for _ in range(600):
        disk.step(1 / 120)
    radius = np.linalg.norm(disk.positions - hole.position, axis=1)
    assert radius / np.linalg.norm(np.c_[start_radius, np.zeros(200)], axis=1) == pytest.approx(1, abs=0.1)
