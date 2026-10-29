"""Profile the simulation without a window: python scripts/profile_frames.py [frames]."""

import cProfile
import os
import pstats
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame

from theblackhole.main import SpaceSimulation3D


def run(simulation, frames):
    for _ in range(frames):
        simulation.update(1 / 60)
        simulation.draw()


def main():
    frames = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    pygame.init()
    simulation = SpaceSimulation3D()
    for mode in ("planet", "free"):
        if simulation.mode != mode:
            simulation.toggle_mode()
        start = time.perf_counter()
        run(simulation, frames)
        ms = (time.perf_counter() - start) / frames * 1000
        print(f"{mode}: {ms:.1f} ms/frame ({1000 / ms:.0f} FPS without the 60 FPS cap)")

    profiler = cProfile.Profile()
    profiler.runcall(run, simulation, frames)
    pstats.Stats(profiler).sort_stats("cumulative").print_stats(15)


if __name__ == "__main__":
    main()
