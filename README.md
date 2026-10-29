# TheBlackHole - 3D Space Simulation
[![CI](https://github.com/francmarra/TheBlackHole/actions/workflows/ci.yml/badge.svg)](https://github.com/francmarra/TheBlackHole/actions/workflows/ci.yml)

A 3D space simulation with a custom renderer written in Python. Walk on a planet in third person, watch the Sun set behind the horizon, or fly freely through a 3D star field.

## Features

- **Walk on a Planet**: Explore a spherical planet in third person as a little astronaut
- **Third-Person Camera**: The camera follows the player, with mouse/arrow control and zoom
- **Real Curvature**: Walk all the way around the planet; the horizon curves away from you
- **Day and Night**: The Sun lights the planet, and the night side falls into the planet's shadow
- **Oceans, Continents and Ice Caps**: Procedurally colored planet surface
- **Free Camera Mode**: Leave the planet and fly freely through 3D space
- **The Sun and 800 Stars**: A realistic 3D star field with twinkling stars of different sizes and colors
- **Custom 3D Renderer**: Perspective projection, back-face culling, near-plane clipping and flat shading, written from scratch with Pygame and NumPy

## Controls

### On the Planet (third person)
- **WASD**: Walk forward/backward and strafe left/right
- **SHIFT**: Run
- **SPACE**: Jump
- **Mouse** (press **C** to capture it) or **Arrow Keys**: Turn the player and tilt the camera
- **Mouse Wheel**: Zoom the camera in and out

### Free Camera
- **WASD**: Move forward/backward/left/right
- **Q/E**: Move up and down
- **SHIFT**: Fast movement (5x speed)
- **Mouse** (press **C**) or **Arrow Keys**: Look around

### Other
- **TAB**: Switch between the planet and the free camera
- **N**: Generate a new random star field
- **ESC**: Exit the simulation

## Installation

1. Install Python 3.10 or higher
2. Install the package and its dependencies (from the project folder):
   ```bash
   pip install -e .
   ```

## Running the Simulation

### 3D Version (Recommended)
```bash
theblackhole
```
or, without installing (after `pip install -r requirements.txt`):
```bash
cd src
python -m theblackhole
```

### 2D Version (Original)
```bash
python space_simulation.py
```

## Tips

1. **Press C** to control the camera with the mouse
2. **Walk in a straight line** and you will come back to where you started
3. **Walk to the night side** and watch the Sun set behind the horizon
4. **Press TAB** to fly away and see the whole planet from space

## What's Next

The project is being developed step by step. See [ROADMAP.md](ROADMAP.md) for the full plan, which includes:

- **Real Gravity**: Orbital mechanics with a Velocity Verlet integrator
- **Orbits**: The planet orbiting the Sun, with orbit trails
- **Black Holes**: Event horizon, accretion disk and gravitational lensing
- **Tests & CI**: Automated tests with pytest and GitHub Actions

## Technical Details

The 3D renderer is written from scratch (no OpenGL):
- **Camera**: Free orientation stored as right/up/forward vectors, used both for the third-person and the free-fly camera
- **Perspective Projection**: Converts 3D coordinates to 2D screen coordinates
- **Cube-Sphere Planet Mesh**: A subdivided cube projected onto a sphere, so all faces have about the same size (no crowded poles)
- **Back-Face Culling and Painter's Algorithm**: Only faces turned towards the camera are drawn, from far to near
- **Near-Plane Clipping**: Faces that cross behind the camera are cut instead of disappearing
- **Flat Shading**: Each face is lit by the Sun according to its normal, with ambient light on the night side
- **Walking on a Sphere**: Moving is a rotation around the planet's center, and the heading is carried along the surface (parallel transport)
- **NumPy Vectorization**: Visibility, lighting and projection of the planet mesh are computed for all faces at once

## File Structure

- `src/theblackhole/` - The 3D simulation package
  - `main.py` - Main loop: planet explorer and free camera
  - `config.py` - Constants (screen, camera, planet, player)
  - `camera.py` - 3D camera and projection
  - `render.py` - Near-plane clipping, painter's algorithm and shading
  - `star.py`, `sun.py`, `starfield.py` - Stars, the Sun and the star field
  - `planet.py` - Cube-sphere planet mesh
  - `player.py` - The astronaut
- `space_simulation.py` - Original 2D simulation with camera controls
- `pyproject.toml` - Package metadata and the `theblackhole` command
- `requirements.txt` - Python dependencies
- `ROADMAP.md` - Development plan and progress log
- `README.md` - This file

Enjoy exploring the 3D cosmos! 🌟🚀