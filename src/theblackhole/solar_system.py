"""Planets orbiting the Sun under real (N-body) gravity."""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
import pygame

from .aliases import ArrayLike, Color, Vector
from .config import (
    AMBIENT_LIGHT,
    ORBITING_PLANETS,
    PHYSICS_MAX_STEP,
    SUN_GRAVITY_MASS,
    TRAIL_INTERVAL,
    TRAIL_LENGTH,
)
from .physics import Body, GravitySystem

if TYPE_CHECKING:
    from .camera import Camera


class OrbitingPlanet(Body):
    """A body that is drawn as a lit sphere, leaving a trail behind it."""

    def __init__(self, position: ArrayLike, velocity: ArrayLike, mass: float, radius: float, color: Color) -> None:
        super().__init__(position, velocity, mass)
        self.radius = radius
        self.color = color
        self.trail: deque[Vector] = deque(maxlen=TRAIL_LENGTH)


def circular_orbit(center_mass: float, orbit_radius: float, angle: float, g: float = 1.0) -> tuple[Vector, Vector]:
    """Position and velocity for a circular orbit in the XZ plane around the origin."""
    position = orbit_radius * np.array([math.cos(angle), 0.0, math.sin(angle)])
    speed = math.sqrt(g * center_mass / orbit_radius)
    velocity = speed * np.array([-math.sin(angle), 0.0, math.cos(angle)])
    return position, velocity


class SolarSystem:
    """The Sun and the planets orbiting it."""

    def __init__(
        self,
        sun_position: ArrayLike = (0.0, 0.0, 0.0),
        sun_mass: float = SUN_GRAVITY_MASS,
        planets: Sequence[tuple[float, float, Color]] = ORBITING_PLANETS,
    ) -> None:
        self.sun = Body(sun_position, (0, 0, 0), sun_mass)
        self.planets = []
        for i, (orbit_radius, radius, color) in enumerate(planets):
            angle = i * 2.4  # Spread the planets around their orbits
            position, velocity = circular_orbit(sun_mass, orbit_radius, angle)
            self.planets.append(OrbitingPlanet(self.sun.position + position, velocity, 1.0, radius, color))
        self.gravity = GravitySystem([self.sun, *self.planets])
        self._since_trail_point = TRAIL_INTERVAL

    def update(self, dt: float) -> None:
        """Advance the orbits by `dt` seconds and record the trails."""
        substeps = max(1, math.ceil(dt / PHYSICS_MAX_STEP))
        for _ in range(substeps):
            self.gravity.step(dt / substeps)

        self._since_trail_point += dt
        if self._since_trail_point >= TRAIL_INTERVAL:
            self._since_trail_point = 0.0
            for planet in self.planets:
                planet.trail.append(planet.position.copy())

    @staticmethod
    def draw_trail(screen: pygame.Surface, camera: Camera, planet: OrbitingPlanet) -> None:
        """Line through the planet's past positions, fading out towards the oldest point."""
        points = [camera.project(*p) for p in planet.trail]
        count = len(points)
        for i in range(1, count):
            a, b = points[i - 1], points[i]
            if a is None or b is None:
                continue
            fade = 0.15 + 0.6 * i / count
            color = tuple(int(c * fade) for c in planet.color)
            pygame.draw.line(screen, color, a[:2], b[:2], 1)

    def draw(
        self,
        screen: pygame.Surface,
        camera: Camera,
        min_distance: float = 0.0,
        max_distance: float = math.inf,
    ) -> None:
        """Draw the planets whose distance to the camera is within [min_distance, max_distance), far to near."""
        visible = []
        for planet in self.planets:
            distance = float(np.linalg.norm(planet.position - camera.position))
            if min_distance <= distance < max_distance:
                visible.append((distance, planet))
        visible.sort(key=lambda item: item[0], reverse=True)

        for distance, planet in visible:
            self.draw_trail(screen, camera, planet)
            projection = camera.project(*planet.position)
            if projection is None:
                continue
            x, y, depth = projection
            radius_px = max(2, int(planet.radius * camera.focal_length / depth))
            # Phase lighting: fully lit when the Sun is behind the camera, dark when it is behind the planet
            to_sun = self.sun.position - planet.position
            to_camera = camera.position - planet.position
            phase = 0.5 + 0.5 * float(to_sun @ to_camera) / (np.linalg.norm(to_sun) * distance + 1e-9)
            light = AMBIENT_LIGHT + (1 - AMBIENT_LIGHT) * phase
            color = tuple(int(c * light) for c in planet.color)
            pygame.draw.circle(screen, color, (int(x), int(y)), radius_px)
