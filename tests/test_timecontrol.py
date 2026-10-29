"""Tests for pausing and changing the simulation speed."""

import pytest

from theblackhole.config import TIME_SCALE_MAX, TIME_SCALE_MIN
from theblackhole.timecontrol import TimeControl


def test_normal_speed_passes_real_time():
    assert TimeControl().scaled(0.016) == pytest.approx(0.016)


def test_pause_stops_time_and_resumes_at_same_speed():
    time = TimeControl()
    time.faster()
    time.toggle_pause()
    assert time.scaled(0.1) == 0.0
    assert time.label() == "x2 (PAUSED)"
    time.toggle_pause()
    assert time.scaled(0.1) == pytest.approx(0.2)


def test_speed_doubles_and_halves_within_limits():
    time = TimeControl()
    for _ in range(20):
        time.faster()
    assert time.scale == TIME_SCALE_MAX
    for _ in range(40):
        time.slower()
    assert time.scale == TIME_SCALE_MIN
    assert time.label() == "x1/8"
