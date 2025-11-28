# interactions.rpy
# Handles interactions with icons (stairs, doors, gathering points, etc.)

init python:
    from collections import namedtuple

    # Named tuples for interaction results
    StepOnResult = namedtuple('StepOnResult', ['icon', 'interaction_type'])
    AdjacentResult = namedtuple('AdjacentResult', ['icon', 'interaction_type', 'adj_x', 'adj_y'])
    OnTileResult = namedtuple('OnTileResult', ['icon', 'interaction_type', 'x', 'y'])

    class InteractionHandler:
        """Manages interactions with map icons during exploration.

        Three types of interactions:
        1. Step-on triggers: gathering, event, enemy (automatic when stepping on tile)
        2. On-tile interact: teleporter (must be on tile AND facing correct direction to interact)
        3. Adjacent triggers: stairs, doors (must be adjacent and facing the icon)
        """

        # Icons that trigger automatically when stepped on
        STEP_ON_ICONS = ["gathering", "event", "enemy"]

        # Icons that require interaction while standing on them (with direction requirement)
        ON_TILE_INTERACT_ICONS = ["teleporter"]

        # Icons that trigger when adjacent and facing
        ADJACENT_ICONS = ["stairs_up", "stairs_down", "door_closed", "door_open"]

        @staticmethod
        def check_step_on_trigger(floor, x, y):
            """Check if stepping on (x, y) triggers an interaction.

            Checks dungeon_icons (real icons from Tiled), not player-drawn icons.
            Returns: StepOnResult(icon, interaction_type)
            """
            # Check dungeon icons for triggers, not player-drawn icons
            icon = floor.get_dungeon_icon(x, y)
            if not icon:
                return StepOnResult(None, None)

            if icon.icon_type in InteractionHandler.STEP_ON_ICONS:
                return StepOnResult(icon, "step_on")

            return StepOnResult(None, None)

        @staticmethod
        def check_adjacent_trigger(floor, x, y, rotation):
            """Check if there's an interactable icon adjacent to player and facing it.

            Checks dungeon_icons (real icons from Tiled), not player-drawn icons.
            For icons with prompt_facing property, only show prompt when facing the specified direction.
            Returns: AdjacentResult(icon, interaction_type, adj_x, adj_y)
            """
            # Get adjacent position based on rotation
            adj_pos = InteractionHandler._get_adjacent_position(x, y, rotation)
            if not adj_pos:
                return AdjacentResult(None, None, None, None)

            adj_x, adj_y = adj_pos

            # Check bounds
            width, height = floor.dimensions
            if adj_x < 0 or adj_x >= width or adj_y < 0 or adj_y >= height:
                return AdjacentResult(None, None, None, None)

            # Get icon at adjacent tile (from dungeon, not player-drawn)
            icon = floor.get_dungeon_icon(adj_x, adj_y)
            if not icon:
                return AdjacentResult(None, None, None, None)

            if icon.icon_type in InteractionHandler.ADJACENT_ICONS:
                # Check if icon has prompt_facing requirement
                if hasattr(icon, 'metadata') and 'prompt_facing' in icon.metadata:
                    required_facing = icon.metadata['prompt_facing'].lower()
                    # Map rotation to direction letter
                    current_dir = ROTATION_TO_DIRECTION_MAP.get(rotation, '')

                    # Only show prompt if facing the required direction
                    if current_dir != required_facing:
                        return AdjacentResult(None, None, None, None)

                return AdjacentResult(icon, "adjacent", adj_x, adj_y)

            return AdjacentResult(None, None, None, None)

        @staticmethod
        def check_on_tile_interact(floor, x, y, rotation):
            """Check if there's an interactable icon on the current tile that requires facing a direction.

            Used for teleporters - player must be on the tile AND facing the correct direction.
            Returns: OnTileResult(icon, interaction_type, x, y)
            """
            # Get icon at current position from dungeon icons
            icon = floor.get_dungeon_icon(x, y)

            if not icon:
                return OnTileResult(None, None, None, None)

            if icon.icon_type in InteractionHandler.ON_TILE_INTERACT_ICONS:
                # Check if icon has prompt_facing requirement
                if hasattr(icon, 'metadata') and 'prompt_facing' in icon.metadata:
                    required_facing = icon.metadata['prompt_facing'].lower()
                    # Map rotation to direction letter
                    current_dir = ROTATION_TO_DIRECTION_MAP.get(rotation, '')

                    # Only show prompt if facing the required direction
                    if current_dir != required_facing:
                        return OnTileResult(None, None, None, None)

                return OnTileResult(icon, "on_tile", x, y)

            return OnTileResult(None, None, None, None)

        @staticmethod
        def _get_adjacent_position(x, y, rotation):
            """Get position adjacent to (x, y) based on rotation."""
            if rotation == 0:    # North
                return (x, y - 1)
            elif rotation == 90:  # East
                return (x + 1, y)
            elif rotation == 180: # South
                return (x, y + 1)
            elif rotation == 270: # West
                return (x - 1, y)
            return None

        @staticmethod
        def handle_interaction(icon, interaction_type, player_state, floor):
            """Handle an interaction and return the result.

            Returns: dict with "type" and type-specific data
            """
            if not icon:
                return {"type": "none"}

            icon_type = icon.icon_type

            # Step-on interactions
            if icon_type == "gathering":
                # Get item type from metadata
                # Valid items: "metal scrap", "electronics", "psionic capsule", "data"
                item = icon.metadata.get("item", "metal scrap")
                amount = icon.metadata.get("amount", 1)
                return {
                    "type": "gathering",
                    "message": "You gathered {} {}!".format(amount, item),
                    "item": item,
                    "amount": amount,
                    "metadata": icon.metadata
                }

            elif icon_type == "event":
                # Check if event has a dialogue label
                event_label = icon.metadata.get("label")
                return {
                    "type": "event",
                    "message": icon.metadata.get("message", "An event occurs!"),
                    "label": event_label,
                    "metadata": icon.metadata
                }

            elif icon_type == "teleporter":
                return {
                    "type": "teleporter",
                    "message": "You step on a teleporter!",
                    "metadata": icon.metadata
                }

            elif icon_type == "enemy":
                # Enemy damages player
                damage = icon.metadata.get("damage", 10)
                player_state.take_damage(damage)
                return {
                    "type": "enemy",
                    "message": "You take {} damage!".format(damage),
                    "damage": damage,
                    "health": player_state.health
                }

            # Adjacent interactions
            elif icon_type == "stairs_up":
                return {
                    "type": "stairs_up",
                    "message": "Stairs leading up",
                    "floor_id": icon.metadata.get("target_floor")
                }

            elif icon_type == "stairs_down":
                return {
                    "type": "stairs_down",
                    "message": "Stairs leading down",
                    "floor_id": icon.metadata.get("target_floor")
                }

            elif icon_type == "door_closed":
                return {
                    "type": "door_closed",
                    "message": "A closed door blocks your path"
                }

            elif icon_type == "door_open":
                return {
                    "type": "door_open",
                    "message": "An open door"
                }

            return {"type": "unknown"}


# Global variable to store pending interaction
default pending_interaction = None
