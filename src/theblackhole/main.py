"""Main loop: the planet explorer and the free camera."""

import math
import sys

import numpy as np
import pygame

from .camera import Camera, normalize
from .config import (
    BLACK,
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
    HUD_STATUS_COLOR,
    HUD_TEXT_COLOR,
    MAX_FRAME_TIME,
    MOUSE_SENSITIVITY,
    NUM_STARS,
    PLANET_CENTER,
    PLANET_RADIUS,
    PLANET_STAR_CLEAR_RADIUS,
    RUN_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TURN_SPEED,
    WALK_SPEED,
    WHITE,
)
from .planet import Planet
from .player import Player
from .solar_system import SolarSystem
from .starfield import StarField3D


class SpaceSimulation3D:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("TheBlackHole - Planet Explorer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.running = True

        self.planet = Planet(PLANET_CENTER, PLANET_RADIUS)
        self.new_star_field()

        self.player = self.create_player()

        self.camera = Camera()
        self.mode = "planet"  # "planet" = third person on the planet, "free" = free-fly camera

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

    def create_player(self):
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

    def new_star_field(self):
        self.star_field = StarField3D(NUM_STARS, clear_zones=[(tuple(self.planet.center), PLANET_STAR_CLEAR_RADIUS)])
        sun = self.star_field.sun
        self.star_field.sun_position = np.array([sun.x, sun.y, sun.z], dtype=float)
        self.solar_system = SolarSystem(self.star_field.sun_position)

    def toggle_mode(self):
        if self.mode == "planet":
            # Start flying from where the third-person camera is
            self.mode = "free"
            self.free_position = self.camera.position.copy()
            forward = self.camera.forward
            self.free_yaw = math.atan2(forward[0], forward[2])
            self.free_pitch = math.asin(max(-1.0, min(1.0, forward[1])))
        else:
            self.mode = "planet"

    def handle_events(self, dt):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_n:
                    self.new_star_field()
                elif event.key == pygame.K_TAB:
                    self.toggle_mode()
                elif event.key == pygame.K_SPACE and self.mode == "planet":
                    self.player.jump()
                elif event.key == pygame.K_c:
                    # Toggle mouse capture
                    self.mouse_captured = not self.mouse_captured
                    pygame.mouse.set_visible(not self.mouse_captured)
                    pygame.event.set_grab(self.mouse_captured)
            elif event.type == pygame.MOUSEWHEEL and self.mode == "planet":
                self.camera_distance = max(CAMERA_ZOOM_MIN, min(CAMERA_ZOOM_MAX, self.camera_distance - event.y * CAMERA_ZOOM_STEP))
            elif event.type == pygame.MOUSEMOTION and self.mouse_captured:
                mouse_x, mouse_y = event.rel
                if self.mode == "planet":
                    self.player.turn(mouse_x * self.mouse_sensitivity)
                    self.tilt_camera(mouse_y * self.mouse_sensitivity)
                else:
                    self.free_yaw += mouse_x * self.mouse_sensitivity
                    self.free_pitch -= mouse_y * self.mouse_sensitivity
                    self.free_pitch = max(-math.pi/2 + 0.1, min(math.pi/2 - 0.1, self.free_pitch))

        keys = pygame.key.get_pressed()
        if self.mode == "planet":
            self.handle_player_keys(keys, dt)
        else:
            self.handle_free_camera_keys(keys, dt)

    def tilt_camera(self, amount):
        self.camera_elevation = max(CAMERA_ELEVATION_MIN, min(CAMERA_ELEVATION_MAX, self.camera_elevation + amount))

    def handle_player_keys(self, keys, dt):
        speed = (RUN_SPEED if keys[pygame.K_LSHIFT] else WALK_SPEED) * dt
        forward = (keys[pygame.K_w] - keys[pygame.K_s]) * speed
        sideways = (keys[pygame.K_d] - keys[pygame.K_a]) * speed
        self.player.move(forward, sideways)

        self.player.turn((keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * TURN_SPEED * dt)
        self.tilt_camera((keys[pygame.K_DOWN] - keys[pygame.K_UP]) * self.rotation_speed * dt)

    def handle_free_camera_keys(self, keys, dt):
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

    def update_camera(self):
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

    def update(self, dt):
        time = pygame.time.get_ticks() / 1000.0
        self.star_field.update(time)
        self.solar_system.update(dt)
        self.player.update(dt)
        self.update_camera()

    def light_direction(self):
        return normalize(self.star_field.sun_position - self.planet.center)

    def draw(self):
        self.screen.fill(BLACK)

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

    def draw_text_lines(self, lines, x, color, title_color=None):
        for i, line in enumerate(lines):
            line_color = title_color if (i == 0 and title_color) else color
            self.screen.blit(self.font.render(line, True, line_color), (x, 10 + i * 22))

    def draw_ui(self):
        if self.mode == "planet":
            instructions = [
                "TheBlackHole - Planet Explorer",
                "WASD - Walk / strafe",
                "SHIFT - Run",
                "SPACE - Jump",
                "Mouse (press C) / Arrows - Turn and tilt camera",
                "Mouse wheel - Zoom",
                "TAB - Free camera",
                "N - New stars",
                "ESC - Exit",
            ]
            player = self.player
            to_sun = normalize(self.star_field.sun_position - player.position)
            sun_elevation = math.degrees(math.asin(max(-1.0, min(1.0, float(np.dot(player.normal, to_sun))))))
            latitude = math.degrees(math.asin(max(-1.0, min(1.0, float(player.normal[1])))))
            longitude = math.degrees(math.atan2(player.normal[2], player.normal[0]))
            status_info = [
                f"FPS: {self.clock.get_fps():.0f}",
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
                "N - New stars",
                "ESC - Exit",
            ]
            position = self.camera.position
            sun = self.star_field.sun
            status_info = [
                f"FPS: {self.clock.get_fps():.0f}",
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

        self.draw_text_lines(instructions, 10, HUD_TEXT_COLOR, WHITE)
        self.draw_text_lines(status_info, SCREEN_WIDTH - 280, HUD_STATUS_COLOR)

        # Crosshair
        if self.mouse_captured and self.mode == "free":
            center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            pygame.draw.line(self.screen, (100, 100, 100),
                           (center_x - 10, center_y), (center_x + 10, center_y), 2)
            pygame.draw.line(self.screen, (100, 100, 100),
                           (center_x, center_y - 10), (center_x, center_y + 10), 2)

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, MAX_FRAME_TIME)
            self.handle_events(dt)
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


def main():
    pygame.init()
    print("Starting TheBlackHole - Planet Explorer...")
    print("Walk on the planet with WASD, jump with SPACE.")
    print("Press C to control the camera with the mouse, TAB for the free camera.")
    simulation = SpaceSimulation3D()
    simulation.run()


if __name__ == "__main__":
    main()
