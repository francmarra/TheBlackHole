"""A twinkling star in 3D space."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from .aliases import Color, Lens
from .config import SCREEN_HEIGHT, SCREEN_WIDTH, STAR_COLORS

if TYPE_CHECKING:
    from .camera import Camera


class Star3D:
    """A star at a fixed point in space."""

    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        size: float | None = None,
        color: Color | None = None,
        brightness: float | None = None,
        mass: float | None = None,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.size = size if size else random.uniform(0.5, 3.0)
        self.color = color if color else random.choice(STAR_COLORS)
        self.brightness = brightness if brightness else random.uniform(0.3, 1.0)
        self.twinkle_speed = random.uniform(0.02, 0.05)
        self.twinkle_offset = random.uniform(0, 2 * math.pi)
        self.current_brightness = self.brightness

        # Mass and gravity properties
        if mass is None:
            # Mass correlates with size and brightness (larger/brighter stars are more massive)
            base_mass = self.size * 1000  # Base mass
            brightness_factor = self.brightness * 2  # Brighter stars are more massive
            self.mass = base_mass * brightness_factor
        else:
            self.mass = mass

        # Gravitational constant (can be adjusted for simulation)
        self.gravitational_constant = 6.67430e-11  # Real physics constant

        # For future physics calculations
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.velocity_z = 0.0
        self.acceleration_x = 0.0
        self.acceleration_y = 0.0
        self.acceleration_z = 0.0

    def calculate_gravitational_force(self, other_star: Star3D) -> tuple[float, float, float]:
        """Calculate gravitational force between this star and another star"""
        # Calculate distance between stars
        dx = other_star.x - self.x
        dy = other_star.y - self.y
        dz = other_star.z - self.z
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)

        # Avoid division by zero
        if distance == 0:
            return 0, 0, 0

        # Calculate gravitational force magnitude: F = G * m1 * m2 / r^2
        force_magnitude = (self.gravitational_constant * self.mass * other_star.mass) / (distance * distance)

        # Calculate force components (unit vector * magnitude)
        force_x = (dx / distance) * force_magnitude
        force_y = (dy / distance) * force_magnitude
        force_z = (dz / distance) * force_magnitude

        return force_x, force_y, force_z

    def get_mass_category(self) -> str:
        """Return the mass category of this star for display purposes"""
        if self.mass < 500:
            return "Dwarf"
        elif self.mass < 2000:
            return "Small"
        elif self.mass < 5000:
            return "Medium"
        elif self.mass < 10000:
            return "Large"
        else:
            return "Giant"

    def update(self, time: float) -> None:
        # Create twinkling effect with brighter range
        """Update the twinkling brightness for the current `time`."""
        twinkle = math.sin(time * self.twinkle_speed + self.twinkle_offset) * 0.4  # Increased from 0.3
        self.current_brightness = max(0.3, self.brightness + twinkle)  # Increased minimum from 0.1

    def project_to_2d(self, camera: Camera) -> tuple[float, float, float, float] | None:
        """Screen position, depth and a distance-based size scale, or None if behind."""
        projection = camera.project(self.x, self.y, self.z)
        if projection is None:
            return None
        screen_x, screen_y, depth = projection

        # Calculate distance-based scale
        dx = self.x - camera._pos[0]
        dy = self.y - camera._pos[1]
        dz = self.z - camera._pos[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        scale = max(0.1, 1.0 / (distance * 0.01 + 1))

        return screen_x, screen_y, depth, scale

    def draw(self, screen: pygame.Surface, camera: Camera, lens: Lens | None = None) -> None:
        """Draw the star; `lens(x, y, distance)` can move it to one or more lensed images."""
        projection = self.project_to_2d(camera)

        if projection is None:
            return

        screen_x, screen_y, _depth, scale = projection
        if lens is None:
            self._draw_at(screen, screen_x, screen_y, scale)
            return
        distance = math.dist((self.x, self.y, self.z), camera._pos)
        for image_x, image_y in lens(screen_x, screen_y, distance):
            self._draw_at(screen, image_x, image_y, scale)

    def _draw_at(self, screen: pygame.Surface, screen_x: float, screen_y: float, scale: float) -> None:
        # Skip if off screen
        if screen_x < -50 or screen_x > SCREEN_WIDTH + 50 or screen_y < -50 or screen_y > SCREEN_HEIGHT + 50:
            return

        # Apply brightness and distance to color with controlled saturation
        distance_brightness = min(1.0, scale * 3)  # Reduced from 4 to 3
        final_brightness = min(1.5, self.current_brightness * distance_brightness)  # Reduced max from 2.0 to 1.5

        # Apply color with moderate enhancement to avoid oversaturation
        bright_color = tuple(max(0, min(255, int(c * final_brightness))) for c in self.color)

        # Calculate star size based on distance and original size - keep reasonable sizes
        star_size = max(1, int(self.size * scale * 3))  # Reduced from 6 to 3 for sharper stars

        # Draw outer glow for larger stars only, with reduced blur
        if star_size >= 3:
            glow_radius = star_size + 1  # Much smaller glow radius
            # Subtle glow
            glow_color = tuple(max(0, min(255, int(c * 0.3))) for c in bright_color)  # Reduced glow intensity
            pygame.draw.circle(screen, glow_color, (int(screen_x), int(screen_y)), glow_radius)

        # Draw main star with sharp edges - use anti-aliased circles for smoothness
        if star_size >= 2:
            pygame.draw.circle(screen, bright_color, (int(screen_x), int(screen_y)), star_size)
            # Add a bright center pixel for sharpness
            pygame.draw.circle(screen, (255, 255, 255), (int(screen_x), int(screen_y)), max(1, star_size // 2))
        else:
            # For small stars, just draw a simple pixel
            pygame.draw.circle(screen, bright_color, (int(screen_x), int(screen_y)), star_size)

        # Draw sharp cross pattern for bigger stars
        if star_size >= 2:
            cross_length = star_size + 1  # Shorter cross lines
            # Sharp, bright cross lines
            cross_color = bright_color  # Use the same bright color
            pygame.draw.line(screen, cross_color,
                           (int(screen_x - cross_length), int(screen_y)),
                           (int(screen_x + cross_length), int(screen_y)), 1)  # Thinner, sharper lines
            pygame.draw.line(screen, cross_color,
                           (int(screen_x), int(screen_y - cross_length)),
                           (int(screen_x), int(screen_y + cross_length)), 1)
