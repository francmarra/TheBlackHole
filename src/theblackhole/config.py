"""Simulation constants."""

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
STAR_COLORS = [
    (255, 255, 255),  # Pure white
    (255, 255, 100),  # Bright yellow
    (255, 150, 50),   # Bright orange
    (150, 200, 255),  # Bright blue-white
    (255, 80, 80),    # Bright red
    (100, 255, 100),  # Bright green
    (255, 100, 255),  # Bright magenta
    (100, 255, 255),  # Bright cyan
]

# Camera
FOCAL_LENGTH = 500
NEAR_PLANE = 0.5

# Planet
PLANET_CENTER = (900.0, 0.0, 0.0)
PLANET_RADIUS = 150.0
AMBIENT_LIGHT = 0.18  # How much light the night side still gets

# Player
WALK_SPEED = 10.0     # units per second
RUN_SPEED = 25.0
TURN_SPEED = 2.0      # radians per second
JUMP_SPEED = 10.0
GRAVITY = 25.0
SUN_COLOR = (255, 255, 150)

# Starfield
NUM_STARS = 800
STARFIELD_EXTENT = 3000      # stars spawn in [-extent, extent] on each axis
STAR_MIN_SUN_DISTANCE = 50
PLANET_STAR_CLEAR_RADIUS = 1200

# Third-person camera
CAMERA_DISTANCE = 14.0
CAMERA_ZOOM_MIN = 5.0
CAMERA_ZOOM_MAX = 60.0
CAMERA_ZOOM_STEP = 1.5
CAMERA_ELEVATION = 0.25      # radians above the player's horizon
CAMERA_ELEVATION_MIN = -0.08
CAMERA_ELEVATION_MAX = 1.4

# Free camera
FREE_CAMERA_SPEED = 600.0
FREE_CAMERA_BOOST = 5        # multiplier while holding Shift
FREE_CAMERA_ROTATION_SPEED = 1.2  # radians per second
MOUSE_SENSITIVITY = 0.003

# Planet mesh / colours
PLANET_NEAR_DETAIL = 72
PLANET_FAR_DETAIL = 16
PLANET_LOD_DISTANCE = 4      # switch to far mesh beyond this many radii
DEEP_OCEAN = (25, 60, 140)
SHALLOW_OCEAN = (45, 115, 185)
GRASS = (70, 140, 60)
ROCK = (130, 110, 75)
ICE = (225, 235, 245)

# Astronaut
SUIT = (230, 230, 235)
SUIT_DARK = (190, 190, 200)
BACKPACK = (150, 150, 165)
VISOR = (235, 170, 60)

# HUD
HUD_TEXT_COLOR = (200, 200, 200)
HUD_STATUS_COLOR = (150, 150, 150)

# Main loop
MAX_FRAME_TIME = 0.05        # seconds; clamps dt after stalls

# Gravity (scene units, not SI: tuned so orbits look good on screen)
GRAVITY_CONSTANT = 1.0
GRAVITY_SOFTENING = 1.0  # Keeps the force finite when two bodies get very close
PHYSICS_MAX_STEP = 1 / 120  # seconds; frames longer than this are split into substeps

# Solar system (orbits in the XZ plane around the Sun at the origin)
SUN_GRAVITY_MASS = 6.0e5
ORBITING_PLANETS = [
    # (orbit radius, planet radius, colour)
    (220.0, 12.0, (180, 160, 140)),
    (380.0, 20.0, (220, 180, 110)),
    (560.0, 18.0, (190, 90, 60)),
    (1500.0, 45.0, (200, 170, 130)),
]
