"""3D camera and vector helpers."""

from __future__ import annotations

import math

import numpy as np

from .aliases import ArrayLike, Vector
from .config import FOCAL_LENGTH, NEAR_PLANE, SCREEN_HEIGHT, SCREEN_WIDTH


def normalize(v: Vector) -> Vector:
    """Unit vector in the direction of `v` (or `v` itself if it is zero)."""
    length = np.linalg.norm(v)
    return v / length if length > 1e-12 else v


class Camera:
    """A 3D camera with a free orientation, stored as right/up/forward vectors."""

    def __init__(self, focal_length: float = FOCAL_LENGTH) -> None:
        self.focal_length = focal_length
        self.position = np.zeros(3)
        self.right = np.array([1.0, 0.0, 0.0])
        self.up = np.array([0.0, 1.0, 0.0])
        self.forward = np.array([0.0, 0.0, 1.0])
        self._update_cache()

    def look_at(self, position: ArrayLike, target: ArrayLike, up_hint: ArrayLike) -> None:
        """Place the camera at `position`, looking at `target`, with `up_hint` as up."""
        self.position = np.array(position, dtype=float)  # Copy: callers keep moving their own array
        self.forward = normalize(np.asarray(target, dtype=float) - self.position)
        self.right = normalize(np.cross(up_hint, self.forward))
        self.up = np.cross(self.forward, self.right)
        self._update_cache()

    def set_yaw_pitch(self, position: ArrayLike, yaw: float, pitch: float) -> None:
        """Classic free-fly orientation, with the world Y axis as up."""
        self.position = np.array(position, dtype=float)  # Copy: callers keep moving their own array
        cos_pitch = math.cos(pitch)
        self.forward = np.array([math.sin(yaw) * cos_pitch, math.sin(pitch), math.cos(yaw) * cos_pitch])
        self.right = np.array([math.cos(yaw), 0.0, -math.sin(yaw)])
        self.up = np.cross(self.forward, self.right)
        self._update_cache()

    def _update_cache(self) -> None:
        # Plain Python floats are much faster than NumPy for projecting single points
        self._pos = self.position.tolist()
        self._right = self.right.tolist()
        self._up = self.up.tolist()
        self._forward = self.forward.tolist()

    def to_camera_space(self, points: ArrayLike) -> Vector:
        """Convert world points (N, 3) to camera space: x right, y up, z forward."""
        basis = np.array([self.right, self.up, self.forward])
        return (np.asarray(points, dtype=float) - self.position) @ basis.T

    def project_camera_space(self, cam_points: Vector) -> Vector:
        """Project camera-space points (..., 3) with z > 0 to screen coordinates (..., 2)."""
        z = cam_points[..., 2]
        screen_x = SCREEN_WIDTH / 2 + cam_points[..., 0] * self.focal_length / z
        screen_y = SCREEN_HEIGHT / 2 - cam_points[..., 1] * self.focal_length / z
        return np.stack([screen_x, screen_y], axis=-1)

    def project(self, x: float, y: float, z: float) -> tuple[float, float, float] | None:
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
