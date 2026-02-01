"""
GitWars - Main Game Engine (OPTIMIZED)
=======================================
CONSOLE Tank Tournament - MNIT Jaipur

This is the GAME ENGINE. Students should NOT modify this file.
Students edit files in the bots/ folder to control their tanks.

Run with: python main.py

PERFORMANCE OPTIMIZED:
- Pre-rendered glow surfaces
- Direct drawing instead of per-frame surface creation
- Efficient trail rendering using pygame.draw.aalines
"""

import pygame
import math
import random
import copy
import time
import os
import sys
import importlib.util
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Callable
from config import *

# Initialize Pygame
pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(32)  # Increase channels to prevent sounds cutting out

# =============================================================================
# AUDIO SYSTEM (Pre-loaded at startup for performance)
# =============================================================================

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Pre-load sounds (CRUCIAL: do NOT load sounds in game loop!)
def load_sound(filename: str) -> Optional[pygame.mixer.Sound]:
    """Safely load a sound file."""
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except:
            print(f"Warning: Could not load sound {filename}")
    return None

# Load all sounds at startup
SFX_SHOOT = load_sound("shoot.mp3")
SFX_DEATH = load_sound("death.mp3")  # Was explosion.wav
SFX_COIN = load_sound("coin.mp3")
SFX_READY = load_sound("ready.mp3")
SFX_WIN_1 = load_sound("win1.mp3")
SFX_WIN_2 = load_sound("win2.mp3")
SFX_WIN_3 = load_sound("win3.mp3")

def play_sound(sound: Optional[pygame.mixer.Sound], volume: float = SFX_VOLUME, pitch_variation: bool = False):
    """Play a sound with optional pitch variation."""
    if sound is None:
        return
    
    sound.set_volume(volume)
    sound.play()

# Reserve channel 0 for critical sounds (win, ready) that should NEVER be cut off
CRITICAL_CHANNEL = pygame.mixer.Channel(0)

def play_critical_sound(sound: Optional[pygame.mixer.Sound], volume: float = 1.0):
    """Play a critical sound on a reserved channel. This ensures it won't be cut off."""
    if sound is None:
        return
    
    sound.set_volume(volume)
    CRITICAL_CHANNEL.play(sound)

def start_background_music():
    """Start the background music loop."""
    bgm_path = os.path.join(ASSETS_DIR, "bgm.mp3")
    if os.path.exists(bgm_path):
        try:
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)  # -1 = loop forever
            print("🎵 Background music loaded!")
        except Exception as e:
            print(f"Warning: Could not load background music: {e}")

# =============================================================================
# PRE-RENDERED SURFACES (Performance Optimization)
# =============================================================================

# Create reusable glow surfaces at startup
def create_glow_surface(size: int, color: Tuple[int, int, int], alpha: int = 100) -> pygame.Surface:
    """Create a pre-rendered glow surface."""
    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    pygame.draw.circle(surf, (*color, alpha), (size, size), size)
    return surf

# Pre-render common glow sizes
GLOW_CACHE: Dict[Tuple[int, Tuple[int, int, int]], pygame.Surface] = {}

def get_glow_surface(size: int, color: Tuple[int, int, int], alpha: int = 100) -> pygame.Surface:
    """Get or create a cached glow surface."""
    key = (size, color, alpha)
    if key not in GLOW_CACHE:
        GLOW_CACHE[key] = create_glow_surface(size, color, alpha)
    return GLOW_CACHE[key]

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))

def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def angle_to(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate angle from point 1 to point 2 in degrees."""
    return math.degrees(math.atan2(y2 - y1, x2 - x1))

def normalize_angle(angle: float) -> float:
    """Normalize angle to -180 to 180 range."""
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle

# Sensor constants
SENSOR_MAX_RANGE = 300.0  # Max detection distance in pixels
SENSOR_ANGLES = {
    "front": 0,      # Straight ahead
    "left": -30,     # 30 degrees to the left
    "right": 30      # 30 degrees to the right
}

def get_sensor_readings(tank_x: float, tank_y: float, tank_angle: float, walls: List) -> Dict[str, float]:
    """
    Cast 3 rays (whiskers) from the tank to detect walls.
    Uses pygame.Rect.clipline for efficient collision detection.
    
    Returns: {"front": dist, "left": dist, "right": dist}
    Max distance is SENSOR_MAX_RANGE (300). If no wall hit, returns 300.
    """
    readings = {}
    
    for sensor_name, offset_angle in SENSOR_ANGLES.items():
        # Calculate ray direction
        ray_angle = math.radians(tank_angle + offset_angle)
        
        # Ray start and end points
        start_x = tank_x
        start_y = tank_y
        end_x = tank_x + math.cos(ray_angle) * SENSOR_MAX_RANGE
        end_y = tank_y + math.sin(ray_angle) * SENSOR_MAX_RANGE
        
        # Find shortest distance to any wall
        min_dist = SENSOR_MAX_RANGE
        
        for wall in walls:
            wall_rect = wall.get_rect()
            # clipline returns the segment of line inside the rect, or empty tuple
            clipped = wall_rect.clipline((start_x, start_y), (end_x, end_y))
            
            if clipped:
                # clipped is ((x1, y1), (x2, y2)) - the segment inside the wall
                hit_x, hit_y = clipped[0]  # First intersection point
                dist = distance(start_x, start_y, hit_x, hit_y)
                if dist < min_dist:
                    min_dist = dist
        
        readings[sensor_name] = round(min_dist, 1)
    
    return readings

# =============================================================================
# CAMERA (Screen Shake)
# =============================================================================

class Camera:
    """Handles screen shake and camera effects."""
    
    def __init__(self):
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.shake_intensity = 0.0
        self.shake_timer = 0.0
    
    def shake(self, intensity: float = SHAKE_INTENSITY, duration: float = SHAKE_DURATION):
        """Trigger screen shake."""
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_timer = max(self.shake_timer, duration)
    
    def update(self, dt: float):
        """Update camera shake."""
        if self.shake_timer > 0:
            self.shake_timer -= dt
            self.offset_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.offset_y = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_intensity *= SHAKE_DECAY
        else:
            self.offset_x = 0
            self.offset_y = 0
            self.shake_intensity = 0
    
    def apply(self, pos: Tuple[float, float]) -> Tuple[int, int]:
        """Apply camera offset to a position."""
        return (int(pos[0] + self.offset_x), int(pos[1] + self.offset_y))

# =============================================================================
# PARTICLE SYSTEM (OPTIMIZED - Direct Drawing)
# =============================================================================

@dataclass
class Particle:
    """A single particle with physics and rendering."""
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    size: float
    alpha: int = 255
    alive: bool = True
    
    def update(self):
        """Update particle position and fade."""
        self.x += self.vx
        self.y += self.vy
        self.vx *= PARTICLE_FRICTION
        self.vy *= PARTICLE_FRICTION
        self.alpha -= PARTICLE_FADE_SPEED
        self.size *= 0.98
        
        if self.alpha <= 0 or self.size < 1:
            self.alive = False
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Draw the particle - OPTIMIZED: direct drawing."""
        if self.alpha <= 0 or self.size < 1:
            return
        
        pos = camera.apply((self.x, self.y))
        size = max(1, int(self.size))
        
        # OPTIMIZED: Draw directly instead of creating surfaces
        # Use color brightness to simulate alpha fade
        fade = self.alpha / 255.0
        faded_color = (
            int(self.color[0] * fade),
            int(self.color[1] * fade),
            int(self.color[2] * fade)
        )
        pygame.draw.rect(surface, faded_color, (pos[0] - size, pos[1] - size, size * 2, size * 2))


class ParticleSystem:
    """Manages all particles in the game."""
    
    def __init__(self):
        self.particles: List[Particle] = []
        self.max_particles = 200  # Cap max particles
    
    def spawn_explosion(self, x: float, y: float, color: Tuple[int, int, int], count: int = PARTICLE_DEATH_COUNT):
        """Spawn an explosion of particles."""
        # Limit particles to prevent lag
        count = min(count, self.max_particles - len(self.particles))
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, PARTICLE_DEATH_SPEED)
            size = random.uniform(*PARTICLE_SIZE_RANGE)
            
            # Vary the color slightly
            r = clamp(color[0] + random.randint(-30, 30), 0, 255)
            g = clamp(color[1] + random.randint(-30, 30), 0, 255)
            b = clamp(color[2] + random.randint(-30, 30), 0, 255)
            
            self.particles.append(Particle(
                x=x,
                y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                color=(int(r), int(g), int(b)),
                size=size
            ))
    
    def spawn_muzzle_flash(self, x: float, y: float, angle: float, color: Tuple[int, int, int]):
        """Spawn muzzle flash particles."""
        # Limit particles
        if len(self.particles) >= self.max_particles:
            return
            
        for _ in range(3):  # Reduced from 5
            spread = random.uniform(-0.3, 0.3)
            speed = random.uniform(3, 6)
            
            self.particles.append(Particle(
                x=x,
                y=y,
                vx=math.cos(math.radians(angle) + spread) * speed,
                vy=math.sin(math.radians(angle) + spread) * speed,
                color=color,
                size=random.uniform(3, 6),
                alpha=200
            ))
    
    def update(self):
        """Update all particles."""
        for particle in self.particles:
            particle.update()
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.alive]
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Draw all particles."""
        for particle in self.particles:
            particle.draw(surface, camera)

# =============================================================================
# BULLET TRAIL (OPTIMIZED - Single polyline instead of surfaces)
# =============================================================================

class Trail:
    """Fading trail effect for bullets - OPTIMIZED."""
    
    def __init__(self, color: Tuple[int, int, int]):
        self.positions: List[Tuple[float, float]] = []
        self.color = color
        self.max_length = BULLET_TRAIL_LENGTH
    
    def add_point(self, x: float, y: float):
        """Add a new point to the trail."""
        self.positions.append((x, y))
        if len(self.positions) > self.max_length:
            self.positions.pop(0)
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Draw the fading trail - OPTIMIZED: single polyline."""
        if len(self.positions) < 2:
            return
        
        # OPTIMIZED: Draw as connected lines with direct pygame.draw
        # No surface creation!
        points = [camera.apply(pos) for pos in self.positions]
        
        # Draw trail as anti-aliased lines (hardware accelerated)
        if len(points) >= 2:
            pygame.draw.aalines(surface, self.color, False, points)

