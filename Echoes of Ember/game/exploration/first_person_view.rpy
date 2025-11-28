# first_person_view.rpy
# Renders first-person dungeon view with occlusion

init python:
    class FirstPersonView:
        """Calculates and renders first-person view of the dungeon.

        Shows up to X tiles ahead in the direction player is facing,
        with walls and obstacles blocking the view.
        """

        @staticmethod
        def get_view_data(floor, player_x, player_y, player_rotation, view_distance=3):
            """Calculate what the player can see ahead.

            Returns: dict with view information
            {
                "tiles": [(x, y, tile, distance), ...],
                "icons": [(x, y, icon, distance), ...],
                "blocked_at": distance or None,
                "can_move_forward": bool
            }
            """
            if not floor:
                return {"tiles": [], "icons": [], "blocked_at": None, "can_move_forward": False}

            # Get direction delta
            dx, dy = FirstPersonView._get_direction_delta(player_rotation)

            tiles_ahead = []
            icons_ahead = []
            blocked_at = None
            can_move_forward = False

            # Trace forward up to view_distance
            for dist in range(1, view_distance + 1):
                look_x = player_x + (dx * dist)
                look_y = player_y + (dy * dist)

                # Check bounds
                width, height = floor.dimensions
                if look_x < 0 or look_x >= width or look_y < 0 or look_y >= height:
                    blocked_at = dist
                    break

                # Get tile
                tile = floor.get_tile(look_x, look_y)
                if not tile:
                    blocked_at = dist
                    break

                # Add tile to view
                tiles_ahead.append((look_x, look_y, tile, dist))

                # Check for icon
                icon = floor.icons.get((look_x, look_y))
                if icon:
                    icons_ahead.append((look_x, look_y, icon, dist))

                # Check if this is the first tile (adjacent) - can we move there?
                if dist == 1:
                    can_move, reason = MovementValidator.can_move_to(
                        floor, player_x, player_y, look_x, look_y, player_rotation
                    )
                    can_move_forward = can_move

                # Check if tile blocks view
                if FirstPersonView._tile_blocks_view(tile, player_rotation, dx, dy):
                    blocked_at = dist
                    break

                # Check if icon blocks view
                if icon and FirstPersonView._icon_blocks_view(icon):
                    blocked_at = dist
                    break

            return {
                "tiles": tiles_ahead,
                "icons": icons_ahead,
                "blocked_at": blocked_at,
                "can_move_forward": can_move_forward,
                "view_distance": view_distance
            }

        @staticmethod
        def _get_direction_delta(rotation):
            """Get (dx, dy) for rotation."""
            if rotation == 0:    # North
                return (0, -1)
            elif rotation == 90:  # East
                return (1, 0)
            elif rotation == 180: # South
                return (0, 1)
            elif rotation == 270: # West
                return (-1, 0)
            return (0, 0)

        @staticmethod
        def _tile_blocks_view(tile, player_rotation, dx, dy):
            """Check if a tile blocks the view ahead.

            Returns True if tile is a wall/obstacle that blocks line of sight.
            """
            tile_type = tile.tile_type

            # Empty blocks view (void)
            if tile_type == "empty":
                return True

            # Check if we're trying to look through a wall face
            # Wall blocks view when looking at the solid face
            if tile_type == "wall":
                # wall rotation 0 = solid face north
                # If looking north (dy = -1) and wall rotation is 0, blocked
                if tile.rotation == 0 and dy == -1:  # Looking north at north-facing wall
                    return True
                elif tile.rotation == 90 and dx == 1:  # Looking east at east-facing wall
                    return True
                elif tile.rotation == 180 and dy == 1:  # Looking south at south-facing wall
                    return True
                elif tile.rotation == 270 and dx == -1:  # Looking west at west-facing wall
                    return True

            # T-intersection blocks view through the wall side
            if tile_type == "t_intersection":
                # rotation 0 = wall at north
                if tile.rotation == 0 and dy == -1:
                    return True
                elif tile.rotation == 90 and dx == 1:
                    return True
                elif tile.rotation == 180 and dy == 1:
                    return True
                elif tile.rotation == 270 and dx == -1:
                    return True

            # Hallways, corners, and crosses don't block view
            return False

        @staticmethod
        def _icon_blocks_view(icon):
            """Check if an icon blocks the view.

            Returns True if icon is a solid obstacle.
            """
            # Closed doors block view
            if icon.icon_type == "door_closed":
                return True

            # Most other icons don't block view
            return False

        @staticmethod
        def get_wall_configuration(floor, x, y):
            """Get information about walls around a tile for rendering.

            Returns: dict with wall info for north/south/east/west
            """
            tile = floor.get_tile(x, y)
            if not tile:
                return {"north": True, "south": True, "east": True, "west": True}

            # Get allowed directions from tile
            allowed_dirs = MovementValidator._get_allowed_directions(tile)

            # Walls exist in directions NOT allowed
            return {
                "north": "north" not in allowed_dirs,
                "south": "south" not in allowed_dirs,
                "east": "east" not in allowed_dirs,
                "west": "west" not in allowed_dirs
            }
