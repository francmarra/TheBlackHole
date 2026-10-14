"""Polygon drawing helpers: near-plane clipping, painter's algorithm and shading."""

import numpy as np
import pygame

from .config import AMBIENT_LIGHT, NEAR_PLANE


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
