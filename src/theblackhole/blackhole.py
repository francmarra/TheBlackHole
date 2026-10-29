"""A black hole: a heavy body with an event horizon, and the scene around it."""

import math

import numpy as np
import pygame

from .config import (
    BLACK_HOLE_MASS,
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


class BlackHoleScene:
    """A black hole at the origin in front of a field of distant stars."""

    def __init__(self):
        self.black_hole = BlackHole()
        self.gravity = GravitySystem([self.black_hole])
        self.star_field = StarField3D(with_sun=False)

    def update(self, dt, time):
        self.star_field.update(time)
        substeps = max(1, math.ceil(dt / PHYSICS_MAX_STEP))
        for _ in range(substeps):
            self.gravity.step(dt / substeps)

    def draw(self, screen, camera):
        hole_distance = float(np.linalg.norm(camera.position - self.black_hole.position))
        self.star_field.draw(screen, camera, min_distance=hole_distance)
        self.black_hole.draw(screen, camera)
        self.star_field.draw(screen, camera, max_distance=hole_distance)
