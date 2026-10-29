"""A spherical planet drawn as a shaded mesh."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from .aliases import ArrayLike, Vector
from .config import (
    AMBIENT_LIGHT,
    DEEP_OCEAN,
    GRASS,
    ICE,
    NEAR_PLANE,
    PLANET_FAR_DETAIL,
    PLANET_LOD_DISTANCE,
    PLANET_NEAR_DETAIL,
    ROCK,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHALLOW_OCEAN,
)
from .render import clip_polygon_near, fill_polygon

if TYPE_CHECKING:
    import pygame

    from .camera import Camera


class Planet:
    """A spherical planet drawn as a shaded mesh of flat faces."""

    def __init__(self, center: ArrayLike, radius: float, seed: int = 7) -> None:
        self.center = np.array(center, dtype=float)
        self.radius = radius
        rng = np.random.default_rng(seed)
        # Detailed mesh for walking on the surface, cheap one for viewing from far away
        self.near_mesh = self._build_mesh(PLANET_NEAR_DETAIL, rng)
        self.far_mesh = self._build_mesh(PLANET_FAR_DETAIL, rng)

    def _build_mesh(self, subdivisions: int, rng: np.random.Generator) -> tuple[Vector, Vector, Vector, Vector, Vector]:
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

        directions: list[Vector] = []
        faces: list[NDArray[np.intp]] = []
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
    def _terrain(normals: Vector) -> tuple[Vector, Vector, Vector, Vector]:
        """Layered sine waves: `continents` > 0 is land, `detail` adds small variations."""
        x, y, z = np.atleast_2d(normals).T
        continents = (np.sin(3.1 * x + 1.7) * np.sin(2.3 * y + 0.5) * np.sin(2.9 * z + 2.1)
                      + 0.5 * np.sin(6.7 * x + 2.9 * z + 0.3) * np.sin(5.3 * y + 1.1))
        detail = np.sin(11 * x + 3) * np.sin(13 * y + 1) * np.sin(12 * z + 2)
        is_ice = np.abs(y) > 0.82 + 0.05 * detail
        is_land = (continents > 0.05) & ~is_ice
        return continents, detail, is_land, is_ice

    def is_land(self, normal: Vector) -> bool:
        """Whether the surface in direction `normal` is above sea level."""
        return bool(self._terrain(normal)[2][0])

    @classmethod
    def _surface_colors(cls, normals: Vector, rng: np.random.Generator) -> Vector:
        """Paint oceans, land and ice caps."""
        continents, detail, is_land, is_ice = cls._terrain(normals)

        deep_ocean = np.array(DEEP_OCEAN)
        shallow_ocean = np.array(SHALLOW_OCEAN)
        grass = np.array(GRASS)
        rock = np.array(ROCK)
        ice = np.array(ICE)

        t_sea = np.clip(1 + continents * 3, 0, 1)[:, None]
        sea = deep_ocean * (1 - t_sea) + shallow_ocean * t_sea
        t_land = np.clip(0.5 + 0.5 * detail, 0, 1)[:, None]
        land = grass * (1 - t_land) + rock * t_land

        colors = np.where(is_land[:, None], land, sea)
        colors = np.where(is_ice[:, None], ice, colors)
        # Small random variation per face so movement on the ground is easy to see
        return colors * rng.uniform(0.9, 1.1, (len(normals), 1))

    def draw(self, screen: pygame.Surface, camera: Camera, light_dir: Vector) -> None:
        """Draw the visible faces, lit from `light_dir`."""
        distance = np.linalg.norm(camera.position - self.center)
        vertices, faces, normals, centers, colors = (
            self.near_mesh if distance < self.radius * PLANET_LOD_DISTANCE else self.far_mesh)

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
            fill_polygon(screen, shaded[k], points)
