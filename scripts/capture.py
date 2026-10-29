"""Render the README screenshots and GIF without a window: python scripts/capture.py.

Needs Pillow for the GIF (pip install pillow). Images go to docs/images/.
"""

import math
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pygame
from PIL import Image

from theblackhole.main import SpaceSimulation3D

OUT = ROOT / "docs" / "images"


def frames(simulation, count, dt=1 / 60):
    for _ in range(count):
        simulation.update(dt)
        simulation.draw()


def save(simulation, name):
    pygame.image.save(simulation.screen, str(OUT / name))
    print("saved", name)


def to_image(surface, scale=0.5):
    size = (int(surface.get_width() * scale), int(surface.get_height() * scale))
    small = pygame.transform.smoothscale(surface, size)
    return Image.frombytes("RGB", size, pygame.image.tobytes(small, "RGB"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pygame.init()
    sim = SpaceSimulation3D()

    frames(sim, 3)
    save(sim, "menu.png")

    sim.start_scene("solar")
    frames(sim, 30)
    save(sim, "planet.png")

    sim.toggle_mode()
    sim.look_from((0.0, 1100.0, -1300.0), (300.0, 0.0, 0.0))
    sim.time.scale = 8
    frames(sim, 600)
    save(sim, "solar_system.png")

    sim.time.scale = 1
    sim.start_scene("blackhole")
    sim.look_from((0.0, 110.0, -800.0), (0.0, 0.0, 0.0))
    frames(sim, 60)
    save(sim, "black_hole.png")

    # GIF: the camera circles the black hole while the disk turns
    gif = []
    for i in range(72):
        angle = -math.pi / 2 + i * 2 * math.pi / 72
        sim.look_from((800 * math.cos(angle), 110.0, 800 * math.sin(angle)), (0.0, 0.0, 0.0))
        frames(sim, 2)
        gif.append(to_image(sim.screen))
    gif[0].save(OUT / "black_hole.gif", save_all=True, append_images=gif[1:], duration=50, loop=0, optimize=True)
    print("saved black_hole.gif")

    sim.start_scene("galaxy")
    sim.time.scale = 8
    frames(sim, 240)
    save(sim, "galaxy.png")
    assert np.isfinite(sim.galaxy_scene.galaxy.positions).all()


if __name__ == "__main__":
    main()
