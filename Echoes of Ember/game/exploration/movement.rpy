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

            # Get destination tile from DUNGEON (real tiles), not drawn map
            dest_tile = MovementValidator._get_dungeon_tile(floor, to_x, to_y)
            if not dest_tile:
                return (False, "Invalid destination")

            # Empty tiles are voids (unreachable)
            if dest_tile.tile_type == "empty":
                return (False, "Empty void")

            # Check if there's a blocking icon at destination
            icon_at_dest = floor.icons.get((to_x, to_y))
            if icon_at_dest:
                if icon_at_dest.icon_type in MovementValidator.BLOCKING_ICONS:
                    return (False, "Blocked by {}".format(icon_at_dest.icon_type))

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
                return (False, "Tile blocks {} movement".format(move_dir))

            # Check if destination tile allows entry from opposite direction
            opposite_dir = MovementValidator._get_opposite_direction(move_dir)
            dest_allowed_dirs = MovementValidator._get_allowed_directions(dest_tile)
            if opposite_dir not in dest_allowed_dirs:
                return (False, "Destination tile blocks entry from {}".format(opposite_dir))

            return (True, "OK")

        @staticmethod
        def _get_allowed_directions(tile):
            """
            Get list of directions player can move FROM this tile.

            Returns: list of strings: ["north", "south", "east", "west"]
            """
            tile_type = tile.tile_type
            rotation = tile.rotation

            if tile_type == "empty":
                return []  # Empty is void

            elif tile_type == "wall":
                # Wall blocks one direction based on rotation
                # Rotation 0 = wall faces North (blocks north)
                # Rotation 90 = wall faces East (blocks east)
                # Rotation 180 = wall faces South (blocks south)
                # Rotation 270 = wall faces West (blocks west)
                all_dirs = ["north", "south", "east", "west"]
                if rotation == 0:
                    all_dirs.remove("north")
                elif rotation == 90:
                    all_dirs.remove("east")
                elif rotation == 180:
                    all_dirs.remove("south")
                elif rotation == 270:
                    all_dirs.remove("west")
                return all_dirs

            elif tile_type == "hallway":
                # Hallway allows 2 directions based on rotation
                # Rotation 0 = horizontal (east/west only)
                # Rotation 90 = vertical (north/south only)
                if rotation == 0 or rotation == 180:
                    return ["east", "west"]
                else:  # 90 or 270
                    return ["north", "south"]

            elif tile_type == "corner":
                # Corner allows 2 perpendicular directions based on rotation
                # Rotation 0 = allows East and South
                # Rotation 90 = allows South and West
                # Rotation 180 = allows West and North
                # Rotation 270 = allows North and East
                if rotation == 0:
                    return ["east", "south"]
                elif rotation == 90:
                    return ["south", "west"]
                elif rotation == 180:
                    return ["west", "north"]
                elif rotation == 270:
                    return ["north", "east"]

            elif tile_type == "t_intersection":
                # T-intersection allows 3 directions based on rotation
                # Rotation 0 = wall at top (blocks north, allows S/E/W)
                # Rotation 90 = wall at right (blocks east, allows N/S/W)
                # Rotation 180 = wall at bottom (blocks south, allows N/E/W)
                # Rotation 270 = wall at left (blocks west, allows N/S/E)
                if rotation == 0:
                    return ["south", "east", "west"]
                elif rotation == 90:
                    return ["north", "south", "west"]
                elif rotation == 180:
                    return ["north", "east", "west"]
                elif rotation == 270:
                    return ["north", "south", "east"]

            elif tile_type == "cross":
                # Cross allows all 4 directions
                return ["north", "south", "east", "west"]

            return []  # Unknown tile type

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
