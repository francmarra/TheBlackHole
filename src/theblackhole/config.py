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
