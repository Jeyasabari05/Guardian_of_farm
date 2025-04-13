import cv2
import numpy as np
import random
import time
import os
import traceback
import math

class CropPlot:
    def __init__(self, img_path, x, y, screen_width, screen_height):
        try:
            self.original_img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            
            # If the image has no alpha channel, add one
            if self.original_img is None:
                # Create a fallback crop image
                self.img = np.zeros((80, 80, 4), dtype=np.uint8)
                self.img[:, :, 0] = 50  # B - Blue component (brown)
                self.img[:, :, 1] = 170  # G - Green component (brown)
                self.img[:, :, 2] = 100  # R - Red component (brown)
                self.img[:, :, 3] = 255  # A - Alpha channel
                
                # Draw a simple crop
                cv2.rectangle(self.img, (20, 40), (60, 70), (20, 120, 30), -1)  # Crop base
                cv2.rectangle(self.img, (30, 20), (50, 40), (20, 200, 50), -1)  # Crop leaves
            elif self.original_img.shape[2] == 3:
                self.original_img = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2BGRA)
                self.img = cv2.resize(self.original_img, (80, 80))
            else:
                self.img = cv2.resize(self.original_img, (80, 80))
                
            self.width, self.height = self.img.shape[1], self.img.shape[0]
            self.screen_width, self.screen_height = screen_width, screen_height
            
            # Position
            self.x = x
            self.y = y
            
            # Health of the crop
            self.max_health = 3
            self.health = self.max_health
            
            # Visual effect for hit
            self.is_being_hit = False
            self.hit_timer = 0
            self.hit_duration = 8  # frames
            
            # Visual effect for health levels
            self.health_colors = [
                (0, 0, 255),    # Red - critical
                (0, 165, 255),  # Orange - damaged
                (0, 255, 0)     # Green - healthy
            ]
            
            # For highlighting when targeted
            self.is_targeted = False
            self.target_pulse = 0
            
        except Exception as e:
            print(f"Error creating crop: {e}")
            traceback.print_exc()
            # Create a fallback crop with default values
            self.img = np.zeros((80, 80, 4), dtype=np.uint8)
            cv2.rectangle(self.img, (20, 40), (60, 70), (20, 120, 30), -1)  # Crop base
            cv2.rectangle(self.img, (30, 20), (50, 40), (20, 200, 50), -1)  # Crop leaves
            self.img[:, :, 3] = 255  # Set alpha channel
            
            self.width, self.height = 80, 80
            self.screen_width, self.screen_height = screen_width, screen_height
            self.x, self.y = x, y
            self.max_health = 3
            self.health = self.max_health
            self.is_being_hit = False
            self.hit_timer = 0
            self.hit_duration = 8
            self.health_colors = [(0, 0, 255), (0, 165, 255), (0, 255, 0)]
            self.is_targeted = False
            self.target_pulse = 0
    
    def update(self):
        # Update hit animation
        if self.is_being_hit:
            self.hit_timer += 1
            if self.hit_timer >= self.hit_duration:
                self.is_being_hit = False
                self.hit_timer = 0
        
        # Update target highlight animation
        if self.is_targeted:
            self.target_pulse = (self.target_pulse + 1) % 30
    
    def take_damage(self):
        """Reduce health when crop is hit by enemy"""
        self.health = max(0, self.health - 1)
        self.is_being_hit = True
        self.hit_timer = 0
        return self.health <= 0  # Return True if destroyed
    
    def heal(self, amount=1):
        """Heal the crop"""
        self.health = min(self.max_health, self.health + amount)
    
    def is_destroyed(self):
        """Check if crop is destroyed"""
        return self.health <= 0
    
    def get_health_color(self):
        """Get color based on current health"""
        index = min(self.health, len(self.health_colors) - 1)
        return self.health_colors[index]

