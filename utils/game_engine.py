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
            
            if self.original_img is None:
                self.img = np.zeros((80, 80, 4), dtype=np.uint8)
                self.img[:, :, 0] = 50
                self.img[:, :, 1] = 170
                self.img[:, :, 2] = 100
                self.img[:, :, 3] = 255
                
                cv2.rectangle(self.img, (20, 40), (60, 70), (20, 120, 30), -1)
                cv2.rectangle(self.img, (30, 20), (50, 40), (20, 200, 50), -1)
            elif self.original_img.shape[2] == 3:
                self.original_img = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2BGRA)
                self.img = cv2.resize(self.original_img, (80, 80))
            else:
                self.img = cv2.resize(self.original_img, (80, 80))
                
            self.width, self.height = self.img.shape[1], self.img.shape[0]
            self.screen_width, self.screen_height = screen_width, screen_height
            
            self.x = x
            self.y = y
            
            self.max_health = 3
            self.health = self.max_health
            
            self.is_being_hit = False
            self.hit_timer = 0
            self.hit_duration = 8
            
            self.health_colors = [
                (0, 0, 255),
                (0, 165, 255),
                (0, 255, 0)
            ]
            
            self.is_targeted = False
            self.target_pulse = 0
            
        except Exception as e:
            print(f"Error creating crop: {e}")
            traceback.print_exc()
            self.img = np.zeros((80, 80, 4), dtype=np.uint8)
            cv2.rectangle(self.img, (20, 40), (60, 70), (20, 120, 30), -1)
            cv2.rectangle(self.img, (30, 20), (50, 40), (20, 200, 50), -1)
            self.img[:, :, 3] = 255
            
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
        if self.is_being_hit:
            self.hit_timer += 1
            if self.hit_timer >= self.hit_duration:
                self.is_being_hit = False
                self.hit_timer = 0
        
        if self.is_targeted:
            self.target_pulse = (self.target_pulse + 1) % 30
    
    def take_damage(self):
        self.health = max(0, self.health - 1)
        self.is_being_hit = True
        self.hit_timer = 0
        return self.health <= 0
    
    def heal(self, amount=1):
        self.health = min(self.max_health, self.health + amount)
    
    def is_destroyed(self):
        return self.health <= 0
    
    def get_health_color(self):
        index = min(self.health, len(self.health_colors) - 1)
        return self.health_colors[index]

