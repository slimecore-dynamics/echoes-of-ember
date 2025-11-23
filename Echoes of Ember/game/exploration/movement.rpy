# movement.rpy
# Movement validation and collision detection for dungeon exploration

init python:
    class MovementValidator:
        """
        Validates player movement based on tile types, rotations, and icon collisions.
        """

        # Icon types that block movement
        BLOCKING_ICONS = ["stairs_up", "stairs_down", "door_closed"]

        # Icon types that are passable
        PASSABLE_ICONS = ["teleporter", "gathering", "event", "enemy", "note", "door_open"]

        @staticmethod
        def can_move_to(floor, from_x, from_y, to_x, to_y, player_rotation):
            """
            Check if player can move from (from_x, from_y) to (to_x, to_y).

            Returns: (can_move: bool, reason: str)
            """
            # Check bounds
            if not floor:
                return (False, "No floor data")

            width, height = floor.dimensions
            if to_x < 0 or to_x >= width or to_y < 0 or to_y >= height:
                return (False, "Out of bounds")

            # Get source tile from DUNGEON (real tiles), not drawn map
            source_tile = MovementValidator._get_dungeon_tile(floor, from_x, from_y)
            if not source_tile:
                return (False, "Invalid source")

            # Calculate direction of movement
            dx = to_x - from_x
            dy = to_y - from_y

            # Determine which direction we're trying to move
            if dx == 1 and dy == 0:
                move_dir = "east"
            elif dx == -1 and dy == 0:
                move_dir = "west"
            elif dx == 0 and dy == 1:
                move_dir = "south"
            elif dx == 0 and dy == -1:
                move_dir = "north"
            else:
                return (False, "Invalid movement (diagonal or too far)")

            # Check if source tile allows this direction of movement
            allowed_dirs = MovementValidator._get_allowed_directions(source_tile)
            if move_dir not in allowed_dirs:
                return (False, "Current tile blocks {} movement".format(move_dir))

            # Get destination tile from DUNGEON (real tiles), not drawn map
            dest_tile = MovementValidator._get_dungeon_tile(floor, to_x, to_y)
            if not dest_tile:
                return (False, "Invalid destination")

            # Empty tiles are voids (unreachable)
            if dest_tile.tile_type == "empty":
                return (False, "Empty void")

            # Check if destination tile allows entry from opposite direction
            opposite_dir = MovementValidator._get_opposite_direction(move_dir)
            dest_allowed_dirs = MovementValidator._get_allowed_directions(dest_tile)
            if opposite_dir not in dest_allowed_dirs:
                return (False, "Destination blocks entry from {}".format(opposite_dir))

            # Check if there's a blocking icon at destination
            icon_at_dest = floor.icons.get((to_x, to_y))
            if icon_at_dest:
                if icon_at_dest.icon_type in MovementValidator.BLOCKING_ICONS:
                    return (False, "Blocked by {}".format(icon_at_dest.icon_type))

            return (True, "OK")

        @staticmethod
        def _get_allowed_directions(tile):
            """
            Get list of directions player can move FROM/TO this tile.
            Parse tile name suffix to get allowed directions (e.g., corner_ws = west/south).

            Returns: list of strings: ["north", "south", "east", "west"]
            """
            tile_type = tile.tile_type

            if tile_type == "empty":
                return []  # Empty is void - no movement allowed

            elif tile_type == "cross":
                # Cross allows all 4 directions
                return ["north", "south", "east", "west"]

            else:
                # Parse suffix letters from tile name (e.g., "corner_ws" -> "ws")
                # Letters indicate passable directions: n=north, s=south, e=east, w=west
                parts = tile_type.split("_")
                if len(parts) < 2:
                    # No suffix, assume all directions for unknown types
                    return ["north", "south", "east", "west"]

                suffix = parts[-1]  # Get last part (e.g., "ws", "nes", "we")
                allowed = []

                # Map letters to directions
                if 'n' in suffix:
                    allowed.append("north")
                if 's' in suffix:
                    allowed.append("south")
                if 'e' in suffix:
                    allowed.append("east")
                if 'w' in suffix:
                    allowed.append("west")

                # Handle special cases for hallway with hor/ver naming
                if "hor" in suffix:
                    return ["east", "west"]
                elif "ver" in suffix:
                    return ["north", "south"]

                return allowed if allowed else []

        @staticmethod
        def _get_opposite_direction(direction):
            """Get opposite direction"""
            opposites = {
                "north": "south",
                "south": "north",
                "east": "west",
                "west": "east"
            }
            return opposites.get(direction, "")

        @staticmethod
        def _get_dungeon_tile(floor, x, y):
            """
            Get tile from real dungeon (for movement validation).
            Falls back to drawn map if dungeon_tiles doesn't exist.
            """
            if hasattr(floor, 'dungeon_tiles') and floor.dungeon_tiles:
                # Use dungeon tiles (real layout)
                if y < len(floor.dungeon_tiles) and x < len(floor.dungeon_tiles[y]):
                    return floor.dungeon_tiles[y][x]
                return None
            else:
                # Fall back to regular tiles (drawn map)
                return floor.get_tile(x, y)

        @staticmethod
        def get_adjacent_icon(floor, x, y, rotation):
            """
            Get icon in the tile the player is facing (adjacent to current position).

            Returns: MapIcon or None
            """
            # Calculate adjacent position based on rotation
            if rotation == 0:    # North
                adj_x, adj_y = x, y - 1
            elif rotation == 90:  # East
                adj_x, adj_y = x + 1, y
            elif rotation == 180: # South
                adj_x, adj_y = x, y + 1
            elif rotation == 270: # West
                adj_x, adj_y = x - 1, y
            else:
                return None

            # Check bounds
            width, height = floor.dimensions
            if adj_x < 0 or adj_x >= width or adj_y < 0 or adj_y >= height:
                return None

            # Get icon at adjacent tile
            return floor.icons.get((adj_x, adj_y))

        @staticmethod
        def get_icon_at_position(floor, x, y):
            """
            Get icon at the player's current position.

            Returns: MapIcon or None
            """
            if not floor:
                return None
            return floor.icons.get((x, y))
