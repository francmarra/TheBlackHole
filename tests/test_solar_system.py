"""Tests for the planets orbiting the Sun."""

import numpy as np
import pytest

from theblackhole.solar_system import SolarSystem, circular_orbit


def test_circular_orbit_speed_balances_gravity():
    position, velocity = circular_orbit(center_mass=1000, orbit_radius=10, angle=0.3)
    assert np.linalg.norm(position) == pytest.approx(10)
    assert position @ velocity == pytest.approx(0, abs=1e-9)  # velocity is tangent
    assert velocity @ velocity / 10 == pytest.approx(1000 / 10**2)  # v²/r = GM/r²


def test_planets_keep_their_orbit_radius():
    orbits = [(220.0, 8.0, (1, 1, 1)), (560.0, 12.0, (1, 1, 1))]
    system = SolarSystem(planets=orbits)
    for _ in range(600):  # 10 s at 60 FPS
        system.update(1 / 60)
    for planet, (orbit_radius, _, _) in zip(system.planets, orbits):
        assert np.linalg.norm(planet.position - system.sun.position) == pytest.approx(orbit_radius, rel=0.01)
    # The planets actually moved along their orbits
    assert not np.allclose(system.planets[0].position, circular_orbit(6e5, 220.0, 0.0)[0])
