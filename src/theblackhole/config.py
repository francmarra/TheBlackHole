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
TRAIL_LENGTH = 240        # points kept per orbit trail
TRAIL_INTERVAL = 0.1      # seconds between trail points
TIME_SCALE_MIN = 1 / 8
TIME_SCALE_MAX = 64.0

# Solar system (orbits in the XZ plane around the Sun at the origin)
SUN_GRAVITY_MASS = 6.0e5
ORBITING_PLANETS = [
    # (orbit radius, planet radius, colour)
    (220.0, 12.0, (180, 160, 140)),
    (380.0, 20.0, (220, 180, 110)),
    (560.0, 18.0, (190, 90, 60)),
    (1500.0, 45.0, (200, 170, 130)),
]

# Black hole scene (scene units: c is tuned so the horizon is visible on screen)
SPEED_OF_LIGHT = 316.0
BLACK_HOLE_MASS = 2.0e6       # r_s = 2GM/c² ≈ 40 units
BLACK_HOLE_START_CAMERA = (0.0, 250.0, -1100.0)
SHADOW_FACTOR = 2.6           # The dark "shadow" seen from afar is ~2.6 r_s (photon capture radius)
BLACK_HOLE_STARS = 1800       # Denser background so the lensing is easy to see
PHOTON_RING_COLOR = (255, 170, 80)
DISK_PARTICLES = 1500
DISK_INNER = 3.0              # Inner edge of the disk in r_s (the innermost stable orbit of a real black hole)
DISK_OUTER = 10.0             # Outer edge in r_s
DISK_THICKNESS = 0.08         # Vertical spread as a fraction of the radius
DISK_HOT_COLOR = (255, 240, 200)   # Inner edge
DISK_COOL_COLOR = (200, 60, 20)    # Outer edge
DISK_DRAG = 0.01              # Fraction of speed lost per second: the gas slowly spirals in (accretion)
ROCK_SPEED = 300.0            # Speed of rocks thrown with F
ROCK_RADIUS = 6.0
ROCK_COLOR = (160, 150, 140)
