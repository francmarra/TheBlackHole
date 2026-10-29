"""Tests for the polygon clipping helpers."""

import numpy as np
import pytest

from theblackhole.render import clip_polygon_near, clip_polygon_screen


def area(points):
    x, y = np.array(points, dtype=float).T
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def test_polygon_inside_the_screen_is_unchanged():
    square = [[10, 10], [50, 10], [50, 50], [10, 50]]
    assert clip_polygon_screen(square) == square


def test_huge_polygon_is_trimmed_to_the_screen():
    huge = [[-30000, -20000], [40000, -20000], [40000, 30000], [-30000, 30000]]
    clipped = clip_polygon_screen(huge, left=0, top=0, right=100, bottom=80)
    assert area(clipped) == pytest.approx(100 * 80)
    assert all(0 <= x <= 100 and 0 <= y <= 80 for x, y in clipped)


def test_polygon_fully_outside_the_screen_disappears():
    assert clip_polygon_screen([[-50, -50], [-10, -50], [-10, -10]], left=0, top=0, right=100, bottom=80) == []


def test_near_plane_clip_keeps_only_the_part_in_front():
    triangle = np.array([[0.0, 0.0, -1.0], [1.0, 0.0, 3.0], [-1.0, 0.0, 3.0]])
    clipped = clip_polygon_near(triangle, near=1.0)
    assert all(p[2] >= 1.0 - 1e-12 for p in clipped)
    assert len(clipped) == 4  # one vertex behind -> the triangle becomes a quad
