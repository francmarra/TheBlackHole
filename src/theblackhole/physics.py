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
    """N bodies pulling on each other. Call `step(dt)` once per frame.

    The state lives in (N, 3) NumPy arrays; each body's `position`, `velocity` and
    `acceleration` become views into those arrays, so update them in place (`+=`).
    """

    def __init__(self, bodies, g=GRAVITY_CONSTANT, softening=GRAVITY_SOFTENING):
        self.g = g
        self.softening = softening
        self._build(bodies)

    def _build(self, bodies):
        """(Re)create the arrays from the bodies' current state and point the bodies at them."""
        self.bodies = list(bodies)
        self.positions = np.array([body.position for body in self.bodies], dtype=float).reshape(-1, 3)
        self.velocities = np.array([body.velocity for body in self.bodies], dtype=float).reshape(-1, 3)
        self.masses = np.array([body.mass for body in self.bodies], dtype=float)
        self.accelerations = np.zeros_like(self.positions)
        for i, body in enumerate(self.bodies):
            body.position = self.positions[i]
            body.velocity = self.velocities[i]
            body.acceleration = self.accelerations[i]
        self._compute_accelerations()

    def add(self, body):
        self._build([*self.bodies, body])

    def remove(self, body):
        self._build([b for b in self.bodies if b is not body])
        # The removed body keeps its last state in its own arrays
        body.position, body.velocity, body.acceleration = (
            body.position.copy(), body.velocity.copy(), body.acceleration.copy())

    def _pairs(self):
        """Offsets between every pair of bodies (offsets[i, j] points from i to j) and softened distances²."""
        offsets = self.positions[np.newaxis, :, :] - self.positions[:, np.newaxis, :]
        dist2 = np.einsum("ijk,ijk->ij", offsets, offsets) + self.softening**2
        return offsets, dist2

    def _compute_accelerations(self):
        offsets, dist2 = self._pairs()
        with np.errstate(divide="ignore"):
            inv_dist3 = dist2**-1.5
        np.fill_diagonal(inv_dist3, 0.0)  # A body does not pull on itself
        self.accelerations[:] = self.g * np.einsum("ij,ijk->ik", inv_dist3 * self.masses, offsets)

    def step(self, dt):
        """Advance every body by `dt` seconds (Velocity Verlet: symplectic, 2nd order)."""
        self.velocities += 0.5 * dt * self.accelerations
        self.positions += dt * self.velocities
        self._compute_accelerations()
        self.velocities += 0.5 * dt * self.accelerations

    def total_momentum(self):
        return self.masses @ self.velocities

    def total_energy(self):
        """Kinetic plus (softened) gravitational potential energy; constant for an exact integrator."""
        kinetic = 0.5 * self.masses @ np.einsum("ij,ij->i", self.velocities, self.velocities)
        _, dist2 = self._pairs()
        i, j = np.triu_indices(len(self.bodies), k=1)
        potential = -self.g * np.sum(self.masses[i] * self.masses[j] / np.sqrt(dist2[i, j]))
        return float(kinetic + potential)
