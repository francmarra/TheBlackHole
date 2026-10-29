"""Polygon drawing helpers: near-plane clipping, painter's algorithm and shading."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import numpy as np
import pygame

from .aliases import Color, Vector
from .config import AMBIENT_LIGHT, NEAR_PLANE, SCREEN_HEIGHT, SCREEN_WIDTH

if TYPE_CHECKING:
    from .camera import Camera

SCREEN_MARGIN = 2  # pixels; clipped edges land just outside the screen so no seam shows


def clip_polygon_near(points: Sequence[Vector], near: float = NEAR_PLANE) -> list[Vector]:
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


def _clip_edge(
    points: list[list[float]],
    inside: Callable[[list[float]], bool],
    intersect: Callable[[list[float], list[float]], list[float]],
) -> list[list[float]]:
    clipped = []
    for i in range(len(points)):
        a, b = points[i], points[(i + 1) % len(points)]
        if inside(a):
            clipped.append(a)
        if inside(a) != inside(b):
            clipped.append(intersect(a, b))
    return clipped


def clip_polygon_screen(
    points: list[list[float]],
    left: float = -SCREEN_MARGIN,
    top: float = -SCREEN_MARGIN,
    right: float = SCREEN_WIDTH + SCREEN_MARGIN,
    bottom: float = SCREEN_HEIGHT + SCREEN_MARGIN,
) -> list[list[float]]:
    """Sutherland-Hodgman clip of a 2D polygon to the screen rectangle.

    Faces cut by the near plane can project to points tens of thousands of pixels away,
    and pygame's fill cost grows with that size, so they are trimmed first.
    """
    def at_x(x: float) -> Callable[[list[float], list[float]], list[float]]:
        return lambda a, b: [x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])]

    def at_y(y: float) -> Callable[[list[float], list[float]], list[float]]:
        return lambda a, b: [a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y]

    for inside, intersect in (
        (lambda p: p[0] >= left, at_x(left)),
        (lambda p: p[0] <= right, at_x(right)),
        (lambda p: p[1] >= top, at_y(top)),
        (lambda p: p[1] <= bottom, at_y(bottom)),
    ):
        points = _clip_edge(points, inside, intersect)
        if not points:
            break
    return points


def fill_polygon(screen: pygame.Surface, color: Color, points: list[list[float]]) -> None:
    """pygame.draw.polygon, trimming polygons that reach far outside the screen first."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if min(xs) < -SCREEN_WIDTH or max(xs) > 2 * SCREEN_WIDTH or min(ys) < -SCREEN_HEIGHT or max(ys) > 2 * SCREEN_HEIGHT:
        points = clip_polygon_screen(points)
        if len(points) < 3:
            return
    pygame.draw.polygon(screen, color, points)


def draw_faces(screen: pygame.Surface, camera: Camera, faces: list[tuple[float, Vector, Color]]) -> None:
    """Draw (depth, camera_space_polygon, color) faces from far to near (painter's algorithm)."""
    faces.sort(key=lambda face: face[0], reverse=True)
    for _, polygon, color in faces:
        if (polygon[:, 2] < NEAR_PLANE).any():
            polygon = clip_polygon_near(polygon)
            if len(polygon) < 3:
                continue
            polygon = np.array(polygon)
        fill_polygon(screen, color, camera.project_camera_space(polygon).tolist())


def shade_color(color: Color, normal: Vector, light_dir: Vector, sunlight: float = 1.0) -> Color:
    """Ambient light plus sunlight on a face; `sunlight` is 0 inside the planet's shadow."""
    diffuse = max(0.0, float(np.dot(normal, light_dir))) * sunlight
    light = AMBIENT_LIGHT + (1 - AMBIENT_LIGHT) * diffuse
    return tuple(max(0, min(255, int(c * light))) for c in color)
