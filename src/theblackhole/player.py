"""The astronaut that walks on the planet."""

import math

import numpy as np
import pygame

from .camera import normalize
from .config import BACKPACK, GRAVITY, JUMP_SPEED, NEAR_PLANE, SUIT, SUIT_DARK, VISOR
from .render import draw_faces, shade_color

# Corner order inside a box: index = x_bit * 4 + y_bit * 2 + z_bit
BOX_FACES = [
    ([0, 2, 3, 1], (-1, 0, 0)),
    ([4, 5, 7, 6], (1, 0, 0)),
    ([0, 1, 5, 4], (0, -1, 0)),
    ([2, 6, 7, 3], (0, 1, 0)),
    ([0, 4, 6, 2], (0, 0, -1)),
    ([1, 3, 7, 5], (0, 0, 1)),
]



class Player:
    """An astronaut walking on the surface of a planet."""

    def __init__(self, planet, normal, heading):
        self.planet = planet
        self.normal = normalize(np.asarray(normal, dtype=float))  # "Up" at the player's position
        self.heading = np.zeros(3)                                 # Where the player is facing
        self._set_heading(heading)
        self.altitude = 0.0
        self.vertical_speed = 0.0
        self.walk_phase = 0.0

    def _set_heading(self, heading):
        heading = np.asarray(heading, dtype=float)
        self.heading = normalize(heading - np.dot(heading, self.normal) * self.normal)

    @property
    def right(self):
        return np.cross(self.normal, self.heading)

    @property
    def position(self):
        return self.planet.center + self.normal * (self.planet.radius + self.altitude)

    @property
    def on_ground(self):
        return self.altitude <= 0.0

    def turn(self, angle):
        self._set_heading(self.heading * math.cos(angle) + self.right * math.sin(angle))

    def move(self, forward, sideways):
        """Walk along the curved surface: moving means rotating around the planet's center."""
        step = self.heading * forward + self.right * sideways
        distance = np.linalg.norm(step)
        if distance < 1e-9:
            return
        direction = step / distance
        angle = distance / (self.planet.radius + self.altitude)

        # Carry the heading along with the rotation so the player keeps facing "forward"
        new_direction = direction * math.cos(angle) - self.normal * math.sin(angle)
        heading = self.heading + np.dot(self.heading, direction) * (new_direction - direction)
        self.normal = normalize(self.normal * math.cos(angle) + direction * math.sin(angle))
        self._set_heading(heading)
        self.walk_phase += distance * 1.5

    def jump(self):
        if self.on_ground:
            self.vertical_speed = JUMP_SPEED

    def update(self, dt):
        if self.on_ground and self.vertical_speed <= 0:
            self.altitude = 0.0
            self.vertical_speed = 0.0
            return
        self.vertical_speed -= GRAVITY * dt
        self.altitude = max(0.0, self.altitude + self.vertical_speed * dt)

    def _parts(self):
        """Boxes in local space (x right, y up, z forward): (min corner, max corner, color)."""
        swing = 0.35 * math.sin(self.walk_phase) if self.on_ground else 0.25
        return [
            ((-0.45, 0.0, -0.2 + swing), (-0.1, 1.1, 0.2 + swing), SUIT_DARK),   # Left leg
            ((0.1, 0.0, -0.2 - swing), (0.45, 1.1, 0.2 - swing), SUIT_DARK),     # Right leg
            ((-0.55, 1.1, -0.3), (0.55, 2.3, 0.3), SUIT),                        # Body
            ((-0.8, 1.3, -0.15 - swing), (-0.55, 2.2, 0.15 - swing), SUIT_DARK), # Left arm
            ((0.55, 1.3, -0.15 + swing), (0.8, 2.2, 0.15 + swing), SUIT_DARK),   # Right arm
            ((-0.45, 1.25, -0.6), (0.45, 2.2, -0.3), BACKPACK),                  # Backpack
            ((-0.35, 2.35, -0.3), (0.35, 3.0, 0.3), SUIT),                       # Helmet
            ((-0.28, 2.45, 0.3), (0.28, 2.85, 0.36), VISOR),                     # Visor
        ]

    def draw(self, screen, camera, light_dir):
        basis = np.array([self.right, self.normal, self.heading])  # local -> world rotation
        origin = self.position
        self._draw_shadow(screen, camera)

        # Once the Sun goes below the horizon, the planet itself blocks the light
        sun_height = float(np.dot(self.normal, light_dir))
        sunlight = min(1.0, max(0.0, (sun_height + 0.05) / 0.1))

        faces = []
        for (x0, y0, z0), (x1, y1, z1), color in self._parts():
            local = np.array([(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
            corners = origin + local @ basis
            cam_corners = camera.to_camera_space(corners)
            for indices, local_normal in BOX_FACES:
                normal = np.asarray(local_normal, dtype=float) @ basis
                center = corners[indices].mean(axis=0)
                if np.dot(center - camera.position, normal) >= 0:
                    continue  # Facing away from the camera
                polygon = cam_corners[indices]
                faces.append((polygon[:, 2].mean(), polygon, shade_color(color, normal, light_dir, sunlight)))
        draw_faces(screen, camera, faces)

    def _draw_shadow(self, screen, camera):
        size = max(0.2, 1.0 - self.altitude * 0.15)
        ground = self.planet.center + self.normal * (self.planet.radius + 0.05)
        points = [ground + self.right * math.cos(a) * 0.8 * size + self.heading * math.sin(a) * 0.6 * size
                  for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
        cam_points = camera.to_camera_space(points)
        if (cam_points[:, 2] < NEAR_PLANE).any():
            return
        pygame.draw.polygon(screen, (15, 20, 15), camera.project_camera_space(cam_points).tolist())
