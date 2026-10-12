import pygame
import random
import math
import sys
import numpy as np

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
STAR_COLORS = [
    (255, 255, 255),  # Pure white
    (255, 255, 100),  # Bright yellow
    (255, 150, 50),   # Bright orange
    (150, 200, 255),  # Bright blue-white
    (255, 80, 80),    # Bright red
    (100, 255, 100),  # Bright green
    (255, 100, 255),  # Bright magenta
    (100, 255, 255),  # Bright cyan
]

# Camera
FOCAL_LENGTH = 500
NEAR_PLANE = 0.5

# Planet
PLANET_CENTER = (900.0, 0.0, 0.0)
PLANET_RADIUS = 150.0
AMBIENT_LIGHT = 0.18  # How much light the night side still gets

# Player
WALK_SPEED = 10.0     # units per second
RUN_SPEED = 25.0
TURN_SPEED = 2.0      # radians per second
JUMP_SPEED = 10.0
GRAVITY = 25.0


def normalize(v):
    length = np.linalg.norm(v)
    return v / length if length > 1e-12 else v


class Camera:
    """A 3D camera with a free orientation, stored as right/up/forward vectors."""

    def __init__(self, focal_length=FOCAL_LENGTH):
        self.focal_length = focal_length
        self.position = np.zeros(3)
        self.right = np.array([1.0, 0.0, 0.0])
        self.up = np.array([0.0, 1.0, 0.0])
        self.forward = np.array([0.0, 0.0, 1.0])
        self._update_cache()

    def look_at(self, position, target, up_hint):
        """Place the camera at `position`, looking at `target`, with `up_hint` as up."""
        self.position = np.asarray(position, dtype=float)
        self.forward = normalize(np.asarray(target, dtype=float) - self.position)
        self.right = normalize(np.cross(up_hint, self.forward))
        self.up = np.cross(self.forward, self.right)
        self._update_cache()

    def set_yaw_pitch(self, position, yaw, pitch):
        """Classic free-fly orientation, with the world Y axis as up."""
        self.position = np.asarray(position, dtype=float)
        cos_pitch = math.cos(pitch)
        self.forward = np.array([math.sin(yaw) * cos_pitch, math.sin(pitch), math.cos(yaw) * cos_pitch])
        self.right = np.array([math.cos(yaw), 0.0, -math.sin(yaw)])
        self.up = np.cross(self.forward, self.right)
        self._update_cache()

    def _update_cache(self):
        # Plain Python floats are much faster than NumPy for projecting single points
        self._pos = self.position.tolist()
        self._right = self.right.tolist()
        self._up = self.up.tolist()
        self._forward = self.forward.tolist()

    def to_camera_space(self, points):
        """Convert world points (N, 3) to camera space: x right, y up, z forward."""
        basis = np.array([self.right, self.up, self.forward])
        return (np.asarray(points, dtype=float) - self.position) @ basis.T

    def project_camera_space(self, cam_points):
        """Project camera-space points (..., 3) with z > 0 to screen coordinates (..., 2)."""
        z = cam_points[..., 2]
        screen_x = SCREEN_WIDTH / 2 + cam_points[..., 0] * self.focal_length / z
        screen_y = SCREEN_HEIGHT / 2 - cam_points[..., 1] * self.focal_length / z
        return np.stack([screen_x, screen_y], axis=-1)

    def project(self, x, y, z):
        """Project a single world point. Returns (screen_x, screen_y, depth) or None if behind."""
        px, py, pz = self._pos
        dx, dy, dz = x - px, y - py, z - pz
        r, u, f = self._right, self._up, self._forward
        depth = dx * f[0] + dy * f[1] + dz * f[2]
        if depth <= NEAR_PLANE:
            return None
        cam_x = dx * r[0] + dy * r[1] + dz * r[2]
        cam_y = dx * u[0] + dy * u[1] + dz * u[2]
        screen_x = SCREEN_WIDTH / 2 + cam_x * self.focal_length / depth
        screen_y = SCREEN_HEIGHT / 2 - cam_y * self.focal_length / depth
        return screen_x, screen_y, depth


