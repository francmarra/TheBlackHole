"""Main loop: start menu, the planet explorer, the black hole and the galaxy."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pygame

from . import scenario
from .aliases import ArrayLike, Color, Vector
from .blackhole import BlackHoleScene, hud_readout
from .camera import Camera, normalize
from .config import (
    BLACK,
    BLACK_HOLE_START_CAMERA,
    CAMERA_DISTANCE,
    CAMERA_ELEVATION,
    CAMERA_ELEVATION_MAX,
    CAMERA_ELEVATION_MIN,
    CAMERA_ZOOM_MAX,
    CAMERA_ZOOM_MIN,
    CAMERA_ZOOM_STEP,
    FPS,
    FREE_CAMERA_BOOST,
    FREE_CAMERA_ROTATION_SPEED,
    FREE_CAMERA_SPEED,
    GALAXY_START_CAMERA,
    HUD_STATUS_COLOR,
    HUD_TEXT_COLOR,
    MAX_FRAME_TIME,
    MENU_ITEM_COLOR,
    MENU_SELECTED_COLOR,
    MENU_TITLE_COLOR,
    MOUSE_SENSITIVITY,
    NUM_STARS,
    PLANET_CENTER,
    PLANET_RADIUS,
    PLANET_STAR_CLEAR_RADIUS,
    RUN_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TIME_SCALE_MAX,
    TIME_SCALE_MIN,
    TURN_SPEED,
    WALK_SPEED,
    WHITE,
)
from .galaxy import Galaxy, GalaxyScene
from .planet import Planet
from .player import Player
from .solar_system import SolarSystem
from .starfield import StarField3D
from .timecontrol import TimeControl

# (scene, title, description) for the start menu
SCENARIOS = [
    ("solar", "Solar System", "Walk on a planet while four planets orbit the Sun"),
    ("blackhole", "Black Hole", "Accretion disk, gravitational lensing and the event horizon"),
    ("galaxy", "Galaxy", "3000 stars whose spiral arms wind up as the galaxy turns"),
]


SAVE_FOLDER = Path("saves")
MESSAGE_SECONDS = 3.0


class SpaceSimulation3D:
    """The window, the start menu and the three scenarios."""

    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("TheBlackHole - Planet Explorer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 84)
        self.item_font = pygame.font.Font(None, 42)
        self.running = True

        self.planet = Planet(PLANET_CENTER, PLANET_RADIUS)
        self.new_star_field()

        self.player = self.create_player()

        self.camera = Camera()
        self.time = TimeControl()
        self.camera_speed = 0.0  # units per real second, for the HUD
        self.message = ""  # Shown at the bottom of the screen for a few seconds (saves and loads)
        self.message_until = 0.0
        self.mode = "planet"  # "planet" = third person on the planet, "free" = free-fly camera
        self.scene = "menu"  # "menu", or one of the SCENARIOS
        self.menu_index = 0
        self.black_hole_scene: BlackHoleScene | None = None  # Built the first time they are opened
        self.galaxy_scene: GalaxyScene | None = None

        # Third-person camera
        self.camera_distance = CAMERA_DISTANCE
        self.camera_elevation = CAMERA_ELEVATION  # Radians above the player's horizon

        # Free camera
        self.free_position = np.zeros(3)
        self.free_yaw = 0.0
        self.free_pitch = 0.0
        self.free_speed = FREE_CAMERA_SPEED
        self.rotation_speed = FREE_CAMERA_ROTATION_SPEED

        # Mouse control variables
        self.mouse_sensitivity = MOUSE_SENSITIVITY
        self.mouse_captured = False

        self.update_camera()

    def create_player(self) -> Player:
        """Start on land, on the day side, with the Sun behind the camera so the player is lit."""
        to_sun = normalize(self.star_field.sun_position - self.planet.center)
        tilt = math.radians(50)  # Angle between the start point and the point right under the Sun
        for angle in np.linspace(0, 2 * math.pi, 72, endpoint=False):
            sideways = np.array([0.0, math.sin(angle), math.cos(angle)])
            normal = to_sun * math.cos(tilt) + sideways * math.sin(tilt)
            if self.planet.is_land(normal):
                break
        sun_ahead = normalize(to_sun - np.dot(to_sun, normal) * normal)
        heading = -sun_ahead * 0.6 + np.cross(normal, sun_ahead) * 0.8
        return Player(self.planet, normal, heading)

    def new_star_field(self) -> None:
        """Generate a new random star field and Solar System."""
        self.star_field = StarField3D(NUM_STARS, clear_zones=[(tuple(self.planet.center), PLANET_STAR_CLEAR_RADIUS)])
        self.solar_system = SolarSystem(self.star_field.sun_position)

    def toggle_mode(self) -> None:
        """Switch between the third-person camera and the free camera."""
        if self.mode == "planet":
            # Start flying from where the third-person camera is
            self.mode = "free"
            self.free_position = self.camera.position.copy()
            forward = self.camera.forward
            self.free_yaw = math.atan2(forward[0], forward[2])
            self.free_pitch = math.asin(max(-1.0, min(1.0, forward[1])))
        else:
            self.mode = "planet"

    def look_from(self, position: ArrayLike, target: ArrayLike) -> None:
        """Put the free camera at `position`, looking at `target`."""
        self.free_position = np.asarray(position, dtype=float).copy()
        direction = normalize(np.asarray(target, dtype=float) - self.free_position)
        self.free_yaw = math.atan2(direction[0], direction[2])
        self.free_pitch = math.asin(max(-1.0, min(1.0, direction[1])))

    def start_scene(self, scene: str) -> None:
        """Open one of the SCENARIOS, building it the first time."""
        self.scene = scene
        if scene == "solar":
            self.mode = "planet"
        elif scene == "blackhole":
            if self.black_hole_scene is None:
                self.black_hole_scene = BlackHoleScene()
            self.mode = "free"
            self.look_from(BLACK_HOLE_START_CAMERA, self.black_hole_scene.black_hole.position)
        elif scene == "galaxy":
            if self.galaxy_scene is None:
                self.galaxy_scene = GalaxyScene()
            self.mode = "free"
            self.look_from(GALAXY_START_CAMERA, (0.0, 0.0, 0.0))

    def active_scene(self) -> BlackHoleScene | GalaxyScene | None:
        """The scene object for the black hole and galaxy scenarios (None for the Solar System)."""
        return {"blackhole": self.black_hole_scene, "galaxy": self.galaxy_scene}.get(self.scene)

    def show_message(self, text: str) -> None:
        """Show `text` at the bottom of the screen for a few seconds."""
        self.message = text
        self.message_until = pygame.time.get_ticks() / 1000.0 + MESSAGE_SECONDS

    def save_path(self) -> Path:
        """Where F5 saves and F9 loads the current scenario."""
        return SAVE_FOLDER / f"{self.scene}.json"

    def save_scene(self) -> None:
        """Save the current scenario to JSON (F5)."""
        if self.scene == "solar":
            data = self.solar_system.to_dict()
        elif self.scene == "blackhole" and self.black_hole_scene is not None:
            data = self.black_hole_scene.to_dict()
        elif self.scene == "galaxy" and self.galaxy_scene is not None:
            data = self.galaxy_scene.galaxy.to_dict()
        else:
            return
        path = self.save_path()
        try:
            scenario.save(path, self.scene, data, self.time.scale)
        except OSError as error:
            self.show_message(f"Could not save: {error}")
            return
        self.show_message(f"Saved to {path}")

    def load_scene(self) -> None:
        """Load the current scenario from JSON (F9), keeping the running one if the file is bad."""
        path = self.save_path()
        try:
            document = scenario.load(path)
            data = document["data"]
            if document["scene"] != self.scene:
                raise scenario.ScenarioError(f"{path.name} holds a '{document['scene']}' scenario")
            if self.scene == "solar":
                self.solar_system = SolarSystem.from_dict(data)
            elif self.scene == "blackhole":
                self.black_hole_scene = BlackHoleScene.from_dict(data)
            else:
                self.galaxy_scene = GalaxyScene(Galaxy.from_dict(data))
        except FileNotFoundError:
            self.show_message(f"Nothing saved yet ({path}): press F5 first")
            return
        except (OSError, scenario.ScenarioError) as error:
            self.show_message(f"Could not load: {error}")
            return
        self.time.scale = min(TIME_SCALE_MAX, max(TIME_SCALE_MIN, document["time_scale"]))
        self.show_message(f"Loaded {path}")

    def handle_menu_key(self, key: int) -> None:
        """Move the menu selection, start a scenario or quit."""
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % len(SCENARIOS)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % len(SCENARIOS)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.start_scene(SCENARIOS[self.menu_index][0])
        elif pygame.K_1 <= key < pygame.K_1 + len(SCENARIOS):
            self.menu_index = key - pygame.K_1
            self.start_scene(SCENARIOS[self.menu_index][0])

    def handle_events(self, dt: float) -> None:
        """Handle the window events and the keys held down this frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and self.scene == "menu":
                self.handle_menu_key(event.key)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.scene = "menu"
                    self.mouse_captured = False
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
                elif event.key == pygame.K_n:
                    self.new_star_field()
                elif event.key == pygame.K_F5:
                    self.save_scene()
                elif event.key == pygame.K_F9:
                    self.load_scene()
                elif event.key == pygame.K_p:
                    self.time.toggle_pause()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    self.time.faster()
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.time.slower()
                elif event.key == pygame.K_TAB and self.scene == "solar":
                    self.toggle_mode()
                elif event.key == pygame.K_f and self.scene == "blackhole":
                    start = self.camera.position + self.camera.forward * 20
                    self.black_hole_scene.throw_rock(start, self.camera.forward)
                elif event.key == pygame.K_SPACE and self.mode == "planet":
                    self.player.jump()
                elif event.key == pygame.K_c:
                    # Toggle mouse capture
                    self.mouse_captured = not self.mouse_captured
                    pygame.mouse.set_visible(not self.mouse_captured)
                    pygame.event.set_grab(self.mouse_captured)
            elif event.type == pygame.MOUSEWHEEL and self.mode == "planet":
                zoomed = self.camera_distance - event.y * CAMERA_ZOOM_STEP
                self.camera_distance = max(CAMERA_ZOOM_MIN, min(CAMERA_ZOOM_MAX, zoomed))
            elif event.type == pygame.MOUSEMOTION and self.mouse_captured:
                mouse_x, mouse_y = event.rel
                if self.mode == "planet":
                    self.player.turn(mouse_x * self.mouse_sensitivity)
                    self.tilt_camera(mouse_y * self.mouse_sensitivity)
                else:
                    self.free_yaw += mouse_x * self.mouse_sensitivity
                    self.free_pitch -= mouse_y * self.mouse_sensitivity
                    self.free_pitch = max(-math.pi/2 + 0.1, min(math.pi/2 - 0.1, self.free_pitch))

        if self.scene == "menu":
            return
        keys = pygame.key.get_pressed()
        if self.mode == "planet":
            self.handle_player_keys(keys, dt)
        else:
            self.handle_free_camera_keys(keys, dt)

    def tilt_camera(self, amount: float) -> None:
        """Raise or lower the third-person camera by `amount` radians."""
        self.camera_elevation = max(CAMERA_ELEVATION_MIN, min(CAMERA_ELEVATION_MAX, self.camera_elevation + amount))

    def handle_player_keys(self, keys: pygame.key.ScancodeWrapper, dt: float) -> None:
        """Walk, run and turn the player."""
        speed = (RUN_SPEED if keys[pygame.K_LSHIFT] else WALK_SPEED) * dt
        forward = (keys[pygame.K_w] - keys[pygame.K_s]) * speed
        sideways = (keys[pygame.K_d] - keys[pygame.K_a]) * speed
        self.player.move(forward, sideways)

        self.player.turn((keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * TURN_SPEED * dt)
        self.tilt_camera((keys[pygame.K_DOWN] - keys[pygame.K_UP]) * self.rotation_speed * dt)

    def handle_free_camera_keys(self, keys: pygame.key.ScancodeWrapper, dt: float) -> None:
        """Fly and turn the free camera."""
        speed = self.free_speed * (FREE_CAMERA_BOOST if keys[pygame.K_LSHIFT] else 1) * dt
        cos_yaw = math.cos(self.free_yaw)
        sin_yaw = math.sin(self.free_yaw)
        forward = np.array([sin_yaw, 0.0, cos_yaw])
        right = np.array([cos_yaw, 0.0, -sin_yaw])
        up = np.array([0.0, 1.0, 0.0])

        self.free_position += forward * (keys[pygame.K_w] - keys[pygame.K_s]) * speed
        self.free_position += right * (keys[pygame.K_d] - keys[pygame.K_a]) * speed
        self.free_position += up * (keys[pygame.K_q] - keys[pygame.K_e]) * speed

        self.free_yaw += (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.rotation_speed * dt
        self.free_pitch += (keys[pygame.K_UP] - keys[pygame.K_DOWN]) * self.rotation_speed * dt
        self.free_pitch = max(-math.pi/2 + 0.1, min(math.pi/2 - 0.1, self.free_pitch))

    def update_camera(self) -> None:
        """Place the camera for the current mode."""
        if self.mode == "free":
            self.camera.set_yaw_pitch(self.free_position, self.free_yaw, self.free_pitch)
            return

        # Third person: behind the player and slightly above, looking at the helmet
        player = self.player
        target = player.position + player.normal * 2.0
        horizontal = self.camera_distance * math.cos(self.camera_elevation)
        vertical = self.camera_distance * math.sin(self.camera_elevation)
        position = target - player.heading * horizontal + player.normal * vertical

        # Never let the camera sink into the ground
        offset = position - self.planet.center
        min_radius = self.planet.radius + 0.8
        if np.linalg.norm(offset) < min_radius:
            position = self.planet.center + normalize(offset) * min_radius
        self.camera.look_at(position, target, player.normal)

    def update(self, dt: float) -> None:
        """Advance the current scene by a real frame of `dt` seconds."""
        time = pygame.time.get_ticks() / 1000.0
        if self.scene == "menu":
            self.star_field.update(time)
            return
        scene = self.active_scene()
        if scene is not None:
            scene.update(self.time.scaled(dt), time)
            previous = self.camera.position.copy()
            self.update_camera()
            if dt > 0:
                self.camera_speed = float(np.linalg.norm(self.camera.position - previous)) / dt
            return
        self.star_field.update(time)
        self.solar_system.update(self.time.scaled(dt))
        self.player.update(dt)
        self.update_camera()

    def light_direction(self) -> Vector:
        """Direction from the planet to the Sun."""
        return normalize(self.star_field.sun_position - self.planet.center)

    def draw(self) -> None:
        """Draw the current scene and the HUD, then flip the display."""
        self.screen.fill(BLACK)
        if self.scene == "menu":
            self.star_field.draw(self.screen, self.camera)
            self.draw_menu()
            pygame.display.flip()
            return
        scene = self.active_scene()
        if scene is not None:
            scene.draw(self.screen, self.camera)
            self.draw_ui()
            pygame.display.flip()
            return

        # Stars behind the planet first, then the planet hides them, then the ones in front
        planet_distance = float(np.linalg.norm(self.camera.position - self.planet.center))
        self.star_field.draw(self.screen, self.camera, min_distance=planet_distance)
        self.solar_system.draw(self.screen, self.camera, min_distance=planet_distance)
        self.planet.draw(self.screen, self.camera, self.light_direction())
        self.player.draw(self.screen, self.camera, self.light_direction())
        self.solar_system.draw(self.screen, self.camera, max_distance=planet_distance)
        self.star_field.draw(self.screen, self.camera, max_distance=planet_distance)

        # Draw UI
        self.draw_ui()

        pygame.display.flip()

    def draw_text_lines(self, lines: list[str], x: float, color: Color, title_color: Color | None = None) -> None:
        """Draw lines of text in a column starting at `x`."""
        for i, line in enumerate(lines):
            line_color = title_color if (i == 0 and title_color) else color
            self.screen.blit(self.font.render(line, True, line_color), (x, 10 + i * 22))

    def draw_centered(self, font: pygame.font.Font, text: str, y: float, color: Color) -> None:
        """Draw `text` centred horizontally at height `y`."""
        surface = font.render(text, True, color)
        self.screen.blit(surface, ((SCREEN_WIDTH - surface.get_width()) // 2, y))

    def draw_menu(self) -> None:
        """Draw the title and the list of scenarios."""
        self.draw_centered(self.title_font, "TheBlackHole", 170, MENU_TITLE_COLOR)
        self.draw_centered(self.font, "A 3D space simulation with a custom renderer", 240, MENU_ITEM_COLOR)
        for i, (_, title, description) in enumerate(SCENARIOS):
            selected = i == self.menu_index
            y = 330 + i * 90
            color = MENU_SELECTED_COLOR if selected else MENU_ITEM_COLOR
            self.draw_centered(self.item_font, f"{'> ' if selected else ''}{i + 1}. {title}", y, color)
            self.draw_centered(self.font, description, y + 38, HUD_STATUS_COLOR)
        self.draw_centered(self.font, "Up/Down + Enter or 1-3 to start  -  ESC in a scene returns here  -  ESC to quit",
                           SCREEN_HEIGHT - 60, HUD_STATUS_COLOR)

    def draw_ui(self) -> None:
        """Draw the controls on the left and the status on the right."""
        if self.scene == "blackhole":
            instructions, status_info = self.black_hole_hud()
        elif self.scene == "galaxy":
            instructions, status_info = self.galaxy_hud()
        elif self.mode == "planet":
            instructions = [
                "TheBlackHole - Planet Explorer",
                "WASD - Walk / strafe",
                "SHIFT - Run",
                "SPACE - Jump",
                "Mouse (press C) / Arrows - Turn and tilt camera",
                "Mouse wheel - Zoom",
                "TAB - Free camera",
                "P - Pause orbits, +/- - Time speed",
                "N - New stars",
                "ESC - Menu",
            ]
            player = self.player
            to_sun = normalize(self.star_field.sun_position - player.position)
            sun_elevation = math.degrees(math.asin(max(-1.0, min(1.0, float(np.dot(player.normal, to_sun))))))
            latitude = math.degrees(math.asin(max(-1.0, min(1.0, float(player.normal[1])))))
            longitude = math.degrees(math.atan2(player.normal[2], player.normal[0]))
            status_info = [
                f"FPS: {self.clock.get_fps():.0f}",
                f"Time: {self.time.label()}",
                f"Latitude: {latitude:.1f}°",
                f"Longitude: {longitude:.1f}°",
                f"Altitude: {player.altitude:.1f}",
                f"Sun Elevation: {sun_elevation:.1f}°",
                f"Time of Day: {'Day' if sun_elevation > 0 else 'Night'}",
                f"Mouse Look: {'ON' if self.mouse_captured else 'OFF'}",
            ]
        else:
            instructions = [
                "TheBlackHole - Free Camera",
                "WASD - Move forward/back/left/right",
                "QE - Move up/down",
                "SHIFT - Fast movement",
                "Mouse (press C) / Arrows - Look around",
                "TAB - Back to the planet",
                "P - Pause orbits, +/- - Time speed",
                "N - New stars",
                "ESC - Menu",
            ]
            position = self.camera.position
            sun = self.star_field.sun
            status_info = [
                f"FPS: {self.clock.get_fps():.0f}",
                f"Time: {self.time.label()}",
                f"Stars: {len(self.star_field.stars)}",
                f"Orbiting Planets: {len(self.solar_system.planets)}",
                f"Sun Mass: {sun.mass:.2e} kg",
                f"Sun Distance: {np.linalg.norm(position - self.star_field.sun_position):.0f} units",
                f"Planet Distance: {np.linalg.norm(position - self.planet.center):.0f} units",
                f"Position: ({position[0]:.0f}, {position[1]:.0f}, {position[2]:.0f})",
                f"Pitch: {math.degrees(self.free_pitch):.1f}°",
                f"Yaw: {math.degrees(self.free_yaw):.1f}°",
                f"Mouse Look: {'ON' if self.mouse_captured else 'OFF'}",
            ]

        instructions = [*instructions[:-1], "F5 - Save, F9 - Load", instructions[-1]]
        self.draw_text_lines(instructions, 10, HUD_TEXT_COLOR, WHITE)
        if self.message and pygame.time.get_ticks() / 1000.0 < self.message_until:
            self.draw_centered(self.font, self.message, SCREEN_HEIGHT - 40, MENU_TITLE_COLOR)
        self.draw_text_lines(status_info, SCREEN_WIDTH - 280, HUD_STATUS_COLOR)

        # Crosshair
        if self.mouse_captured and self.mode == "free":
            center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            pygame.draw.line(self.screen, (100, 100, 100),
                           (center_x - 10, center_y), (center_x + 10, center_y), 2)
            pygame.draw.line(self.screen, (100, 100, 100),
                           (center_x, center_y - 10), (center_x, center_y + 10), 2)

    def black_hole_hud(self) -> tuple[list[str], list[str]]:
        """Controls and status lines for the black hole scene."""
        instructions = [
            "TheBlackHole - Black Hole",
            "WASD - Move forward/back/left/right",
            "QE - Move up/down",
            "SHIFT - Fast movement",
            "Mouse (press C) / Arrows - Look around",
            "F - Throw a rock",
            "P - Pause, +/- - Time speed",
            "ESC - Menu",
        ]
        hole = self.black_hole_scene.black_hole
        info = hud_readout(hole, self.camera.position, self.camera_speed)
        status_info = [
            f"FPS: {self.clock.get_fps():.0f}",
            f"Time: {self.time.label()}",
            f"Mass: {info['mass']:.2e}",
            f"Event horizon (r_s): {info['horizon']:.1f} units",
            f"Distance: {info['distance']:.0f} units ({info['distance_rs']:.1f} r_s)",
            f"Camera speed: {info['speed']:.0f} units/s ({info['speed_c']:.2f} c)",
            f"Escape speed here: {info['escape_c']:.2f} c",
            f"Your clock runs at: {info['clock_rate'] * 100:.1f} %",
            f"Captured: {self.black_hole_scene.captured}",
        ]
        return instructions, status_info

    def galaxy_hud(self) -> tuple[list[str], list[str]]:
        """Controls and status lines for the galaxy scene."""
        instructions = [
            "TheBlackHole - Galaxy",
            "WASD - Move forward/back/left/right",
            "QE - Move up/down",
            "SHIFT - Fast movement",
            "Mouse (press C) / Arrows - Look around",
            "P - Pause, +/- - Time speed",
            "ESC - Menu",
        ]
        status_info = [
            f"FPS: {self.clock.get_fps():.0f}",
            f"Time: {self.time.label()}",
            f"Stars: {len(self.galaxy_scene.galaxy.positions)}",
            f"Distance to center: {np.linalg.norm(self.camera.position):.0f} units",
            f"Camera speed: {self.camera_speed:.0f} units/s",
        ]
        return instructions, status_info

    def run(self) -> None:
        """Main loop: events, update and draw until the window closes."""
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, MAX_FRAME_TIME)
            self.handle_events(dt)
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


def main() -> None:
    """Start pygame and run the simulation."""
    pygame.init()
    print("Starting TheBlackHole... pick a scenario in the menu (1-3).")
    simulation = SpaceSimulation3D()
    simulation.run()


if __name__ == "__main__":
    main()