# =============================================================================
# BULLET (OPTIMIZED)
# =============================================================================

class Bullet:
    """Projectile with trail effect and critical hits."""
    
    def __init__(self, x: float, y: float, angle: float, owner_id: int, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.angle = angle
        self.owner_id = owner_id
        self.color = color
        
        # Velocity
        rad = math.radians(angle)
        self.vx = math.cos(rad) * BULLET_SPEED
        self.vy = math.sin(rad) * BULLET_SPEED
        
        # Critical hit check
        self.is_critical = random.random() < CRITICAL_HIT_CHANCE
        if self.is_critical:
            self.color = COLOR_CRITICAL
            self.damage = BULLET_DAMAGE * CRITICAL_HIT_MULTIPLIER
        else:
            self.damage = BULLET_DAMAGE
        
        # Trail
        self.trail = Trail(self.color)
        self.alive = True
    
    def update(self):
        """Update bullet position."""
        self.trail.add_point(self.x, self.y)
        self.x += self.vx
        self.y += self.vy
        
        # Check bounds
        if self.x < 0 or self.x > SCREEN_WIDTH or self.y < 0 or self.y > SCREEN_HEIGHT:
            self.alive = False
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Draw bullet and trail - OPTIMIZED."""
        # Draw trail first
        self.trail.draw(surface, camera)
        
        # Draw bullet - OPTIMIZED: direct drawing
        pos = camera.apply((self.x, self.y))
        
        # Glow effect - simple larger circle
        glow_size = BULLET_SIZE * 2 if self.is_critical else BULLET_SIZE + 2
        glow_color = tuple(max(0, c - 100) for c in self.color)  # Darker glow
        pygame.draw.circle(surface, glow_color, pos, glow_size)
        
        # Core
        pygame.draw.circle(surface, self.color, pos, BULLET_SIZE)
        pygame.draw.circle(surface, (255, 255, 255), pos, BULLET_SIZE // 2)
    
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle."""
        return pygame.Rect(self.x - BULLET_SIZE, self.y - BULLET_SIZE, 
                          BULLET_SIZE * 2, BULLET_SIZE * 2)

# =============================================================================
# TANK (OPTIMIZED - Pre-rendered surfaces)
# =============================================================================

class Tank:
    """Player/Bot controlled tank with Euler physics."""
    
    def __init__(self, tank_id: int, x: float, y: float, color: Tuple[int, int, int]):
        self.id = tank_id
        self.x = x
        self.y = y
        self.angle = 0.0
        self.color = color
        
        self.health = TANK_MAX_HEALTH
        self.max_health = TANK_MAX_HEALTH  # Track max for health bar display
        self.ammo = TANK_STARTING_AMMO
        self.coins = 0
        self.alive = True
        self.team_name = f"Tank_{tank_id}"  # Default, will be set from bot filename
        
        # =====================================================================
        # EULER PHYSICS SYSTEM
        # =====================================================================
        self.mass = TANK_MASS
        self.pos = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = pygame.math.Vector2(0, 0)
        self.friction = TANK_FRICTION
        
        # State
        self.is_jammed = False
        self.jam_timer = 0.0
        self.shoot_cooldown = 0.0
        self.last_action = None
        
        # Visual state
        self.muzzle_flash_timer = 0
        
        # OPTIMIZATION: Pre-render tank body surface
        self._base_surface = pygame.Surface((TANK_SIZE, TANK_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(self._base_surface, self.color, (2, 2, TANK_SIZE - 4, TANK_SIZE - 4), border_radius=5)
        pygame.draw.rect(self._base_surface, (255, 255, 255), (2, 2, TANK_SIZE - 4, TANK_SIZE - 4), 2, border_radius=5)
        
        # Cache rotated surfaces
        self._last_angle = None
        self._rotated_surface = None
    
    def apply_force(self, force_vector: pygame.math.Vector2):
        """
        Apply a force to the tank. F = ma -> a = F / m
        Multiple forces in one frame will accumulate naturally.
        """
        self.acceleration += force_vector / self.mass
    
    def update(self, dt: float, walls: List['Wall'] = None):
        """Update tank state with Force Accumulation physics."""
        # Handle jam timer (but do NOT block physics!)
        if self.jam_timer > 0:
            self.jam_timer -= dt
            self.is_jammed = self.jam_timer > 0
        
        # =====================================================================
        # FORCE ACCUMULATION PHYSICS (User's exact pattern)
        # =====================================================================
        
        # 1. APPLY FRICTION (Force opposing velocity)
        # This naturally slows down BOTH movement and knockback smoothly.
        if self.velocity.length() > 0.5:
            friction_force = self.velocity.normalize() * (-self.friction) * self.velocity.length()
            self.acceleration += friction_force
        
        # 2. INTEGRATE PHYSICS (Euler Integration)
        # Velocity changes by Acceleration over Time
        self.velocity += self.acceleration * dt
        # Position changes by Velocity over Time
        self.pos += self.velocity * dt
        
        # 3. RESET ACCELERATION (At END of frame, ready for next)
        self.acceleration = pygame.math.Vector2(0, 0)
        
        # 4. Sync x/y for compatibility
        self.x = self.pos.x
        self.y = self.pos.y
        
        # Clamp to screen bounds
        self.x = clamp(self.x, TANK_SIZE, SCREEN_WIDTH - TANK_SIZE)
        self.y = clamp(self.y, TANK_SIZE, SCREEN_HEIGHT - TANK_SIZE)
        self.pos.x = self.x
        self.pos.y = self.y
        
        # Wall collision (SLIDING - not sticky!)
        if walls:
            tank_rect = self.get_rect()
            for wall in walls:
                wall_rect = wall.get_rect()
                if tank_rect.colliderect(wall_rect):
                    # Calculate overlap on each axis
                    overlap_left = tank_rect.right - wall_rect.left
                    overlap_right = wall_rect.right - tank_rect.left
                    overlap_top = tank_rect.bottom - wall_rect.top
                    overlap_bottom = wall_rect.bottom - tank_rect.top
                    
                    # Find minimum overlap (the axis we need to resolve)
                    min_overlap_x = min(overlap_left, overlap_right)
                    min_overlap_y = min(overlap_top, overlap_bottom)
                    
                    # Resolve collision on the axis with smaller overlap (allows sliding!)
                    if min_overlap_x < min_overlap_y:
                        # Horizontal collision - push out horizontally, KEEP vertical velocity
                        if overlap_left < overlap_right:
                            self.pos.x -= overlap_left + 1
                        else:
                            self.pos.x += overlap_right + 1
                        self.velocity.x = 0  # Stop horizontal, but slide vertically
                    else:
                        # Vertical collision - push out vertically, KEEP horizontal velocity
                        if overlap_top < overlap_bottom:
                            self.pos.y -= overlap_top + 1
                        else:
                            self.pos.y += overlap_bottom + 1
                        self.velocity.y = 0  # Stop vertical, but slide horizontally
                    
                    # Sync position
                    self.x = self.pos.x
                    self.y = self.pos.y
                    tank_rect = self.get_rect()  # Update rect for next wall check
        
        # Update cooldowns
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        
        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer -= 1
    
    def move(self, dx: float, dy: float):
        """Move the tank in a direction (bot command). Adds force, never overwrites velocity!"""
        if self.is_jammed:
            return
        
        # Random jam check
        if random.random() < JAM_CHANCE:
            self.is_jammed = True
            self.jam_timer = 1.0
            return
        
        # Normalize and ADD as force (NEVER overwrite velocity!)
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            input_force = pygame.math.Vector2(
                (dx / length) * TANK_ENGINE_FORCE,
                (dy / length) * TANK_ENGINE_FORCE
            )
            # ADD to acceleration, don't replace
            self.acceleration += input_force / self.mass
            self.angle = math.degrees(math.atan2(dy, dx))
    
    def shoot(self, target_angle: float) -> Optional[Bullet]:
        """Fire a bullet if possible."""
        if self.is_jammed or self.ammo <= 0 or self.shoot_cooldown > 0:
            return None
        
        self.ammo -= 1
        self.shoot_cooldown = 0.2
        self.muzzle_flash_timer = MUZZLE_FLASH_DURATION
        
        # Recoil as force
        rad = math.radians(target_angle)
        recoil_force = pygame.math.Vector2(
            -math.cos(rad) * TANK_RECOIL * 2,
            -math.sin(rad) * TANK_RECOIL * 2
        )
        self.apply_force(recoil_force)
        
        # Create bullet at barrel tip
        barrel_x = self.x + math.cos(rad) * (TANK_SIZE / 2 + 5)
        barrel_y = self.y + math.sin(rad) * (TANK_SIZE / 2 + 5)
        
        return Bullet(barrel_x, barrel_y, target_angle, self.id, self.color)
    
    def take_damage(self, damage: float):
        """Apply damage to the tank."""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False
    
    def apply_knockback(self, angle: float, force: float):
        """Apply knockback as IMPULSE (direct velocity change, not acceleration)."""
        rad = math.radians(angle)
        # Impulse: directly add to velocity (not acceleration)
        # This gives INSTANT kick that friction will smooth out
        impulse = pygame.math.Vector2(
            math.cos(rad) * force * 15.0,  # Scale for impact
            math.sin(rad) * force * 15.0
        )
        self.velocity += impulse  # IMPULSE: Add directly to velocity!
    
    def draw(self, surface: pygame.Surface, camera: Camera, particles: ParticleSystem):
        """Draw the tank - OPTIMIZED."""
        if not self.alive:
            return
        
        pos = camera.apply((self.x, self.y))
        
        # OPTIMIZED: Simple glow circle (no surface creation)
        glow_color = tuple(max(0, c - 180) for c in self.color)
        pygame.draw.circle(surface, glow_color, pos, TANK_SIZE)
        
        # OPTIMIZED: Cache rotated surface
        rounded_angle = round(self.angle / 5) * 5  # Round to 5 degrees
        if self._last_angle != rounded_angle:
            self._rotated_surface = pygame.transform.rotate(self._base_surface, -rounded_angle)
            self._last_angle = rounded_angle
        
        rect = self._rotated_surface.get_rect(center=pos)
        surface.blit(self._rotated_surface, rect)
        
        # Barrel
        barrel_end_x = pos[0] + math.cos(math.radians(self.angle)) * (TANK_SIZE / 2 + 10)
        barrel_end_y = pos[1] + math.sin(math.radians(self.angle)) * (TANK_SIZE / 2 + 10)
        pygame.draw.line(surface, self.color, pos, (int(barrel_end_x), int(barrel_end_y)), 6)
        pygame.draw.line(surface, (255, 255, 255), pos, (int(barrel_end_x), int(barrel_end_y)), 2)
        
        # Muzzle flash - OPTIMIZED: simple circle
        if self.muzzle_flash_timer > 0:
            pygame.draw.circle(surface, (255, 255, 200), (int(barrel_end_x), int(barrel_end_y)), MUZZLE_FLASH_SIZE // 2)
        
        # Health bar (always show)
        bar_width = TANK_SIZE
        bar_height = 6
        bar_x = pos[0] - bar_width // 2
        bar_y = pos[1] - TANK_SIZE // 2 - 15
        
        max_hp = getattr(self, 'max_health', TANK_MAX_HEALTH)
        pygame.draw.rect(surface, COLOR_HEALTH_BG, (bar_x, bar_y, bar_width, bar_height))
        health_width = int(bar_width * (self.health / max_hp))
        health_color = COLOR_HEALTH_BAR if self.health > (max_hp * 0.3) else COLOR_DANGER
        pygame.draw.rect(surface, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Jam indicator - cache font
        if self.is_jammed:
            # Use a simple rect indicator instead of text (text is expensive)
            pygame.draw.rect(surface, COLOR_DANGER, (pos[0] - 15, pos[1] + TANK_SIZE // 2 + 5, 30, 5))
        
        # Team name label below tank
        if hasattr(self, 'team_name') and self.team_name:
            font = pygame.font.Font(None, 20)
            name_surface = font.render(self.team_name, True, (200, 200, 200))
            name_rect = name_surface.get_rect(center=(pos[0], pos[1] + TANK_SIZE // 2 + 18))
            surface.blit(name_surface, name_rect)
    
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle."""
        return pygame.Rect(self.x - TANK_SIZE // 2, self.y - TANK_SIZE // 2, 
                          TANK_SIZE, TANK_SIZE)
    
    def get_context(self) -> Dict:
        """Get context data for bot (read-only copy)."""
        return {
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
            "health": self.health,
            "ammo": self.ammo,
            "coins": self.coins
        }

# =============================================================================
# COIN (OPTIMIZED)
# =============================================================================

class Coin:
    """Collectible coin for The Scramble mode."""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.collected = False
        self.pulse_phase = random.uniform(0, 2 * math.pi)
    
    def update(self, dt: float):
        """Update coin animation."""
        self.pulse_phase += COIN_GLOW_SPEED
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Draw coin - OPTIMIZED: direct drawing."""
        if self.collected:
            return
        
        pos = camera.apply((self.x, self.y))
        
        # Pulsing glow - simple circles
        pulse = abs(math.sin(self.pulse_phase))
        glow_size = int(COIN_SIZE // 2 + pulse * 5)
        
        # Outer glow (darker gold)
        pygame.draw.circle(surface, (180, 150, 0), pos, glow_size)
        
        # Coin core
        pygame.draw.circle(surface, COLOR_GOLD, pos, COIN_SIZE // 2)
        pygame.draw.circle(surface, (255, 255, 200), pos, COIN_SIZE // 4)
    
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle."""
        return pygame.Rect(self.x - COIN_SIZE // 2, self.y - COIN_SIZE // 2, 
                          COIN_SIZE, COIN_SIZE)

# =============================================================================
# WALL (OPTIMIZED)
# =============================================================================

class Wall:
    """Indestructible wall for maze mode."""
    
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Draw wall - OPTIMIZED: direct drawing."""
        pos = camera.apply((self.x, self.y))
        
        # Wall (no glow surface - direct draw)
        pygame.draw.rect(surface, WALL_GLOW_COLOR, (pos[0] - 3, pos[1] - 3, self.width + 6, self.height + 6))
        pygame.draw.rect(surface, WALL_COLOR, (pos[0], pos[1], self.width, self.height))
        pygame.draw.rect(surface, (255, 255, 255), (pos[0], pos[1], self.width, self.height), 2)
    
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_context(self) -> Dict:
        """Get context data for bot."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }

# =============================================================================
# ZONE (OPTIMIZED)
# =============================================================================

class Zone:
    """Shrinking damage zone for The Labyrinth mode."""
    
    def __init__(self):
        self.margin = 0
        self.shrink_timer = 0.0
        self.target_margin = 0
        self._zone_surface = None
        self._last_margin = -1
    
    def update(self, dt: float):
        """Update zone shrinking."""
        self.shrink_timer += dt
        
        if self.shrink_timer >= LABYRINTH_ZONE_SHRINK_INTERVAL:
            self.shrink_timer = 0
            self.target_margin += GRID_CELL_SIZE
        
        # Smooth shrink animation
        if self.margin < self.target_margin:
            self.margin = lerp(self.margin, self.target_margin, 0.02)
    
    def is_in_danger(self, x: float, y: float) -> bool:
        """Check if position is in the danger zone."""
        return (x < self.margin or x > SCREEN_WIDTH - self.margin or
                y < self.margin or y > SCREEN_HEIGHT - self.margin)
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Draw the danger zone - OPTIMIZED."""
        if self.margin <= 0:
            return
        
        margin = int(self.margin)
        
        # OPTIMIZED: Draw danger zone as rectangles directly (no surface)
        danger_color = (150, 0, 0)
        
        # Draw the 4 edge rectangles
        pygame.draw.rect(surface, danger_color, (0, 0, SCREEN_WIDTH, margin))  # Top
        pygame.draw.rect(surface, danger_color, (0, SCREEN_HEIGHT - margin, SCREEN_WIDTH, margin))  # Bottom
        pygame.draw.rect(surface, danger_color, (0, 0, margin, SCREEN_HEIGHT))  # Left
        pygame.draw.rect(surface, danger_color, (SCREEN_WIDTH - margin, 0, margin, SCREEN_HEIGHT))  # Right
        
        # Warning line
        pygame.draw.rect(surface, COLOR_DANGER, (margin, margin, 
                        SCREEN_WIDTH - 2 * margin, SCREEN_HEIGHT - 2 * margin), 3)

# =============================================================================
# LASER (OPTIMIZED)
# =============================================================================

class Laser:
    """Sudden death laser for The Duel mode."""
    
    def __init__(self):
        self.active = False
        self.x = 0
        self.direction = 1  # 1 = left to right, -1 = right to left
    
    def activate(self):
        """Start the laser sweep."""
        self.active = True
        self.direction = random.choice([-1, 1])
        self.x = 0 if self.direction == 1 else SCREEN_WIDTH
    
    def update(self, dt: float):
        """Update laser position."""
        if not self.active:
            return
        
        self.x += DUEL_LASER_SPEED * self.direction
    
    def check_hit(self, tank: Tank) -> bool:
        """Check if laser hits a tank."""
        if not self.active:
            return False
        
        # Laser is a vertical line
        if self.direction == 1:
            return tank.x < self.x
        else:
            return tank.x > self.x
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Draw the laser beam - OPTIMIZED."""
        if not self.active:
            return
        
        laser_x = int(self.x)
        
        # OPTIMIZED: Simple lines instead of surfaces
        pygame.draw.line(surface, (100, 0, 0), (laser_x - 10, 0), (laser_x - 10, SCREEN_HEIGHT), 8)
        pygame.draw.line(surface, (200, 0, 0), (laser_x - 3, 0), (laser_x - 3, SCREEN_HEIGHT), 4)
        pygame.draw.line(surface, (255, 255, 255), (laser_x, 0), (laser_x, SCREEN_HEIGHT), 2)
        pygame.draw.line(surface, (200, 0, 0), (laser_x + 3, 0), (laser_x + 3, SCREEN_HEIGHT), 4)
        pygame.draw.line(surface, (100, 0, 0), (laser_x + 10, 0), (laser_x + 10, SCREEN_HEIGHT), 8)

# =============================================================================
# DANGER ZONE (Orbital Strike - Mode 2)
# =============================================================================

class DangerZone:
    """
    Orbital Strike danger zone for Labyrinth mode.
    Phases: WARNING (pulsing red) -> ACTIVE (explosions) -> DESPAWN
    """
    
    # Phase constants
    PHASE_WARNING = 0
    PHASE_ACTIVE = 1
    PHASE_DEAD = 2
    
    def __init__(self, x: float, y: float, particles: ParticleSystem):
        self.x = x
        self.y = y
        self.radius = DANGER_ZONE_RADIUS
        self.particles = particles
        
        # Timing
        self.phase = self.PHASE_WARNING
        self.timer = 0.0
        self.blast_timer = 0.0
        
        # Visual
        self.pulse_time = 0.0
        
        # Pre-render warning circle surface (with alpha)
        self.warning_surface = pygame.Surface((self.radius * 2 + 20, self.radius * 2 + 20), pygame.SRCALPHA)
        self.active_surface = pygame.Surface((self.radius * 2 + 20, self.radius * 2 + 20), pygame.SRCALPHA)
        
        # Play siren sound on spawn
        play_sound(SFX_COIN)  # Use coin sound as placeholder for siren
    
    def update(self, dt: float) -> bool:
        """Update the danger zone. Returns False when zone should be removed."""
        self.timer += dt
        self.pulse_time += dt * 8  # Faster pulsing
        
        if self.phase == self.PHASE_WARNING:
            if self.timer >= DANGER_ZONE_WARNING_DURATION:
                self.phase = self.PHASE_ACTIVE
                self.timer = 0.0
                self.blast_timer = 0.0
        
        elif self.phase == self.PHASE_ACTIVE:
            # Spawn explosion particles periodically
            self.blast_timer += dt
            if self.blast_timer >= DANGER_ZONE_BLAST_INTERVAL:
                self.blast_timer = 0.0
                self._spawn_blast()
            
            if self.timer >= DANGER_ZONE_ACTIVE_DURATION:
                self.phase = self.PHASE_DEAD
                return False
        
        return True
    
    def _spawn_blast(self):
        """Spawn explosion particles at random point inside zone."""
        # Random point inside circle
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(0, self.radius * 0.8)
        blast_x = self.x + math.cos(angle) * dist
        blast_y = self.y + math.sin(angle) * dist
        
        # Spawn particles
        self.particles.spawn_explosion(blast_x, blast_y, (255, 100, 50))
        play_sound(SFX_DEATH, VOL_DEATH)
    
    def check_hit(self, tank) -> bool:
        """Check if tank is inside active zone."""
        if self.phase != self.PHASE_ACTIVE:
            return False
        
        dist = distance(self.x, self.y, tank.x, tank.y)
        return dist < self.radius
    
    def apply_damage(self, tank):
        """Apply damage and knockback to tank in zone."""
        if not self.check_hit(tank):
            return
        
        # Damage
        tank.take_damage(DANGER_ZONE_DAMAGE)
        
        # Knockback away from center
        angle = angle_to(self.x, self.y, tank.x, tank.y)
        tank.apply_knockback(angle, DANGER_ZONE_KNOCKBACK)
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Draw the danger zone with visual effects."""
        pos = camera.apply((self.x, self.y))
        center = (self.radius + 10, self.radius + 10)
        
        if self.phase == self.PHASE_WARNING:
            # Pulsing warning circle
            pulse = (math.sin(self.pulse_time) + 1) / 2  # 0 to 1
            alpha = int(50 + pulse * 100)  # 50 to 150
            
            self.warning_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(self.warning_surface, (255, 50, 50, alpha), center, self.radius)
            pygame.draw.circle(self.warning_surface, (255, 100, 100, alpha + 50), center, self.radius, 4)
            
            # Draw "X" crosshair
            cross_alpha = int(100 + pulse * 100)
            pygame.draw.line(self.warning_surface, (255, 0, 0, cross_alpha), 
                           (center[0] - self.radius, center[1]), 
                           (center[0] + self.radius, center[1]), 2)
            pygame.draw.line(self.warning_surface, (255, 0, 0, cross_alpha), 
                           (center[0], center[1] - self.radius), 
                           (center[0], center[1] + self.radius), 2)
            
            blit_pos = (pos[0] - self.radius - 10, pos[1] - self.radius - 10)
            surface.blit(self.warning_surface, blit_pos)
        
        elif self.phase == self.PHASE_ACTIVE:
            # Flashing active zone
            flash = (math.sin(self.pulse_time * 3) + 1) / 2
            alpha = int(100 + flash * 80)
            
            self.active_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(self.active_surface, (255, 150 + int(flash * 100), 150, alpha), center, self.radius)
            pygame.draw.circle(self.active_surface, (255, 255, 255, alpha), center, self.radius, 3)
            
            blit_pos = (pos[0] - self.radius - 10, pos[1] - self.radius - 10)
            surface.blit(self.active_surface, blit_pos)

# =============================================================================
# JUGGERNAUT (Boss - Mode 3)
# =============================================================================

class Juggernaut:
    """
    The Juggernaut - A massive AI-controlled boss that attacks all players.
    Features:
    - Spinning saw-blade visual (3x tank size)
    - Creeps toward nearest player
    - Melee contact = rapid damage + massive knockback
    - Burst Cannon: Idle -> Charge (glow) -> 5-shot burst
    """
    
    # Weapon phases
    PHASE_IDLE = 0
    PHASE_CHARGE = 1
    PHASE_BURST = 2
    
    def __init__(self, x: float, y: float, particles: ParticleSystem):
        self.x = x
        self.y = y
        self.radius = JUGGERNAUT_SIZE // 2
        self.particles = particles
        
        # Movement
        self.vel = pygame.math.Vector2(0, 0)
        
        # Visual rotation (spinning saw-blade effect)
        self.rotation = 0.0
        
        # Weapon state
        self.weapon_phase = self.PHASE_IDLE
        self.weapon_timer = 0.0
        self.burst_count = 0
        self.burst_cooldown = 0.0
        self.target_angle = 0.0  # Turret tracking angle
        self.target_tank = None  # Current target
        
        # Pre-render saw-blade surface
        self._create_surfaces()
    
    def _create_surfaces(self):
        """Pre-render the saw-blade body surface."""
        size = JUGGERNAUT_SIZE + 20
        self.body_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        
        # Outer glow
        pygame.draw.circle(self.body_surface, (*JUGGERNAUT_COLOR, 80), (center, center), self.radius + 10)
        
        # Main body
        pygame.draw.circle(self.body_surface, JUGGERNAUT_COLOR, (center, center), self.radius)
        
        # Saw-blade teeth (8 triangular notches)
        for i in range(8):
            angle = i * (math.pi / 4)
            # Outer point
            ox = center + math.cos(angle) * (self.radius + 15)
            oy = center + math.sin(angle) * (self.radius + 15)
            # Inner points
            a1 = angle - 0.2
            a2 = angle + 0.2
            ix1 = center + math.cos(a1) * (self.radius - 5)
            iy1 = center + math.sin(a1) * (self.radius - 5)
            ix2 = center + math.cos(a2) * (self.radius - 5)
            iy2 = center + math.sin(a2) * (self.radius - 5)
            pygame.draw.polygon(self.body_surface, JUGGERNAUT_BLADE_COLOR, [(ox, oy), (ix1, iy1), (ix2, iy2)])
        
        # Inner ring
        pygame.draw.circle(self.body_surface, (100, 30, 30), (center, center), self.radius // 2)
        pygame.draw.circle(self.body_surface, (60, 15, 15), (center, center), self.radius // 3)
    
    def find_nearest_target(self, tanks: List) -> Optional[any]:
        """Find the nearest alive player tank."""
        nearest = None
        min_dist = float('inf')
        
        for tank in tanks:
            if tank.alive:
                dist = distance(self.x, self.y, tank.x, tank.y)
                if dist < min_dist:
                    min_dist = dist
                    nearest = tank
        
        return nearest
    
    def update(self, dt: float, tanks: List, bullets: List):
        """Update Juggernaut movement, AI, and weapon."""
        # Spin the saw-blade
        self.rotation += JUGGERNAUT_ROTATION_SPEED * dt
        
        # Store ALL alive tanks for omni-burst
        self.all_targets = [t for t in tanks if t.alive]
        
        # Find nearest target for movement
        self.target_tank = self.find_nearest_target(tanks)
        
        if self.target_tank:
            # Move toward target (slow creep)
            dx = self.target_tank.x - self.x
            dy = self.target_tank.y - self.y
            dist = max((dx*dx + dy*dy)**0.5, 1)
            
            # Normalize and apply speed
            self.vel.x = (dx / dist) * JUGGERNAUT_SPEED * dt
            self.vel.y = (dy / dist) * JUGGERNAUT_SPEED * dt
            
            self.x += self.vel.x
            self.y += self.vel.y
            
            # Update turret tracking angle (for visual)
            self.target_angle = math.degrees(math.atan2(dy, dx))
        
        # Keep in bounds
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))
        
        # Weapon state machine
        self._update_weapon(dt, bullets)
    
    def _update_weapon(self, dt: float, bullets: List):
        """Update burst cannon state machine."""
        self.weapon_timer += dt
        
        if self.weapon_phase == self.PHASE_IDLE:
            if self.weapon_timer >= JUGGERNAUT_IDLE_TIME:
                self.weapon_phase = self.PHASE_CHARGE
                self.weapon_timer = 0.0
        
        elif self.weapon_phase == self.PHASE_CHARGE:
            if self.weapon_timer >= JUGGERNAUT_CHARGE_TIME:
                self.weapon_phase = self.PHASE_BURST
                self.weapon_timer = 0.0
                self.burst_count = 0
                self.burst_cooldown = 0.0
        
        elif self.weapon_phase == self.PHASE_BURST:
            self.burst_cooldown -= dt
            
            if self.burst_cooldown <= 0 and self.burst_count < JUGGERNAUT_BURST_COUNT:
                # OMNI-BURST: Fire at ALL alive tanks simultaneously!
                self._fire_omni_burst(bullets)
                self.burst_count += 1
                self.burst_cooldown = JUGGERNAUT_BURST_INTERVAL
            
            if self.burst_count >= JUGGERNAUT_BURST_COUNT:
                self.weapon_phase = self.PHASE_IDLE
                self.weapon_timer = 0.0
    
    def _fire_omni_burst(self, bullets: List):
        """Fire heavy bullets at ALL alive tanks simultaneously."""
        if not self.all_targets:
            return
        
        for target in self.all_targets:
            # Calculate angle to this specific target
            dx = target.x - self.x
            dy = target.y - self.y
            target_angle = math.degrees(math.atan2(dy, dx))
            angle_rad = math.radians(target_angle)
            
            # Spawn bullet at turret position toward this target
            bx = self.x + math.cos(angle_rad) * (self.radius + 10)
            by = self.y + math.sin(angle_rad) * (self.radius + 10)
            
            # Create bullet
            bullet = Bullet(bx, by, target_angle, -1, (255, 100, 100))
            
            # Override with Juggernaut's heavy bullet stats
            bullet.vx = math.cos(angle_rad) * JUGGERNAUT_BULLET_SPEED
            bullet.vy = math.sin(angle_rad) * JUGGERNAUT_BULLET_SPEED
            bullet.damage = JUGGERNAUT_BULLET_DAMAGE
            bullet.is_critical = False
            
            bullets.append(bullet)
            
            # Muzzle flash for each bullet
            self.particles.spawn_muzzle_flash(bx, by, target_angle, (255, 150, 100))
        
        # Single sound for the burst
        play_sound(SFX_SHOOT, VOL_SHOOT)
    
    def check_melee(self, tank) -> bool:
        """Check if tank is touching the Juggernaut."""
        dist = distance(self.x, self.y, tank.x, tank.y)
        return dist < self.radius + TANK_SIZE // 2
    
    def apply_melee_damage(self, tank):
        """Apply contact damage and knockback to tank."""
        if not self.check_melee(tank):
            return
        
        # Damage (per frame, called every update)
        tank.take_damage(JUGGERNAUT_MELEE_DAMAGE)
        
        # CRITICAL: Knockback to push tank OUT (prevents getting stuck inside boss)
        angle = angle_to(self.x, self.y, tank.x, tank.y)
        tank.apply_knockback(angle, JUGGERNAUT_MELEE_KNOCKBACK)
    
    def draw(self, surface: pygame.Surface, camera: Camera):
        """Draw the Juggernaut with spinning effect."""
        pos = camera.apply((self.x, self.y))
        
        # Rotate and blit body
        rotated_body = pygame.transform.rotate(self.body_surface, -self.rotation)
        body_rect = rotated_body.get_rect(center=pos)
        surface.blit(rotated_body, body_rect)
        
        # Draw turret on top
        turret_len = JUGGERNAUT_TURRET_SIZE
        angle_rad = math.radians(self.target_angle)
        tx = pos[0] + math.cos(angle_rad) * turret_len
        ty = pos[1] + math.sin(angle_rad) * turret_len
        
        # Turret color changes during charge/burst
        if self.weapon_phase == self.PHASE_CHARGE:
            # Flashing warning glow
            flash = abs(math.sin(self.weapon_timer * 10))
            turret_color = (255, int(100 + flash * 155), int(flash * 100))
        elif self.weapon_phase == self.PHASE_BURST:
            turret_color = (255, 255, 200)  # Bright during firing
        else:
            turret_color = (150, 50, 50)
        
        pygame.draw.line(surface, turret_color, pos, (tx, ty), 8)
        pygame.draw.circle(surface, turret_color, (int(tx), int(ty)), 6)
    
    def get_context_data(self) -> Dict:
        """Return data for bot context."""
        return {
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "weapon_phase": self.weapon_phase,
            "target_angle": self.target_angle
        }

# =============================================================================
# BOT LOADER (Sandboxed Execution)
# =============================================================================


class BotLoader:
    """Safely loads and executes student bot scripts."""
    
    def __init__(self, bot_path: str):
        self.bot_path = bot_path
        self.bot_name = os.path.basename(bot_path)
        self.update_func: Optional[Callable] = None
        self.error_message: Optional[str] = None
        self.error_logged = False  # Prevent spam - log each error once
        self.load_bot()
    
    def _log_error(self, error_type: str, error: Exception, show_traceback: bool = True):
        """Print error to terminal with formatting."""
        if self.error_logged:
            return  # Don't spam the same error
        
        import traceback
        print(f"\n{'='*60}")
        print(f"🚨 BOT ERROR: {self.bot_name}")
        print(f"{'='*60}")
        print(f"Error Type: {error_type}")
        print(f"Message: {str(error)}")
        if show_traceback:
            print(f"\nTraceback:")
            traceback.print_exc()
        print(f"{'='*60}\n")
        self.error_logged = True
    
    def load_bot(self):
        """Load the bot module."""
        try:
            spec = importlib.util.spec_from_file_location("bot", self.bot_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'update'):
                    self.update_func = module.update
                    print(f"✅ Loaded bot: {self.bot_name}")
                else:
                    self.error_message = "Bot missing update() function"
                    print(f"⚠️  {self.bot_name}: Missing update() function!")
        except Exception as e:
            self.error_message = f"Bot load error: {str(e)}"
            self._log_error("LOAD ERROR", e)
    
    def execute(self, context: Dict) -> Tuple[Optional[str], Optional[any]]:
        """Execute bot update with timeout and error handling."""
        if not self.update_func:
            return None, None
        
        # Pass a DEEP COPY to prevent cheating
        safe_context = copy.deepcopy(context)
        
        try:
            start_time = time.time()
            result = self.update_func(safe_context)
            elapsed_ms = (time.time() - start_time) * 1000
            
            if elapsed_ms > BOT_TIMEOUT_MS:
                return "LAG", None
            
            if isinstance(result, tuple) and len(result) == 2:
                action, param = result
                if action in ["MOVE", "SHOOT", "STOP", "MOVE_AND_SHOOT"]:
                    return action, param
            
            return None, None
            
        except Exception as e:
            self.error_message = f"Bot error: {str(e)}"
            self._log_error("RUNTIME ERROR", e)
            return None, None

# =============================================================================
# GAME ENGINE
# =============================================================================

class GitWarsEngine:
    """Main game engine."""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        
        self.camera = Camera()
        self.particles = ParticleSystem()
        
        self.tanks: List[Tank] = []
        self.bullets: List[Bullet] = []
        self.coins: List[Coin] = []
        self.walls: List[Wall] = []
        self.bots: Dict[int, BotLoader] = {}
        
        self.zone = Zone()
        self.juggernaut = None  # Spawned in Mode 3
        
        # Danger Zones (Orbital Strikes - Mode 2)
        self.danger_zones: List[DangerZone] = []
        self.danger_zone_timer = 0.0
        
        self.game_mode = GAME_MODE
        self.game_timer = 0.0
        self.coin_spawn_timer = 0.0
        self.running = True
        self.game_over = False
        self.winner_text = ""
        
        # Kill feed for Level 2 death messages
        self.kill_feed = []  # List of {"text": str, "timer": float, "alpha": int}
        
        # Fonts - pre-load once
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        
        # Pre-render static text
        self._mode_titles = {
            1: self.font_medium.render("THE SCRAMBLE", True, COLOR_TEXT),
            2: self.font_medium.render("THE LABYRINTH", True, COLOR_TEXT),
            3: self.font_medium.render("THE JUGGERNAUT", True, COLOR_TEXT)
        }
        
        # Initialize game
        self.setup_game()
    
    def setup_game(self):
        """Set up game based on current mode."""
        self.tanks.clear()
        self.bullets.clear()
        self.coins.clear()
        self.walls.clear()
        self.bots.clear()
        self.particles.particles.clear()  # Clear particles too
        self.last_top5 = []  # Track top 5 ranking for coin sound on rank change
        
        # Spawn tanks in circle
        num_tanks = BOT_DEFAULT_COUNT if self.game_mode != 3 else 2
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        radius = min(SCREEN_WIDTH, SCREEN_HEIGHT) // 3
        
        # Scan bots folder for all bot_*.py files
        import glob
        bots_dir = os.path.join(os.path.dirname(__file__), "bots")
        bot_files = sorted(glob.glob(os.path.join(bots_dir, "bot_*.py")))
        
        # Extract team names from filenames (bot_teamname.py -> teamname)
        bot_info = []
        for bot_file in bot_files:
            filename = os.path.basename(bot_file)
            team_name = filename[4:-3]  # Remove "bot_" prefix and ".py" suffix
            bot_info.append((bot_file, team_name))
        
        # Fallback to my_bot.py if not enough bots
        default_bot_path = os.path.join(bots_dir, "my_bot.py")
        
        for i in range(num_tanks):
            angle = (2 * math.pi * i) / num_tanks
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius
            color = TANK_COLORS[i % len(TANK_COLORS)]
            
            tank = Tank(i, x, y, color)
            tank.angle = math.degrees(math.atan2(center_y - y, center_x - x))
            
            # Apply Level 3 health multiplier
            if self.game_mode == 3:
                new_health = int(TANK_MAX_HEALTH * LEVEL3_HEALTH_MULTIPLIER)
                tank.health = new_health
                tank.max_health = new_health
            
            # Load bot and assign team name
            if i < len(bot_info):
                bot_path, team_name = bot_info[i]
                tank.team_name = team_name
                self.bots[i] = BotLoader(bot_path)
            elif os.path.exists(default_bot_path):
                tank.team_name = f"Bot_{i}"
                self.bots[i] = BotLoader(default_bot_path)
            
            self.tanks.append(tank)
        
        # Mode-specific setup
        if self.game_mode == 2:
            self.generate_maze()
            self.zone = Zone()  # Reset zone
        
        # Reset timers
        if self.game_mode == 1:
            self.game_timer = SCRAMBLE_DURATION
        elif self.game_mode == 2:
            self.danger_zones = []  # Reset danger zones
            self.danger_zone_timer = 0.0
        elif self.game_mode == 3:
            self.juggernaut = Juggernaut(
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                self.particles
            )
            
        # Play Level-Specific BGM
        try:
            bgm_file = f"bgm{self.game_mode}.mp3"
            path = os.path.join(ASSETS_DIR, bgm_file)
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(MUSIC_VOLUME)
                pygame.mixer.music.play(-1)
            else:
                # Fallback to generic "bgm.mp3" if specific level music missing
                default_path = os.path.join(ASSETS_DIR, "bgm.mp3")
                if os.path.exists(default_path):
                    pygame.mixer.music.load(default_path)
                    pygame.mixer.music.set_volume(MUSIC_VOLUME)
                    pygame.mixer.music.play(-1)
        except:
            pass
            
        # Play Start Sound (on reserved channel so it won't get cut off)
        play_critical_sound(SFX_READY, VOL_READY)
    
    def generate_maze(self):
        """Generate walls for labyrinth mode."""
        # Simple symmetrical maze
        wall_positions = [
            (200, 150, 20, 200),
            (SCREEN_WIDTH - 220, 150, 20, 200),
            (200, SCREEN_HEIGHT - 350, 20, 200),
            (SCREEN_WIDTH - 220, SCREEN_HEIGHT - 350, 20, 200),
            (400, 300, 200, 20),
            (SCREEN_WIDTH - 600, 300, 200, 20),
            (400, SCREEN_HEIGHT - 320, 200, 20),
            (SCREEN_WIDTH - 600, SCREEN_HEIGHT - 320, 200, 20),
            (SCREEN_WIDTH // 2 - 10, 100, 20, 150),
            (SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT - 250, 20, 150),
        ]
        
        for x, y, w, h in wall_positions:
            self.walls.append(Wall(x, y, w, h))
    
    def spawn_coin(self):
        """Spawn a new coin at random position."""
        if len(self.coins) >= SCRAMBLE_MAX_COINS:
            return
        
        # Avoid spawning on tanks
        for _ in range(10):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(50, SCREEN_HEIGHT - 50)
            
            valid = True
            for tank in self.tanks:
                if distance(x, y, tank.x, tank.y) < TANK_SIZE * 2:
                    valid = False
                    break
            
            if valid:
                self.coins.append(Coin(x, y))
                break
    
    def spawn_danger_zone(self):
        """Spawn a new danger zone (Orbital Strike) at random position."""
        # Ensure zone is fully on screen
        margin = DANGER_ZONE_RADIUS + 50
        x = random.randint(margin, SCREEN_WIDTH - margin)
        y = random.randint(margin, SCREEN_HEIGHT - margin)
        
        self.danger_zones.append(DangerZone(x, y, self.particles))
    
    def build_context(self, tank: Tank) -> Dict:
        """Build the context dictionary for a tank's bot."""
        enemies = []
        for other in self.tanks:
            if other.id != tank.id and other.alive:
                enemies.append({
                    "x": other.x,
                    "y": other.y,
                    "id": other.id
                })
        
        coin_data = []
        if self.game_mode == 1:
            for coin in self.coins:
                if not coin.collected:
                    coin_data.append({"x": coin.x, "y": coin.y})
        
        wall_data = [wall.get_context() for wall in self.walls]
        
        bullet_data = []
        for bullet in self.bullets:
            if bullet.owner_id != tank.id:
                bullet_data.append({
                    "x": bullet.x,
                    "y": bullet.y,
                    "vx": bullet.vx,
                    "vy": bullet.vy
                })
        
        # Get sensor readings for obstacle avoidance
        sensor_readings = get_sensor_readings(tank.x, tank.y, tank.angle, self.walls)
        
        return {
            "me": tank.get_context(),
            "enemies": enemies,
            "coins": coin_data,
            "walls": wall_data,
            "bullets": bullet_data,
            "sensors": sensor_readings,  # NEW: Raycast sensors for wall detection
            "juggernaut": self.juggernaut.get_context_data() if self.juggernaut and self.game_mode == 3 else None,
            "game_mode": self.game_mode,
            "time_left": self.game_timer
        }
    
    def process_bot_action(self, tank: Tank, action: str, param: any):
        """Process a bot's action."""
        if action == "MOVE" and param:
            try:
                dx, dy = param
                tank.move(float(dx), float(dy))
            except:
                pass
        
        elif action == "SHOOT" and param is not None:
            try:
                angle = float(param)
                bullet = tank.shoot(angle)
                if bullet:
                    self.bullets.append(bullet)
                    self.particles.spawn_muzzle_flash(bullet.x, bullet.y, angle, tank.color)
                    self.particles.spawn_muzzle_flash(bullet.x, bullet.y, angle, tank.color)
                    play_sound(SFX_SHOOT, VOL_SHOOT)  # Shoot SFX
            except:
                pass
        
        elif action == "STOP":
            tank.velocity.x = 0
            tank.velocity.y = 0
        
        elif action == "MOVE_AND_SHOOT" and param is not None:
            # Strafing: Move AND shoot in the same frame!
            try:
                move_dir, shoot_angle = param
                
                # Apply movement
                if move_dir:
                    dx, dy = move_dir
                    tank.move(float(dx), float(dy))
                
                # Fire bullet
                if shoot_angle is not None:
                    bullet = tank.shoot(float(shoot_angle))
                    if bullet:
                        self.bullets.append(bullet)
                        self.particles.spawn_muzzle_flash(bullet.x, bullet.y, float(shoot_angle), tank.color)
                        self.particles.spawn_muzzle_flash(bullet.x, bullet.y, float(shoot_angle), tank.color)
                        play_sound(SFX_SHOOT, VOL_SHOOT)
            except:
                pass
    
    def update(self, dt: float):
        """Update game state."""
        if self.game_over:
            return
        
        # Update camera
        self.camera.update(dt)
        
        # Update particles
        self.particles.update()
        
        # Update kill feed timers (fade out over time)
        if self.game_mode == 2:
            for msg in self.kill_feed:
                msg["timer"] -= dt
                # Fade alpha as timer approaches 0
                if msg["timer"] < 1.0:
                    msg["alpha"] = int(255 * msg["timer"])
            # Remove expired messages
            self.kill_feed = [m for m in self.kill_feed if m["timer"] > 0]
        
        # =====================================================================
        # PHYSICS LOOP REORDERING (Bullets/Collisions FIRST, then Tanks)
        # =====================================================================
        
        # 1. Update Bullets & Resolve Collisions (Apply Forces)
        for bullet in self.bullets:
            bullet.update()
            
            # Wall collision
            bullet_rect = bullet.get_rect()
            for wall in self.walls:
                if bullet_rect.colliderect(wall.get_rect()):
                    bullet.alive = False
                    break
            
            # Tank collision
            for tank in self.tanks:
                if tank.alive and tank.id != bullet.owner_id:
                    if bullet_rect.colliderect(tank.get_rect()):
                        bullet.alive = False
                        
                        if self.game_mode == 1:
                            # Knockback only
                            angle = angle_to(bullet.x, bullet.y, tank.x, tank.y)
                            tank.apply_knockback(angle, SCRAMBLE_KNOCKBACK)
                        else:
                            # Damage
                            tank.take_damage(bullet.damage)
                            if not tank.alive:
                                self.on_tank_death(tank)
                        break
        
        # Remove dead bullets
        self.bullets = [b for b in self.bullets if b.alive]
        
        # 2. Execute Bot Logic (Apply Input Forces BEFORE physics update)
        for tank in self.tanks:
            if tank.alive and tank.id in self.bots:
                context = self.build_context(tank)
                action, param = self.bots[tank.id].execute(context)
                tank.last_action = action
                if action and action != "LAG":
                    self.process_bot_action(tank, action, param)
        
        # 3. Update Tanks (Integrate Physics - AFTER all forces applied)
        for tank in self.tanks:
            if tank.alive:
                tank.update(dt, self.walls)
                
                # Zone damage (Mode 2)
                if self.game_mode == 2 and self.zone.is_in_danger(tank.x, tank.y):
                    tank.take_damage(LABYRINTH_ZONE_DAMAGE * dt)
                    if not tank.alive:
                        self.on_tank_death(tank)
                
        # Update timers
        if self.game_mode == 1:
            self.game_timer -= dt
            self.coin_spawn_timer += dt
            
            if self.coin_spawn_timer >= SCRAMBLE_COIN_SPAWN_INTERVAL:
                self.coin_spawn_timer = 0
                self.spawn_coin()
            
            if self.game_timer <= 0:
                self.end_scramble()
        
        elif self.game_mode == 2:
            self.zone.update(dt)
            
            # Danger Zone spawning (Orbital Strikes)
            self.danger_zone_timer += dt
            if self.danger_zone_timer >= DANGER_ZONE_SPAWN_INTERVAL:
                self.danger_zone_timer = 0.0
                self.spawn_danger_zone()
            
            # Update danger zones
            for dz in self.danger_zones[:]:
                if not dz.update(dt):
                    self.danger_zones.remove(dz)
                else:
                    # Apply damage to tanks inside active zones
                    for tank in self.tanks:
                        if tank.alive:
                            dz.apply_damage(tank)
                            if not tank.alive:
                                self.on_tank_death(tank)
            
            alive_count = sum(1 for t in self.tanks if t.alive)
            if alive_count <= LABYRINTH_FINAL_SURVIVORS:
                self.end_labyrinth()
        
        elif self.game_mode == 3:
            # Update Juggernaut (movement, AI, weapon)
            if self.juggernaut:
                self.juggernaut.update(dt, self.tanks, self.bullets)
                
                # Apply melee damage to ALL tanks touching Juggernaut
                for tank in self.tanks:
                    if tank.alive:
                        self.juggernaut.apply_melee_damage(tank)
                        if not tank.alive:
                            self.on_tank_death(tank)

        # (Bullets updated earlier)
        
        # Coin collection (Mode 1)
        if self.game_mode == 1:
            for coin in self.coins:
                if coin.collected:
                    continue
                coin.update(dt)
                
                for tank in self.tanks:
                    if tank.alive and coin.get_rect().colliderect(tank.get_rect()):
                        coin.collected = True
                        tank.coins += COIN_VALUE
                        break
            
            self.coins = [c for c in self.coins if not c.collected]
            
            # Check if top 5 ranking changed - play coin sound only on rank change
            sorted_tanks = sorted(self.tanks, key=lambda t: t.coins, reverse=True)
            current_top5 = [t.id for t in sorted_tanks[:5]]
            if current_top5 != self.last_top5:
                play_sound(SFX_COIN, VOL_COIN)  # Ranking changed!
                self.last_top5 = current_top5
        
        # Check game end (Mode 3)
        if self.game_mode == 3:
            alive_tanks = [t for t in self.tanks if t.alive]
            if len(alive_tanks) <= 1:
                self.end_duel(alive_tanks[0] if alive_tanks else None)
    
    def on_tank_death(self, tank: Tank):
        """Handle tank death effects."""
        # Explosion particles
        self.particles.spawn_explosion(tank.x, tank.y, tank.color)
        
        # Screen shake
        self.camera.shake()
        
        # Explosion SFX
        play_sound(SFX_DEATH, VOL_DEATH)
        
        # Add kill feed message for Level 2
        if self.game_mode == 2:
            team_name = getattr(tank, 'team_name', f'Tank_{tank.id}')
            self.kill_feed.append({
                "text": f"{team_name} ELIMINATED",
                "timer": 3.0,  # Display for 3 seconds
                "alpha": 255
            })
    
    def end_scramble(self):
        """End The Scramble mode."""
        self.game_over = True
        sorted_tanks = sorted(self.tanks, key=lambda t: t.coins, reverse=True)
        winners = sorted_tanks[:SCRAMBLE_TOP_SURVIVORS]
        
        self.winner_text = "SCRAMBLE COMPLETE!\n"
        for i, tank in enumerate(winners):
            name = getattr(tank, 'team_name', f'Tank_{tank.id}')
            self.winner_text += f"\n#{i+1}: {name} - {tank.coins} coins"
        
        pygame.mixer.music.stop()
        play_critical_sound(SFX_WIN_1, VOL_WIN)
    
    def end_labyrinth(self):
        """End The Labyrinth mode."""
        self.game_over = True
        survivors = [t for t in self.tanks if t.alive]
        self.winner_text = "LABYRINTH SURVIVORS:\n"
        for tank in survivors:
            name = getattr(tank, 'team_name', f'Tank_{tank.id}')
            self.winner_text += f"\n{name}"
            
        pygame.mixer.music.stop()
        play_critical_sound(SFX_WIN_2, VOL_WIN)
    
    def end_duel(self, winner: Optional[Tank]):
        """End The Duel mode."""
        self.game_over = True
        if winner:
            name = getattr(winner, 'team_name', f'Tank_{winner.id}')
            self.winner_text = f"CHAMPION: {name}!"
        else:
            self.winner_text = "DRAW!"
            
        pygame.mixer.music.stop()
        play_critical_sound(SFX_WIN_3, VOL_WIN)
    
    def draw_background(self):
        """Draw the neon grid background."""
        self.screen.fill(COLOR_BACKGROUND)
        
        # Grid lines - OPTIMIZED: draw fewer lines
        for x in range(0, SCREEN_WIDTH + 1, GRID_CELL_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT + 1, GRID_CELL_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (SCREEN_WIDTH, y), 1)
    
    def draw_ui(self):
        """Draw the game UI."""
        # Mode title (pre-rendered)
        title = self._mode_titles.get(self.game_mode)
        if title:
            self.screen.blit(title, (20, 20))
        
        # Timer
        if self.game_mode in [1, 3]:
            mins = int(self.game_timer // 60)
            secs = int(self.game_timer % 60)
            timer_text = self.font_medium.render(f"{mins}:{secs:02d}", True, COLOR_TEXT)
            self.screen.blit(timer_text, (SCREEN_WIDTH - 120, 20))
        
        # Scoreboard (Mode 1)
        if self.game_mode == 1:
            sorted_tanks = sorted(self.tanks, key=lambda t: t.coins, reverse=True)
            y_offset = 80
            for i, tank in enumerate(sorted_tanks[:5]):
                color = tank.color if tank.alive else (100, 100, 100)
                name = getattr(tank, 'team_name', f'Tank_{tank.id}')
                score_text = self.font_small.render(f"{name}: {tank.coins}", True, color)
                self.screen.blit(score_text, (20, y_offset + i * 30))
        
        # Alive count (Mode 2)
        if self.game_mode == 2:
            alive = sum(1 for t in self.tanks if t.alive)
            alive_text = self.font_small.render(f"Alive: {alive}", True, COLOR_TEXT)
            self.screen.blit(alive_text, (SCREEN_WIDTH - 120, 20))
            
            # Kill feed messages (fading death notifications)
            y_offset = 60
            for i, msg in enumerate(self.kill_feed[:5]):  # Show max 5 messages
                if msg["alpha"] > 0:
                    alpha = msg["alpha"]
                    text_surface = self.font_small.render(msg["text"], True, (255, 80, 80))
                    text_surface.set_alpha(alpha)
                    self.screen.blit(text_surface, (SCREEN_WIDTH - text_surface.get_width() - 20, y_offset + i * 28))
        
        # FPS
        if SHOW_FPS:
            fps = self.font_small.render(f"FPS: {int(self.clock.get_fps())}", True, COLOR_GRID_ACCENT)
            self.screen.blit(fps, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 30))
    
    def draw_game_over(self):
        """Draw game over screen."""
        # Darken background - simple rect
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))
        
        # Winner text
        lines = self.winner_text.split('\n')
        y_offset = SCREEN_HEIGHT // 2 - len(lines) * 25
        
        for i, line in enumerate(lines):
            font = self.font_large if i == 0 else self.font_medium
            text = font.render(line, True, COLOR_GOLD if i == 0 else COLOR_TEXT)
            x = SCREEN_WIDTH // 2 - text.get_width() // 2
            self.screen.blit(text, (x, y_offset + i * 50))
        
        # Restart hint
        hint = self.font_small.render("Press R to restart | ESC to quit", True, COLOR_GRID_ACCENT)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 50))
    
    def draw(self):
        """Draw everything."""
        self.draw_background()
        
        # Draw zone (Mode 2)
        if self.game_mode == 2:
            self.zone.draw(self.screen, self.camera)
            # Draw danger zones (Orbital Strikes)
            for dz in self.danger_zones:
                dz.draw(self.screen, self.camera)
        
        # Draw walls
        for wall in self.walls:
            wall.draw(self.screen, self.camera)
        
        # Draw coins
        for coin in self.coins:
            coin.draw(self.screen, self.camera)
        
        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.screen, self.camera)
        
        # Draw tanks
        for tank in self.tanks:
            tank.draw(self.screen, self.camera, self.particles)
            
            # Show LAG PENALTY text if bot exceeded timeout
            if tank.last_action == "LAG":
                pos = self.camera.apply((tank.x, tank.y - 50))
                lag_txt = self.font_small.render("LAG PENALTY!", True, (255, 50, 50))
                self.screen.blit(lag_txt, (pos[0] - lag_txt.get_width() // 2, pos[1]))
        
        # Draw particles (on top)
        self.particles.draw(self.screen, self.camera)
        
        # Draw Juggernaut (Mode 3)
        if self.game_mode == 3 and self.juggernaut:
            self.juggernaut.draw(self.screen, self.camera)
        
        # Draw UI
        self.draw_ui()
        
        # Draw game over
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                elif event.key == pygame.K_r:
                    self.game_over = False
                    self.setup_game()
                
                # Mode switching (for testing)
                elif event.key == pygame.K_1:
                    self.game_mode = 1
                    self.game_over = False
                    self.setup_game()
                elif event.key == pygame.K_2:
                    self.game_mode = 2
                    self.game_over = False
                    self.setup_game()
                elif event.key == pygame.K_3:
                    self.game_mode = 3
                    self.game_over = False
                    self.setup_game()
    
    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        sys.exit()


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Entry point."""
    print("=" * 50)
    print("  GitWars - CONSOLE Tank Tournament")
    print("  MNIT Jaipur")
    print("=" * 50)
    print(f"\n  Game Mode: {GAME_MODE}")
    print("  Press 1/2/3 to switch modes")
    print("  Press R to restart")
    print("  Press ESC to quit\n")
    
    # Start background music
    start_background_music()
    
    engine = GitWarsEngine()
    engine.run()


if __name__ == "__main__":
    main()