def clip_polygon_near(points, near=NEAR_PLANE):
    """Cut away the part of a camera-space polygon that is behind the near plane."""
    clipped = []
    for i in range(len(points)):
        a = points[i]
        b = points[(i + 1) % len(points)]
        a_inside = a[2] >= near
        b_inside = b[2] >= near
        if a_inside:
            clipped.append(a)
        if a_inside != b_inside:
            t = (near - a[2]) / (b[2] - a[2])
            clipped.append(a + (b - a) * t)
    return clipped


def draw_faces(screen, camera, faces):
    """Draw (depth, camera_space_polygon, color) faces from far to near (painter's algorithm)."""
    faces.sort(key=lambda face: face[0], reverse=True)
    for _, polygon, color in faces:
        if (polygon[:, 2] < NEAR_PLANE).any():
            polygon = clip_polygon_near(polygon)
            if len(polygon) < 3:
                continue
            polygon = np.array(polygon)
        pygame.draw.polygon(screen, color, camera.project_camera_space(polygon).tolist())


def shade_color(color, normal, light_dir, sunlight=1.0):
    """Ambient light plus sunlight on a face; `sunlight` is 0 inside the planet's shadow."""
    diffuse = max(0.0, float(np.dot(normal, light_dir))) * sunlight
    light = AMBIENT_LIGHT + (1 - AMBIENT_LIGHT) * diffuse
    return tuple(max(0, min(255, int(c * light))) for c in color)


class Star3D:
    def __init__(self, x, y, z, size=None, color=None, brightness=None, mass=None):
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

    def calculate_gravitational_force(self, other_star):
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

    def get_mass_category(self):
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

    def update(self, time):
        # Create twinkling effect with brighter range
        twinkle = math.sin(time * self.twinkle_speed + self.twinkle_offset) * 0.4  # Increased from 0.3
        self.current_brightness = max(0.3, self.brightness + twinkle)  # Increased minimum from 0.1

    def project_to_2d(self, camera):
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

    def draw(self, screen, camera):
        projection = self.project_to_2d(camera)

        if projection is None:
            return

        screen_x, screen_y, depth, scale = projection

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

class StarField3D:
    def __init__(self, num_stars=800, clear_zones=()):
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
            x = random.randint(-3000, 3000)
            y = random.randint(-3000, 3000)
            z = random.randint(-3000, 3000)

            # Avoid placing stars too close to the Sun
            distance_from_sun = math.sqrt(x*x + y*y + z*z)
            if distance_from_sun < 50:  # Minimum distance from Sun
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