class Enemy:
    def __init__(self, img_path, screen_width, screen_height, target_type="farmer"):
        try:
            self.original_img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            
            # If the image has no alpha channel, add one
            if self.original_img is None:
                # Create a fallback enemy
                self.original_img = np.zeros((80, 80, 4), dtype=np.uint8)
                cv2.circle(self.original_img, (40, 40), 30, (0, 0, 255, 255), -1)  # Red circle
                print(f"Created fallback enemy image as {img_path} was not found")
            elif self.original_img.shape[2] == 3:
                self.original_img = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2BGRA)
                
            # Resize the enemy image (random size between 80-120 pixels)
            size = random.randint(80, 120)
            self.img = cv2.resize(self.original_img, (size, size))
            
            self.width, self.height = self.img.shape[1], self.img.shape[0]
            self.screen_width, self.screen_height = screen_width, screen_height
            
            # Random starting position (from edges)
            side = random.choice(['left', 'right', 'top', 'bottom'])
            if side == 'left':
                self.x = -self.width
                self.y = random.randint(0, screen_height - self.height)
            elif side == 'right':
                self.x = screen_width
                self.y = random.randint(0, screen_height - self.height)
            elif side == 'top':
                self.x = random.randint(0, screen_width - self.width)
                self.y = -self.height
            else:  # bottom
                self.x = random.randint(0, screen_width - self.width)
                self.y = screen_height
            
            # Target type (farmer or crop)
            self.target_type = target_type
            self.target_crop = None  # Will be set if targeting a crop
            
            # Calculate direction vector towards center initially
            center_x, center_y = screen_width // 2, screen_height // 2
            dx, dy = center_x - self.x, center_y - self.y
            dist = max(1, np.sqrt(dx**2 + dy**2))  # Avoid division by zero
            
            self.speed_x = (dx / dist) * random.uniform(1, 3)
            self.speed_y = (dy / dist) * random.uniform(1, 3)
            
            # Add some randomness to movement
            self.speed_x += random.uniform(-0.5, 0.5)
            self.speed_y += random.uniform(-0.5, 0.5)
            
            # Add movement pattern (zigzag, spiral, etc.)
            self.movement_pattern = random.choice(['direct', 'zigzag', 'spiral'])
            self.pattern_timer = 0
            self.original_speed_x = self.speed_x
            self.original_speed_y = self.speed_y
            
            self.active = True
            
            # For hit animation
            self.is_being_hit = False
            self.hit_timer = 0
            self.hit_duration = 5  # frames
            
            # For death animation
            self.is_dying = False
            self.death_timer = 0
            self.death_duration = 10  # frames
            
            # For trail effect
            self.trail_positions = []
            self.max_trail_length = 5
            
            # The amount of time added when this enemy is destroyed
            self.time_reward = random.uniform(1.0, 2.0)
            
            # To prevent double scoring
            self.scored = False
            
        except Exception as e:
            print(f"Error creating enemy: {e}")
            traceback.print_exc()
            # Create a fallback enemy with default values
            self.img = np.zeros((80, 80, 4), dtype=np.uint8)
            cv2.circle(self.img, (40, 40), 30, (0, 0, 255, 255), -1)  # Red circle
            self.width, self.height = 80, 80
            self.screen_width, self.screen_height = screen_width, screen_height
            self.x, self.y = -80, screen_height // 2
            self.speed_x, self.speed_y = 2, 0
            self.target_type = target_type
            self.target_crop = None
            self.active = True
            self.is_being_hit = False
            self.hit_timer = 0
            self.hit_duration = 5
            self.is_dying = False
            self.death_timer = 0
            self.death_duration = 10
            self.movement_pattern = 'direct'
            self.trail_positions = []
            self.max_trail_length = 5
            self.time_reward = 1.5
            self.scored = False
    
    def set_target_crop(self, crop):
        """Set a specific crop as the target"""
        self.target_crop = crop
        self.target_type = "crop"
        if crop:
            crop.is_targeted = True
    
    def update_target_direction(self, farmer, crops):
        """Update direction to move toward the target (farmer or chosen crop)"""
        if self.is_dying:
            return
            
        target_x, target_y = None, None
            
        if self.target_type == "crop" and self.target_crop is not None:
            # Check if target crop is still valid (not destroyed)
            if self.target_crop.is_destroyed():
                # Find a new crop target
                valid_crops = [crop for crop in crops if not crop.is_destroyed()]
                if valid_crops:
                    self.target_crop.is_targeted = False  # Remove target from old crop
                    self.target_crop = random.choice(valid_crops)
                    self.target_crop.is_targeted = True
                else:
                    # No more crops, target the farmer
                    if self.target_crop:
                        self.target_crop.is_targeted = False
                    self.target_type = "farmer"
                    self.target_crop = None
                    
            # If we have a valid crop target, use it
            if self.target_crop and not self.target_crop.is_destroyed():
                target_x = self.target_crop.x + self.target_crop.width // 2
                target_y = self.target_crop.y + self.target_crop.height // 2
            else:
                # Target the farmer as fallback
                target_x = farmer.x + farmer.width // 2
                target_y = farmer.y + farmer.height // 2
                
        else:  # Target is farmer
            target_x = farmer.x + farmer.width // 2
            target_y = farmer.y + farmer.height // 2
        
        # Calculate new direction vector
        dx = target_x - (self.x + self.width // 2)
        dy = target_y - (self.y + self.height // 2)
        dist = max(1, np.sqrt(dx**2 + dy**2))  # Avoid division by zero
        
        # Update speed, but keep the same magnitude
        current_speed = np.sqrt(self.speed_x**2 + self.speed_y**2)
        self.original_speed_x = (dx / dist) * current_speed
        self.original_speed_y = (dy / dist) * current_speed
    
    def update(self, farmer=None, crops=None):
        # Store current position for trail
        self.trail_positions.append((int(self.x) + self.width//2, int(self.y) + self.height//2))
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)
        
        # Handle death animation
        if self.is_dying:
            self.death_timer += 1
            if self.death_timer >= self.death_duration:
                self.active = False
            return
        
        # Update target direction if targets are provided
        if farmer is not None and crops is not None:
            self.update_target_direction(farmer, crops)
        
        # Apply movement pattern
        if self.movement_pattern == 'zigzag':
            # Zigzag pattern
            self.pattern_timer += 1
            if self.pattern_timer % 30 == 0:  # Change direction every 30 frames
                self.speed_x = self.original_speed_x * random.uniform(0.8, 1.2)
                self.speed_y = self.original_speed_y * random.uniform(0.8, 1.2)
        
        elif self.movement_pattern == 'spiral':
            # Spiral-like movement
            self.pattern_timer += 1
            angle = self.pattern_timer * 0.1
            spiral_x = math.sin(angle) * 2
            spiral_y = math.cos(angle) * 2
            self.speed_x = self.original_speed_x + spiral_x
            self.speed_y = self.original_speed_y + spiral_y
        else:
            # Direct movement toward target
            self.speed_x = self.original_speed_x
            self.speed_y = self.original_speed_y
        
        # Move towards target
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Update hit animation
        if self.is_being_hit:
            self.hit_timer += 1
            if self.hit_timer >= self.hit_duration:
                self.is_being_hit = False
                self.hit_timer = 0
        
        # Check if enemy is out of bounds (far outside screen)
        if (self.x > self.screen_width + 100 or self.x < -self.width - 100 or 
            self.y > self.screen_height + 100 or self.y < -self.height - 100):
            self.active = False
            # If enemy had a crop target, untarget it
            if self.target_crop:
                self.target_crop.is_targeted = False
                self.target_crop = None
            
    def start_hit_animation(self):
        self.is_being_hit = True
        self.hit_timer = 0
    
    def start_death_animation(self):
        self.is_dying = True
        self.death_timer = 0
        self.speed_x = 0
        self.speed_y = 0
        # If enemy had a crop target, untarget it
        if self.target_crop:
            self.target_crop.is_targeted = False
            self.target_crop = None
            
    def is_hit(self, x, y, radius=50):  # Increased radius for easier hit detection
        # Don't register hits if already dying
        if self.is_dying:
            return False
            
        # Check if the point (x, y) is within the enemy's bounding box plus some radius
        enemy_center_x = self.x + self.width // 2
        enemy_center_y = self.y + self.height // 2
        distance = np.sqrt((x - enemy_center_x)**2 + (y - enemy_center_y)**2)
        
        # Debug info for collision detection
        if distance < 100:  # Only print for somewhat close shots to avoid console spam
            print(f"Shot distance to enemy: {distance}, Need: {radius}")
            
        return distance < radius  # Larger radius = easier to hit
    
    def is_colliding_with_crop(self, crop):
        """Check if enemy is colliding with a crop"""
        if self.is_dying or crop.is_destroyed():
            return False
            
        # Get center points
        enemy_center_x = self.x + self.width // 2
        enemy_center_y = self.y + self.height // 2
        crop_center_x = crop.x + crop.width // 2
        crop_center_y = crop.y + crop.height // 2
        
        # Calculate distance
        distance = np.sqrt((enemy_center_x - crop_center_x)**2 + (enemy_center_y - crop_center_y)**2)
        return distance < (self.width // 2 + crop.width // 2) * 0.6  # 60% of combined radii for more precise collision

class Farmer:
    def __init__(self, img_path, screen_width, screen_height):
        try:
            self.original_img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            
            # If the image has no alpha channel, add one
            if self.original_img is None:
                # Create a fallback farmer
                self.original_img = np.zeros((120, 120, 4), dtype=np.uint8)
                cv2.rectangle(self.original_img, (40, 40), (80, 90), (0, 0, 255, 255), -1)  # Body
                cv2.circle(self.original_img, (60, 30), 20, (0, 0, 255, 255), -1)  # Head
                print(f"Created fallback farmer image as {img_path} was not found")
                self.img = self.original_img
            elif self.original_img.shape[2] == 3:
                self.original_img = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2BGRA)
                # Resize to appropriate size
                self.img = cv2.resize(self.original_img, (120, 120))
            else:
                # Resize to appropriate size
                self.img = cv2.resize(self.original_img, (120, 120))
            
            self.width, self.height = self.img.shape[1], self.img.shape[0]
            self.screen_width, self.screen_height = screen_width, screen_height
            
            # Position in center
            self.x = screen_width // 2 - self.width // 2
            self.y = screen_height // 2 - self.height // 2
            
            # For animations
            self.is_moving = False
            self.move_timer = 0
            self.move_duration = 10  # frames
            self.move_direction = None
            self.original_x = self.x
            self.original_y = self.y
            
            # For attack animation
            self.is_attacking = False
            self.attack_timer = 0
            self.attack_duration = 5  # frames
            
            # For superpower mode
            self.has_superpower = False
            self.superpower_timer = 0
            self.superpower_duration = 300  # 10 seconds (at 30fps)
            self.superpower_multiplier = 3.0  # Damage multiplier during superpower
            
        except Exception as e:
            print(f"Error creating farmer: {e}")
            traceback.print_exc()
            # Create a fallback farmer
            self.img = np.zeros((100, 100, 4), dtype=np.uint8)
            cv2.circle(self.img, (50, 50), 40, (0, 0, 255, 255), -1)  # Red circle
            self.width, self.height = 100, 100
            self.screen_width, self.screen_height = screen_width, screen_height
            self.x = screen_width // 2 - self.width // 2
            self.y = screen_height // 2 - self.height // 2
            self.is_moving = False
            self.move_timer = 0
            self.move_duration = 10
            self.move_direction = None
            self.original_x = self.x
            self.original_y = self.y
            self.is_attacking = False
            self.attack_timer = 0
            self.attack_duration = 5
            self.has_superpower = False
            self.superpower_timer = 0
            self.superpower_duration = 300
            self.superpower_multiplier = 3.0
            
    def update(self):
        # Update movement animation
        if self.is_moving:
            self.move_timer += 1
            
            # During first half of animation, move in the direction
            if self.move_timer < self.move_duration / 2:
                if self.move_direction == 'left':
                    self.x -= 3
                elif self.move_direction == 'right':
                    self.x += 3
                elif self.move_direction == 'up':
                    self.y -= 3
                elif self.move_direction == 'down':
                    self.y += 3
            # During second half, return to original position
            elif self.move_timer < self.move_duration:
                self.x = self.original_x + (self.x - self.original_x) * (1 - (self.move_timer - self.move_duration/2) / (self.move_duration/2))
                self.y = self.original_y + (self.y - self.original_y) * (1 - (self.move_timer - self.move_duration/2) / (self.move_duration/2))
            else:
                self.is_moving = False
                self.move_timer = 0
                self.x = self.original_x
                self.y = self.original_y
        
        # Update attack animation
        if self.is_attacking:
            self.attack_timer += 1
            if self.attack_timer >= self.attack_duration:
                self.is_attacking = False
                self.attack_timer = 0
        
        # Update superpower timer
        if self.has_superpower:
            self.superpower_timer += 1
            if self.superpower_timer >= self.superpower_duration:
                self.has_superpower = False
                self.superpower_timer = 0
    
    def move_by_direction(self, direction, amount=10):
        """Move farmer in a specified direction"""
        # Save original position for animation return
        self.original_x = self.x
        self.original_y = self.y
        
        # Move farmer based on direction
        if direction == 'left':
            self.x = max(0, self.x - amount)
        elif direction == 'right':
            self.x = min(self.screen_width - self.width, self.x + amount)
        elif direction == 'up':
            self.y = max(0, self.y - amount)
        elif direction == 'down':
            self.y = min(self.screen_height - self.height, self.y + amount)
    
    def set_position(self, x, y):
        """Set the farmer's position directly"""
        self.x = max(0, min(x, self.screen_width - self.width))
        self.y = max(0, min(y, self.screen_height - self.height))
        self.original_x = self.x
        self.original_y = self.y
    
    def start_move_animation(self, direction):
        if not self.is_moving:
            self.is_moving = True
            self.move_timer = 0
            self.move_direction = direction
    
    def start_attack_animation(self):
        self.is_attacking = True
        self.attack_timer = 0
    
    def activate_superpower(self):
        """Activate superpower mode for the farmer"""
        self.has_superpower = True
        self.superpower_timer = 0
        return True

class GameEngine:
    def __init__(self, assets_path='assets', game_duration=90):
        try:
            # Ensure assets directory exists
            if not os.path.exists(assets_path):
                os.makedirs(assets_path, exist_ok=True)
                print(f"Created assets directory: {assets_path}")
                
            # Define paths
            self.assets_path = assets_path
            bg_path = os.path.join(assets_path, 'background.png')
            farmer_path = os.path.join(assets_path, 'farmer.png')
            
            # Find enemy images
            self.enemy_img_paths = []
            
            # Try to find default enemy.png
            default_enemy_path = os.path.join(assets_path, 'enemy.png')
            if os.path.exists(default_enemy_path):
                self.enemy_img_paths.append(default_enemy_path)
                print(f"Found enemy image: {default_enemy_path}")
            
            # Try to find enemy1.png
            enemy1_path = os.path.join(assets_path, 'enemy1.png')
            if os.path.exists(enemy1_path):
                self.enemy_img_paths.append(enemy1_path)
                print(f"Found enemy1 image: {enemy1_path}")
            
            # If no enemy images found, use default path (it will create placeholders)
            if not self.enemy_img_paths:
                print("No enemy images found, will create enemies dynamically")
                self.enemy_img_paths = [default_enemy_path]
                
            # Find crop image
            self.crop_img_path = os.path.join(assets_path, 'crop.png')
            if not os.path.exists(self.crop_img_path):
                print(f"Crop image not found at: {self.crop_img_path}")
                print("Will create placeholder crop graphics")
                # Placeholder path will lead to creating default graphics in the CropPlot class
            else:
                print(f"Found crop image at: {self.crop_img_path}")
            
            # Load or create background
            if os.path.exists(bg_path):
                print(f"Loading background from: {bg_path}")
                self.background = cv2.imread(bg_path)
                # Make sure background has correct dimensions
                if self.background is not None:
                    self.background = cv2.resize(self.background, (1280, 720))
            else:
                print(f"Background image not found at: {bg_path}")
                print("Creating placeholder background...")
                self.background = np.zeros((720, 1280, 3), dtype=np.uint8)
                
                # Create a nice farm background with sky and field
                # Sky (top 2/3)
                self.background[:480, :] = (230, 180, 100)  # Light blue sky
                
                # Field (bottom 1/3)
                self.background[480:, :] = (100, 190, 50)  # Green field
                
                # Draw sun
                cv2.circle(self.background, (100, 100), 60, (80, 200, 255), -1)
                
                # Draw some clouds
                cv2.ellipse(self.background, (300, 150), (100, 40), 0, 0, 360, (240, 240, 240), -1)
                cv2.ellipse(self.background, (500, 100), (120, 50), 0, 0, 360, (240, 240, 240), -1)
                cv2.ellipse(self.background, (800, 180), (150, 60), 0, 0, 360, (240, 240, 240), -1)
                
                # Save the generated background
                cv2.imwrite(bg_path, self.background)
                print(f"Saved placeholder background to: {bg_path}")
            
            # Game dimensions
            self.width = self.background.shape[1]
            self.height = self.background.shape[0]
            
            # Initialize farmer
            self.farmer = Farmer(farmer_path, self.width, self.height)
            
            # Initialize crops (typically 4 crops placed in a semi-circle pattern around the center)
            self.crops = []
            self.create_crops()
            
            # Time-based challenge - game duration in seconds
            self.game_duration = game_duration
            self.remaining_time = game_duration
            self.last_time_update = time.time()
            self.frame_count = 0  # Used to calculate time passing
            self.fps_estimate = 30  # Default estimate, will be adjusted
            
            # Game state
            self.score = 0
            self.game_over = False
            self.game_won = False
            self.enemies = []
            self.bullets = []
            self.last_enemy_spawn = time.time()
            self.last_superpower_time = time.time() - 30  # Initialize with cooldown already over
            self.superpower_cooldown = 30  # 30 seconds cooldown
            
            # Superpower effect
            self.superpower_active = False
            self.superpower_effect_timer = 0
            self.superpower_effect_duration = 20  # frames
            
            # Notification system
            self.notifications = []  # List of {text, color, timer, duration}
            
            # Smoke particles for enemy death
            self.smoke_particles = []  # List of {x, y, size, life, color}
            
            # For smooth farmer movement
            self.last_farmer_pos = None
            
            # Enemy spawn settings for dynamic difficulty
            self.min_enemy_spawn_interval = 2.0  # Minimum seconds between enemy spawns
            self.max_enemy_spawn_interval = 4.0  # Maximum seconds between enemy spawns
            # Maximum number of enemies active at once
            self.max_enemies = 8
            
            # Percentage chance that an enemy will target crops instead of the farmer
            self.crop_targeting_chance = 0.8  # 80% chance to target crops
            
        except Exception as e:
            print(f"Error initializing GameEngine: {e}")
            traceback.print_exc()
            # Create a basic fallback game environment
            self.background = np.zeros((720, 1280, 3), dtype=np.uint8)
            self.background[:] = (100, 180, 100)  # Green background
            
            self.width, self.height = 1280, 720
            
            # Create a default farmer
            self.farmer = Farmer("", self.width, self.height)
            
            # Initialize other game elements
            self.enemy_img_paths = []
            self.crops = []
            self.create_crops()  # Create crops in fallback mode
            self.score = 0
            self.game_over = False
            self.game_won = False
            self.enemies = []
            self.bullets = []
            self.smoke_particles = []
            self.last_enemy_spawn = time.time()
            self.last_superpower_time = time.time() - 30
            self.superpower_cooldown = 30
            self.superpower_active = False
            self.superpower_effect_timer = 0
            self.superpower_effect_duration = 20
            self.notifications = []
            self.last_farmer_pos = None
            self.remaining_time = game_duration
            self.last_time_update = time.time()
            self.frame_count = 0
            self.fps_estimate = 30
            self.min_enemy_spawn_interval = 2.0
            self.max_enemy_spawn_interval = 4.0
            self.max_enemies = 8
            self.crop_targeting_chance = 0.8
    
    def create_crops(self):
        """Create crop plots around the field"""
        # Clear existing crops
        for crop in self.crops:
            if hasattr(crop, 'is_targeted') and crop.is_targeted:
                # Make sure enemies targeting this crop no longer do
                for enemy in self.enemies:
                    if enemy.target_crop == crop:
                        enemy.target_crop = None
                        enemy.target_type = "farmer"
        
        self.crops = []
        
        # Create 4 crops arranged in a semi-circle pattern
        center_x = self.width // 2
        center_y = self.height // 2
        radius = 250  # Distance from center
        
        # Create crops in a semi-circle facing the bottom of the screen
        for i in range(4):
            angle = (i / 3) * math.pi + math.pi/6  # 210 degrees spread starting at 30 degrees
            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))
            
            # Adjust for crop size
            crop_size = 80
            x -= crop_size // 2
            y -= crop_size // 2
            
            # Create the crop
            crop = CropPlot(self.crop_img_path, x, y, self.width, self.height)
            self.crops.append(crop)
    
    def update_time_remaining(self):
        """Update the time remaining in the game"""
        # Update frame count for FPS calculation
        self.frame_count += 1
        
        current_time = time.time()
        time_elapsed = current_time - self.last_time_update
        
        # Only update every 0.25 seconds to smooth out the timer
        if time_elapsed >= 0.25:
            # Update FPS estimate for more accurate timing
            self.fps_estimate = self.frame_count / time_elapsed
            
            # Decrease time based on real elapsed time
            self.remaining_time -= time_elapsed
            
            # Reset for next update
            self.last_time_update = current_time
            self.frame_count = 0
            
            # Check if time has run out
            if self.remaining_time <= 0:
                self.remaining_time = 0
                self.handle_game_end(True)  # Win if time runs out (survived until the end)
    
    def add_time(self, seconds):
        """Add time to the clock (when destroying enemies)"""
        self.remaining_time += seconds
        # Add notification about time bonus
        self.add_notification(f"+{seconds:.1f}s", (0, 255, 255))
    
    def handle_game_end(self, time_expired):
        """Handle game ending conditions"""
        if time_expired and self.are_any_crops_alive():
            # Player survived until time ran out with at least one crop alive - victory!
            self.game_won = True
            self.game_over = True
            
            # Calculate bonus points based on number of crops surviving
            surviving_crops = sum(1 for crop in self.crops if not crop.is_destroyed())
            bonus_points = surviving_crops * 50
            
            # Add bonus points for winning
            self.score += bonus_points
            
            # Add victory notification
            self.add_notification(f"VICTORY! +{bonus_points} BONUS POINTS!", (0, 255, 0), 300)
        else:
            # Game over - either time ran out with no crops or all crops were destroyed
            self.game_over = True
            
            # Add game over notification
            reason = "Time's up!" if time_expired else "All crops destroyed!"
            self.add_notification(f"GAME OVER! {reason}", (255, 0, 0), 300)
    
    def are_any_crops_alive(self):
        """Check if any crops are still alive"""
        return any(not crop.is_destroyed() for crop in self.crops)
    
    def are_all_crops_destroyed(self):
        """Check if all crops are destroyed"""
        return all(crop.is_destroyed() for crop in self.crops)
    
    def create_smoke_particles(self, x, y, count=10):
        """Create smoke particles for death animation"""
        for _ in range(count):
            # Randomize particle properties
            size = random.randint(5, 15)
            life = random.randint(20, 40)
            # Gray smoke with some transparency
            color = (random.randint(150, 200), random.randint(150, 200), random.randint(150, 200))
            # Random velocity
            vel_x = random.uniform(-2, 2)
            vel_y = random.uniform(-2, 2)
            
            self.smoke_particles.append({
                'x': x,
                'y': y,
                'size': size,
                'life': life,
                'max_life': life,
                'color': color,
                'vel_x': vel_x,
                'vel_y': vel_y
            })
    def update_smoke_particles(self):
        """Update all smoke particles"""
        for particle in self.smoke_particles[:]:
            # Decrease life
            particle['life'] -= 1
            
            # Remove dead particles
            if particle['life'] <= 0:
                self.smoke_particles.remove(particle)
                continue
                
            # Move particle
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            
            # Slow down over time
            particle['vel_x'] *= 0.95
            particle['vel_y'] *= 0.95
    
    def spawn_enemy(self, force=False):
        # Spawn a new enemy periodically or when forced
        current_time = time.time()
        
        # Dynamic spawn interval based on remaining time (gets more intense as time goes on)
        spawn_interval = max(
            self.min_enemy_spawn_interval,
            self.max_enemy_spawn_interval * (self.remaining_time / self.game_duration)
        )
        
        # Spawn an enemy with dynamic interval, with max enemies limit
        if force or (current_time - self.last_enemy_spawn > random.uniform(spawn_interval * 0.8, spawn_interval * 1.2) 
                     and len(self.enemies) < self.max_enemies):
            try:
                # Choose a random enemy image path
                enemy_img_path = random.choice(self.enemy_img_paths)
                
                # Choose target type - farmer or crop
                target_type = "crop" if random.random() < self.crop_targeting_chance and self.are_any_crops_alive() else "farmer"
                
                # Create enemy
                enemy = Enemy(enemy_img_path, self.width, self.height, target_type)
                
                # If targeting crop, assign a specific crop
                if target_type == "crop" and self.are_any_crops_alive():
                    # Filter for non-destroyed crops
                    valid_crops = [crop for crop in self.crops if not crop.is_destroyed()]
                    if valid_crops:
                        target_crop = random.choice(valid_crops)
                        enemy.set_target_crop(target_crop)
                
                self.enemies.append(enemy)
                self.last_enemy_spawn = current_time
            except Exception as e:
                print(f"Error spawning enemy: {e}")
                traceback.print_exc()
    
    def shoot(self, x, y):
        # Create a new bullet at the given position
        try:
            # Print debug info about shooting coordinates
            print(f"Shooting at camera coordinates: ({x}, {y})")
            
            # Scale the coordinates from camera resolution to game resolution
            scaled_x = int(x * (self.width / 640))
            scaled_y = int(y * (self.height / 480))
            
            print(f"Scaled shooting coordinates: ({scaled_x}, {scaled_y})")
            
            # Set bullet direction based on position relative to farmer
            farmer_center_x = self.farmer.x + self.farmer.width // 2
            farmer_center_y = self.farmer.y + self.farmer.height // 2
            
            # Determine direction for farmer animation
            dx = scaled_x - farmer_center_x
            dy = scaled_y - farmer_center_y
            
            # Determine which direction has the larger component
            if abs(dx) > abs(dy):
                direction = 'right' if dx > 0 else 'left'
            else:
                direction = 'down' if dy > 0 else 'up'
            
            # Start farmer attack animation in that direction
            self.farmer.start_move_animation(direction)
            self.farmer.start_attack_animation()
            
            # Create bullet
            bullet_color = (0, 255, 255)  # Default cyan
            if self.farmer.has_superpower:
                bullet_color = (0, 0, 255)  # Red for superpower
                
            self.bullets.append({
                'x': scaled_x, 
                'y': scaled_y, 
                'radius': 50,  # Increased radius for easier hits
                'life': 10,  # Bullet lasts for 10 frames
                'color': bullet_color,
                'is_superpower': self.farmer.has_superpower
            })
            
            # Add a notification to show shooting is working
            self.add_notification(f"Shoot!", bullet_color, 30)
            
        except Exception as e:
            print(f"Error creating bullet: {e}")
            traceback.print_exc()
    
    def use_superpower(self):
        # Check if superpower is available
        try:
            current_time = time.time()
            if current_time - self.last_superpower_time > self.superpower_cooldown:
                # Activate superpower mode for the farmer
                self.farmer.activate_superpower()
                
                # Add notification
                self.add_notification("SUPERPOWER ACTIVATED!", (0, 255, 255))
                
                # Start superpower effect
                self.superpower_active = True
                self.superpower_effect_timer = 0
                
                # Reset cooldown
                self.last_superpower_time = current_time
                
                return True
            return False
        except Exception as e:
            print(f"Error using superpower: {e}")
            traceback.print_exc()
            return False
    
    def add_notification(self, text, color, duration=90):
        """Add a notification to be displayed on screen"""
        self.notifications.append({
            'text': text,
            'color': color,
            'timer': 0,
            'duration': duration  # frames
        })
    
    def update_notifications(self):
        """Update all active notifications"""
        for notification in self.notifications[:]:
            notification['timer'] += 1
            if notification['timer'] >= notification['duration']:
                self.notifications.remove(notification)
                
    def check_farmer_enemy_collisions(self):
        """Check for collisions between the farmer and enemies"""
        farmer_center_x = self.farmer.x + self.farmer.width // 2
        farmer_center_y = self.farmer.y + self.farmer.height // 2
        
        for enemy in self.enemies[:]:
            if enemy.is_dying:
                continue
                
            # Calculate distance between farmer and enemy
            enemy_center_x = enemy.x + enemy.width // 2
            enemy_center_y = enemy.y + enemy.height // 2
            
            distance = np.sqrt((farmer_center_x - enemy_center_x)**2 + 
                              (farmer_center_y - enemy_center_y)**2)
            
            # If farmer and enemy are close enough, destroy the enemy
            if distance < 70:  # Adjust collision radius as needed
                print(f"Farmer collided with enemy! Distance: {distance}")
                
                # Start enemy death animation
                enemy.start_death_animation()
                
                # Create smoke effect
                self.create_smoke_particles(enemy_center_x, enemy_center_y, 15)
                
                # Add to score
                self.score += 1
                
                # Add notification
                self.add_notification("Enemy defeated!", (0, 255, 0), 60)
                
                # Make farmer react
                self.farmer.start_attack_animation()
    
    def update(self):
        try:
            if self.game_over:
                return
                
            # Update time remaining
            self.update_time_remaining()
            
            # Check if game is over due to all crops being destroyed
            if not self.are_any_crops_alive():
                self.handle_game_end(False)  # Game over due to crop destruction
                return
            
            # Update farmer animations
            self.farmer.update()
            
            # Update crop animations and states
            for crop in self.crops:
                crop.update()
            
            # Update superpower effect
            if self.superpower_active:
                self.superpower_effect_timer += 1
                if self.superpower_effect_timer >= self.superpower_effect_duration:
                    self.superpower_active = False
            
            # Update notifications
            self.update_notifications()
            
            # Update smoke particles
            self.update_smoke_particles()
            
            # Spawn new enemies
            self.spawn_enemy()
            
            # Update enemies
            for enemy in self.enemies[:]:
                # Pass the farmer and crops for targeting
                enemy.update(self.farmer, self.crops)
                
                # Remove dead enemies and add score
                if not enemy.active:
                    # Add score when enemy disappears
                    if not hasattr(enemy, 'scored') or not enemy.scored:
                        self.score += 1
                        enemy.scored = True  # Mark as scored to avoid double counting
                        print(f"Enemy removed, score increased to {self.score}")
                        
                    # Remove the enemy from the list
                    self.enemies.remove(enemy)
                    continue
            # Check if enemy reached a crop
                for crop in self.crops:
                    if not crop.is_destroyed() and enemy.is_colliding_with_crop(crop):
                        # Damage the crop
                        is_destroyed = crop.take_damage()
                        
                        # Create smoke effect
                        crop_center_x = crop.x + crop.width // 2
                        crop_center_y = crop.y + crop.height // 2
                        self.create_smoke_particles(crop_center_x, crop_center_y, 10)
                        
                        # Start enemy death animation
                        enemy.start_death_animation()
                        
                        # Add notification
                        if is_destroyed:
                            self.add_notification("Crop destroyed!", (255, 0, 0))
                        else:
                            self.add_notification(f"Crop damaged! Health: {crop.health}/{crop.max_health}", (255, 165, 0))
                        
                        # Check if game over (all crops destroyed)
                        if self.are_all_crops_destroyed():
                            self.handle_game_end(False)  # Game over due to crop destruction
                        
                        break
            
            # Check for collisions between farmer and enemies
            self.check_farmer_enemy_collisions()
            
            # Check collisions with bullets
            for bullet in self.bullets[:]:
                hit = False
                for enemy in self.enemies[:]:
                    if enemy.is_hit(bullet['x'], bullet['y'], bullet['radius']):
                        if enemy in self.enemies:  # Make sure enemy is still in the list
                            # Start hit animation
                            enemy.start_hit_animation()
                            
                            # Start death animation
                            enemy.start_death_animation()
                            
                            # Create smoke effect at bullet impact point
                            self.create_smoke_particles(bullet['x'], bullet['y'], 10)
                            
                            # Add time to the clock
                            self.add_time(enemy.time_reward)
                            
                            # Increment score (double points during superpower)
                            points = 2 if bullet.get('is_superpower', False) else 1
                            self.score += points
                            
                            # Notification for score (only if significant)
                            if points > 1:
                                self.add_notification(f"+{points} points!", (0, 255, 0), 60)
                            else:
                                self.add_notification(f"Enemy hit!", (0, 255, 255), 30)
                            
                            # Make farmer react
                            self.farmer.start_attack_animation()
                            
                            hit = True
                            break  # Only hit one enemy per bullet
                
                if hit and bullet in self.bullets:
                    self.bullets.remove(bullet)
                elif bullet['life'] <= 0:  # Remove bullets that have expired
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                else:
                    bullet['life'] -= 1  # Decrease bullet life
                
        except Exception as e:
            print(f"Error in update: {e}")
            traceback.print_exc()
    
    def draw_farmer(self, game_frame):
        """Helper method to draw the farmer with proper alpha blending"""
        try:
            y1, y2 = int(self.farmer.y), int(self.farmer.y + self.farmer.height)
            x1, x2 = int(self.farmer.x), int(self.farmer.x + self.farmer.width)
            
            # Make sure coordinates are within frame bounds
            if x1 >= 0 and y1 >= 0 and x2 <= game_frame.shape[1] and y2 <= game_frame.shape[0]:
                if self.farmer.img.shape[2] == 4:  # With alpha channel
                    alpha_farmer = self.farmer.img[:, :, 3] / 255.0
                    for c in range(0, 3):
                        game_frame[y1:y2, x1:x2, c] = (
                            (1 - alpha_farmer) * game_frame[y1:y2, x1:x2, c] + 
                            alpha_farmer * self.farmer.img[:, :, c]
                        )
                else:  # Without alpha channel
                    game_frame[y1:y2, x1:x2] = self.farmer.img
        except Exception as e:
            print(f"Error drawing farmer: {e}")
            traceback.print_exc()
    
    def render_game_only(self):
        """Render the game without overlaying on camera feed"""
        try:
            # Create a copy of the background to avoid modifying original
            game_frame = self.background.copy() if self.background is not None else np.zeros((720, 1280, 3), dtype=np.uint8)
            
            # Draw farm field (bottom area)
            cv2.rectangle(game_frame, (0, self.height - 50), (self.width, self.height), (30, 120, 30), -1)
            
            # Draw superpower effect if active
            if self.superpower_active:
                # Add text notification only
                cv2.putText(game_frame, "SUPERPOWER ACTIVATED!", (self.width // 2 - 250, 100), 
                          cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            
            # Draw bullets
            for bullet in self.bullets:
                # Draw actual bullet
                cv2.circle(game_frame, (int(bullet['x']), int(bullet['y'])), 
                          bullet['radius'], bullet.get('color', (0, 255, 255)), -1)
            
            # Draw smoke particles
            for particle in self.smoke_particles:
                # Calculate opacity based on remaining life
                alpha = particle['life'] / particle['max_life']
                size = int(particle['size'] * alpha)  # Particles
                # Calculate opacity based on remaining life
                alpha = particle['life'] / particle['max_life']
                size = int(particle['size'] * alpha)  # Particles shrink as they die
                
                # Draw the particle
                cv2.circle(game_frame, 
                          (int(particle['x']), int(particle['y'])), 
                          size, 
                          particle['color'], 
                          -1)
            
            # Draw crops
            for crop in self.crops:
                # Skip if destroyed
                if crop.is_destroyed():
                    continue
                    
                # Get crop position
                y1, y2 = int(crop.y), int(crop.y + crop.height)
                x1, x2 = int(crop.x), int(crop.x + crop.width)
                
                # Draw targeting highlight if targeted
                if crop.is_targeted:
                    # Pulsing circle for target indicator
                    pulse_size = 5 + int(3 * math.sin(crop.target_pulse * 0.2))
                    cv2.circle(game_frame,
                              (x1 + crop.width // 2, y1 + crop.height // 2),
                              crop.width // 2 + pulse_size,
                              (0, 0, 255),
                              2)
                
                # Handle crop image with alpha channel
                if crop.img.shape[2] == 4:  # With alpha channel
                    alpha_crop = crop.img[:, :, 3] / 255.0
                    for c in range(0, 3):
                        game_frame[y1:y2, x1:x2, c] = (
                            (1 - alpha_crop) * game_frame[y1:y2, x1:x2, c] + 
                            alpha_crop * crop.img[:, :, c]
                        )
                else:  # Without alpha channel
                    game_frame[y1:y2, x1:x2] = crop.img
                    # Draw health bar above crop
                health_width = 60
                health_height = 8
                health_x = x1 + (crop.width - health_width) // 2
                health_y = y1 - 15
                
                # Draw health background
                cv2.rectangle(game_frame,
                             (health_x, health_y),
                             (health_x + health_width, health_y + health_height),
                             (50, 50, 50),
                             -1)
                             
                # Draw current health
                current_health_width = int((crop.health / crop.max_health) * health_width)
                health_color = crop.get_health_color()
                cv2.rectangle(game_frame,
                             (health_x, health_y),
                             (health_x + current_health_width, health_y + health_height),
                             health_color,
                             -1)
                             
                # Visual effect for hit
                if crop.is_being_hit:
                    # Flash crop during hit animation
                    if crop.hit_timer % 3 < 2:  # Flash every 3 frames
                        cv2.rectangle(game_frame,
                                    (x1, y1),
                                    (x2, y2),
                                    (0, 0, 255),
                                    2)
            
            # Draw enemies with their trails
            for enemy in self.enemies:
                # Skip if enemy is not active
                if not enemy.active:
                    continue
                
                # Draw trail
                if len(enemy.trail_positions) >= 2:
                    # Simple gradient trail (fades out)
                    for i in range(len(enemy.trail_positions) - 1):
                        p1 = enemy.trail_positions[i]
                        p2 = enemy.trail_positions[i + 1]
                        
                        # Calculate opacity based on position in trail
                        alpha = 0.7 * (i / len(enemy.trail_positions))
                        thickness = max(1, int((i + 1) * 3 / len(enemy.trail_positions)))
                        
                        cv2.line(game_frame, p1, p2, (50, 100, 255), thickness)
                
                # Apply hit effect if being hit
                if enemy.is_being_hit:
                    # Flash color between normal and white
                    if enemy.hit_timer % 2 == 0:
                        # Create a white version of the enemy image
                        hit_img = enemy.img.copy()
                        hit_img[:, :, 0:3] = 255  # Set all color channels to white
                        img_to_draw = hit_img
                    else:
                        img_to_draw = enemy.img
                elif enemy.is_dying:
                    # During death animation, make enemy fade out
                    img_to_draw = enemy.img.copy()
                    # Calculate fade based on death animation progress
                    alpha_mult = 1.0 - (enemy.death_timer / enemy.death_duration)
                    # Apply alpha multiplier to make it fade out
                    img_to_draw[:, :, 3] = (img_to_draw[:, :, 3] * alpha_mult).astype(np.uint8)
                else:
                    img_to_draw = enemy.img
                
                # Handle enemy image with alpha channel
                y1, y2 = int(enemy.y), int(enemy.y + enemy.height)
                x1, x2 = int(enemy.x), int(enemy.x + enemy.width)
                
                # Make sure coordinates are within frame bounds
                if x1 < 0: x1 = 0
                if y1 < 0: y1 = 0
                if x2 > game_frame.shape[1]: x2 = game_frame.shape[1]
                if y2 > game_frame.shape[0]: y2 = game_frame.shape[0]
                
                # Skip if out of bounds
                if x1 >= x2 or y1 >= y2:
                    continue
                    
                # Calculate crop dimensions for the enemy image
                crop_width = x2 - x1
                crop_height = y2 - y1
                
                # Crop enemy image if needed
                crop_x1 = 0 if x1 >= 0 else -x1
                crop_y1 = 0 if y1 >= 0 else -y1
                crop_x2 = img_to_draw.shape[1] if x2 <= game_frame.shape[1] else img_to_draw.shape[1] - (x2 - game_frame.shape[1])
                crop_y2 = img_to_draw.shape[0] if y2 <= game_frame.shape[0] else img_to_draw.shape[0] - (y2 - game_frame.shape[0])
                
                # Skip if crop dimensions are invalid
                if crop_x1 >= crop_x2 or crop_y1 >= crop_y2:
                    continue
                
                # Ensure cropped dimensions match the target region
                target_height = y2 - y1
                target_width = x2 - x1
                crop_height = crop_y2 - crop_y1
                crop_width = crop_x2 - crop_x1
                
                # Ensure dimensions match
                if crop_height != target_height or crop_width != target_width:
                    # Adjust crop dimensions or target region
                    crop_y2 = min(crop_y2, crop_y1 + target_height)
                    crop_x2 = min(crop_x2, crop_x1 + target_width)
                    y2 = min(y2, y1 + (crop_y2 - crop_y1))
                    x2 = min(x2, x1 + (crop_x2 - crop_x1))
                
                # Skip if dimensions are still invalid
                if crop_y2 <= crop_y1 or crop_x2 <= crop_x1 or y2 <= y1 or x2 <= x1:
                    continue
                
                try:
                    cropped_enemy = img_to_draw[crop_y1:crop_y2, crop_x1:crop_x2]
                    
                    # Verify shape
                    if cropped_enemy.shape[0] == 0 or cropped_enemy.shape[1] == 0:
                        continue
                    
                    if cropped_enemy.shape[2] == 4:  # With alpha channel
                        alpha = cropped_enemy[:, :, 3] / 255.0
                        for c in range(0, 3):
                            game_frame[y1:y2, x1:x2, c] = (
                                (1 - alpha) * game_frame[y1:y2, x1:x2, c] + 
                                alpha * cropped_enemy[:, :, c]
                            )
                    else:  # Without alpha channel
                        game_frame[y1:y2, x1:x2] = cropped_enemy[:, :, :3]
                except Exception as e:
                    print(f"Error rendering enemy: {e}")
                    # Just skip this enemy
                    continue
            
            # Draw farmer with subtle attack animation
            if self.farmer.is_attacking:
                # Small visual indicator for attack
                cv2.circle(game_frame, 
                          (int(self.farmer.x + self.farmer.width//2), 
                           int(self.farmer.y + self.farmer.height//2)), 
                          60, (0, 255, 255), 2)
            
            # Draw the farmer
            self.draw_farmer(game_frame)
            
            # Draw UI elements in a box at the top
            ui_box_height = 50
            
            # Draw background box for top UI
            cv2.rectangle(game_frame, 
                         (0, 0), 
                         (self.width, ui_box_height), 
                         (0, 0, 0, 128), -1)
            
            # Score 
            score_text = f"Score: {self.score}"
            cv2.putText(game_frame, score_text, (20, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
                       
            # Time remaining
            minutes = int(self.remaining_time) // 60
            seconds = int(self.remaining_time) % 60
            time_color = (255, 255, 255)  # Default white
            if self.remaining_time < 10:  # Red when low on time
                time_color = (0, 0, 255)
            elif self.remaining_time < 30:  # Yellow when time is getting low
                time_color = (0, 200, 255)
            time_text = f"Time: {minutes:02}:{seconds:02}"
            cv2.putText(game_frame, time_text, (250, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, time_color, 2)
            
            # Crop status
            alive_crops = sum(1 for crop in self.crops if not crop.is_destroyed())
            crop_text = f"Crops: {alive_crops}/{len(self.crops)}"
            cv2.putText(game_frame, crop_text, (450, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            
            # Superpower status
            cooldown_remaining = max(0, self.superpower_cooldown - (time.time() - self.last_superpower_time))
            
            if self.farmer.has_superpower:
                # Show superpower active time remaining
                time_left = int((self.farmer.superpower_duration - self.farmer.superpower_timer) / 30)  # Convert to seconds
                superpower_text = f"SUPERPOWER: {time_left}s"
                color = (0, 0, 255)  # Red
            elif cooldown_remaining == 0:
                superpower_text = "SUPERPOWER: READY!"
                color = (0, 255, 0)  # Green
            else:
                superpower_text = f"SUPERPOWER: {int(cooldown_remaining)}s"
                color = (0, 0, 255)  # Red
                
            cv2.putText(game_frame, superpower_text, (self.width - 350, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            # Game over screen
            if self.game_over:
                # Add semi-transparent overlay
                overlay = game_frame.copy()
                cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.7, game_frame, 0.3, 0, game_frame)
                
                # Game over message - different for win vs loss
                if self.game_won:
                    # Victory screen
                    cv2.putText(game_frame, "VICTORY!", (self.width // 2 - 150, self.height // 2 - 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)
                    cv2.putText(game_frame, f"Final Score: {self.score}", (self.width // 2 - 130, self.height // 2 + 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
                    # Show surviving crops count
                    surviving_crops = sum(1 for crop in self.crops if not crop.is_destroyed())
                    cv2.putText(game_frame, f"Crops Saved: {surviving_crops}/{len(self.crops)}", 
                               (self.width // 2 - 150, self.height // 2 + 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                else:
                    # Defeat screen
                    cv2.putText(game_frame, "GAME OVER", (self.width // 2 - 150, self.height // 2 - 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)
                    cv2.putText(game_frame, f"Final Score: {self.score}", (self.width // 2 - 130, self.height // 2 + 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Restart instructions
                cv2.putText(game_frame, "Press 'r' to Restart or 'q' to Quit", 
                           (self.width // 2 - 250, self.height // 2 + 80), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Draw notifications (centered on screen)
            notification_y = 200
            for notification in self.notifications:
                # Calculate fade based on notification lifetime
                fade = 1.0
                if notification['timer'] > notification['duration'] * 0.7:
                    # Start fading out in the last 30% of duration
                    fade = 1.0 - ((notification['timer'] - notification['duration'] * 0.7) / (notification['duration'] * 0.3))
                
                # Get adjusted color with fade
                color = notification['color']
                
                # Calculate text position (centered)
                text_size = cv2.getTextSize(notification['text'], cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                text_x = (self.width - text_size[0]) // 2
                
                # Draw text with drop shadow
                cv2.putText(game_frame, notification['text'], (text_x+2, notification_y+2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                cv2.putText(game_frame, notification['text'], (text_x, notification_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                
                notification_y += 40
            
            return game_frame
            
        except Exception as e:
            print(f"Error in render_game_only: {e}")
            traceback.print_exc()
            # Return a blank frame with error message
            error_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            cv2.putText(error_frame, "Rendering Error", (self.width // 2 - 100, self.height // 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return error_frame
    
    def render(self, frame):
        """Legacy render method that blends with camera feed - kept for backward compatibility"""
        try:
            # Create the game frame
            game_frame = self.render_game_only()
            
            # Resize game_frame to match the camera frame dimensions
            game_frame_resized = cv2.resize(game_frame, (frame.shape[1], frame.shape[0]))
            
            # Blend the frames (0.7 weight for game, 0.3 for camera)
            result = cv2.addWeighted(game_frame_resized, 0.7, frame, 0.3, 0)
            
            return result
        except Exception as e:
            print(f"Error in render: {e}")
            traceback.print_exc()
            return frame  # Return original frame on error