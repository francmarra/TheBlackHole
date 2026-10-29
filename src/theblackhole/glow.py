"""Soft glow sprites drawn with additive blending (bright where they overlap)."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pygame

from .aliases import Color, Point2


@lru_cache(maxsize=512)
def glow_sprite(radius: int, color: Color) -> pygame.Surface:
    """A (2r+1)² surface with `color` fading out from the center (quadratic falloff)."""
    size = 2 * radius + 1
    y, x = np.mgrid[-radius : radius + 1, -radius : radius + 1]
    falloff = np.clip(1 - np.sqrt(x * x + y * y) / (radius + 1e-9), 0, 1) ** 2
    pixels = (falloff[..., None] * np.array(color, dtype=float)).astype(np.uint8)
    surface = pygame.Surface((size, size))
    pygame.surfarray.blit_array(surface, pixels.transpose(1, 0, 2))
    return surface


def draw_glow(screen: pygame.Surface, center: Point2, radius: float, color: Color, intensity: float = 1.0) -> None:
    """Add a glow of `radius` pixels around `center`; colours are quantised so sprites can be reused."""
    radius = int(radius)
    if radius < 1:
        return
    color = tuple(int(min(255, c * intensity)) // 8 * 8 for c in color)
    sprite = glow_sprite(radius, color)
    screen.blit(sprite, (int(center[0]) - radius, int(center[1]) - radius), special_flags=pygame.BLEND_ADD)
