"""
GitWars - Configuration File
============================
All game constants and settings are defined here.
Students should NOT modify this file.

Change GAME_MODE to switch between tournament rounds:
- 1: The Scramble (Coin Collection)
- 2: The Labyrinth (Deathmatch)
- 3: The Duel (1v1 Finals)
"""

import pygame

# =============================================================================
# DISPLAY SETTINGS
# =============================================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "GitWars - CONSOLE Tank Tournament"

# =============================================================================
# COLOR PALETTE (Neon/Tron Aesthetic)
# =============================================================================
# Background & Grid
COLOR_BACKGROUND = (5, 5, 16)       # Deep space blue-black
COLOR_GRID = (20, 40, 80)           # Faint neon blue grid
COLOR_GRID_ACCENT = (30, 60, 120)   # Brighter grid accents

# Tank Colors (Neon)
TANK_COLORS = [
    (0, 255, 255),    # Cyan
    (255, 0, 255),    # Magenta
    (0, 255, 128),    # Lime Green
    (255, 128, 0),    # Orange
    (255, 255, 0),    # Yellow
    (128, 0, 255),    # Purple
    (255, 64, 128),   # Pink
    (0, 200, 255),    # Sky Blue
]

# UI Colors
COLOR_TEXT = (255, 255, 255)
COLOR_HEALTH_BAR = (0, 255, 128)
COLOR_HEALTH_BG = (50, 50, 50)
COLOR_DANGER = (255, 50, 50)
COLOR_GOLD = (255, 215, 0)
COLOR_CRITICAL = (255, 0, 0)       # Critical hit glow

# Zone Colors (for shrinking boundary)
COLOR_ZONE_SAFE = (0, 100, 50, 100)
COLOR_ZONE_DANGER = (150, 0, 0, 150)

# =============================================================================
# TANK SETTINGS
# =============================================================================
TANK_SIZE = 40                      # Tank hitbox size (pixels)
TANK_SPEED = 4.0                    # Movement speed (pixels/frame) [DEPRECATED in favor of FORCE]
TANK_ENGINE_FORCE = 1200.0          # Force applied when moving
TANK_FRICTION = 5.0                 # Friction/Drag factor
TANK_MASS = 1.0                     # Tank mass
TANK_ROTATION_SPEED = 5.0           # Degrees per frame
TANK_MAX_HEALTH = 100
TANK_STARTING_AMMO = 200
TANK_RECOIL = 3.0                   # Pushback when shooting

# =============================================================================
# BULLET SETTINGS
# =============================================================================
BULLET_SPEED = 12.0
BULLET_DAMAGE = 15
BULLET_SIZE = 6
BULLET_TRAIL_LENGTH = 15            # Number of trail segments
BULLET_TRAIL_FADE = 0.85            # Trail opacity decay

# RNG Factors
CRITICAL_HIT_CHANCE = 0.10          # 10% chance for 3x damage
CRITICAL_HIT_MULTIPLIER = 3.0
JAM_CHANCE = 0.01                   # 1% chance tank stalls

# =============================================================================
# PARTICLE SETTINGS
# =============================================================================
PARTICLE_DEATH_COUNT = 25           # Particles on tank death
PARTICLE_DEATH_SPEED = 8.0          # Initial velocity
PARTICLE_FRICTION = 0.92            # Velocity decay per frame
PARTICLE_FADE_SPEED = 5             # Alpha decrease per frame
PARTICLE_SIZE_RANGE = (4, 12)       # Min/max particle size

MUZZLE_FLASH_SIZE = 20
MUZZLE_FLASH_DURATION = 5           # Frames

# =============================================================================
# SCREEN SHAKE SETTINGS
# =============================================================================
SHAKE_INTENSITY = 8                 # Max pixel offset
SHAKE_DURATION = 0.5                # Seconds
SHAKE_DECAY = 0.9                   # Intensity decay per frame

# =============================================================================
# GAME MODE SETTINGS
# =============================================================================
GAME_MODE = 1                       # 1=Scramble, 2=Labyrinth, 3=Duel

# Mode 1: The Scramble
SCRAMBLE_DURATION = 30             # 3 minutes in seconds
SCRAMBLE_COIN_SPAWN_INTERVAL = 0.25  # Seconds between coin spawns
SCRAMBLE_MAX_COINS = 20             # Maximum coins on screen
SCRAMBLE_KNOCKBACK = 15.0           # Bullet knockback (no damage)
SCRAMBLE_TOP_SURVIVORS = 5          # How many advance to next round

# Mode 2: The Labyrinth
LABYRINTH_ZONE_SHRINK_INTERVAL = 5 # Seconds between zone shrinks
LABYRINTH_ZONE_DAMAGE = 5           # DPS when in the zone
LABYRINTH_FINAL_SURVIVORS = 2       # How many advance to finals

# Mode 3: The Duel
DUEL_SUDDEN_DEATH_TIME = 60         # Seconds before laser
DUEL_LASER_SPEED = 3.0              # Pixels per frame
DUEL_LASER_DAMAGE = 100             # Instant kill

# =============================================================================
# COIN SETTINGS
# =============================================================================
COIN_SIZE = 20
COIN_VALUE = 1
COIN_GLOW_SPEED = 0.1               # Pulsing animation speed

# =============================================================================
# WALL SETTINGS
# =============================================================================
WALL_COLOR = (200, 200, 220)
WALL_GLOW_COLOR = (100, 100, 150)
GRID_CELL_SIZE = 50                 # For maze generation

# =============================================================================
# BOT SETTINGS
# =============================================================================
BOT_TIMEOUT_MS = 100                # Max execution time for bot logic
BOT_DEFAULT_COUNT = 8               # Number of bots in game

# =============================================================================
# AUDIO SETTINGS
# =============================================================================
MUSIC_VOLUME = 0.5
SFX_VOLUME = 0.7
PITCH_VARIATION = 0.2               # Random pitch shift for SFX

# =============================================================================
# DEBUG SETTINGS
# =============================================================================
DEBUG_MODE = False
SHOW_HITBOXES = False
SHOW_FPS = True