"""
GitWars - Bot Template
======================

This is your STARTER CODE! Edit this file to control your tank.
Read the comments carefully to understand the API.
Note: Avoid using AI tools to write your code.

Your tank will call your update() function every frame.
You must return an action tuple: (ACTION, PARAMETER)

ACTIONS:
--------
You must return one of the following actions:

("MOVE", (dx, dy))   - Move in direction (dx, dy). Values are normalized.
                       Example: ("MOVE", (3, 0)) = move right by 3 px
                       Example: ("MOVE", (0, -1)) = move up
                       Example: ("MOVE", (-1, 1)) = move down-left

("SHOOT", angle)     - Fire a bullet at the given angle (in degrees).
                       Example: ("SHOOT", 0) = shoot right
                       Example: ("SHOOT", 90) = shoot down
                       Example: ("SHOOT", 180) = shoot left

("STOP", None)       - Stop moving, stay in place.

CONTEXT DICTIONARY:
-------------------
The game engine passes a `context` dictionary (If you don't know about dictionaries, have a quick Google search!) to your tank every frame.
It contains all the information you need:

context = {
    "me": {
        "x": float,      # Your tank's X position
        "y": float,      # Your tank's Y position  
        "angle": float,  # Your tank's facing angle (degrees)
        "health": int,   # Your current health (0-1000)
        "ammo": int,     # Your remaining bullets
        "coins": int     # Coins collected (Mode 1 only)
    },
    "enemies": [
        {"x": float, "y": float, "id": int},  # List of enemy positions
        ...
    ],
    "coins": [
        {"x": float, "y": float},  # List of coin positions (Mode 1 only)
        ...
    ],
    "walls": [
        {"x": float, "y": float, "width": float, "height": float},  # Walls
        ...
    ],
    "bullets": [
        {"x": float, "y": float, "vx": float, "vy": float},  # Enemy bullets
        ...
    ],
    "sensors": {
        "front": float,  # Distance to wall ahead (max 300 pixels)
        "left": float,   # Distance to wall at -30 degrees
        "right": float   # Distance to wall at +30 degrees
    },
    "game_mode": int,     # 1=Scramble, 2=Labyrinth, 3=Juggernaut
    "time_left": float    # Time remaining in seconds
}

SENSORS (Obstacle Avoidance): (SKIP FOR LEVEL 1!!!!)
-----------------------------
The 'sensors' key contains raycast distances to walls in 3 directions.

(What is a Raycast? Think of it like an invisible laser beam or a "whisker" 
that shoots out from your tank to measure the distance to the nearest object.)

- "front": Distance to wall straight ahead (0 degrees from facing)
- "left":  Distance to wall at -30 degrees (left whisker)
- "right": Distance to wall at +30 degrees (right whisker)

Max range is 300 pixels. If no wall is detected, the value is 300.
- If the sensor sees a wall at 50px, it returns 50.
- If it sees nothing (or the wall is too far), it returns 300.

Example Usage:
    sensors = context["sensors"]
    if sensors["front"] < 50:  # Wall is close ahead!
        if sensors["left"] > sensors["right"]:
            # More space on left -> turn left
            return ("MOVE", (-1, 0))
        else:
            # More space on right -> turn right
            return ("MOVE", (1, 0))

TIPS:
-----
1. Before writing the code, view all the necessary comments above!
2. Don't try to modify the 'context' - it's a read-only copy!
3. Your update() function has a 100ms time limit - keep it fast! (avoid any hardcore logic)
4. If your code crashes, your tank will freeze but the game continues.
5. Use math.atan2(dy, dx) to calculate angles to targets.
6. In Mode 1 (Scramble), bullets only cause knockback - they don't damage!
"""

# =============================================================================
# HELPER FUNCTIONS (You can use these, but you don't need to edit them)
# =============================================================================

import math
import random


