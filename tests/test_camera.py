"""Tests for the 3D camera: projection to the screen and orientation."""

import math

import numpy as np
import pytest

from theblackhole.camera import Camera
from theblackhole.config import NEAR_PLANE, SCREEN_HEIGHT, SCREEN_WIDTH

CENTER = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)


@pytest.fixture
def camera():
    """Camera at the origin looking down +z (the default orientation)."""
    return Camera()


def assert_orthonormal(cam):
    for v in (cam.right, cam.up, cam.forward):
        assert np.linalg.norm(v) == pytest.approx(1.0)
    assert np.dot(cam.right, cam.up) == pytest.approx(0.0, abs=1e-9)
    assert np.dot(cam.right, cam.forward) == pytest.approx(0.0, abs=1e-9)
    assert np.dot(cam.up, cam.forward) == pytest.approx(0.0, abs=1e-9)


# --- Projection 3D -> 2D ---


def test_point_straight_ahead_lands_on_screen_center(camera):
    x, y, depth = camera.project(0, 0, 10)
    assert (x, y) == pytest.approx(CENTER)
    assert depth == pytest.approx(10)


def test_right_and_up_map_to_screen_directions(camera):
    right_x, right_y, _ = camera.project(1, 0, 10)
    up_x, up_y, _ = camera.project(0, 1, 10)
    assert right_x > CENTER[0] and right_y == pytest.approx(CENTER[1])
    # Screen y grows downwards, so "up" in the world means a smaller y
    assert up_y < CENTER[1] and up_x == pytest.approx(CENTER[0])


def test_doubling_distance_halves_offset_from_center(camera):
    near_x, _, _ = camera.project(1, 0, 10)
    far_x, _, _ = camera.project(1, 0, 20)
    assert far_x - CENTER[0] == pytest.approx((near_x - CENTER[0]) / 2)


@pytest.mark.parametrize("z", [-5, 0, NEAR_PLANE])
def test_points_behind_or_at_near_plane_are_not_projected(camera, z):
    assert camera.project(0, 0, z) is None


def test_single_and_batch_projection_agree():
    cam = Camera()
    cam.set_yaw_pitch((3, -2, 1), yaw=0.7, pitch=-0.3)
    points = np.array([[5.0, -1.0, 12.0], [-2.0, 4.0, 9.0], [8.0, 0.5, 6.0]])

    batch = cam.project_camera_space(cam.to_camera_space(points))
    for point, expected in zip(points, batch):
        x, y, _ = cam.project(*point)
        assert (x, y) == pytest.approx(tuple(expected))


# --- Camera orientation ---


def test_zero_yaw_pitch_matches_world_axes(camera):
    camera.set_yaw_pitch((0, 0, 0), yaw=0, pitch=0)
    assert camera.right == pytest.approx([1, 0, 0])
    assert camera.up == pytest.approx([0, 1, 0])
    assert camera.forward == pytest.approx([0, 0, 1])


def test_yaw_90_degrees_looks_down_positive_x(camera):
    camera.set_yaw_pitch((0, 0, 0), yaw=math.pi / 2, pitch=0)
    assert camera.forward == pytest.approx([1, 0, 0], abs=1e-9)
    assert camera.right == pytest.approx([0, 0, -1], abs=1e-9)
    x, y, _ = camera.project(10, 0, 0)
    assert (x, y) == pytest.approx(CENTER)


@pytest.mark.parametrize("yaw, pitch", [(0.3, 0.2), (2.5, -1.0), (-1.2, 1.4)])
def test_yaw_pitch_basis_is_orthonormal(camera, yaw, pitch):
    camera.set_yaw_pitch((1, 2, 3), yaw, pitch)
    assert_orthonormal(camera)


def test_look_at_points_at_target(camera):
    position, target = np.array([4.0, 3.0, -2.0]), np.array([-1.0, 0.0, 5.0])
    camera.look_at(position, target, up_hint=np.array([0.0, 1.0, 0.0]))

    assert_orthonormal(camera)
    expected = (target - position) / np.linalg.norm(target - position)
    assert camera.forward == pytest.approx(expected)
    x, y, _ = camera.project(*target)
    assert (x, y) == pytest.approx(CENTER)
