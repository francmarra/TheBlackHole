"""Tests for the glow sprites."""

import pygame

from theblackhole.glow import draw_glow, glow_sprite


def test_glow_is_brightest_in_the_center_and_black_at_the_edge():
    sprite = glow_sprite(10, (200, 100, 50))
    assert sprite.get_size() == (21, 21)
    assert sprite.get_at((10, 10))[:3] == (200, 100, 50)
    assert sprite.get_at((0, 0))[:3] == (0, 0, 0)
    assert sprite.get_at((10, 15))[0] < 200


def test_glows_add_up_where_they_overlap():
    screen = pygame.Surface((40, 40))
    draw_glow(screen, (20, 20), 10, (80, 80, 80))
    once = screen.get_at((20, 20))[0]
    draw_glow(screen, (20, 20), 10, (80, 80, 80))
    assert screen.get_at((20, 20))[0] == 2 * once
