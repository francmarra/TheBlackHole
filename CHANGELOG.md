# Changelog

All notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-29

The first complete version: three scenarios on a custom 3D renderer with real N-body physics.

### Added
- **Start menu** with three scenarios: Solar System, Black Hole and Galaxy (ESC goes back to the menu).
- **N-body gravity** with a Velocity Verlet integrator, vectorised with NumPy (about 60x faster than the pairwise loop at 100 bodies).
- **Solar System**: four planets orbiting the Sun, drawn with phase lighting and fading **orbit trails**.
- **Time control**: P pauses, +/- change the speed from x1/8 to x64.
- **Black hole**: event horizon from the Schwarzschild radius, shadow and photon ring, an **accretion disk** of 1500 particles that spiral in, **captures** of everything that crosses the horizon, rocks thrown with F, and point-lens **gravitational lensing** of the background stars.
- **Black hole HUD**: distance in r_s, camera speed in c, escape speed and gravitational time dilation.
- **Galaxy**: 3000 stars in two logarithmic spiral arms on a flat rotation curve, so the arms wind up over time.
- **Glow** effects with additive blending for the Sun, the disk and the photon ring.
- **Save and load** every scenario as JSON with F5 / F9, with validation of every value read from the file.
- **Standalone executable** built with PyInstaller (`scripts/build_exe.py`).
- Tools: `scripts/profile_frames.py` (headless profiling) and `scripts/capture.py` (README screenshots and GIF).
- **58 tests** (camera, physics, energy conservation, orbits, black hole, lensing, galaxy, clipping, saves) and **CI** on GitHub Actions with ruff and pytest on Python 3.11, 3.12 and 3.13.
- Type hints and docstrings across the package, enforced by ruff.

### Changed
- Faces cut by the near plane are clipped to the screen before filling (Sutherland-Hodgman): the frame time on the planet went from 19.5 to 10.4 ms.
- The minimum Python version is 3.11 (required by NumPy 2.3).

### Fixed
- The camera kept a reference to the free camera's position array instead of a copy.

## [0.1.0] - 2026-10-15

### Added
- Walk on a cube-sphere planet in third person, with day and night, a free-fly camera and a 3D star field.
- Package layout in `src/theblackhole/`, `config.py` with every constant, MIT license.
