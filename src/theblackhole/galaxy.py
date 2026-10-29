"""A spiral galaxy: stars on a flat rotation curve around a central black hole."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np
import pygame

from .aliases import Vector
from .blackhole import BlackHole
from .config import (
    GALAXY_ARM_COLOR,
    GALAXY_ARM_TWIST,
    GALAXY_ARMS,
    GALAXY_BLACK_HOLE_MASS,
    GALAXY_CORE_COLOR,
    GALAXY_CORE_RADIUS,
    GALAXY_RADIUS,
    GALAXY_ROTATION_SPEED,
    GALAXY_STARS,
    PHYSICS_MAX_STEP,
)
from .glow import draw_glow
from .scenario import array

if TYPE_CHECKING:
    from .camera import Camera


def rotation_speed(radius: Vector, v0: float = GALAXY_ROTATION_SPEED, core: float = GALAXY_CORE_RADIUS) -> Vector:
    """Circular speed at `radius`: rises in the core, then stays flat like in real spiral galaxies."""
    return v0 * radius / np.sqrt(radius * radius + core * core)


class Galaxy:
    """Massless stars pulled by a halo potential whose circular speed is `rotation_speed`.

    Inner stars go round in less time than outer ones (differential rotation),
    so the spiral arms they start in wind up as time passes.
    """

    def __init__(self, count: int = GALAXY_STARS, seed: int = 4) -> None:
        rng = np.random.default_rng(seed)
        self.black_hole = BlackHole(mass=GALAXY_BLACK_HOLE_MASS)
        radius = GALAXY_RADIUS * np.sqrt(rng.random(count)) + 20
        arm = rng.integers(0, GALAXY_ARMS, count)
        # Logarithmic spiral: angle grows with log(radius), plus some scatter around each arm
        angle = arm * 2 * math.pi / GALAXY_ARMS + np.log(radius) / GALAXY_ARM_TWIST + rng.normal(0, 0.35, count)
        height = rng.normal(0, 25, count) * np.exp(-radius / GALAXY_RADIUS)
        cos, sin = np.cos(angle), np.sin(angle)
        self.positions = np.stack([radius * cos, height, radius * sin], axis=1)
        speed = rotation_speed(radius)
        self.velocities = np.stack([-speed * sin, np.zeros(count), speed * cos], axis=1)
        core = np.exp(-radius / (0.25 * GALAXY_RADIUS))[:, None]
        self.colors = np.array(GALAXY_ARM_COLOR) * (1 - core) + np.array(GALAXY_CORE_COLOR) * core
        self.accelerations = self._accelerations()

    def to_dict(self) -> dict[str, Any]:
        """Positions, velocities and colours of every star."""
        return {
            "positions": np.round(self.positions, 3).tolist(),
            "velocities": np.round(self.velocities, 4).tolist(),
            "colors": self.colors.astype(int).tolist(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Galaxy:
        """Rebuild a galaxy saved with `to_dict` (validates every value)."""
        positions = array(data.get("positions"), "positions")
        galaxy = cls.__new__(cls)
        galaxy.black_hole = BlackHole(mass=GALAXY_BLACK_HOLE_MASS)
        galaxy.positions = positions
        galaxy.velocities = array(data.get("velocities"), "velocities", rows=len(positions))
        galaxy.colors = np.clip(array(data.get("colors"), "colors", rows=len(positions)), 0, 255)
        galaxy.accelerations = galaxy._accelerations()
        return galaxy

    def _accelerations(self) -> Vector:
        # a = v(r)² / r towards the center, which keeps every star on its circular orbit
        r = np.linalg.norm(self.positions, axis=1)
        v = rotation_speed(r)
        return -self.positions * (v * v / (r * r))[:, None]

    def step(self, dt: float) -> None:
        """Advance every star by `dt` seconds (Velocity Verlet)."""
        self.velocities += 0.5 * dt * self.accelerations
        self.positions += dt * self.velocities
        self.accelerations = self._accelerations()
        self.velocities += 0.5 * dt * self.accelerations


class GalaxyScene:
    """The galaxy seen with the free camera."""

    def __init__(self, galaxy: Galaxy | None = None) -> None:
        self.galaxy = galaxy or Galaxy()

    def update(self, dt: float, time: float) -> None:
        """Advance the galaxy by `dt` seconds."""
        substeps = max(1, math.ceil(dt / PHYSICS_MAX_STEP))
        for _ in range(substeps):
            self.galaxy.step(dt / substeps)

    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw the bulge glow, the stars far to near and the central black hole."""
        galaxy = self.galaxy
        center = camera.project(0.0, 0.0, 0.0)
        if center is not None:  # Bright bulge of old stars
            bulge_px = 0.25 * GALAXY_RADIUS * camera.focal_length / center[2]
            draw_glow(screen, center[:2], bulge_px, GALAXY_CORE_COLOR, 0.5)
        cam = camera.to_camera_space(galaxy.positions)
        keep = np.nonzero(cam[:, 2] > 1.0)[0]
        keep = keep[np.argsort(-cam[keep, 2])]
        points = camera.project_camera_space(cam[keep]).astype(int).tolist()
        sizes = np.clip(4000.0 / cam[keep, 2], 1, 3).astype(int).tolist()
        colors = galaxy.colors[keep].astype(int).tolist()
        for point, size, color in zip(points, sizes, colors):
            pygame.draw.circle(screen, color, point, size)
        galaxy.black_hole.draw(screen, camera)
