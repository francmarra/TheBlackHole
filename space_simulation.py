import pygame
import random
import math
import sys

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

class Star:
    def __init__(self, x, y, size=None, color=None, brightness=None, mass=None):
        self.x = x
        self.y = y
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
        self.acceleration_x = 0.0
        self.acceleration_y = 0.0
        
    def calculate_gravitational_force(self, other_star):
        """Calculate gravitational force between this star and another star"""
        # Calculate distance between stars
        dx = other_star.x - self.x
        dy = other_star.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Avoid division by zero
        if distance == 0:
            return 0, 0
        
        # Calculate gravitational force magnitude: F = G * m1 * m2 / r^2
        force_magnitude = (self.gravitational_constant * self.mass * other_star.mass) / (distance * distance)
        
        # Calculate force components (unit vector * magnitude)
        force_x = (dx / distance) * force_magnitude
        force_y = (dy / distance) * force_magnitude
        
        return force_x, force_y
    
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
        
    def draw(self, screen, camera_x, camera_y, zoom):
        # Apply camera transform
        screen_x = (self.x - camera_x) * zoom + screen.get_width() // 2
        screen_y = (self.y - camera_y) * zoom + screen.get_height() // 2
        
        # Skip drawing if star is off screen
        if screen_x < -50 or screen_x > screen.get_width() + 50 or screen_y < -50 or screen_y > screen.get_height() + 50:
            return
        
        # Apply brightness to color with proper clamping
        bright_color = tuple(max(0, min(255, int(c * self.current_brightness))) for c in self.color)
        
        # Draw the star with a glow effect (scale size with zoom)
        star_size = max(1, int(self.size * self.current_brightness * zoom))
        
        # Draw outer glow
        if star_size > 1:
            glow_color = tuple(max(0, min(255, int(c * 0.3))) for c in bright_color)
            pygame.draw.circle(screen, glow_color, (int(screen_x), int(screen_y)), star_size + 2)
        
        # Draw main star
        pygame.draw.circle(screen, bright_color, (int(screen_x), int(screen_y)), star_size)
        
        # Draw cross pattern for bigger stars
        if star_size >= 2:
            pygame.draw.line(screen, bright_color, 
                           (int(screen_x - star_size - 1), int(screen_y)), 
                           (int(screen_x + star_size + 1), int(screen_y)), 1)
            pygame.draw.line(screen, bright_color, 
                           (int(screen_x), int(screen_y - star_size - 1)), 
                           (int(screen_x), int(screen_y + star_size + 1)), 1)

class StarField:
    def __init__(self, num_stars=200):
        self.stars = []
        self.generate_stars(num_stars)
        
    def generate_stars(self, num_stars):
        """Generate a realistic distribution of stars across a larger space"""
        for _ in range(num_stars):
            # Generate stars in a much larger area for exploration
            x = random.randint(-2000, 2000)
            y = random.randint(-2000, 2000)
            
            # Create different types of stars with different probabilities
            star_type = random.random()
            
            if star_type < 0.7:  # 70% small dim stars
                size = random.uniform(0.5, 1.5)
                brightness = random.uniform(0.6, 0.9)  # Increased from 0.3-0.6
            elif star_type < 0.9:  # 20% medium stars
                size = random.uniform(1.5, 2.5)
                brightness = random.uniform(0.8, 1.0)  # Increased from 0.6-0.8
            else:  # 10% bright large stars
                size = random.uniform(2.5, 4.0)
                brightness = random.uniform(1.0, 1.3)  # Increased from 0.8-1.0
                
            star = Star(x, y, size, brightness=brightness)
            self.stars.append(star)
    
    def update(self, time):
        for star in self.stars:
            star.update(time)
            
    def draw(self, screen, camera_x, camera_y, zoom):
        for star in self.stars:
            star.draw(screen, camera_x, camera_y, zoom)

class SpaceSimulation:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Simulation - Star Field")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Create star field
        self.star_field = StarField(500)  # More stars for larger space
        
        # Camera/view variables
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # Mouse control variables
        self.mouse_dragging = False
        self.last_mouse_pos = (0, 0)
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    # Regenerate stars
                    self.star_field = StarField(500)
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self.zoom = min(3.0, self.zoom * 1.2)
                elif event.key == pygame.K_MINUS:
                    self.zoom = max(0.1, self.zoom / 1.2)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.mouse_dragging = True
                    self.last_mouse_pos = event.pos
                elif event.button == 4:  # Mouse wheel up
                    self.zoom = min(3.0, self.zoom * 1.1)
                elif event.button == 5:  # Mouse wheel down
                    self.zoom = max(0.1, self.zoom / 1.1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.mouse_dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_dragging:
                    mouse_x, mouse_y = event.pos
                    last_x, last_y = self.last_mouse_pos
                    
                    # Move camera based on mouse movement
                    self.camera_x -= (mouse_x - last_x) / self.zoom
                    self.camera_y -= (mouse_y - last_y) / self.zoom
                    
                    self.last_mouse_pos = event.pos
        
        # Handle continuous key presses for movement
        keys = pygame.key.get_pressed()
        move_speed = 5.0 / self.zoom  # Adjust speed based on zoom
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.camera_x -= move_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.camera_x += move_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.camera_y -= move_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.camera_y += move_speed
    
    def update(self):
        time = pygame.time.get_ticks() / 1000.0
        self.star_field.update(time)
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw star field with camera transforms
        self.star_field.draw(self.screen, self.camera_x, self.camera_y, self.zoom)
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        font = pygame.font.Font(None, 24)  # Smaller font size
        
        # Instructions
        instructions = [
            "Space Star Field Simulation",
            "Controls:",
            "WASD or Arrow Keys - Move camera",
            "Mouse Drag - Pan around",
            "Mouse Wheel - Zoom in/out",
            "+/- - Zoom in/out",
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
        mass_counts = {"Dwarf": 0, "Small": 0, "Medium": 0, "Large": 0, "Giant": 0}
        for star in self.star_field.stars:
            category = star.get_mass_category()
            mass_counts[category] += 1
        
        # Status info
        status_info = [
            f"Stars: {len(self.star_field.stars)}",
            f"Total Mass: {total_mass:.0f}",
            f"Dwarf/Small/Med/Large/Giant: {mass_counts['Dwarf']}/{mass_counts['Small']}/{mass_counts['Medium']}/{mass_counts['Large']}/{mass_counts['Giant']}",
            f"Camera: ({self.camera_x:.0f}, {self.camera_y:.0f})",
            f"Zoom: {self.zoom:.1f}x"
        ]
        
        for i, info in enumerate(status_info):
            text = font.render(info, True, (150, 150, 150))
            self.screen.blit(text, (SCREEN_WIDTH - 200, 10 + i * 25))
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("Starting Space Simulation...")
    print("This will create a beautiful star field in space!")
    simulation = SpaceSimulation()
    simulation.run()
