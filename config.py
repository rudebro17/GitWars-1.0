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
GAME_MODE = 1                       # 1=Scramble, 2=Labyrinth, 3=Duel
BOT_DEFAULT_COUNT =  4      # Number of bots in games
SCRAMBLE_TOP_SURVIVORS = 2          # How many advance to next round
SCRAMBLE_DURATION = 60             # 3 minutes in seconds
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
TANK_MAX_HEALTH = 1500
TANK_STARTING_AMMO = 1500
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
JAM_CHANCE = 0.005              # 1% chance tank stalls

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


# Mode 1: The Scramble

SCRAMBLE_COIN_SPAWN_INTERVAL = 0.25  # Seconds between coin spawns
SCRAMBLE_MAX_COINS = 20             # Maximum coins on screen
SCRAMBLE_KNOCKBACK = 20.0           # Bullet knockback (no damage)


# Mode 2: The Labyrinth
LABYRINTH_ZONE_SHRINK_INTERVAL = 13 # Seconds between zone shrinks
LABYRINTH_ZONE_DAMAGE = 50           # DPS when in the zone
LABYRINTH_FINAL_SURVIVORS = 2       # How many advance to finals

# Danger Zones (Orbital Strike - Mode 2)
DANGER_ZONE_SPAWN_INTERVAL = 10.0   # Seconds between spawns
DANGER_ZONE_WARNING_DURATION = 2.0  # Warning phase (time to escape)
DANGER_ZONE_ACTIVE_DURATION = 5.0   # Active bombardment phase
DANGER_ZONE_RADIUS = 120            # Size of the circle
DANGER_ZONE_DAMAGE = 75             # Damage per blast hit
DANGER_ZONE_KNOCKBACK = 40.0       # Knockback force from blasts
DANGER_ZONE_BLAST_INTERVAL = 0.5    # Seconds between explosions
COLOR_DANGER_WARNING = (255, 50, 50, 100)   # Semi-transparent red
COLOR_DANGER_ACTIVE = (255, 150, 150, 180)  # Bright red-white

# Mode 3: The Juggernaut (Boss Fight)
# Juggernaut Body
JUGGERNAUT_SIZE = 120               # 3x tank size (diameter)
JUGGERNAUT_SPEED = 20.0            # Slow creep (0.5x player speed)
JUGGERNAUT_HEALTH = 9999            # Effectively invincible
JUGGERNAUT_ROTATION_SPEED = 180     # Visual spin (degrees/sec)
JUGGERNAUT_COLOR = (80, 20, 20)     # Dark red body
JUGGERNAUT_BLADE_COLOR = (40, 10, 10)  # Darker blade accents

# Juggernaut Melee (Contact Damage)
JUGGERNAUT_MELEE_DAMAGE = 5         # Per-frame damage on contact
JUGGERNAUT_MELEE_KNOCKBACK = 800.0  # Massive push force

# Juggernaut Burst Cannon
JUGGERNAUT_IDLE_TIME = 0.0          # Seconds tracking before charge
JUGGERNAUT_CHARGE_TIME = 0.0        # Seconds of warning (turret glows)
JUGGERNAUT_BURST_TIME = 2.0         # Seconds of burst fire
JUGGERNAUT_BURST_COUNT = 10          # Bullets per burst
JUGGERNAUT_BURST_INTERVAL = 0.2     # Seconds between burst shots
JUGGERNAUT_BULLET_SPEED = 6.0      # Fast heavy bullets
JUGGERNAUT_BULLET_DAMAGE = 50       # High damage per hit
JUGGERNAUT_BULLET_KNOCKBACK = 1000.0 # Heavy knockback
JUGGERNAUT_BULLET_SIZE = 20         # Larger bullets
JUGGERNAUT_TURRET_SIZE = 30         # Turret visual size

# Level 3 Tank Modifiers
LEVEL3_HEALTH_MULTIPLIER = 2.0      # Multiply tank health by this factor in Level 3


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


# =============================================================================
# AUDIO SETTINGS
# =============================================================================
MUSIC_VOLUME = 0.5
SFX_VOLUME = 0.7  # Master SFX volume (base)

# Individual Sound Volumes (0.0 to 1.0)
VOL_SHOOT = 0.00      # Lower volume for frequent shooting
VOL_DEATH = 0.8      # Loud explosion
VOL_COIN = 0.6       # Moderate pickup sound
VOL_READY = 0.9      # Loud start announcement
VOL_WIN = 1.0        # Loud victory music
PITCH_VARIATION = 0.2               # Random pitch shift for SFX

# =============================================================================
# DEBUG SETTINGS
# =============================================================================
DEBUG_MODE = False
SHOW_HITBOXES = False
SHOW_FPS = True