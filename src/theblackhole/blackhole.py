"""A black hole: a heavy body with an event horizon, and the scene around it."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np
import pygame
from numpy.typing import NDArray

from .aliases import ArrayLike, Point2, Vector
from .config import (
    BLACK_HOLE_MASS,
    BLACK_HOLE_STARS,
    DISK_COOL_COLOR,
    DISK_DRAG,
    DISK_HOT_COLOR,
    DISK_INNER,
    DISK_OUTER,
    DISK_PARTICLES,
    DISK_THICKNESS,
    GRAVITY_CONSTANT,
    PHOTON_RING_COLOR,
    PHYSICS_MAX_STEP,
    ROCK_COLOR,
    ROCK_RADIUS,
    ROCK_SPEED,
    SHADOW_FACTOR,
    SPEED_OF_LIGHT,
)
from .glow import draw_glow
from .physics import Body, GravitySystem
from .scenario import ScenarioError, number, vector
from .starfield import StarField3D

if TYPE_CHECKING:
    from .camera import Camera


def schwarzschild_radius(mass: float, g: float = GRAVITY_CONSTANT, c: float = SPEED_OF_LIGHT) -> float:
    """Radius of the event horizon of a non-rotating black hole: r_s = 2GM/c²."""
    return 2 * g * mass / c**2


class BlackHole(Body):
    """A non-rotating (Schwarzschild) black hole."""

    def __init__(self, position: ArrayLike = (0.0, 0.0, 0.0), mass: float = BLACK_HOLE_MASS) -> None:
        super().__init__(position, (0, 0, 0), mass)

    @property
    def horizon_radius(self) -> float:
        """Schwarzschild radius r_s of this black hole."""
        return schwarzschild_radius(self.mass)

    @property
    def shadow_radius(self) -> float:
        """Radius of the dark shadow seen from far away."""
        return SHADOW_FACTOR * self.horizon_radius

    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw the shadow with its glow and photon ring."""
        projection = camera.project(*self.position)
        if projection is None:
            return
        x, y, depth = projection
        radius_px = max(2, int(self.shadow_radius * camera.focal_length / depth))
        center = (int(x), int(y))
        draw_glow(screen, center, radius_px * 1.8, PHOTON_RING_COLOR, 0.35)
        # Thin bright ring where light orbits just outside the shadow, then pure black inside
        pygame.draw.circle(screen, PHOTON_RING_COLOR, center, radius_px + max(1, radius_px // 25))
        pygame.draw.circle(screen, (0, 0, 0), center, radius_px)


def lensed_offsets(beta: float, einstein_radius: float) -> tuple[float, float]:
    """Point-mass lens: a source at angle `beta` from the lens appears at two angles.

    theta = (beta ± sqrt(beta² + 4 θ_E²)) / 2. The + image is outside the Einstein ring,
    the - image is inside it, on the other side of the lens.
    """
    root = math.sqrt(beta * beta + 4 * einstein_radius * einstein_radius)
    return (beta + root) / 2, (beta - root) / 2


def hud_readout(black_hole: BlackHole, position: ArrayLike, speed: float) -> dict[str, float]:
    """Numbers shown in the HUD for an observer at `position` moving at `speed`."""
    distance = float(np.linalg.norm(np.asarray(position, dtype=float) - black_hole.position))
    r_s = black_hole.horizon_radius
    escape = math.sqrt(2 * GRAVITY_CONSTANT * black_hole.mass / distance)
    # Gravitational time dilation for a static observer: dτ/dt = sqrt(1 - r_s / r)
    clock_rate = math.sqrt(max(0.0, 1 - r_s / distance))
    return {
        "mass": black_hole.mass,
        "horizon": r_s,
        "distance": distance,
        "distance_rs": distance / r_s,
        "speed": speed,
        "speed_c": speed / SPEED_OF_LIGHT,
        "escape_c": escape / SPEED_OF_LIGHT,
        "clock_rate": clock_rate,
    }


class GravitationalLens:
    """Moves background stars on screen as the black hole's gravity bends their light."""

    def __init__(self, black_hole: BlackHole, camera: Camera) -> None:
        self.camera = camera
        self.lens_distance = float(np.linalg.norm(black_hole.position - camera.position))
        projection = camera.project(*black_hole.position)
        self.center = projection[:2] if projection else None
        self.r_s = black_hole.horizon_radius
        self.shadow_px = black_hole.shadow_radius * camera.focal_length / max(self.lens_distance, 1e-9)

    def __call__(self, x: float, y: float, source_distance: float) -> list[Point2]:
        """Lensed screen positions of a star drawn at (x, y) that is `source_distance` away."""
        if self.center is None or source_distance <= self.lens_distance:
            return [(x, y)]
        # Einstein radius in radians: θ_E = sqrt(4GM/c² · D_ls / (D_l · D_s)), and 4GM/c² = 2 r_s
        d_ls = source_distance - self.lens_distance
        theta_e = math.sqrt(2 * self.r_s * d_ls / (self.lens_distance * source_distance))
        einstein_px = theta_e * self.camera.focal_length
        dx, dy = x - self.center[0], y - self.center[1]
        beta = math.hypot(dx, dy)
        if beta < 1e-6 or beta > 20 * einstein_px:
            return [(x, y)]  # Far from the lens the shift is too small to see
        ux, uy = dx / beta, dy / beta
        images = []
        for theta in lensed_offsets(beta, einstein_px):
            if abs(theta) > self.shadow_px:  # Images inside the shadow are swallowed
                images.append((self.center[0] + ux * theta, self.center[1] + uy * theta))
        return images


class AccretionDisk:
    """Massless particles orbiting a black hole, integrated together as NumPy arrays."""

    def __init__(self, black_hole: BlackHole, count: int = DISK_PARTICLES, seed: int = 1) -> None:
        self.black_hole = black_hole
        self.rng = np.random.default_rng(seed)
        r_s = black_hole.horizon_radius
        self.inner, self.outer = DISK_INNER * r_s, DISK_OUTER * r_s
        self.positions = np.zeros((count, 3))
        self.velocities = np.zeros((count, 3))
        self.colors = np.zeros((count, 3))
        self.spawn(np.arange(count))
        self.accelerations = self._accelerations()

    def spawn(self, index: NDArray[np.intp]) -> None:
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

    def _accelerations(self) -> Vector:
        offset = self.black_hole.position - self.positions
        dist2 = np.einsum("ij,ij->i", offset, offset)
        return GRAVITY_CONSTANT * self.black_hole.mass * offset / (dist2 * np.sqrt(dist2))[:, None]

    def step(self, dt: float) -> int:
        """Advance the disk; returns how many particles crossed the horizon (they respawn outside)."""
        self.velocities += 0.5 * dt * self.accelerations
        self.positions += dt * self.velocities
        self.accelerations = self._accelerations()
        self.velocities += 0.5 * dt * self.accelerations
        self.velocities *= 1 - DISK_DRAG * dt

        distance = np.linalg.norm(self.positions - self.black_hole.position, axis=1)
        captured = np.nonzero(distance < self.black_hole.horizon_radius)[0]
        if len(captured):
            self.spawn(captured)
            self.accelerations[captured] = self._accelerations()[captured]
        return len(captured)

    def draw(
        self,
        screen: pygame.Surface,
        camera: Camera,
        min_distance: float = 0.0,
        max_distance: float = math.inf,
    ) -> None:
        """Draw the particles at [min_distance, max_distance) from the camera, far to near."""
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
            draw_glow(screen, point, size * 3, color, 0.4)
            pygame.draw.circle(screen, color, point, max(1, size - 1))


class Rock(Body):
    """A small body thrown at the black hole."""

    radius = ROCK_RADIUS
    color = ROCK_COLOR


class BlackHoleScene:
    """A black hole at the origin in front of a field of distant stars."""

    def __init__(self) -> None:
        self.black_hole = BlackHole()
        self.gravity = GravitySystem([self.black_hole])
        self.disk = AccretionDisk(self.black_hole)
        self.star_field = StarField3D(BLACK_HOLE_STARS, with_sun=False)
        self.rocks: list[Rock] = []
        self.captured = 0  # Everything that crossed the event horizon so far

    def to_dict(self) -> dict[str, Any]:
        """The black hole, the rocks and the capture count (the disk and stars are regenerated on load)."""
        return {
            "black_hole": {"position": self.black_hole.position.tolist(), "mass": self.black_hole.mass},
            "rocks": [{"position": r.position.tolist(), "velocity": r.velocity.tolist()} for r in self.rocks],
            "captured": self.captured,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlackHoleScene:
        """Rebuild a scene saved with `to_dict` (validates every value)."""
        hole_data = data.get("black_hole")
        rocks_data = data.get("rocks", [])
        if not isinstance(hole_data, dict) or not isinstance(rocks_data, list):
            raise ScenarioError("a black hole scene needs a 'black_hole' and a list of 'rocks'")
        scene = cls()
        scene.black_hole = BlackHole(vector(hole_data.get("position"), "black hole position"),
                                     number(hole_data.get("mass"), "black hole mass", positive=True))
        scene.rocks = []
        for i, r in enumerate(rocks_data):
            if not isinstance(r, dict):
                raise ScenarioError(f"rock {i} must be an object")
            scene.rocks.append(Rock(vector(r.get("position"), f"rock {i} position"),
                                    vector(r.get("velocity"), f"rock {i} velocity"), mass=1.0))
        scene.gravity = GravitySystem([scene.black_hole, *scene.rocks])
        scene.disk = AccretionDisk(scene.black_hole)
        scene.captured = int(number(data.get("captured", 0), "captured"))
        return scene

    def throw_rock(self, position: ArrayLike, direction: ArrayLike) -> None:
        """Throw a rock from `position` along `direction`."""
        rock = Rock(position, np.asarray(direction, dtype=float) * ROCK_SPEED, mass=1.0)
        self.rocks.append(rock)
        self.gravity.add(rock)

    def update(self, dt: float, time: float) -> None:
        """Advance the stars, the gravity, the disk and the captures by `dt` seconds."""
        self.star_field.update(time)
        substeps = max(1, math.ceil(dt / PHYSICS_MAX_STEP))
        for _ in range(substeps):
            self.gravity.step(dt / substeps)
            self.captured += self.disk.step(dt / substeps)
            self.capture_rocks()

    def capture_rocks(self) -> None:
        """Remove the rocks that crossed the event horizon."""
        for rock in list(self.rocks):
            if np.linalg.norm(rock.position - self.black_hole.position) < self.black_hole.horizon_radius:
                self.rocks.remove(rock)
                self.gravity.remove(rock)
                self.captured += 1

    def draw_rocks(
        self,
        screen: pygame.Surface,
        camera: Camera,
        min_distance: float = 0.0,
        max_distance: float = math.inf,
    ) -> None:
        """Draw the rocks at [min_distance, max_distance) from the camera."""
        for rock in self.rocks:
            distance = float(np.linalg.norm(rock.position - camera.position))
            projection = camera.project(*rock.position)
            if projection is None or not min_distance <= distance < max_distance:
                continue
            x, y, depth = projection
            radius_px = max(2, int(rock.radius * camera.focal_length / depth))
            pygame.draw.circle(screen, rock.color, (int(x), int(y)), radius_px)

    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        """Draw the scene: lensed stars, disk, rocks and the black hole, in depth order."""
        hole_distance = float(np.linalg.norm(camera.position - self.black_hole.position))
        lens = GravitationalLens(self.black_hole, camera)
        self.star_field.draw(screen, camera, min_distance=hole_distance, lens=lens)
        self.disk.draw(screen, camera, min_distance=hole_distance)
        self.draw_rocks(screen, camera, min_distance=hole_distance)
        self.black_hole.draw(screen, camera)
        self.disk.draw(screen, camera, max_distance=hole_distance)
        self.draw_rocks(screen, camera, max_distance=hole_distance)
        self.star_field.draw(screen, camera, max_distance=hole_distance)
