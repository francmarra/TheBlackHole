"""The Sun and a random field of stars around it."""

import math
import random

from .config import NUM_STARS, STAR_MIN_SUN_DISTANCE, STARFIELD_EXTENT
from .star import Star3D
from .sun import Sun3D


class StarField3D:
    def __init__(self, num_stars=NUM_STARS, clear_zones=()):
        self.stars = []
        self.sun = None
        self.clear_zones = clear_zones  # (center, radius) regions kept free of stars
        self.generate_stars(num_stars)

    def generate_stars(self, num_stars):
        """Generate a 3D distribution of stars with the Sun at the center"""
        # Clear existing stars
        self.stars = []

        # Add the Sun at the center
        self.sun = Sun3D(0, 0, 0)
        self.stars.append(self.sun)

        # Generate other stars around the Sun
        while len(self.stars) < num_stars:
            # Generate stars in a large 3D space around the Sun
            x = random.randint(-STARFIELD_EXTENT, STARFIELD_EXTENT)
            y = random.randint(-STARFIELD_EXTENT, STARFIELD_EXTENT)
            z = random.randint(-STARFIELD_EXTENT, STARFIELD_EXTENT)

            # Avoid placing stars too close to the Sun
            distance_from_sun = math.sqrt(x*x + y*y + z*z)
            if distance_from_sun < STAR_MIN_SUN_DISTANCE:
                continue

            # Keep stars away from planets so they never float next to the player
            if any(math.dist((x, y, z), center) < radius for center, radius in self.clear_zones):
                continue

            # Create different types of stars with different probabilities
            star_type = random.random()

            if star_type < 0.7:  # 70% small dim stars
                size = random.uniform(0.5, 1.5)
                brightness = random.uniform(0.6, 0.9)
            elif star_type < 0.9:  # 20% medium stars
                size = random.uniform(1.5, 2.5)
                brightness = random.uniform(0.8, 1.0)
            else:  # 10% bright large stars
                size = random.uniform(2.5, 4.0)
                brightness = random.uniform(1.0, 1.3)

            star = Star3D(x, y, z, size, brightness=brightness)
            self.stars.append(star)

    def update(self, time):
        for star in self.stars:
            star.update(time)

    def draw(self, screen, camera, min_distance=0.0, max_distance=math.inf):
        """Draw the stars whose distance to the camera is within [min_distance, max_distance)."""
        cx, cy, cz = camera._pos
        min_sq, max_sq = min_distance * min_distance, max_distance * max_distance
        star_distances = []
        for star in self.stars:
            dx = star.x - cx
            dy = star.y - cy
            dz = star.z - cz
            distance = dx*dx + dy*dy + dz*dz
            if min_sq <= distance < max_sq:
                star_distances.append((distance, star))

        # Sort by distance (far to near)
        star_distances.sort(key=lambda x: x[0], reverse=True)

        # Draw stars
        for distance, star in star_distances:
            star.draw(screen, camera)
