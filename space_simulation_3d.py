import pygame
import random
import math
import sys
import numpy as np

# Initialize Pygame
pygame.init()

# Constants
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

class Star3D:
    def __init__(self, x, y, z, size=None, color=None, brightness=None, mass=None):
        self.x = x
        self.y = y
        self.z = z
        self.size = size if size else random.uniform(0.5, 3.0)
        self.color = color if color else random.choice(STAR_COLORS)
        self.brightness = brightness if brightness else random.uniform(0.3, 1.0)
        self.twinkle_speed = random.uniform(0.02, 0.05)
        self.twinkle_offset = random.uniform(0, 2 * math.pi)
        self.current_brightness = self.brightness
        
        # Mass and gravity properties
        if mass is None:
            # Mass correlates with size and brightness (larger/brighter stars are more massive)
            base_mass = self.size * 1000  # Base mass
            brightness_factor = self.brightness * 2  # Brighter stars are more massive
            self.mass = base_mass * brightness_factor
        else:
            self.mass = mass
            
        # Gravitational constant (can be adjusted for simulation)
        self.gravitational_constant = 6.67430e-11  # Real physics constant
        
        # For future physics calculations
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.velocity_z = 0.0
        self.acceleration_x = 0.0
        self.acceleration_y = 0.0
        self.acceleration_z = 0.0
        
    def calculate_gravitational_force(self, other_star):
        """Calculate gravitational force between this star and another star"""
        # Calculate distance between stars
        dx = other_star.x - self.x
        dy = other_star.y - self.y
        dz = other_star.z - self.z
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # Avoid division by zero
        if distance == 0:
            return 0, 0, 0
        
        # Calculate gravitational force magnitude: F = G * m1 * m2 / r^2
        force_magnitude = (self.gravitational_constant * self.mass * other_star.mass) / (distance * distance)
        
        # Calculate force components (unit vector * magnitude)
        force_x = (dx / distance) * force_magnitude
        force_y = (dy / distance) * force_magnitude
        force_z = (dz / distance) * force_magnitude
        
        return force_x, force_y, force_z
    
    def get_mass_category(self):
        """Return the mass category of this star for display purposes"""
        if self.mass < 500:
            return "Dwarf"
        elif self.mass < 2000:
            return "Small"
        elif self.mass < 5000:
            return "Medium"
        elif self.mass < 10000:
            return "Large"
        else:
            return "Giant"
        
    def update(self, time):
        # Create twinkling effect with brighter range
        twinkle = math.sin(time * self.twinkle_speed + self.twinkle_offset) * 0.4  # Increased from 0.3
        self.current_brightness = max(0.3, self.brightness + twinkle)  # Increased minimum from 0.1
        
    def project_to_2d(self, camera_x, camera_y, camera_z, camera_pitch, camera_yaw):
        # Translate relative to camera
        dx = self.x - camera_x
        dy = self.y - camera_y
        dz = self.z - camera_z
        
        # Rotate around Y-axis (yaw)
        cos_yaw = math.cos(camera_yaw)
        sin_yaw = math.sin(camera_yaw)
        
        rotated_x = dx * cos_yaw - dz * sin_yaw
        rotated_z = dx * sin_yaw + dz * cos_yaw
        
        # Rotate around X-axis (pitch)
        cos_pitch = math.cos(camera_pitch)
        sin_pitch = math.sin(camera_pitch)
        
        rotated_y = dy * cos_pitch - rotated_z * sin_pitch
        final_z = dy * sin_pitch + rotated_z * cos_pitch
        
        # Skip if behind camera
        if final_z <= 0.1:
            return None
            
        # Perspective projection
        focal_length = 400
        screen_x = (rotated_x * focal_length) / final_z + SCREEN_WIDTH // 2
        screen_y = (rotated_y * focal_length) / final_z + SCREEN_HEIGHT // 2
        
        # Calculate distance-based scale
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        scale = max(0.1, 1.0 / (distance * 0.01 + 1))
        
        return screen_x, screen_y, final_z, scale
        
    def draw(self, screen, camera_x, camera_y, camera_z, camera_pitch, camera_yaw):
        projection = self.project_to_2d(camera_x, camera_y, camera_z, camera_pitch, camera_yaw)
        
        if projection is None:
            return
            
        screen_x, screen_y, depth, scale = projection
        
        # Skip if off screen
        if screen_x < -50 or screen_x > SCREEN_WIDTH + 50 or screen_y < -50 or screen_y > SCREEN_HEIGHT + 50:
            return
        
        # Apply brightness and distance to color with controlled saturation
        distance_brightness = min(1.0, scale * 3)  # Reduced from 4 to 3
        final_brightness = min(1.5, self.current_brightness * distance_brightness)  # Reduced max from 2.0 to 1.5
        
        # Apply color with moderate enhancement to avoid oversaturation
        bright_color = tuple(max(0, min(255, int(c * final_brightness))) for c in self.color)
        
        # Calculate star size based on distance and original size - keep reasonable sizes
        star_size = max(1, int(self.size * scale * 3))  # Reduced from 6 to 3 for sharper stars
        
        # Draw outer glow for larger stars only, with reduced blur
        if star_size >= 3:
            glow_radius = star_size + 1  # Much smaller glow radius
            # Subtle glow
            glow_color = tuple(max(0, min(255, int(c * 0.3))) for c in bright_color)  # Reduced glow intensity
            pygame.draw.circle(screen, glow_color, (int(screen_x), int(screen_y)), glow_radius)
        
        # Draw main star with sharp edges - use anti-aliased circles for smoothness
        if star_size >= 2:
            pygame.draw.circle(screen, bright_color, (int(screen_x), int(screen_y)), star_size)
            # Add a bright center pixel for sharpness
            pygame.draw.circle(screen, (255, 255, 255), (int(screen_x), int(screen_y)), max(1, star_size // 2))
        else:
            # For small stars, just draw a simple pixel
            pygame.draw.circle(screen, bright_color, (int(screen_x), int(screen_y)), star_size)
        
        # Draw sharp cross pattern for bigger stars
        if star_size >= 2:
            cross_length = star_size + 1  # Shorter cross lines
            # Sharp, bright cross lines
            cross_color = bright_color  # Use the same bright color
            pygame.draw.line(screen, cross_color, 
                           (int(screen_x - cross_length), int(screen_y)), 
                           (int(screen_x + cross_length), int(screen_y)), 1)  # Thinner, sharper lines
            pygame.draw.line(screen, cross_color, 
                           (int(screen_x), int(screen_y - cross_length)), 
                           (int(screen_x), int(screen_y + cross_length)), 1)

class Sun3D(Star3D):
    def __init__(self, x, y, z):
        # Sun properties based on real astronomical data
        sun_size = 10.0  # Larger visual size for the Sun
        sun_color = (255, 255, 150)  # Yellowish color
        sun_brightness = 2.0  # Very bright
        sun_mass = 1.9885e30  # Real Sun mass in kg
        
        super().__init__(x, y, z, size=sun_size, color=sun_color, brightness=sun_brightness, mass=sun_mass)
        
        # Sun-specific properties
        self.volume = 1.412e18  # km³
        self.density = 1.408  # g/cm³
        self.earth_mass_ratio = 332950  # Times Earth's mass
        self.earth_volume_ratio = 1300000  # Times Earth's volume
        self.is_sun = True
        
        # Enhanced visual properties for the Sun
        self.corona_size = 15  # Corona glow size
        self.flare_intensity = 0.5  # Solar flare effect
        
    def update(self, time):
        # Sun has more complex twinkling (solar activity)
        primary_twinkle = math.sin(time * 0.01) * 0.1
        secondary_twinkle = math.sin(time * 0.03 + 1.5) * 0.05
        solar_flare = math.sin(time * 0.02 + 2.0) * 0.1
        
        self.current_brightness = max(1.5, self.brightness + primary_twinkle + secondary_twinkle + solar_flare)
        
    def draw(self, screen, camera_x, camera_y, camera_z, camera_pitch, camera_yaw):
        projection = self.project_to_2d(camera_x, camera_y, camera_z, camera_pitch, camera_yaw)
        
        if projection is None:
            return
            
        screen_x, screen_y, depth, scale = projection
        
        # Skip if off screen
        if screen_x < -100 or screen_x > SCREEN_WIDTH + 100 or screen_y < -100 or screen_y > SCREEN_HEIGHT + 100:
            return
        
        # Sun is always visible and bright
        distance_brightness = max(0.8, min(1.5, scale * 5))  # Sun stays bright at distance
        final_brightness = min(2.5, self.current_brightness * distance_brightness)
        
        # Enhanced Sun color with brightness
        bright_color = tuple(max(0, min(255, int(c * final_brightness))) for c in self.color)
        
        # Calculate Sun size (always significant)
        sun_size = max(5, int(self.size * scale * 4))
        
        # Draw corona (outermost layer)
        corona_radius = sun_size + int(self.corona_size * scale)
        corona_color = tuple(max(0, min(255, int(c * 0.1))) for c in bright_color)
        if corona_radius > 0:
            pygame.draw.circle(screen, corona_color, (int(screen_x), int(screen_y)), corona_radius)
        
        # Draw outer atmosphere
        atmosphere_radius = sun_size + int(8 * scale)
        atmosphere_color = tuple(max(0, min(255, int(c * 0.3))) for c in bright_color)
        if atmosphere_radius > 0:
            pygame.draw.circle(screen, atmosphere_color, (int(screen_x), int(screen_y)), atmosphere_radius)
        
        # Draw main Sun body
        pygame.draw.circle(screen, bright_color, (int(screen_x), int(screen_y)), sun_size)
        
        # Draw bright core
        core_size = max(2, sun_size // 2)
        core_color = (255, 255, 255)  # White hot core
        pygame.draw.circle(screen, core_color, (int(screen_x), int(screen_y)), core_size)
        
        # Draw solar flares (cross pattern)
        flare_length = sun_size + int(10 * scale)
        flare_color = tuple(max(0, min(255, int(c * 0.8))) for c in bright_color)
        
        # Main cross
        pygame.draw.line(screen, flare_color, 
                       (int(screen_x - flare_length), int(screen_y)), 
                       (int(screen_x + flare_length), int(screen_y)), 3)
        pygame.draw.line(screen, flare_color, 
                       (int(screen_x), int(screen_y - flare_length)), 
                       (int(screen_x), int(screen_y + flare_length)), 3)
        
        # Diagonal cross for extra solar effect
        diagonal_length = int(flare_length * 0.7)
        pygame.draw.line(screen, flare_color, 
                       (int(screen_x - diagonal_length), int(screen_y - diagonal_length)), 
                       (int(screen_x + diagonal_length), int(screen_y + diagonal_length)), 2)
        pygame.draw.line(screen, flare_color, 
                       (int(screen_x - diagonal_length), int(screen_y + diagonal_length)), 
                       (int(screen_x + diagonal_length), int(screen_y - diagonal_length)), 2)
    
    def get_mass_category(self):
        return "Sun"

class StarField3D:
    def __init__(self, num_stars=800):
        self.stars = []
        self.sun = None
        self.generate_stars(num_stars)
        
    def generate_stars(self, num_stars):
        """Generate a 3D distribution of stars with the Sun at the center"""
        # Clear existing stars
        self.stars = []
        
        # Add the Sun at the center
        self.sun = Sun3D(0, 0, 0)
        self.stars.append(self.sun)
        
        # Generate other stars around the Sun
        for _ in range(num_stars - 1):  # -1 because we already added the Sun
            # Generate stars in a large 3D space around the Sun
            x = random.randint(-3000, 3000)
            y = random.randint(-3000, 3000)
            z = random.randint(-3000, 3000)
            
            # Avoid placing stars too close to the Sun
            distance_from_sun = math.sqrt(x*x + y*y + z*z)
            if distance_from_sun < 50:  # Minimum distance from Sun
                # Push star away from Sun
                factor = 50 / distance_from_sun
                x *= factor
                y *= factor
                z *= factor
            
            # Create different types of stars with different probabilities
            star_type = random.random()
            
            if star_type < 0.7:  # 70% small dim stars
                size = random.uniform(0.5, 1.5)
                brightness = random.uniform(0.6, 0.9)
            elif star_type < 0.9:  # 20% medium stars
                size = random.uniform(1.5, 2.5)
                brightness = random.uniform(0.8, 1.0)
            else:  # 10% bright large stars
                size = random.uniform(2.5, 4.0)
                brightness = random.uniform(1.0, 1.3)
                
            star = Star3D(x, y, z, size, brightness=brightness)
            self.stars.append(star)
    
    def update(self, time):
        for star in self.stars:
            star.update(time)
            
    def draw(self, screen, camera_x, camera_y, camera_z, camera_pitch, camera_yaw):
        # Sort stars by distance for proper rendering order
        star_distances = []
        for star in self.stars:
            dx = star.x - camera_x
            dy = star.y - camera_y
            dz = star.z - camera_z
            distance = dx*dx + dy*dy + dz*dz
            star_distances.append((distance, star))
        
        # Sort by distance (far to near)
        star_distances.sort(key=lambda x: x[0], reverse=True)
        
        # Draw stars
        for distance, star in star_distances:
            star.draw(screen, camera_x, camera_y, camera_z, camera_pitch, camera_yaw)

class SpaceSimulation3D:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("3D Space Simulation - Star Field")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Create 3D star field
        self.star_field = StarField3D(800)  # 800 stars in 3D space
        
        # 3D Camera variables
        self.camera_x = 0
        self.camera_y = 0
        self.camera_z = 0
        self.camera_pitch = 0  # Rotation around X-axis
        self.camera_yaw = 0    # Rotation around Y-axis
        
        # Movement variables
        self.move_speed = 10.0
        self.rotation_speed = 0.02
        
        # Mouse control variables
        self.mouse_sensitivity = 0.003
        self.mouse_captured = False
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    # Regenerate stars
                    self.star_field = StarField3D(800)
                elif event.key == pygame.K_c:
                    # Toggle mouse capture
                    self.mouse_captured = not self.mouse_captured
                    if self.mouse_captured:
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                    else:
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
            elif event.type == pygame.MOUSEMOTION and self.mouse_captured:
                # Mouse look
                mouse_x, mouse_y = event.rel
                self.camera_yaw += mouse_x * self.mouse_sensitivity
                self.camera_pitch -= mouse_y * self.mouse_sensitivity
                
                # Clamp pitch to avoid flipping
                self.camera_pitch = max(-math.pi/2 + 0.1, min(math.pi/2 - 0.1, self.camera_pitch))
        
        # Handle continuous key presses for movement
        keys = pygame.key.get_pressed()
        
        # Calculate movement vectors based on camera orientation
        cos_yaw = math.cos(self.camera_yaw)
        sin_yaw = math.sin(self.camera_yaw)
        
        # Forward/backward movement
        if keys[pygame.K_w]:
            self.camera_x += sin_yaw * self.move_speed
            self.camera_z += cos_yaw * self.move_speed
        if keys[pygame.K_s]:
            self.camera_x -= sin_yaw * self.move_speed
            self.camera_z -= cos_yaw * self.move_speed
            
        # Left/right strafing
        if keys[pygame.K_a]:
            self.camera_x -= cos_yaw * self.move_speed
            self.camera_z += sin_yaw * self.move_speed
        if keys[pygame.K_d]:
            self.camera_x += cos_yaw * self.move_speed
            self.camera_z -= sin_yaw * self.move_speed
            
        # Up/down movement
        if keys[pygame.K_q]:
            self.camera_y += self.move_speed
        if keys[pygame.K_e]:
            self.camera_y -= self.move_speed
            
        # Rotation with arrow keys
        if keys[pygame.K_LEFT]:
            self.camera_yaw -= self.rotation_speed
        if keys[pygame.K_RIGHT]:
            self.camera_yaw += self.rotation_speed
        if keys[pygame.K_UP]:
            self.camera_pitch += self.rotation_speed
        if keys[pygame.K_DOWN]:
            self.camera_pitch -= self.rotation_speed
            
        # Speed controls
        if keys[pygame.K_LSHIFT]:
            self.move_speed = 50.0  # Fast movement
        else:
            self.move_speed = 10.0  # Normal speed
    
    def update(self):
        time = pygame.time.get_ticks() / 1000.0
        self.star_field.update(time)
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw 3D star field
        self.star_field.draw(self.screen, self.camera_x, self.camera_y, self.camera_z, 
                           self.camera_pitch, self.camera_yaw)
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        font = pygame.font.Font(None, 24)
        
        # Instructions
        instructions = [
            "3D Space Simulation",
            "Controls:",
            "WASD - Move forward/back/left/right",
            "QE - Move up/down",
            "Arrow Keys - Look around",
            "C - Toggle mouse look",
            "SHIFT - Fast movement",
            "SPACE - Generate new stars",
            "ESC - Exit"
        ]
        
        for i, instruction in enumerate(instructions):
            color = WHITE if i == 0 else (200, 200, 200)
            text = font.render(instruction, True, color)
            self.screen.blit(text, (10, 10 + i * 22))
        
        # Calculate total mass in the system
        total_mass = sum(star.mass for star in self.star_field.stars)
        
        # Count stars by mass category
        mass_counts = {"Dwarf": 0, "Small": 0, "Medium": 0, "Large": 0, "Giant": 0, "Sun": 0}
        for star in self.star_field.stars:
            category = star.get_mass_category()
            mass_counts[category] += 1
        
        # Get Sun distance from camera
        sun_distance = 0
        if self.star_field.sun:
            dx = self.star_field.sun.x - self.camera_x
            dy = self.star_field.sun.y - self.camera_y
            dz = self.star_field.sun.z - self.camera_z
            sun_distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # Status info
        status_info = [
            f"Stars: {len(self.star_field.stars)}",
            f"Sun Mass: {self.star_field.sun.mass:.2e} kg" if self.star_field.sun else "No Sun",
            f"Sun Distance: {sun_distance:.0f} units",
            f"Total Mass: {total_mass:.2e}",
            f"Dwarf Stars: {mass_counts['Dwarf']}",
            f"Small Stars: {mass_counts['Small']}",
            f"Medium Stars: {mass_counts['Medium']}",
            f"Large Stars: {mass_counts['Large']}",
            f"Giant Stars: {mass_counts['Giant']}",
            f"Position: ({self.camera_x:.0f}, {self.camera_y:.0f}, {self.camera_z:.0f})",
            f"Pitch: {math.degrees(self.camera_pitch):.1f}°",
            f"Yaw: {math.degrees(self.camera_yaw):.1f}°",
            f"Mouse Look: {'ON' if self.mouse_captured else 'OFF'}",
            f"Speed: {'FAST' if self.move_speed > 10 else 'NORMAL'}"
        ]
        
        for i, info in enumerate(status_info):
            text = font.render(info, True, (150, 150, 150))
            self.screen.blit(text, (SCREEN_WIDTH - 280, 10 + i * 22))
        
        # Crosshair
        if self.mouse_captured:
            center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            pygame.draw.line(self.screen, (100, 100, 100), 
                           (center_x - 10, center_y), (center_x + 10, center_y), 2)
            pygame.draw.line(self.screen, (100, 100, 100), 
                           (center_x, center_y - 10), (center_x, center_y + 10), 2)
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("Starting 3D Space Simulation...")
    print("Navigate through 3D space with WASD, QE, and mouse look!")
    print("Press C to toggle mouse look for better 3D navigation.")
    simulation = SpaceSimulation3D()
    simulation.run()
