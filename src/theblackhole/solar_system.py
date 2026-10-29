"""Planets orbiting the Sun under real (N-body) gravity."""

import math

import numpy as np
import pygame

from .config import AMBIENT_LIGHT, ORBITING_PLANETS, PHYSICS_MAX_STEP, SUN_GRAVITY_MASS
from .physics import Body, GravitySystem


class OrbitingPlanet(Body):
    """A body that is drawn as a lit sphere."""

    def __init__(self, position, velocity, mass, radius, color):
        super().__init__(position, velocity, mass)
        self.radius = radius
        self.color = color


def circular_orbit(center_mass, orbit_radius, angle, g=1.0):
    """Position and velocity for a circular orbit in the XZ plane around the origin."""
    position = orbit_radius * np.array([math.cos(angle), 0.0, math.sin(angle)])
    speed = math.sqrt(g * center_mass / orbit_radius)
    velocity = speed * np.array([-math.sin(angle), 0.0, math.cos(angle)])
    return position, velocity


class SolarSystem:
    def __init__(self, sun_position=(0.0, 0.0, 0.0), sun_mass=SUN_GRAVITY_MASS, planets=ORBITING_PLANETS):
        self.sun = Body(sun_position, (0, 0, 0), sun_mass)
        self.planets = []
        for i, (orbit_radius, radius, color) in enumerate(planets):
            angle = i * 2.4  # Spread the planets around their orbits
            position, velocity = circular_orbit(sun_mass, orbit_radius, angle)
            self.planets.append(OrbitingPlanet(self.sun.position + position, velocity, 1.0, radius, color))
        self.gravity = GravitySystem([self.sun, *self.planets])

    def update(self, dt):
        substeps = max(1, math.ceil(dt / PHYSICS_MAX_STEP))
        for _ in range(substeps):
            self.gravity.step(dt / substeps)

    def draw(self, screen, camera, min_distance=0.0, max_distance=math.inf):
        """Draw the planets whose distance to the camera is within [min_distance, max_distance), far to near."""
        visible = []
        for planet in self.planets:
            distance = float(np.linalg.norm(planet.position - camera.position))
            if min_distance <= distance < max_distance:
                visible.append((distance, planet))
        visible.sort(key=lambda item: item[0], reverse=True)

        for distance, planet in visible:
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
