# TheBlackHole - 3D Space Simulation

A stunning 3D space simulation program that creates realistic star fields in three-dimensional space. Navigate through the cosmos with full 3D movement and perspective!

## Features

- **True 3D Space**: Navigate through a 3D star field with realistic perspective projection
- **The Sun at the Center**: A glowing Sun at the origin with real astronomical mass and size
- **800 3D Stars**: Stars distributed throughout a massive 6000x6000x6000 unit space
- **Realistic Star Field**: Different sizes, colors, and brightness levels with distance-based scaling
- **Twinkling Effect**: Stars twinkle naturally with varying intensities
- **Full 3D Movement**: Move forward, backward, left, right, up, and down
- **Mouse Look**: FPS-style mouse controls for looking around
- **Multiple Star Types**: Different star colors including white, blue-white, orange, red, and rare green stars
- **Distance-Based Rendering**: Stars get smaller and dimmer as you move away
- **Depth Sorting**: Proper rendering order for 3D depth perception

## Controls

### Movement
- **WASD**: Move forward/backward/left/right relative to your view direction
- **Q/E**: Move up and down
- **SHIFT**: Hold for fast movement (5x speed)

### Looking Around
- **Arrow Keys**: Look around (pitch and yaw)
- **C**: Toggle mouse look (recommended for 3D navigation)
- **Mouse**: Look around when mouse look is enabled

### Other
- **SPACE**: Generate a new random 3D star field
- **ESC**: Exit the simulation

## Installation

1. Install Python 3.7 or higher
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Simulation

### 3D Version (Recommended)
```bash
python space_simulation_3d.py
```

### 2D Version (Original)
```bash
python space_simulation.py
```

## 3D Navigation Tips

1. **Press C** to enable mouse look for the best 3D experience
2. **Use WASD** like a first-person game to move through space
3. **Hold SHIFT** to move faster when exploring large distances
4. **Use Q/E** to move up and down to get different perspectives
5. **Watch the position display** to track your location in 3D space

## What's Next

The project is being developed step by step. See [ROADMAP.md](ROADMAP.md) for the full plan, which includes:

- **Real Gravity**: Orbital mechanics with a Velocity Verlet integrator
- **Planetary Systems**: Planets orbiting the Sun, with orbit trails
- **Black Holes**: Event horizon, accretion disk and gravitational lensing
- **Tests & CI**: Automated tests with pytest and GitHub Actions

## Technical Details

The 3D simulation uses:
- **Perspective Projection**: Converts 3D coordinates to 2D screen coordinates
- **3D Rotations**: Pitch and yaw rotations using trigonometry
- **Distance-Based Scaling**: Stars appear smaller and dimmer when far away
- **Depth Sorting**: Stars are rendered back-to-front for proper depth perception
- **Optimized Rendering**: Frustum culling and distance-based LOD
- **Smooth 60 FPS**: Optimized for real-time 3D navigation

## File Structure

- `space_simulation_3d.py` - Main 3D simulation with full 3D movement and the Sun
- `space_simulation.py` - Original 2D simulation with camera controls
- `requirements.txt` - Python dependencies
- `ROADMAP.md` - Development plan and progress log
- `README.md` - This file

Enjoy exploring the 3D cosmos! 🌟🚀