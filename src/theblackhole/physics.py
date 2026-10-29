"""Newtonian gravity between bodies, integrated with Velocity Verlet."""

import numpy as np

from .config import GRAVITY_CONSTANT, GRAVITY_SOFTENING


class Body:
    """A point mass with a position and a velocity."""

    def __init__(self, position, velocity, mass):
        self.position = np.asarray(position, dtype=float)
        self.velocity = np.asarray(velocity, dtype=float)
        self.mass = float(mass)
        self.acceleration = np.zeros(3)


class GravitySystem:
    """N bodies pulling on each other. Call `step(dt)` once per frame."""

    def __init__(self, bodies, g=GRAVITY_CONSTANT, softening=GRAVITY_SOFTENING):
        self.bodies = list(bodies)
        self.g = g
        self.softening = softening
        self._compute_accelerations()

    def _compute_accelerations(self):
        # shortcut: O(N²) pairwise loop, vectorised with NumPy on Day 13
        for body in self.bodies:
            body.acceleration = np.zeros(3)
        eps2 = self.softening**2
        for i, a in enumerate(self.bodies):
            for b in self.bodies[i + 1 :]:
                offset = b.position - a.position
                dist2 = offset @ offset + eps2
                pull = self.g * offset / (dist2 * np.sqrt(dist2))
                a.acceleration += pull * b.mass
                b.acceleration -= pull * a.mass

    def step(self, dt):
        """Advance every body by `dt` seconds (Velocity Verlet: symplectic, 2nd order)."""
        for body in self.bodies:
            body.velocity += 0.5 * dt * body.acceleration
            body.position += dt * body.velocity
        self._compute_accelerations()
        for body in self.bodies:
            body.velocity += 0.5 * dt * body.acceleration

    def total_momentum(self):
        return sum((body.mass * body.velocity for body in self.bodies), np.zeros(3))
