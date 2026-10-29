"""A black hole: a heavy body with an event horizon, and the scene around it."""

import math

import numpy as np
import pygame

from .config import (
    BLACK_HOLE_MASS,
    DISK_COOL_COLOR,
    DISK_HOT_COLOR,
    DISK_INNER,
    DISK_OUTER,
    DISK_PARTICLES,
    DISK_THICKNESS,
    GRAVITY_CONSTANT,
    PHOTON_RING_COLOR,
    PHYSICS_MAX_STEP,
    SHADOW_FACTOR,
    SPEED_OF_LIGHT,
)
from .physics import Body, GravitySystem
from .starfield import StarField3D


def schwarzschild_radius(mass, g=GRAVITY_CONSTANT, c=SPEED_OF_LIGHT):
    """Radius of the event horizon of a non-rotating black hole: r_s = 2GM/c²."""
    return 2 * g * mass / c**2


class BlackHole(Body):
    def __init__(self, position=(0.0, 0.0, 0.0), mass=BLACK_HOLE_MASS):
        super().__init__(position, (0, 0, 0), mass)

    @property
    def horizon_radius(self):
        return schwarzschild_radius(self.mass)

    @property
    def shadow_radius(self):
        return SHADOW_FACTOR * self.horizon_radius

    def draw(self, screen, camera):
        projection = camera.project(*self.position)
        if projection is None:
            return
        x, y, depth = projection
        radius_px = max(2, int(self.shadow_radius * camera.focal_length / depth))
        center = (int(x), int(y))
        # Thin bright ring where light orbits just outside the shadow, then pure black inside
        pygame.draw.circle(screen, PHOTON_RING_COLOR, center, radius_px + max(1, radius_px // 25))
        pygame.draw.circle(screen, (0, 0, 0), center, radius_px)


class AccretionDisk:
    """Massless particles orbiting a black hole, integrated together as NumPy arrays."""

    def __init__(self, black_hole, count=DISK_PARTICLES, seed=1):
        self.black_hole = black_hole
        self.rng = np.random.default_rng(seed)
        r_s = black_hole.horizon_radius
        self.inner, self.outer = DISK_INNER * r_s, DISK_OUTER * r_s
        self.positions = np.zeros((count, 3))
        self.velocities = np.zeros((count, 3))
        self.colors = np.zeros((count, 3))
        self.spawn(np.arange(count))
        self.accelerations = self._accelerations()

    def spawn(self, index):
        """Put particles `index` on circular orbits somewhere in the disk."""
        n = len(index)
        # More particles near the hole: uniform in area would leave the hot inner edge too empty
        radius = self.inner + (self.outer - self.inner) * self.rng.random(n) ** 1.5
        angle = self.rng.uniform(0, 2 * math.pi, n)
        height = self.rng.normal(0, DISK_THICKNESS, n) * radius
        cos, sin = np.cos(angle), np.sin(angle)
        self.positions[index] = self.black_hole.position + np.stack([radius * cos, height, radius * sin], axis=1)
        speed = np.sqrt(GRAVITY_CONSTANT * self.black_hole.mass / radius)
        self.velocities[index] = np.stack([-speed * sin, np.zeros(n), speed * cos], axis=1)
        heat = ((self.outer - radius) / (self.outer - self.inner))[:, None]
        self.colors[index] = np.array(DISK_COOL_COLOR) * (1 - heat) + np.array(DISK_HOT_COLOR) * heat

    def _accelerations(self):
        offset = self.black_hole.position - self.positions
        dist2 = np.einsum("ij,ij->i", offset, offset)
        return GRAVITY_CONSTANT * self.black_hole.mass * offset / (dist2 * np.sqrt(dist2))[:, None]

    def step(self, dt):
        self.velocities += 0.5 * dt * self.accelerations
        self.positions += dt * self.velocities
        self.accelerations = self._accelerations()
        self.velocities += 0.5 * dt * self.accelerations

    def draw(self, screen, camera, min_distance=0.0, max_distance=math.inf):
        cam = camera.to_camera_space(self.positions)
        distance = np.linalg.norm(self.positions - camera.position, axis=1)
        keep = np.nonzero((cam[:, 2] > 1.0) & (distance >= min_distance) & (distance < max_distance))[0]
        if len(keep) == 0:
            return
        keep = keep[np.argsort(-cam[keep, 2])]
        screen_points = camera.project_camera_space(cam[keep]).astype(int).tolist()
        sizes = np.clip(6.0 * camera.focal_length / cam[keep, 2], 1, 4).astype(int).tolist()
        colors = self.colors[keep].astype(int).tolist()
        for point, size, color in zip(screen_points, sizes, colors):
            pygame.draw.circle(screen, color, point, size)


class BlackHoleScene:
    """A black hole at the origin in front of a field of distant stars."""

    def __init__(self):
        self.black_hole = BlackHole()
        self.gravity = GravitySystem([self.black_hole])
        self.disk = AccretionDisk(self.black_hole)
        self.star_field = StarField3D(with_sun=False)

    def update(self, dt, time):
        self.star_field.update(time)
        substeps = max(1, math.ceil(dt / PHYSICS_MAX_STEP))
        for _ in range(substeps):
            self.gravity.step(dt / substeps)
            self.disk.step(dt / substeps)

    def draw(self, screen, camera):
        hole_distance = float(np.linalg.norm(camera.position - self.black_hole.position))
        self.star_field.draw(screen, camera, min_distance=hole_distance)
        self.disk.draw(screen, camera, min_distance=hole_distance)
        self.black_hole.draw(screen, camera)
        self.disk.draw(screen, camera, max_distance=hole_distance)
        self.star_field.draw(screen, camera, max_distance=hole_distance)