class Enemy:
    def __init__(self, img_path, screen_width, screen_height, target_type="farmer"):
        try:
            self.original_img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            
            if self.original_img is None:
                self.original_img = np.zeros((80, 80, 4), dtype=np.uint8)
                cv2.circle(self.original_img, (40, 40), 30, (0, 0, 255, 255), -1)
                print(f"Created fallback enemy image as {img_path} was not found")
            elif self.original_img.shape[2] == 3:
                self.original_img = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2BGRA)
                
            size = random.randint(80, 120)
            self.img = cv2.resize(self.original_img, (size, size))
            
            self.width, self.height = self.img.shape[1], self.img.shape[0]
            self.screen_width, self.screen_height = screen_width, screen_height
            
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
            else:
                self.x = random.randint(0, screen_width - self.width)
                self.y = screen_height
            
            self.target_type = target_type
            self.target_crop = None
            
            center_x, center_y = screen_width // 2, screen_height // 2
            dx, dy = center_x - self.x, center_y - self.y
            dist = max(1, np.sqrt(dx**2 + dy**2))
            
            self.speed_x = (dx / dist) * random.uniform(1, 3)
            self.speed_y = (dy / dist) * random.uniform(1, 3)
            
            self.speed_x += random.uniform(-0.5, 0.5)
            self.speed_y += random.uniform(-0.5, 0.5)
            
            self.movement_pattern = random.choice(['direct', 'zigzag', 'spiral'])
            self.pattern_timer = 0
            self.original_speed_x = self.speed_x
            self.original_speed_y = self.speed_y
            
            self.active = True
            
            self.is_being_hit = False
            self.hit_timer = 0
            self.hit_duration = 5
            
            self.is_dying = False
            self.death_timer = 0
            self.death_duration = 10
            
            self.trail_positions = []
            self.max_trail_length = 5
            
            self.time_reward = random.uniform(1.0, 2.0)
            
            self.scored = False
            
        except Exception as e:
            print(f"Error creating enemy: {e}")
            traceback.print_exc()
            self.img = np.zeros((80, 80, 4), dtype=np.uint8)
            cv2.circle(self.img, (40, 40), 30, (0, 0, 255, 255), -1)
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
        self.target_crop = crop
        self.target_type = "crop"
        if crop:
            crop.is_targeted = True
    
    def update_target_direction(self, farmer, crops):
        if self.is_dying:
            return
            
        target_x, target_y = None, None
            
        if self.target_type == "crop" and self.target_crop is not None:
            if self.target_crop.is_destroyed():
                valid_crops = [crop for crop in crops if not crop.is_destroyed()]
                if valid_crops:
                    self.target_crop.is_targeted = False
                    self.target_crop = random.choice(valid_crops)
                    self.target_crop.is_targeted = True
                else:
                    if self.target_crop:
                        self.target_crop.is_targeted = False
                    self.target_type = "farmer"
                    self.target_crop = None
                    
            if self.target_crop and not self.target_crop.is_destroyed():
                target_x = self.target_crop.x + self.target_crop.width // 2
                target_y = self.target_crop.y + self.target_crop.height // 2
            else:
                target_x = farmer.x + farmer.width // 2
                target_y = farmer.y + farmer.height // 2
                
        else:
            target_x = farmer.x + farmer.width // 2
            target_y = farmer.y + farmer.height // 2
        
        dx = target_x - (self.x + self.width // 2)
        dy = target_y - (self.y + self.height // 2)
        dist = max(1, np.sqrt(dx**2 + dy**2))
        
        current_speed = np.sqrt(self.speed_x**2 + self.speed_y**2)
        self.original_speed_x = (dx / dist) * current_speed
        self.original_speed_y = (dy / dist) * current_speed
    
    def update(self, farmer=None, crops=None):
        self.trail_positions.append((int(self.x) + self.width//2, int(self.y) + self.height//2))
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)
        
        if self.is_dying:
            self.death_timer += 1
            if self.death_timer >= self.death_duration:
                self.active = False
            return
        
        if farmer is not None and crops is not None:
            self.update_target_direction(farmer, crops)
        
        if self.movement_pattern == 'zigzag':
            self.pattern_timer += 1
            if self.pattern_timer % 30 == 0:
                self.speed_x = self.original_speed_x * random.uniform(0.8, 1.2)
                self.speed_y = self.original_speed_y * random.uniform(0.8, 1.2)
        
        elif self.movement_pattern == 'spiral':
            self.pattern_timer += 1
            angle = self.pattern_timer * 0.1
            spiral_x = math.sin(angle) * 2
            spiral_y = math.cos(angle) * 2
            self.speed_x = self.original_speed_x + spiral_x
            self.speed_y = self.original_speed_y + spiral_y
        else:
            self.speed_x = self.original_speed_x
            self.speed_y = self.original_speed_y
        
        self.x += self.speed_x
        self.y += self.speed_y
        
        if self.is_being_hit:
            self.hit_timer += 1
            if self.hit_timer >= self.hit_duration:
                self.is_being_hit = False
                self.hit_timer = 0
        
        if (self.x > self.screen_width + 100 or self.x < -self.width - 100 or 
            self.y > self.screen_height + 100 or self.y < -self.height - 100):
            self.active = False
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
        if self.target_crop:
            self.target_crop.is_targeted = False
            self.target_crop = None
            
    def is_hit(self, x, y, radius=50):
        if self.is_dying:
            return False
            
        enemy_center_x = self.x + self.width // 2
        enemy_center_y = self.y + self.height // 2
        distance = np.sqrt((x - enemy_center_x)**2 + (y - enemy_center_y)**2)
        
        if distance < 100:
            print(f"Shot distance to enemy: {distance}, Need: {radius}")
            
        return distance < radius
    
    def is_colliding_with_crop(self, crop):
        if self.is_dying or crop.is_destroyed():
            return False
            
        enemy_center_x = self.x + self.width // 2
        enemy_center_y = self.y + self.height // 2
        crop_center_x = crop.x + crop.width // 2
        crop_center_y = crop.y + crop.height // 2
        
        distance = np.sqrt((enemy_center_x - crop_center_x)**2 + (enemy_center_y - crop_center_y)**2)
        return distance < (self.width // 2 + crop.width // 2) * 0.6

class Farmer:
    def __init__(self, img_path, screen_width, screen_height):
        try:
            self.original_img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            
            if self.original_img is None:
                self.original_img = np.zeros((120, 120, 4), dtype=np.uint8)
                cv2.rectangle(self.original_img, (40, 40), (80, 90), (0, 0, 255, 255), -1)
                cv2.circle(self.original_img, (60, 30), 20, (0, 0, 255, 255), -1)
                print(f"Created fallback farmer image as {img_path} was not found")
                self.img = self.original_img
            elif self.original_img.shape[2] == 3:
                self.original_img = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2BGRA)
                self.img = cv2.resize(self.original_img, (120, 120))
            else:
                self.img = cv2.resize(self.original_img, (120, 120))
            
            self.width, self.height = self.img.shape[1], self.img.shape[0]
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
            
        except Exception as e:
            print(f"Error creating farmer: {e}")
            traceback.print_exc()
            self.img = np.zeros((100, 100, 4), dtype=np.uint8)
            cv2.circle(self.img, (50, 50), 40, (0, 0, 255, 255), -1)
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
        if self.is_moving:
            self.move_timer += 1
            
            if self.move_timer < self.move_duration / 2:
                if self.move_direction == 'left':
                    self.x -= 3
                elif self.move_direction == 'right':
                    self.x += 3
                elif self.move_direction == 'up':
                    self.y -= 3
                elif self.move_direction == 'down':
                    self.y += 3
            elif self.move_timer < self.move_duration:
                self.x = self.original_x + (self.x - self.original_x) * (1 - (self.move_timer - self.move_duration/2) / (self.move_duration/2))
                self.y = self.original_y + (self.y - self.original_y) * (1 - (self.move_timer - self.move_duration/2) / (self.move_duration/2))
            else:
                self.is_moving = False
                self.move_timer = 0
                self.x = self.original_x
                self.y = self.original_y
        
        if self.is_attacking:
            self.attack_timer += 1
            if self.attack_timer >= self.attack_duration:
                self.is_attacking = False
                self.attack_timer = 0
        
        if self.has_superpower:
            self.superpower_timer += 1
            if self.superpower_timer >= self.superpower_duration:
                self.has_superpower = False
                self.superpower_timer = 0
    
    def move_by_direction(self, direction, amount=10):
        self.original_x = self.x
        self.original_y = self.y
        
        if direction == 'left':
            self.x = max(0, self.x - amount)
        elif direction == 'right':
            self.x = min(self.screen_width - self.width, self.x + amount)
        elif direction == 'up':
            self.y = max(0, self.y - amount)
        elif direction == 'down':
            self.y = min(self.screen_height - self.height, self.y + amount)
    
    def set_position(self, x, y):
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
        self.has_superpower = True
        self.superpower_timer = 0
        return True

class GameEngine:
    def __init__(self, assets_path='assets', game_duration=90):
        try:
            if not os.path.exists(assets_path):
                os.makedirs(assets_path, exist_ok=True)
                print(f"Created assets directory: {assets_path}")
                
            self.assets_path = assets_path
            bg_path = os.path.join(assets_path, 'background.png')
            farmer_path = os.path.join(assets_path, 'farmer.png')
            
            self.enemy_img_paths = []
            
            default_enemy_path = os.path.join(assets_path, 'enemy.png')
            if os.path.exists(default_enemy_path):
                self.enemy_img_paths.append(default_enemy_path)
                print(f"Found enemy image: {default_enemy_path}")
            
            enemy1_path = os.path.join(assets_path, 'enemy1.png')
            if os.path.exists(enemy1_path):
                self.enemy_img_paths.append(enemy1_path)
                print(f"Found enemy1 image: {enemy1_path}")
            
            if not self.enemy_img_paths:
                print("No enemy images found, will create enemies dynamically")
                self.enemy_img_paths = [default_enemy_path]
                
            self.crop_img_path = os.path.join(assets_path, 'crop.png')
            if not os.path.exists(self.crop_img_path):
                print(f"Crop image not found at: {self.crop_img_path}")
                print("Will create placeholder crop graphics")
            else:
                print(f"Found crop image at: {self.crop_img_path}")
            
            self.font = cv2.FONT_HERSHEY_SIMPLEX
            self.font_scale = 0.9
            self.font_thickness = 2
            
            if os.path.exists(bg_path):
                print(f"Loading background from: {bg_path}")
                self.background = cv2.imread(bg_path)
                if self.background is not None:
                    self.background = cv2.resize(self.background, (1280, 720))
            else:
                print(f"Background image not found at: {bg_path}")
                print("Creating placeholder background...")
                self.background = np.zeros((720, 1280, 3), dtype=np.uint8)
                
                self.background[:480, :] = (230, 180, 100)
                
                self.background[480:, :] = (100, 190, 50)
                
                cv2.circle(self.background, (100, 100), 60, (80, 200, 255), -1)
                
                cv2.ellipse(self.background, (300, 150), (100, 40), 0, 0, 360, (240, 240, 240), -1)
                cv2.ellipse(self.background, (500, 100), (120, 50), 0, 0, 360, (240, 240, 240), -1)
                cv2.ellipse(self.background, (800, 180), (150, 60), 0, 0, 360, (240, 240, 240), -1)
                
                cv2.imwrite(bg_path, self.background)
                print(f"Saved placeholder background to: {bg_path}")
            
            self.width = self.background.shape[1]
            self.height = self.background.shape[0]
            
            self.farmer = Farmer(farmer_path, self.width, self.height)
            
            self.crops = []
            self.create_crops()
            
            self.game_duration = game_duration
            self.remaining_time = game_duration
            self.last_time_update = time.time()
            self.frame_count = 0
            self.fps_estimate = 30
            
            self.score = 0
            self.game_over = False
            self.game_won = False
            self.enemies = []
            self.bullets = []
            self.last_enemy_spawn = time.time()
            self.last_superpower_time = time.time() - 30
            self.superpower_cooldown = 30
            
            self.superpower_active = False
            self.superpower_effect_timer = 0
            self.superpower_effect_duration = 20
            
            self.notifications = []
            
            self.smoke_particles = []
            
            self.last_farmer_pos = None
            
            self.min_enemy_spawn_interval = 2.0
            self.max_enemy_spawn_interval = 4.0
            self.max_enemies = 8
            
            self.crop_targeting_chance = 0.8
            
        except Exception as e:
            print(f"Error initializing GameEngine: {e}")
            traceback.print_exc()
            self.background = np.zeros((720, 1280, 3), dtype=np.uint8)
            self.background[:] = (100, 180, 100)
            
            self.width, self.height = 1280, 720
            
            self.farmer = Farmer("", self.width, self.height)
            
            self.enemy_img_paths = []
            self.crops = []
            self.create_crops()
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
            self.font = cv2.FONT_HERSHEY_SIMPLEX
            self.font_scale = 0.9
            self.font_thickness = 2
    
    def draw_pixelated_text(self, img, text, position, color, font_scale=1.0, thickness=2):
        x, y = position
        
        shadow_offset = int(2 * font_scale)
        cv2.putText(img, text, (x + shadow_offset, y + shadow_offset), 
                    self.font, font_scale, (0, 0, 0), thickness + 1)
        
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            cv2.putText(img, text, (x + dx, y + dy), 
                        self.font, font_scale, (0, 0, 0), thickness)
        
        cv2.putText(img, text, (x, y), 
                    self.font, font_scale, color, thickness)
        
        return img
    
    def draw_ui_panel(self, img, pos, size, color=(60, 60, 60), alpha=0.7, border_color=None, border_size=2):
        x, y, w, h = pos[0], pos[1], size[0], size[1]
        
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
        
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        
        if border_color:
            cv2.rectangle(img, (x, y), (x + w, y + h), border_color, border_size)
        
        return img
    
    def create_crops(self):
        for crop in self.crops:
            if hasattr(crop, 'is_targeted') and crop.is_targeted:
                for enemy in self.enemies:
                    if enemy.target_crop == crop:
                        enemy.target_crop = None
                        enemy.target_type = "farmer"
        
        self.crops = []
        
        center_x = self.width // 2
        center_y = self.height // 2
        radius = 250
        
        for i in range(4):
            angle = (i / 3) * math.pi + math.pi/6
            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))
            
            crop_size = 80
            x -= crop_size // 2
            y -= crop_size // 2
            
            crop = CropPlot(self.crop_img_path, x, y, self.width, self.height)
            self.crops.append(crop)
    
    def update_time_remaining(self):
        self.frame_count += 1
        
        current_time = time.time()
        time_elapsed = current_time - self.last_time_update
        
        if time_elapsed >= 0.25:
            self.fps_estimate = self.frame_count / time_elapsed
            
            self.remaining_time -= time_elapsed
            
            self.last_time_update = current_time
            self.frame_count = 0
            
            if self.remaining_time <= 0:
                self.remaining_time = 0
                self.handle_game_end(True)
    
    def add_time(self, seconds):
        self.remaining_time += seconds
        self.add_notification(f"+{seconds:.1f}s", (0, 255, 255), category="time")
    
    def handle_game_end(self, time_expired):
        if time_expired and self.are_any_crops_alive():
            self.game_won = True
            self.game_over = True
            
            surviving_crops = sum(1 for crop in self.crops if not crop.is_destroyed())
            bonus_points = surviving_crops * 50
            
            self.score += bonus_points
            
            self.add_notification(f"VICTORY! +{bonus_points} BONUS POINTS!", (0, 255, 0), 300, category="endgame")
        else:
            self.game_over = True
            
            reason = "Time's up!" if time_expired else "All crops destroyed!"
            self.add_notification(f"GAME OVER! {reason}", (255, 0, 0), 300, category="endgame")
    
    def are_any_crops_alive(self):
        return any(not crop.is_destroyed() for crop in self.crops)
    
    def are_all_crops_destroyed(self):
        return all(crop.is_destroyed() for crop in self.crops)
    
    def create_smoke_particles(self, x, y, count=10):
        for _ in range(count):
            size = random.randint(5, 15)
            life = random.randint(20, 40)
            color = (random.randint(150, 200), random.randint(150, 200), random.randint(150, 200))
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
        for particle in self.smoke_particles[:]:
            particle['life'] -= 1
            
            if particle['life'] <= 0:
                self.smoke_particles.remove(particle)
                continue
                
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            
            particle['vel_x'] *= 0.95
            particle['vel_y'] *= 0.95
    
    def spawn_enemy(self, force=False):
        current_time = time.time()
        
        spawn_interval = max(
            self.min_enemy_spawn_interval,
            self.max_enemy_spawn_interval * (self.remaining_time / self.game_duration)
        )
        
        if force or (current_time - self.last_enemy_spawn > random.uniform(spawn_interval * 0.8, spawn_interval * 1.2) 
                     and len(self.enemies) < self.max_enemies):
            try:
                enemy_img_path = random.choice(self.enemy_img_paths)
                
                target_type = "crop" if random.random() < self.crop_targeting_chance and self.are_any_crops_alive() else "farmer"
                
                enemy = Enemy(enemy_img_path, self.width, self.height, target_type)
                
                if target_type == "crop" and self.are_any_crops_alive():
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
        try:
            print(f"Shooting at camera coordinates: ({x}, {y})")
            
            scaled_x = int(x * (self.width / 640))
            scaled_y = int(y * (self.height / 480))
            
            print(f"Scaled shooting coordinates: ({scaled_x}, {scaled_y})")
            
            farmer_center_x = self.farmer.x + self.farmer.width // 2
            farmer_center_y = self.farmer.y + self.farmer.height // 2
            
            dx = scaled_x - farmer_center_x
            dy = scaled_y - farmer_center_y
            
            if abs(dx) > abs(dy):
                direction = 'right' if dx > 0 else 'left'
            else:
                direction = 'down' if dy > 0 else 'up'
            
            self.farmer.start_move_animation(direction)
            self.farmer.start_attack_animation()
            
            bullet_color = (0, 255, 255)
            if self.farmer.has_superpower:
                bullet_color = (0, 0, 255)
                
            self.bullets.append({
                'x': scaled_x, 
                'y': scaled_y, 
                'radius': 50,
                'life': 10,
                'color': bullet_color,
                'is_superpower': self.farmer.has_superpower
            })
            
            self.add_notification(f"Shoot!", bullet_color, 30, category="shoot")
            
        except Exception as e:
            print(f"Error creating bullet: {e}")
            traceback.print_exc()
    
    def use_superpower(self):
        try:
            current_time = time.time()
            if current_time - self.last_superpower_time > self.superpower_cooldown:
                self.farmer.activate_superpower()
                
                self.add_notification("SUPERPOWER ACTIVATED!", (0, 255, 255), category="superpower")
                
                self.superpower_active = True
                self.superpower_effect_timer = 0
                
                self.last_superpower_time = current_time
                
                return True
            return False
        except Exception as e:
            print(f"Error using superpower: {e}")
            traceback.print_exc()
            return False
    
    def add_notification(self, text, color, duration=90, category="default"):
        for i, notification in enumerate(self.notifications):
            if notification.get('category') == category and category != "default":
                self.notifications[i] = {
                    'text': text,
                    'color': color,
                    'timer': 0,
                    'duration': duration,
                    'category': category,
                    'animation': 0
                }
                return
                
        self.notifications.append({
            'text': text,
            'color': color,
            'timer': 0,
            'duration': duration,
            'category': category,
            'animation': 0
        })
    
    def update_notifications(self):
        for notification in self.notifications[:]:
            notification['timer'] += 1
            
            if notification['animation'] < 10:
                notification['animation'] += 1
                
            if notification['timer'] >= notification['duration']:
                self.notifications.remove(notification)
                
    def check_farmer_enemy_collisions(self):
        farmer_center_x = self.farmer.x + self.farmer.width // 2
        farmer_center_y = self.farmer.y + self.farmer.height // 2
        
        for enemy in self.enemies[:]:
            if enemy.is_dying:
                continue
                
            enemy_center_x = enemy.x + enemy.width // 2
            enemy_center_y = enemy.y + enemy.height // 2
            
            distance = np.sqrt((farmer_center_x - enemy_center_x)**2 + 
                              (farmer_center_y - enemy_center_y)**2)
            
            if distance < 70:
                print(f"Farmer collided with enemy! Distance: {distance}")
                
                enemy.start_death_animation()
                
                self.create_smoke_particles(enemy_center_x, enemy_center_y, 15)
                
                self.score += 1
                
                self.add_notification("Enemy defeated!", (0, 255, 0), 60, category="enemy_hit")
                
                self.farmer.start_attack_animation()
    
    def update(self):
        try:
            if self.game_over:
                return
                
            self.update_time_remaining()
            
            if not self.are_any_crops_alive():
                self.handle_game_end(False)
                return
            
            self.farmer.update()
            
            for crop in self.crops:
                crop.update()
            
            if self.superpower_active:
                self.superpower_effect_timer += 1
                if self.superpower_effect_timer >= self.superpower_effect_duration:
                    self.superpower_active = False
            
            self.update_notifications()
            
            self.update_smoke_particles()
            
            self.spawn_enemy()
            
            for enemy in self.enemies[:]:
                enemy.update(self.farmer, self.crops)
                
                if not enemy.active:
                    if not hasattr(enemy, 'scored') or not enemy.scored:
                        self.score += 1
                        enemy.scored = True
                        print(f"Enemy removed, score increased to {self.score}")
                        
                    self.enemies.remove(enemy)
                    continue
                for crop in self.crops:
                    if not crop.is_destroyed() and enemy.is_colliding_with_crop(crop):
                        is_destroyed = crop.take_damage()
                        
                        crop_center_x = crop.x + crop.width // 2
                        crop_center_y = crop.y + crop.height // 2
                        self.create_smoke_particles(crop_center_x, crop_center_y, 10)
                        
                        enemy.start_death_animation()
                        
                        if is_destroyed:
                            self.add_notification("Crop destroyed!", (255, 0, 0), category="crop_status")
                        else:
                            self.add_notification(f"Crop damaged! Health: {crop.health}/{crop.max_health}", (255, 165, 0), category="crop_status")
                        
                        if self.are_all_crops_destroyed():
                            self.handle_game_end(False)
                        
                        break
            
            self.check_farmer_enemy_collisions()
            
            for bullet in self.bullets[:]:
                hit = False
                for enemy in self.enemies[:]:
                    if enemy.is_hit(bullet['x'], bullet['y'], bullet['radius']):
                        if enemy in self.enemies:
                            enemy.start_hit_animation()
                            
                            enemy.start_death_animation()
                            
                            self.create_smoke_particles(bullet['x'], bullet['y'], 10)
                            
                            self.add_time(enemy.time_reward)
                            
                            points = 2 if bullet.get('is_superpower', False) else 1
                            self.score += points
                            
                            if points > 1:
                                self.add_notification(f"+{points} points!", (0, 255, 0), 60, category="points")
                            else:
                                self.add_notification(f"Enemy hit!", (0, 255, 255), 30, category="enemy_hit")
                            
                            self.farmer.start_attack_animation()
                            
                            hit = True
                            break
                
                if hit and bullet in self.bullets:
                    self.bullets.remove(bullet)
                elif bullet['life'] <= 0:
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                else:
                    bullet['life'] -= 1
                
        except Exception as e:
            print(f"Error in update: {e}")
            traceback.print_exc()
    
    def draw_farmer(self, game_frame):
        try:
            y1, y2 = int(self.farmer.y), int(self.farmer.y + self.farmer.height)
            x1, x2 = int(self.farmer.x), int(self.farmer.x + self.farmer.width)
            
            if x1 >= 0 and y1 >= 0 and x2 <= game_frame.shape[1] and y2 <= game_frame.shape[0]:
                if self.farmer.img.shape[2] == 4:
                    alpha_farmer = self.farmer.img[:, :, 3] / 255.0
                    for c in range(0, 3):
                        game_frame[y1:y2, x1:x2, c] = (
                            (1 - alpha_farmer) * game_frame[y1:y2, x1:x2, c] + 
                            alpha_farmer * self.farmer.img[:, :, c]
                        )
                else:
                    game_frame[y1:y2, x1:x2] = self.farmer.img
        except Exception as e:
            print(f"Error drawing farmer: {e}")
            traceback.print_exc()
    
    def render_game_only(self):
        try:
            game_frame = self.background.copy() if self.background is not None else np.zeros((720, 1280, 3), dtype=np.uint8)
            
            self.draw_ui_panel(game_frame, (0, self.height - 50), (self.width, 50), 
                               color=(30, 80, 30), alpha=0.8, border_color=(40, 120, 40), border_size=2)
            
            if self.superpower_active:
                self.draw_ui_panel(game_frame, (self.width // 2 - 260, 50), (520, 60), 
                                  color=(0, 0, 100), alpha=0.7, border_color=(0, 0, 255), border_size=3)
                
                self.draw_pixelated_text(game_frame, "SUPERPOWER ACTIVATED!", 
                                       (self.width // 2 - 250, 100), (0, 140, 255), 1.5, 3)
            
            for bullet in self.bullets:
                cv2.circle(game_frame, (int(bullet['x']), int(bullet['y'])), 
                          bullet['radius'], bullet.get('color', (0, 255, 255)), -1)
            
            for particle in self.smoke_particles:
                alpha = particle['life'] / particle['max_life']
                size = int(particle['size'] * alpha)
                alpha = particle['life'] / particle['max_life']
                size = int(particle['size'] * alpha)
                
                cv2.circle(game_frame, 
                          (int(particle['x']), int(particle['y'])), 
                          size, 
                          particle['color'], 
                          -1)
            
            for crop in self.crops:
                if crop.is_destroyed():
                    continue
                    
                y1, y2 = int(crop.y), int(crop.y + crop.height)
                x1, x2 = int(crop.x), int(crop.x + crop.width)
                
                if crop.is_targeted:
                    pulse_size = 5 + int(3 * math.sin(crop.target_pulse * 0.2))
                    cv2.circle(game_frame,
                              (x1 + crop.width // 2, y1 + crop.height // 2),
                              crop.width // 2 + pulse_size,
                              (0, 0, 255),
                              2)
                
                if crop.img.shape[2] == 4:
                    alpha_crop = crop.img[:, :, 3] / 255.0
                    for c in range(0, 3):
                        game_frame[y1:y2, x1:x2, c] = (
                            (1 - alpha_crop) * game_frame[y1:y2, x1:x2, c] + 
                            alpha_crop * crop.img[:, :, c]
                        )
                else:
                    game_frame[y1:y2, x1:x2] = crop.img
                
                health_width = 60
                health_height = 10
                health_x = x1 + (crop.width - health_width) // 2
                health_y = y1 - 18
                
                cv2.rectangle(game_frame,
                             (health_x-2, health_y-2),
                             (health_x + health_width+2, health_y + health_height+2),
                             (20, 20, 20),
                             -1)
                cv2.rectangle(game_frame,
                             (health_x, health_y),
                             (health_x + health_width, health_y + health_height),
                             (50, 50, 50),
                             -1)
                             
                current_health_width = int((crop.health / crop.max_health) * health_width)
                health_color = crop.get_health_color()
                
                for i in range(health_height):
                    bar_color = list(health_color)
                    brightness_factor = 1.3 - (i / health_height)
                    bar_color = [min(255, int(c * brightness_factor)) for c in bar_color]
                    
                    cv2.line(game_frame,
                            (health_x, health_y + i),
                            (health_x + current_health_width, health_y + i),
                            tuple(bar_color),
                            1)
                             
                if crop.is_being_hit:
                    if crop.hit_timer % 3 < 2:
                        cv2.rectangle(game_frame,
                                    (x1, y1),
                                    (x2, y2),
                                    (0, 0, 255),
                                    2)
            
            for enemy in self.enemies:
                if not enemy.active:
                    continue
                
                if len(enemy.trail_positions) >= 2:
                    for i in range(len(enemy.trail_positions) - 1):
                        p1 = enemy.trail_positions[i]
                        p2 = enemy.trail_positions[i + 1]
                        
                        alpha = 0.7 * (i / len(enemy.trail_positions))
                        thickness = max(1, int((i + 1) * 3 / len(enemy.trail_positions)))
                        
                        cv2.line(game_frame, p1, p2, (50, 100, 255), thickness)
                
                if enemy.is_being_hit:
                    if enemy.hit_timer % 2 == 0:
                        hit_img = enemy.img.copy()
                        hit_img[:, :, 0:3] = 255
                        img_to_draw = hit_img
                    else:
                        img_to_draw = enemy.img
                elif enemy.is_dying:
                    img_to_draw = enemy.img.copy()
                    alpha_mult = 1.0 - (enemy.death_timer / enemy.death_duration)
                    img_to_draw[:, :, 3] = (img_to_draw[:, :, 3] * alpha_mult).astype(np.uint8)
                else:
                    img_to_draw = enemy.img
                
                y1, y2 = int(enemy.y), int(enemy.y + enemy.height)
                x1, x2 = int(enemy.x), int(enemy.x + enemy.width)
                
                if x1 < 0: x1 = 0
                if y1 < 0: y1 = 0
                if x2 > game_frame.shape[1]: x2 = game_frame.shape[1]
                if y2 > game_frame.shape[0]: y2 = game_frame.shape[0]
                
                if x1 >= x2 or y1 >= y2:
                    continue
                    
                crop_width = x2 - x1
                crop_height = y2 - y1
                
                crop_x1 = 0 if x1 >= 0 else -x1
                crop_y1 = 0 if y1 >= 0 else -y1
                crop_x2 = img_to_draw.shape[1] if x2 <= game_frame.shape[1] else img_to_draw.shape[1] - (x2 - game_frame.shape[1])
                crop_y2 = img_to_draw.shape[0] if y2 <= game_frame.shape[0] else img_to_draw.shape[0] - (y2 - game_frame.shape[0])
                
                if crop_x1 >= crop_x2 or crop_y1 >= crop_y2:
                    continue
                
                target_height = y2 - y1
                target_width = x2 - x1
                crop_height = crop_y2 - crop_y1
                crop_width = crop_x2 - crop_x1
                
                if crop_height != target_height or crop_width != target_width:
                    crop_y2 = min(crop_y2, crop_y1 + target_height)
                    crop_x2 = min(crop_x2, crop_x1 + target_width)
                    y2 = min(y2, y1 + (crop_y2 - crop_y1))
                    x2 = min(x2, x1 + (crop_x2 - crop_x1))
                
                if crop_y2 <= crop_y1 or crop_x2 <= crop_x1 or y2 <= y1 or x2 <= x1:
                    continue
                
                try:
                    cropped_enemy = img_to_draw[crop_y1:crop_y2, crop_x1:crop_x2]
                    
                    if cropped_enemy.shape[0] == 0 or cropped_enemy.shape[1] == 0:
                        continue
                    
                    if cropped_enemy.shape[2] == 4:
                        alpha = cropped_enemy[:, :, 3] / 255.0
                        for c in range(0, 3):
                            game_frame[y1:y2, x1:x2, c] = (
                                (1 - alpha) * game_frame[y1:y2, x1:x2, c] + 
                                alpha * cropped_enemy[:, :, c]
                            )
                    else:
                        game_frame[y1:y2, x1:x2] = cropped_enemy[:, :, :3]
                except Exception as e:
                    print(f"Error rendering enemy: {e}")
                    continue
            
            if self.farmer.is_attacking:
                cv2.circle(game_frame, 
                          (int(self.farmer.x + self.farmer.width//2), 
                           int(self.farmer.y + self.farmer.height//2)), 
                          60, (0, 255, 255), 2)
            self.draw_farmer(game_frame)
            
            ui_box_height = 50
            
            self.draw_ui_panel(game_frame, 
                              (0, 0), 
                              (self.width, ui_box_height), 
                              color=(40, 40, 60),
                              alpha=0.85,
                              border_color=(60, 60, 100),
                              border_size=2)
            
            score_text = f"Score: {self.score}"
            score_width = cv2.getTextSize(score_text, self.font, self.font_scale, self.font_thickness)[0][0]
            score_panel_width = score_width + 30
            
            self.draw_ui_panel(game_frame, 
                              (10, 8), 
                              (score_panel_width, 35), 
                              color=(60, 60, 100),
                              alpha=0.7,
                              border_color=(100, 100, 180),
                              border_size=1)
                              
            self.draw_pixelated_text(game_frame, score_text, (25, 35), 
                                   (255, 255, 255), 0.9, 2)
            
            minutes = int(self.remaining_time) // 60
            seconds = int(self.remaining_time) % 60
            time_color = (255, 255, 255)  
            if self.remaining_time < 10:  
                time_color = (255, 50, 50)
            elif self.remaining_time < 30:  
                time_color = (255, 200, 50)
                
            time_text = f"Time: {minutes:02}:{seconds:02}"
            time_width = cv2.getTextSize(time_text, self.font, self.font_scale, self.font_thickness)[0][0]
            
            time_panel_color = (80, 50, 50) if self.remaining_time < 10 else (70, 70, 100)
            time_border_color = (180, 50, 50) if self.remaining_time < 10 else (100, 100, 180)
            
            self.draw_ui_panel(game_frame, 
                              (score_panel_width + 30, 8), 
                              (time_width + 30, 35), 
                              color=time_panel_color,
                              alpha=0.7,
                              border_color=time_border_color,
                              border_size=1)
            
            self.draw_pixelated_text(game_frame, time_text, (score_panel_width + 45, 35), 
                                    time_color, 0.9, 2)
            
            alive_crops = sum(1 for crop in self.crops if not crop.is_destroyed())
            crop_text = f"Crops: {alive_crops}/{len(self.crops)}"
            crop_width = cv2.getTextSize(crop_text, self.font, self.font_scale, self.font_thickness)[0][0]
            
            crop_panel_x = score_panel_width + time_width + 80
            
            self.draw_ui_panel(game_frame, 
                              (crop_panel_x, 8), 
                              (crop_width + 30, 35), 
                              color=(50, 80, 50),
                              alpha=0.7,
                              border_color=(80, 160, 80),
                              border_size=1)
                              
            self.draw_pixelated_text(game_frame, crop_text, (crop_panel_x + 15, 35), 
                                   (180, 255, 180), 0.9, 2)
            
            cooldown_remaining = max(0, self.superpower_cooldown - (time.time() - self.last_superpower_time))
            
            if self.farmer.has_superpower:
                time_left = int((self.farmer.superpower_duration - self.farmer.superpower_timer) / 30)
                superpower_text = f"SUPERPOWER: {time_left}s"
                color = (50, 50, 255)
                panel_color = (30, 30, 150)
                border_color = (80, 80, 255)
            elif cooldown_remaining == 0:
                superpower_text = "SUPERPOWER: READY!"
                color = (50, 255, 50)
                panel_color = (20, 120, 20)
                border_color = (80, 255, 80)
            else:
                superpower_text = f"SUPERPOWER: {int(cooldown_remaining)}s"
                color = (200, 150, 50)
                panel_color = (100, 70, 20)
                border_color = (200, 150, 50)
            
            if cooldown_remaining == 0 and not self.farmer.has_superpower:
                pulse = abs(math.sin(time.time() * 5)) * 0.5 + 0.5
                border_color = tuple([int(c * pulse + c * (1-pulse) * 0.5) for c in border_color])
            
            superpower_width = cv2.getTextSize(superpower_text, self.font, self.font_scale, self.font_thickness)[0][0]
            
            self.draw_ui_panel(game_frame, 
                              (self.width - superpower_width - 40, 8), 
                              (superpower_width + 30, 35), 
                              color=panel_color,
                              alpha=0.7,
                              border_color=border_color,
                              border_size=2)
                              
            self.draw_pixelated_text(game_frame, superpower_text, (self.width - superpower_width - 25, 35), 
                                   color, 0.9, 2)
            
            notification_groups = {}
            for notification in self.notifications:
                category = notification.get('category', 'default')
                if category not in notification_groups:
                    notification_groups[category] = []
                notification_groups[category].append(notification)
            
            category_positions = {
                'default': (self.width // 2, 200),          
                'time': (self.width - 150, 150),            
                'crop_status': (self.width // 2, 160),      
                'enemy_hit': (self.width // 2, 240),        
                'points': (self.width // 2, 280),           
                'shoot': (self.width // 2 + 100, 200),      
                'superpower': (self.width // 2, 120),       
                'endgame': (self.width // 2, self.height // 2 - 50)  
            }
            
            for category, notifications in notification_groups.items():
                if category in category_positions:
                    base_x, base_y = category_positions[category]
                else:
                    base_x, base_y = category_positions['default']
                    
                notification_y = base_y
                
                for notification in notifications:
                    fade = 1.0
                    if notification['timer'] > notification['duration'] * 0.7:
                        fade = 1.0 - ((notification['timer'] - notification['duration'] * 0.7) / (notification['duration'] * 0.3))
                    
                    anim_offset = 0
                    if notification['animation'] < 10:
                        anim_offset = 50 - (notification['animation'] * 5)
                    
                    color = notification['color']
                    color = tuple([int(c * fade) for c in color])
                    
                    text = notification['text']
                    text_size = cv2.getTextSize(text, self.font, 1, 2)[0]
                    text_width, text_height = text_size
                    
                    text_x = base_x - (text_width // 2) + anim_offset
                    
                    panel_padding = 10
                    panel_height = text_height + panel_padding * 2
                    panel_width = text_width + panel_padding * 2
                    
                    panel_alpha = 0.7 * fade
                    
                    panel_color = (30, 30, 40)
                    self.draw_ui_panel(game_frame,
                                     (text_x - panel_padding, notification_y - text_height - panel_padding),
                                     (panel_width, panel_height),
                                     color=panel_color,
                                     alpha=panel_alpha,
                                     border_color=color,
                                     border_size=2)
                    
                    self.draw_pixelated_text(game_frame, 
                                          text, 
                                          (text_x, notification_y), 
                                          color, 
                                          1, 
                                          2)
                    
                    notification_y += panel_height + 5
            
            if self.game_over:
                overlay = game_frame.copy()
                cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.7, game_frame, 0.3, 0, game_frame)
                
                panel_width = 600
                panel_height = 300
                panel_x = (self.width - panel_width) // 2
                panel_y = (self.height - panel_height) // 2
                
                if self.game_won:
                    panel_color = (0, 70, 0)
                    border_color = (0, 200, 0)
                    title_color = (100, 255, 100)
                else:
                    panel_color = (70, 0, 0)
                    border_color = (200, 0, 0)
                    title_color = (255, 100, 100)
                
                pulse = abs(math.sin(time.time() * 2)) * 0.5 + 0.5
                adjusted_border = tuple([int(c * pulse + c * (1-pulse) * 0.5) for c in border_color])
                
                self.draw_ui_panel(game_frame, 
                                  (panel_x, panel_y), 
                                  (panel_width, panel_height), 
                                  color=panel_color, 
                                  alpha=0.85,
                                  border_color=adjusted_border, 
                                  border_size=4)
                
                cv2.rectangle(game_frame, 
                             (panel_x + 10, panel_y + 10), 
                             (panel_x + panel_width - 10, panel_y + panel_height - 10),
                             adjusted_border, 1)
                
                if self.game_won:
                    self.draw_pixelated_text(game_frame, 
                                           "VICTORY!", 
                                           (panel_x + panel_width//2 - 120, panel_y + 80), 
                                           title_color, 2, 5)
                    
                    self.draw_pixelated_text(game_frame, 
                                           f"Final Score: {self.score}", 
                                           (panel_x + panel_width//2 - 120, panel_y + 150), 
                                           (255, 255, 255), 1, 2)
                    
                    surviving_crops = sum(1 for crop in self.crops if not crop.is_destroyed())
                    self.draw_pixelated_text(game_frame, 
                                           f"Crops Saved: {surviving_crops}/{len(self.crops)}", 
                                           (panel_x + panel_width//2 - 140, panel_y + 190), 
                                           (100, 255, 255), 1, 2)
                else:
                    self.draw_pixelated_text(game_frame, 
                                           "GAME OVER!", 
                                           (panel_x + panel_width//2 - 140, panel_y + 80), 
                                           title_color, 2, 5)
                    self.draw_pixelated_text(game_frame, 
                                           f"Final Score: {self.score}", 
                                           (panel_x + panel_width//2 - 120, panel_y + 150), 
                                           (255, 255, 255), 1, 2)
                instruction_text = "Press 'r' to Restart or 'q' to Quit"
                blink_effect = 0.7 + 0.3 * math.sin(time.time() * 4)
                instruction_color = (int(255 * blink_effect), int(255 * blink_effect), int(255 * blink_effect))
    
                instruction_width = cv2.getTextSize(instruction_text, self.font, 1, 2)[0][0]
                instruction_x = panel_x + (panel_width - instruction_width) // 2
                instruction_y = panel_y + panel_height - 40
                
                self.draw_ui_panel(game_frame, 
                                 (instruction_x - 20, instruction_y - 30), 
                                 (instruction_width + 40, 40), 
                                 color=(60, 60, 60), 
                                 alpha=0.7, 
                                 border_color=(150, 150, 150), 
                                 border_size=1)
                                 
                self.draw_pixelated_text(game_frame, 
                                       instruction_text, 
                                       (instruction_x, instruction_y), 
                                       instruction_color, 1, 2)
            
            return game_frame
            
        except Exception as e:
            print(f"Error in render_game_only: {e}")
            traceback.print_exc()
            error_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            cv2.putText(error_frame, "Rendering Error", (self.width // 2 - 100, self.height // 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return error_frame
    
    def render(self, frame):
        try:
            game_frame = self.render_game_only()
            
            game_frame_resized = cv2.resize(game_frame, (frame.shape[1], frame.shape[0]))
            
            result = cv2.addWeighted(game_frame_resized, 0.7, frame, 0.3, 0)
            
            return result
        except Exception as e:
            print(f"Error in render: {e}")
            traceback.print_exc()
            return frame