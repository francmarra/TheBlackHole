"""Tests for the gravity engine."""

import math

import numpy as np
import pytest

from theblackhole.physics import Body, GravitySystem


def test_lone_body_moves_in_a_straight_line():
    body = Body((0, 0, 0), (2, -1, 0.5), mass=10)
    system = GravitySystem([body])
    for _ in range(100):
        system.step(0.01)
    assert body.position == pytest.approx([2, -1, 0.5])
    assert body.velocity == pytest.approx([2, -1, 0.5])


def test_two_bodies_attract_each_other_with_opposite_forces():
    light, heavy = Body((-5, 0, 0), (0, 0, 0), mass=1), Body((5, 0, 0), (0, 0, 0), mass=3)
    GravitySystem([light, heavy], softening=0)

    # Newton's third law: m_a * a_a = -m_b * a_b, and each pulls towards the other
    assert light.mass * light.acceleration == pytest.approx(-heavy.mass * heavy.acceleration)
    assert light.acceleration[0] > 0 > heavy.acceleration[0]
    assert light.acceleration[0] == pytest.approx(3 / 10**2)


def test_momentum_is_conserved():
    bodies = [
        Body((0, 0, 0), (0, 0.1, 0), mass=50),
        Body((10, 0, 0), (0, 2, 0.3), mass=1),
        Body((-7, 4, 1), (1, -1, 0), mass=2),
    ]
    system = GravitySystem(bodies)
    start = system.total_momentum()
    for _ in range(500):
        system.step(0.01)
    assert system.total_momentum() == pytest.approx(start, abs=1e-9)


def test_circular_orbit_returns_to_start_after_one_period():
    sun_mass, radius = 1000.0, 50.0
    speed = math.sqrt(sun_mass / radius)  # circular orbit with G = 1
    period = 2 * math.pi * radius / speed
    planet = Body((radius, 0, 0), (0, 0, speed), mass=1e-6)
    sun = Body((0, 0, 0), (0, 0, 0), mass=sun_mass)
    system = GravitySystem([sun, planet], softening=0)

    steps = 2000
    for _ in range(steps):
        system.step(period / steps)
        assert np.linalg.norm(planet.position - sun.position) == pytest.approx(radius, rel=1e-3)
    assert planet.position == pytest.approx([radius, 0, 0], abs=0.05 * radius)


def eccentric_binary():
    """A light planet on an orbit with eccentricity 0.6 around a heavy star."""
    star_mass, distance = 1000.0, 20.0
    speed = 0.6 * math.sqrt(star_mass / distance)  # slower than circular -> ellipse
    star = Body((0, 0, 0), (0, 0, 0), mass=star_mass)
    planet = Body((distance, 0, 0), (0, speed, 0), mass=1.0)
    return GravitySystem([star, planet], softening=0)


def test_energy_is_conserved_over_many_eccentric_orbits():
    system = eccentric_binary()
    start = system.total_energy()
    worst = 0.0
    for _ in range(20_000):  # ~10 orbits
        system.step(0.002)
        worst = max(worst, abs(system.total_energy() - start))
    # Velocity Verlet is symplectic: the error oscillates but does not grow
    assert worst / abs(start) < 1e-4


def test_explicit_euler_would_drift_much_more():
    """Same orbit with a naive integrator, to show why Verlet was chosen."""
    system = eccentric_binary()
    start = system.total_energy()
    for _ in range(20_000):
        for body in system.bodies:
            body.position += 0.002 * body.velocity
        for body in system.bodies:
            body.velocity += 0.002 * body.acceleration
        system._compute_accelerations()
    assert abs(system.total_energy() - start) / abs(start) > 1e-2
