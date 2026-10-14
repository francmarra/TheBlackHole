"""The Sun: a bigger, brighter star with a corona and flares."""

import math

import pygame

from .config import SCREEN_HEIGHT, SCREEN_WIDTH
from .star import Star3D


class Sun3D(Star3D):
    def __init__(self, x, y, z):
        # Sun properties based on real astronomical data
        sun_size = 10.0  # Larger visual size for the Sun
        sun_color = (255, 255, 150)  # Yellowish color
        sun_brightness = 2.0  # Very bright
        sun_mass = 1.9885e30  # Real Sun mass in kg

        super().__init__(x, y, z, size=sun_size, color=sun_color, brightness=sun_brightness, mass=sun_mass)

        # Sun-specific properties
        self.volume = 1.412e18  # km³
        self.density = 1.408  # g/cm³
        self.earth_mass_ratio = 332950  # Times Earth's mass
        self.earth_volume_ratio = 1300000  # Times Earth's volume
        self.is_sun = True

        # Enhanced visual properties for the Sun
        self.corona_size = 15  # Corona glow size
        self.flare_intensity = 0.5  # Solar flare effect

    def update(self, time):
        # Sun has more complex twinkling (solar activity)
        primary_twinkle = math.sin(time * 0.01) * 0.1
        secondary_twinkle = math.sin(time * 0.03 + 1.5) * 0.05
        solar_flare = math.sin(time * 0.02 + 2.0) * 0.1

        self.current_brightness = max(1.5, self.brightness + primary_twinkle + secondary_twinkle + solar_flare)

    def draw(self, screen, camera):
        projection = self.project_to_2d(camera)

        if projection is None:
            return

        screen_x, screen_y, depth, scale = projection

        # Skip if off screen
        if screen_x < -100 or screen_x > SCREEN_WIDTH + 100 or screen_y < -100 or screen_y > SCREEN_HEIGHT + 100:
            return

        # Sun is always visible and bright
        distance_brightness = max(0.8, min(1.5, scale * 5))  # Sun stays bright at distance
        final_brightness = min(2.5, self.current_brightness * distance_brightness)

        # Enhanced Sun color with brightness
        bright_color = tuple(max(0, min(255, int(c * final_brightness))) for c in self.color)

        # Calculate Sun size (always significant)
        sun_size = max(5, int(self.size * scale * 4))

        # Draw corona (outermost layer)
        corona_radius = sun_size + int(self.corona_size * scale)
        corona_color = tuple(max(0, min(255, int(c * 0.1))) for c in bright_color)
        if corona_radius > 0:
            pygame.draw.circle(screen, corona_color, (int(screen_x), int(screen_y)), corona_radius)

        # Draw outer atmosphere
        atmosphere_radius = sun_size + int(8 * scale)
        atmosphere_color = tuple(max(0, min(255, int(c * 0.3))) for c in bright_color)
        if atmosphere_radius > 0:
            pygame.draw.circle(screen, atmosphere_color, (int(screen_x), int(screen_y)), atmosphere_radius)

        # Draw main Sun body
        pygame.draw.circle(screen, bright_color, (int(screen_x), int(screen_y)), sun_size)

        # Draw bright core
        core_size = max(2, sun_size // 2)
        core_color = (255, 255, 255)  # White hot core
        pygame.draw.circle(screen, core_color, (int(screen_x), int(screen_y)), core_size)

        # Draw solar flares (cross pattern)
        flare_length = sun_size + int(10 * scale)
        flare_color = tuple(max(0, min(255, int(c * 0.8))) for c in bright_color)

        # Main cross
        pygame.draw.line(screen, flare_color,
                       (int(screen_x - flare_length), int(screen_y)),
                       (int(screen_x + flare_length), int(screen_y)), 3)
        pygame.draw.line(screen, flare_color,
                       (int(screen_x), int(screen_y - flare_length)),
                       (int(screen_x), int(screen_y + flare_length)), 3)

        # Diagonal cross for extra solar effect
        diagonal_length = int(flare_length * 0.7)
        pygame.draw.line(screen, flare_color,
                       (int(screen_x - diagonal_length), int(screen_y - diagonal_length)),
                       (int(screen_x + diagonal_length), int(screen_y + diagonal_length)), 2)
        pygame.draw.line(screen, flare_color,
                       (int(screen_x - diagonal_length), int(screen_y + diagonal_length)),
                       (int(screen_x + diagonal_length), int(screen_y - diagonal_length)), 2)

    def get_mass_category(self):
        return "Sun"