def distance(x1, y1, x2, y2):
    """Calculate distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def angle_to(x1, y1, x2, y2):
    """Calculate angle from point (x1, y1) to point (x2, y2) in degrees. Returns -180° to +180°"""
    return math.degrees(math.atan2(y2 - y1, x2 - x1))


def find_nearest(my_x, my_y, targets):
    """
    Find the nearest target from a list of targets.
    Each target must have 'x' and 'y' keys.
    Returns (target, distance) or (None, float('inf')) if list is empty.
    """
    nearest = None
    min_dist = float('inf')
    
    for target in targets:
        dist = distance(my_x, my_y, target["x"], target["y"])
        if dist < min_dist:
            min_dist = dist
            nearest = target
    
    return nearest, min_dist


def will_bullet_hit_me(my_x, my_y, bullet, danger_radius=50):
    """
    Predict if a bullet will come close to your position.
    Returns True if bullet is dangerous.
    """
    # Future position of bullet
    # Look ~10 frames ahead to estimate bullet direction (heuristic, not exact)
    future_x = bullet["x"] + bullet["vx"] * 10
    future_y = bullet["y"] + bullet["vy"] * 10
    
    # Check if bullet path intersects with our position
    dist_now = distance(my_x, my_y, bullet["x"], bullet["y"])
    dist_future = distance(my_x, my_y, future_x, future_y)
    
    # Bullet is approaching if it gets closer
    return dist_future < dist_now and dist_now < danger_radius * 2

# =============================================================================
# YOUR CODE STARTS HERE!
# =============================================================================

def update(context):
    """
    This function is called every frame.
    
    Args:
        context: Dictionary containing game state (view above for structure)
    
    Returns:
        (ACTION, PARAMETER) tuple - your tank's action for this frame as discussed above
    """
    
    # Get my tank's info
    me = context["me"]
    my_x = me["x"]
    my_y = me["y"]
    
    enemies = context["enemies"]
    coins = context["coins"]
    bullets = context["bullets"]
    game_mode = context["game_mode"]
    
    # =========================================================================
    # EXAMPLE STRATEGY: This is a basic bot, modify it!
    # =========================================================================
    
    # PRIORITY 0: OBSTACLE AVOIDANCE REFLEX (Prevents getting stuck!)
    # all info related to sensors is discussed above and is only to learn and not edit anything!

    sensors = context["sensors"]
    my_angle = me["angle"]
    
    # EMERGENCY REVERSE: If face-planted into wall (< 10 pixels)
    if sensors["front"] < 10:
        # Full reverse! Move opposite to facing direction
        reverse_angle = math.radians(my_angle + 180)
        return ("MOVE", (math.cos(reverse_angle), math.sin(reverse_angle)))
    
    # STANDARD AVOIDANCE: Wall approaching (< 50 pixels)
    elif sensors["front"] < 50:
        # Turn toward open space
        if sensors["left"] > sensors["right"]:
            # More space on left - turn left (perpendicular to facing)
            turn_angle = math.radians(my_angle - 90)
        else:
            # More space on right - turn right
            turn_angle = math.radians(my_angle + 90)
        dx = math.cos(turn_angle)
        dy = math.sin(turn_angle)
        return ("MOVE", (dx, dy))
    
    elif sensors["left"] < 30:
        # Wall on left - nudge right
        turn_angle = math.radians(my_angle + 45)
        return ("MOVE", (math.cos(turn_angle), math.sin(turn_angle)))
    
    elif sensors["right"] < 30:
        # Wall on right - nudge left
        turn_angle = math.radians(my_angle - 45)
        return ("MOVE", (math.cos(turn_angle), math.sin(turn_angle)))   
    
    # note: If none of the conditions above trigger,
    # you must return your own action later (or tank will stop)

    # =========================================================================
    # LEVEL 1 - THE SCRAMBLE
    # =========================================================================

    if game_mode == 1: # Collect the coins

        # Priority 1: Dodge incoming bullets (standard MOVE)
        for bullet in bullets:
            if will_bullet_hit_me(my_x, my_y, bullet):
                bullet_angle =math.degrees(math.atan2(bullet["vy"],bullet["vx"]))
                dodge_agl= bullet_angle + 90
                return ("MOVE",(5*math.cos(math.radians(dodge_agl)),5*math.sin(math.radians(dodge_agl))))
                #return ("MOVE",(dx,dy))

        if coins:
            nearest_coin, dist = find_nearest(my_x, my_y, coins)
            if nearest_coin:
                angle_coin=angle_to(my_x,my_y,nearest_coin["x"],nearest_coin["y"])
                return ("MOVE",(10*math.cos(math.radians(angle_coin)),10*math.sin(math.radians(angle_coin))))
                for enemy in enemies:
                    enemy_dist = distance(enemy["x"], enemy["y"], nearest_coin["x"], nearest_coin["y"])
                    my_dist = distance(my_x["x"], my_y["y"], nearest_coin["x"], nearest_coin["y"])
                    if(enemy_dist<my_dist):
                        return("SHOOT",angle_to(my_x,my_y,enemy["x"], enemy["y"]))
                    # WRITE YOUR LOGIC HERE

                    # # TIP: Compare enemy_dist with my_dist.
                    # If an enemy is closer to this coin, you may want to shoot to knock them back first.
                    # Also, don’t forget to move toward the coin!

    # =========================================================================
    # LEVEL 2 - THE LABYRINTH
    # =========================================================================
    
    elif game_mode == 2: # Combat game

        # Priority 1: Dodge incoming bullets (standard MOVE)
        for bullet in bullets:
            if will_bullet_hit_me(my_x, my_y, bullet):

                # WRITE YOUR LOGIC HERE
                
                #return ("MOVE",(dx,dy))
                pass

        if enemies and me["ammo"] > 0:
            # Find and attack nearest enemy
            nearest_enemy, dist = find_nearest(my_x, my_y, enemies)
            if nearest_enemy:

                if dist < 80:
                    # What if the two tanks are stuck to each other (very close range)?

                    # WRITE YOUR LOGIC HERE (example: move away, strafe, or reposition)
                    pass

                elif dist < 200:
                     # Enemy in range — attack
                    target_angle = angle_to(my_x, my_y, nearest_enemy["x"], nearest_enemy["y"])
                    return ("SHOOT", target_angle)
                
                else:
                    # TO-DO: If enemy is far, should you move toward it? flank it? or reposition?
                    
                    # note: If you don't return an action here, your tank will stop!
                    pass

    # =========================================================================
    # LEVEL 3 - THE JUGGERNAUT
    # =========================================================================
    
    elif game_mode == 3: # Juggernaut game

        total_move_x = 0
        total_move_y = 0

        # A. Dodge Juggernaut
        juggernaut = context.get("juggernaut")
        if juggernaut:
            jug_x, jug_y = juggernaut["x"], juggernaut["y"]
            jug_dist = distance(my_x, my_y, jug_x, jug_y)
            
            if jug_dist < 300:  # Fear radius
                # Vector away from Juggernaut
                target_angle = angle_to(my_x, my_y, jug_x, jug_y)
                new_angle=target_angle + 180
                total_move_x += math.cos(math.radians(new_angle))
                total_move_y+= math.sin(math.radians(new_angle))
        
        # B. Dodge Bullets
        for bullet in bullets:
            if will_bullet_hit_me(my_x, my_y, bullet):
                # Perpendicular dodge
                dodge_angle = math.degrees(math.atan2(bullet["vy"], bullet["vx"])) + 90
                dx = math.cos(math.radians(dodge_angle))
                dy = math.sin(math.radians(dodge_angle))
                return ("MOVE", (dx, dy))
        
        # C. Enemy logic
        target_enemy = None
        if enemies:
            target_enemy, enemy_dist = find_nearest(my_x, my_y, enemies)

            if enemy_dist < 250:

                # WRITE YOUR LOGIC HERE
                pass
        
        # Shooting
        if target_enemy and me["ammo"] > 0:
            shoot_angle = angle_to(my_x, my_y, target_enemy["x"], target_enemy["y"])
            shoot_angle += random.uniform(-5, 5) # Slight spread
            return ("SHOOT",shoot_angle)
        
        # Fallback: Just Move
        return ("MOVE", (total_move_x, total_move_y))
    

    # Default: Wander around
    angle = random.uniform(0, 360)
    dx = math.cos(math.radians(angle))
    dy = math.sin(math.radians(angle))
    return ("MOVE", (dx, dy))