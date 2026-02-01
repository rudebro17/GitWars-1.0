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

def update(context):
    
    # Get my tank's info
    me = context["me"]
    my_x = me["x"]
    my_y = me["y"]
    
    enemies = context["enemies"]
    coins = context["coins"]
    bullets = context["bullets"]
    game_mode = context["game_mode"]
    
    # PRIORITY 0: OBSTACLE AVOIDANCE REFLEX (Prevents getting stuck!)

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


    if game_mode == 1:

        r = random.random()

        # 40% - Pure random wandering
        if r < 0.4:
            angle = random.uniform(0, 360)
            return ("MOVE", (
                math.cos(math.radians(angle)),
                math.sin(math.radians(angle))
            ))

        # 30% - Move toward nearest coin
        elif r < 0.7 and coins:
            nearest_coin, _ = find_nearest(my_x, my_y, coins)
            if nearest_coin:
                dx = nearest_coin["x"] - my_x
                dy = nearest_coin["y"] - my_y
                length = math.hypot(dx, dy)
                if length > 0:
                    dx /= length
                    dy /= length
                return ("MOVE", (dx, dy))

        # 30% - Drift toward enemy + shoot
        elif enemies:
            enemy, _ = find_nearest(my_x, my_y, enemies)

            dx = enemy["x"] - my_x
            dy = enemy["y"] - my_y
            length = math.hypot(dx, dy)
            if length > 0:
                dx /= length
                dy /= length

            # Half the time move closer
            if random.random() < 0.5:
                return ("MOVE", (dx, dy))

            # Half the time shoot (slightly inaccurate)
            if me["ammo"] > 0:
                shoot_angle = angle_to(my_x, my_y, enemy["x"], enemy["y"])
                shoot_angle += random.uniform(-10, 10)
                return ("SHOOT", shoot_angle)

        # Fallback random move
        angle = random.uniform(0, 360)
        return ("MOVE", (
            math.cos(math.radians(angle)),
            math.sin(math.radians(angle))
        ))
    
    elif game_mode == 2:

        r = random.random()

        # 50% - Random wandering
        if r < 0.5:
            angle = random.uniform(0, 360)
            return ("MOVE", (
                math.cos(math.radians(angle)),
                math.sin(math.radians(angle))
            ))

        # 25% - Move toward nearest enemy
        elif r < 0.75 and enemies:
            enemy, _ = find_nearest(my_x, my_y, enemies)

            dx = enemy["x"] - my_x
            dy = enemy["y"] - my_y
            length = math.hypot(dx, dy)
            if length > 0:
                dx /= length
                dy /= length

            return ("MOVE", (dx, dy))

        # 25% - Shoot nearest enemy (slightly inaccurate)
        elif enemies and me["ammo"] > 0:
            enemy, _ = find_nearest(my_x, my_y, enemies)

            shoot_angle = angle_to(my_x, my_y, enemy["x"], enemy["y"])
            shoot_angle += random.uniform(-8, 8)

            return ("SHOOT", shoot_angle)

        # Fallback random move
        angle = random.uniform(0, 360)
        return ("MOVE", (
            math.cos(math.radians(angle)),
            math.sin(math.radians(angle))
        ))
    
    elif game_mode == 3:

        # 1. Always avoid Juggernaut if nearby
        juggernaut = context.get("juggernaut")
        if juggernaut:
            jug_x, jug_y = juggernaut["x"], juggernaut["y"]
            jug_dist = distance(my_x, my_y, jug_x, jug_y)

            if jug_dist < 300:
                # Run directly away
                away_angle = angle_to(my_x, my_y, jug_x, jug_y) + 180
                return ("MOVE", (
                    math.cos(math.radians(away_angle)),
                    math.sin(math.radians(away_angle))
                ))
            
        for bullet in bullets:
            if will_bullet_hit_me(my_x, my_y, bullet) and random.random() < 0.5:
                dodge_angle = math.degrees(math.atan2(bullet["vy"], bullet["vx"])) + 90
                return ("MOVE", (
                    math.cos(math.radians(dodge_angle)),
                    math.sin(math.radians(dodge_angle))
                ))
        
        r = random.random()

        # 40% - Random wandering
        if r < 0.4:
            angle = random.uniform(0, 360)
            return ("MOVE", (
                math.cos(math.radians(angle)),
                math.sin(math.radians(angle))
            ))

        # 30% - Move toward nearest enemy
        elif r < 0.7 and enemies:
            enemy, _ = find_nearest(my_x, my_y, enemies)

            dx = enemy["x"] - my_x
            dy = enemy["y"] - my_y
            length = math.hypot(dx, dy)
            if length > 0:
                dx /= length
                dy /= length

            return ("MOVE", (dx, dy))

        # 30% - Shoot nearest enemy (light accuracy)
        elif enemies and me["ammo"] > 0:
            enemy, _ = find_nearest(my_x, my_y, enemies)

            shoot_angle = angle_to(my_x, my_y, enemy["x"], enemy["y"])
            shoot_angle += random.uniform(-8, 8)
            return ("SHOOT", shoot_angle)

        # Fallback random move
        angle = random.uniform(0, 360)
        return ("MOVE", (
            math.cos(math.radians(angle)),
            math.sin(math.radians(angle))
        ))

    

    # Default: Wander around
    angle = random.uniform(0, 360)
    dx = math.cos(math.radians(angle))
    dy = math.sin(math.radians(angle))
    return ("MOVE", (dx, dy))