class Planet:
    """A spherical planet drawn as a shaded mesh of flat faces."""

    def __init__(self, center, radius, seed=7):
        self.center = np.array(center, dtype=float)
        self.radius = radius
        rng = np.random.default_rng(seed)
        # Detailed mesh for walking on the surface, cheap one for viewing from far away
        self.near_mesh = self._build_mesh(72, rng)
        self.far_mesh = self._build_mesh(16, rng)

    def _build_mesh(self, subdivisions, rng):
        """Build a "cube sphere": a subdivided cube pushed out into a sphere.

        Unlike a latitude/longitude sphere, all faces have about the same size,
        so the poles don't end up with thousands of tiny faces.
        """
        n = subdivisions
        # tan() spreads the grid so the faces stay evenly sized after projection
        steps = np.tan(np.linspace(-math.pi / 4, math.pi / 4, n + 1))
        a, b = np.meshgrid(steps, steps, indexing="ij")
        a, b = a.ravel(), b.ravel()

        i, j = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
        corner = (i * (n + 1) + j).ravel()
        quad = np.stack([corner, corner + n + 1, corner + n + 2, corner + 1], axis=-1)

        directions, faces = [], []
        for axis in range(3):
            for sign in (-1.0, 1.0):
                points = np.empty((len(a), 3))
                points[:, axis] = sign
                points[:, (axis + 1) % 3] = a
                points[:, (axis + 2) % 3] = b
                faces.append(quad + len(directions) * len(a))
                directions.append(points)
        directions = np.concatenate(directions)
        directions /= np.linalg.norm(directions, axis=1, keepdims=True)
        faces = np.concatenate(faces)
        vertices = self.center + directions * self.radius

        normals = directions[faces].mean(axis=1)
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)
        centers = self.center + normals * self.radius
        colors = self._surface_colors(normals, rng)
        return vertices, faces, normals, centers, colors

    @staticmethod
    def _terrain(normals):
        """Layered sine waves: `continents` > 0 is land, `detail` adds small variations."""
        x, y, z = np.atleast_2d(normals).T
        continents = (np.sin(3.1 * x + 1.7) * np.sin(2.3 * y + 0.5) * np.sin(2.9 * z + 2.1)
                      + 0.5 * np.sin(6.7 * x + 2.9 * z + 0.3) * np.sin(5.3 * y + 1.1))
        detail = np.sin(11 * x + 3) * np.sin(13 * y + 1) * np.sin(12 * z + 2)
        is_ice = np.abs(y) > 0.82 + 0.05 * detail
        is_land = (continents > 0.05) & ~is_ice
        return continents, detail, is_land, is_ice

    def is_land(self, normal):
        return bool(self._terrain(normal)[2][0])

    @classmethod
    def _surface_colors(cls, normals, rng):
        """Paint oceans, land and ice caps."""
        continents, detail, is_land, is_ice = cls._terrain(normals)

        deep_ocean = np.array([25, 60, 140])
        shallow_ocean = np.array([45, 115, 185])
        grass = np.array([70, 140, 60])
        rock = np.array([130, 110, 75])
        ice = np.array([225, 235, 245])

        t_sea = np.clip(1 + continents * 3, 0, 1)[:, None]
        sea = deep_ocean * (1 - t_sea) + shallow_ocean * t_sea
        t_land = np.clip(0.5 + 0.5 * detail, 0, 1)[:, None]
        land = grass * (1 - t_land) + rock * t_land

        colors = np.where(is_land[:, None], land, sea)
        colors = np.where(is_ice[:, None], ice, colors)
        # Small random variation per face so movement on the ground is easy to see
        return colors * rng.uniform(0.9, 1.1, (len(normals), 1))

    def draw(self, screen, camera, light_dir):
        distance = np.linalg.norm(camera.position - self.center)
        vertices, faces, normals, centers, colors = (
            self.near_mesh if distance < self.radius * 4 else self.far_mesh)

        # Back-face culling: keep only the faces turned towards the camera
        facing = np.einsum("ij,ij->i", centers - camera.position, normals) < 0
        visible = np.nonzero(facing)[0]
        if len(visible) == 0:
            return

        cam_vertices = camera.to_camera_space(vertices)
        face_points = cam_vertices[faces[visible]]          # (k, 4, 3)
        z = face_points[..., 2]
        in_front = (z >= NEAR_PLANE).all(axis=1)
        partly_in_front = (z >= NEAR_PLANE).any(axis=1)

        # Faces fully in front of the camera are projected all at once
        safe = cam_vertices.copy()
        safe[:, 2] = np.maximum(safe[:, 2], NEAR_PLANE)
        screen_points = camera.project_camera_space(safe)[faces[visible]]  # (k, 4, 2)
        sx, sy = screen_points[..., 0], screen_points[..., 1]
        off_screen = ((sx.max(axis=1) < 0) | (sx.min(axis=1) > SCREEN_WIDTH)
                      | (sy.max(axis=1) < 0) | (sy.min(axis=1) > SCREEN_HEIGHT))

        light = AMBIENT_LIGHT + (1 - AMBIENT_LIGHT) * np.clip(normals[visible] @ light_dir, 0, 1)
        shaded = np.clip(colors[visible] * light[:, None], 0, 255).astype(int).tolist()

        screen_list = screen_points.tolist()
        for k in np.argsort(-z.mean(axis=1)):
            if not partly_in_front[k] or (in_front[k] and off_screen[k]):
                continue
            if in_front[k]:
                points = screen_list[k]
            else:
                clipped = clip_polygon_near(face_points[k])
                if len(clipped) < 3:
                    continue
                points = camera.project_camera_space(np.array(clipped)).tolist()
            pygame.draw.polygon(screen, shaded[k], points)


