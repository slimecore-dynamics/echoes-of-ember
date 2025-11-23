# exploration_state.rpy
# Player state for dungeon exploration

init -1 python:
    class PlayerState:
        # Stores player position and rotation during dungeon exploration.
        #
        # Position: (x, y) coordinates on the current floor
        # Rotation: 0 = North, 90 = East, 180 = South, 270 = West

        def __init__(self, x=0, y=0, rotation=0, floor_id=None):
            self.x = x
            self.y = y
            self.rotation = rotation  # 0, 90, 180, 270
            self.current_floor_id = floor_id
            self.health = 100  # For enemy damage
            self.max_health = 100

        def get_position(self):
            # Return current position as tuple
            return (self.x, self.y)

        def set_position(self, x, y):
            # Set player position
            self.x = x
            self.y = y

        def get_rotation(self):
            # Return current rotation (0, 90, 180, 270)
            return self.rotation

        def rotate_left(self):
            # Rotate 90 degrees counter-clockwise
            self.rotation = (self.rotation - 90) % 360

        def rotate_right(self):
            # Rotate 90 degrees clockwise
            self.rotation = (self.rotation + 90) % 360

        def get_forward_position(self):
            # Get the position one tile ahead in current direction
            dx, dy = self._get_direction_delta()
            return (self.x + dx, self.y + dy)

        def get_backward_position(self):
            # Get the position one tile behind in current direction
            dx, dy = self._get_direction_delta()
            return (self.x - dx, self.y - dy)

        def _get_direction_delta(self):
            # Get (dx, dy) for current rotation
            if self.rotation == 0:    # North
                return (0, -1)
            elif self.rotation == 90:  # East
                return (1, 0)
            elif self.rotation == 180: # South
                return (0, 1)
            elif self.rotation == 270: # West
                return (-1, 0)
            return (0, 0)

        def get_facing_direction_name(self):
            # Get human-readable direction name
            if self.rotation == 0:
                return "North"
            elif self.rotation == 90:
                return "East"
            elif self.rotation == 180:
                return "South"
            elif self.rotation == 270:
                return "West"
            return "Unknown"

        def take_damage(self, amount):
            # Reduce health by amount
            self.health = max(0, self.health - amount)

        def heal(self, amount):
            # Increase health by amount (up to max)
            self.health = min(self.max_health, self.health + amount)

        def is_alive(self):
            # Check if player is alive
            return self.health > 0

        def to_dict(self):
            # Serialize to dictionary for JSON storage
            return {
                "x": self.x,
                "y": self.y,
                "rotation": self.rotation,
                "current_floor_id": self.current_floor_id,
                "health": self.health,
                "max_health": self.max_health
            }

        @staticmethod
        def from_dict(data):
            # Deserialize from dictionary
            player = PlayerState(
                x=data.get("x", 0),
                y=data.get("y", 0),
                rotation=data.get("rotation", 0),
                floor_id=data.get("current_floor_id")
            )
            player.health = data.get("health", 100)
            player.max_health = data.get("max_health", 100)
            return player


# Global variables (not saved in Ren'Py saves - managed externally)
init -10 python:
    if not hasattr(store, 'player_state'):
        store.player_state = None
    if not hasattr(store, 'map_grid'):
        store.map_grid = None