# Corner order inside a box: index = x_bit * 4 + y_bit * 2 + z_bit
BOX_FACES = [
    ([0, 2, 3, 1], (-1, 0, 0)),
    ([4, 5, 7, 6], (1, 0, 0)),
    ([0, 1, 5, 4], (0, -1, 0)),
    ([2, 6, 7, 3], (0, 1, 0)),
    ([0, 4, 6, 2], (0, 0, -1)),
    ([1, 3, 7, 5], (0, 0, 1)),
]

SUIT = (230, 230, 235)
SUIT_DARK = (190, 190, 200)
BACKPACK = (150, 150, 165)
VISOR = (235, 170, 60)


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


class SpaceSimulation3D:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("TheBlackHole - Planet Explorer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.running = True

        self.planet = Planet(PLANET_CENTER, PLANET_RADIUS)
        self.new_star_field()

        self.player = self.create_player()

        self.camera = Camera()
        self.mode = "planet"  # "planet" = third person on the planet, "free" = free-fly camera

        # Third-person camera
        self.camera_distance = 14.0
        self.camera_elevation = 0.25  # Radians above the player's horizon

        # Free camera
        self.free_position = np.zeros(3)
        self.free_yaw = 0.0
        self.free_pitch = 0.0
        self.free_speed = 600.0
        self.rotation_speed = 1.2  # radians per second

        # Mouse control variables
        self.mouse_sensitivity = 0.003
        self.mouse_captured = False

        self.update_camera()

    def create_player(self):
        """Start on land, on the day side, with the Sun behind the camera so the player is lit."""
        to_sun = normalize(self.star_field.sun_position - self.planet.center)
        tilt = math.radians(50)  # Angle between the start point and the point right under the Sun
        for angle in np.linspace(0, 2 * math.pi, 72, endpoint=False):
            sideways = np.array([0.0, math.sin(angle), math.cos(angle)])
            normal = to_sun * math.cos(tilt) + sideways * math.sin(tilt)
            if self.planet.is_land(normal):
                break
        sun_ahead = normalize(to_sun - np.dot(to_sun, normal) * normal)
        heading = -sun_ahead * 0.6 + np.cross(normal, sun_ahead) * 0.8
        return Player(self.planet, normal, heading)

    def new_star_field(self):
        self.star_field = StarField3D(800, clear_zones=[(tuple(self.planet.center), 1200)])
        sun = self.star_field.sun
        self.star_field.sun_position = np.array([sun.x, sun.y, sun.z], dtype=float)

    def toggle_mode(self):
        if self.mode == "planet":
            # Start flying from where the third-person camera is
            self.mode = "free"
            self.free_position = self.camera.position.copy()
            forward = self.camera.forward
            self.free_yaw = math.atan2(forward[0], forward[2])
            self.free_pitch = math.asin(max(-1.0, min(1.0, forward[1])))
        else:
            self.mode = "planet"

    def handle_events(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_n:
                    self.new_star_field()
                elif event.key == pygame.K_TAB:
                    self.toggle_mode()
                elif event.key == pygame.K_SPACE and self.mode == "planet":
                    self.player.jump()
                elif event.key == pygame.K_c:
                    # Toggle mouse capture
                    self.mouse_captured = not self.mouse_captured
                    pygame.mouse.set_visible(not self.mouse_captured)
                    pygame.event.set_grab(self.mouse_captured)
            elif event.type == pygame.MOUSEWHEEL and self.mode == "planet":
                self.camera_distance = max(5.0, min(60.0, self.camera_distance - event.y * 1.5))
            elif event.type == pygame.MOUSEMOTION and self.mouse_captured:
                mouse_x, mouse_y = event.rel
                if self.mode == "planet":
                    self.player.turn(mouse_x * self.mouse_sensitivity)
                    self.tilt_camera(mouse_y * self.mouse_sensitivity)
                else:
                    self.free_yaw += mouse_x * self.mouse_sensitivity
                    self.free_pitch -= mouse_y * self.mouse_sensitivity
                    self.free_pitch = max(-math.pi/2 + 0.1, min(math.pi/2 - 0.1, self.free_pitch))

        keys = pygame.key.get_pressed()
        if self.mode == "planet":
            self.handle_player_keys(keys, dt)
        else:
            self.handle_free_camera_keys(keys, dt)

    def tilt_camera(self, amount):
        self.camera_elevation = max(-0.08, min(1.4, self.camera_elevation + amount))

    def handle_player_keys(self, keys, dt):
        speed = (RUN_SPEED if keys[pygame.K_LSHIFT] else WALK_SPEED) * dt
        forward = (keys[pygame.K_w] - keys[pygame.K_s]) * speed
        sideways = (keys[pygame.K_d] - keys[pygame.K_a]) * speed
        self.player.move(forward, sideways)

        self.player.turn((keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * TURN_SPEED * dt)
        self.tilt_camera((keys[pygame.K_DOWN] - keys[pygame.K_UP]) * self.rotation_speed * dt)

    def handle_free_camera_keys(self, keys, dt):
        speed = self.free_speed * (5 if keys[pygame.K_LSHIFT] else 1) * dt
        cos_yaw = math.cos(self.free_yaw)
        sin_yaw = math.sin(self.free_yaw)
        forward = np.array([sin_yaw, 0.0, cos_yaw])
        right = np.array([cos_yaw, 0.0, -sin_yaw])
        up = np.array([0.0, 1.0, 0.0])

        self.free_position += forward * (keys[pygame.K_w] - keys[pygame.K_s]) * speed
        self.free_position += right * (keys[pygame.K_d] - keys[pygame.K_a]) * speed
        self.free_position += up * (keys[pygame.K_q] - keys[pygame.K_e]) * speed

        self.free_yaw += (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.rotation_speed * dt
        self.free_pitch += (keys[pygame.K_UP] - keys[pygame.K_DOWN]) * self.rotation_speed * dt
        self.free_pitch = max(-math.pi/2 + 0.1, min(math.pi/2 - 0.1, self.free_pitch))

    def update_camera(self):
        if self.mode == "free":
            self.camera.set_yaw_pitch(self.free_position, self.free_yaw, self.free_pitch)
            return

        # Third person: behind the player and slightly above, looking at the helmet
        player = self.player
        target = player.position + player.normal * 2.0
        horizontal = self.camera_distance * math.cos(self.camera_elevation)
        vertical = self.camera_distance * math.sin(self.camera_elevation)
        position = target - player.heading * horizontal + player.normal * vertical

        # Never let the camera sink into the ground
        offset = position - self.planet.center
        min_radius = self.planet.radius + 0.8
        if np.linalg.norm(offset) < min_radius:
            position = self.planet.center + normalize(offset) * min_radius
        self.camera.look_at(position, target, player.normal)

    def update(self, dt):
        time = pygame.time.get_ticks() / 1000.0
        self.star_field.update(time)
        self.player.update(dt)
        self.update_camera()

    def light_direction(self):
        return normalize(self.star_field.sun_position - self.planet.center)

    def draw(self):
        self.screen.fill(BLACK)

        # Stars behind the planet first, then the planet hides them, then the ones in front
        planet_distance = float(np.linalg.norm(self.camera.position - self.planet.center))
        self.star_field.draw(self.screen, self.camera, min_distance=planet_distance)
        self.planet.draw(self.screen, self.camera, self.light_direction())
        self.player.draw(self.screen, self.camera, self.light_direction())
        self.star_field.draw(self.screen, self.camera, max_distance=planet_distance)

        # Draw UI
        self.draw_ui()

        pygame.display.flip()

    def draw_text_lines(self, lines, x, color, title_color=None):
        for i, line in enumerate(lines):
            line_color = title_color if (i == 0 and title_color) else color
            self.screen.blit(self.font.render(line, True, line_color), (x, 10 + i * 22))

    def draw_ui(self):
        if self.mode == "planet":
            instructions = [
                "TheBlackHole - Planet Explorer",
                "WASD - Walk / strafe",
                "SHIFT - Run",
                "SPACE - Jump",
                "Mouse (press C) / Arrows - Turn and tilt camera",
                "Mouse wheel - Zoom",
                "TAB - Free camera",
                "N - New stars",
                "ESC - Exit",
            ]
            player = self.player
            to_sun = normalize(self.star_field.sun_position - player.position)
            sun_elevation = math.degrees(math.asin(max(-1.0, min(1.0, float(np.dot(player.normal, to_sun))))))
            latitude = math.degrees(math.asin(max(-1.0, min(1.0, float(player.normal[1])))))
            longitude = math.degrees(math.atan2(player.normal[2], player.normal[0]))
            status_info = [
                f"FPS: {self.clock.get_fps():.0f}",
                f"Latitude: {latitude:.1f}°",
                f"Longitude: {longitude:.1f}°",
                f"Altitude: {player.altitude:.1f}",
                f"Sun Elevation: {sun_elevation:.1f}°",
                f"Time of Day: {'Day' if sun_elevation > 0 else 'Night'}",
                f"Mouse Look: {'ON' if self.mouse_captured else 'OFF'}",
            ]
        else:
            instructions = [
                "TheBlackHole - Free Camera",
                "WASD - Move forward/back/left/right",
                "QE - Move up/down",
                "SHIFT - Fast movement",
                "Mouse (press C) / Arrows - Look around",
                "TAB - Back to the planet",
                "N - New stars",
                "ESC - Exit",
            ]
            position = self.camera.position
            sun = self.star_field.sun
            status_info = [
                f"FPS: {self.clock.get_fps():.0f}",
                f"Stars: {len(self.star_field.stars)}",
                f"Sun Mass: {sun.mass:.2e} kg",
                f"Sun Distance: {np.linalg.norm(position - self.star_field.sun_position):.0f} units",
                f"Planet Distance: {np.linalg.norm(position - self.planet.center):.0f} units",
                f"Position: ({position[0]:.0f}, {position[1]:.0f}, {position[2]:.0f})",
                f"Pitch: {math.degrees(self.free_pitch):.1f}°",
                f"Yaw: {math.degrees(self.free_yaw):.1f}°",
                f"Mouse Look: {'ON' if self.mouse_captured else 'OFF'}",
            ]

        self.draw_text_lines(instructions, 10, (200, 200, 200), WHITE)
        self.draw_text_lines(status_info, SCREEN_WIDTH - 280, (150, 150, 150))

        # Crosshair
        if self.mouse_captured and self.mode == "free":
            center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            pygame.draw.line(self.screen, (100, 100, 100),
                           (center_x - 10, center_y), (center_x + 10, center_y), 2)
            pygame.draw.line(self.screen, (100, 100, 100),
                           (center_x, center_y - 10), (center_x, center_y + 10), 2)

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.handle_events(dt)
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("Starting TheBlackHole - Planet Explorer...")
    print("Walk on the planet with WASD, jump with SPACE.")
    print("Press C to control the camera with the mouse, TAB for the free camera.")
    simulation = SpaceSimulation3D()
    simulation.run()
