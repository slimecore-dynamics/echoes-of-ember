# exploration_handlers.rpy
# Handler functions for exploration: movement, interactions, map editing

init python:
    import math

    # === MAP EDITING HANDLERS ===

    def handle_map_click(x, y, floor, map_grid):
        """Handle clicking on a map cell to place tiles or icons."""
        if not map_grid:
            return

        if map_grid.current_mode == "edit_tiles" and map_grid.selected_tile_type:
            # Place selected tile
            tile = MapTile(map_grid.selected_tile_type)
            floor.set_tile(x, y, tile)
            renpy.restart_interaction()

        elif map_grid.current_mode == "edit_icons" and map_grid.selected_icon_type:
            # Special handling for note icons - show input popup
            if map_grid.selected_icon_type == "note":
                renpy.show_screen("note_input_popup", x, y, floor, map_grid)
            else:
                # Place selected icon
                icon = MapIcon(map_grid.selected_icon_type, (x, y))
                floor.place_icon(x, y, icon)
                renpy.restart_interaction()

    def confirm_note_placement(x, y, floor, map_grid, note_text):
        """Confirm note placement with text from input."""
        # Hide the popup
        renpy.hide_screen("note_input_popup")

        # Create note icon with text in metadata
        icon = MapIcon("note", (x, y), metadata={"note_text": note_text})
        floor.place_icon(x, y, icon)

        renpy.restart_interaction()

    def select_tile_type(tile_type):
        """Select a tile type from the palette."""
        if map_grid:
            map_grid.selected_tile_type = tile_type
            map_grid.selected_icon_type = None
            map_grid.current_mode = "edit_tiles"
            renpy.restart_interaction()

    def select_icon_for_placement(icon_type):
        """Select an icon type from the palette."""
        if map_grid:
            map_grid.selected_icon_type = icon_type
            map_grid.selected_tile_type = None
            map_grid.current_mode = "edit_icons"
            renpy.restart_interaction()

    # === UTILITY FUNCTIONS ===

    def calculate_exploration_percent(floor):
        """Calculate exploration percentage.

        Formula uses weights from variables.rpy:
        (tiles_drawn / total_walkable) * EXPLORATION_TILES_WEIGHT + (discovered_items / total_items) * EXPLORATION_ITEMS_WEIGHT
        """
        if not floor:
            return 0

        # Count total walkable tiles
        total_walkable = 0
        tiles_drawn = 0

        for y in range(floor.dimensions[1]):
            for x in range(floor.dimensions[0]):
                tile = floor.get_tile(x, y)
                if tile and tile.tile_type != "empty":
                    total_walkable += 1
                    # Count as "drawn" if tile type is not empty
                    if tile.tile_type != "empty":
                        tiles_drawn += 1

        # Count discoverable items (gathering points and notes)
        total_items = 0
        discovered_items = 0

        for (icon_x, icon_y), icon in floor.icons.items():
            if icon.icon_type in ["gathering", "note"]:
                total_items += 1
                # Mark as discovered if metadata has "discovered" flag
                if icon.metadata.get("discovered", False):
                    discovered_items += 1

        # Calculate percentages
        tile_pct = (float(tiles_drawn) / float(total_walkable)) if total_walkable > 0 else 0.0
        item_pct = (float(discovered_items) / float(total_items)) if total_items > 0 else 0.0

        # Weighted average (defined in variables.rpy)
        exploration = (tile_pct * EXPLORATION_TILES_WEIGHT) + (item_pct * EXPLORATION_ITEMS_WEIGHT)

        # Round to nearest percent
        return int(round(exploration * 100))

    def toggle_auto_map():
        """Toggle auto-mapping on/off - ONLY toggles, does not exit."""
        global map_grid

        if not map_grid:
            return

        # Initialize auto_map_enabled if it doesn't exist
        if not hasattr(map_grid, 'auto_map_enabled'):
            map_grid.auto_map_enabled = False

        # Toggle the flag
        map_grid.auto_map_enabled = not map_grid.auto_map_enabled

        # Show notification
        status = "ON" if map_grid.auto_map_enabled else "OFF"
        renpy.notify("Auto-map: " + status)

        # Restart interaction to update UI
        renpy.restart_interaction()

    def auto_reveal_tile(floor, x, y):
        """Auto-reveal tile when walking on it - copy from dungeon to drawn map."""
        # Get the REAL tile from dungeon
        if hasattr(floor, 'dungeon_tiles') and floor.dungeon_tiles:
            if y < len(floor.dungeon_tiles) and x < len(floor.dungeon_tiles[y]):
                dungeon_tile = floor.dungeon_tiles[y][x]

                if dungeon_tile and dungeon_tile.tile_type != "empty":
                    # Copy tile type from dungeon to drawn map
                    floor.set_tile(x, y, MapTile(dungeon_tile.tile_type))

    # === MOVEMENT HANDLERS ===

    def handle_turn_left():
        """Rotate player 90 degrees left."""
        global player_state
        if player_state:
            player_state.rotate_left()
            renpy.restart_interaction()

    def handle_turn_right():
        """Rotate player 90 degrees right."""
        global player_state
        if player_state:
            player_state.rotate_right()
            renpy.restart_interaction()

    def handle_move_forward():
        """Move player one tile forward."""
        global player_state, map_grid

        if not player_state or not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        # Get forward position
        new_x, new_y = player_state.get_forward_position()

        # Validate movement
        can_move, reason = MovementValidator.can_move_to(
            floor, player_state.x, player_state.y, new_x, new_y, player_state.rotation
        )

        if can_move:
            # Move player
            player_state.set_position(new_x, new_y)

            # Auto-map: reveal tile if enabled
            if getattr(map_grid, 'auto_map_enabled', False):
                auto_reveal_tile(floor, new_x, new_y)

            # Check for step-on triggers
            icon, trigger_type = InteractionHandler.check_step_on_trigger(floor, new_x, new_y)
            if icon:
                handle_step_on_trigger(icon, floor, new_x, new_y)

            renpy.restart_interaction()
        else:
            renpy.notify("Cannot move: {}".format(reason))

    def handle_move_backward():
        """Move player one tile backward."""
        global player_state, map_grid

        if not player_state or not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        # Get backward position
        new_x, new_y = player_state.get_backward_position()

        # Validate movement
        can_move, reason = MovementValidator.can_move_to(
            floor, player_state.x, player_state.y, new_x, new_y, player_state.rotation
        )

        if can_move:
            # Move player
            player_state.set_position(new_x, new_y)

            # Auto-map: reveal tile if enabled
            if getattr(map_grid, 'auto_map_enabled', False):
                auto_reveal_tile(floor, new_x, new_y)

            # Check for step-on triggers
            icon, trigger_type = InteractionHandler.check_step_on_trigger(floor, new_x, new_y)
            if icon:
                handle_step_on_trigger(icon, floor, new_x, new_y)

            renpy.restart_interaction()
        else:
            renpy.notify("Cannot move: {}".format(reason))

    # === INTERACTION HANDLERS ===

    def handle_step_on_trigger(icon, floor, x, y):
        """Handle step-on interactions (gathering, event, teleporter, enemy)."""
        global player_state, exploration_dialogue_active

        result = InteractionHandler.handle_interaction(icon, "step_on", player_state, None)

        if result["type"] == "enemy":
            renpy.notify("You take {} damage! Health: {}".format(
                result["damage"], result["health"]
            ))
        elif result["type"] == "gathering":
            # Mark as discovered
            icon.metadata["discovered"] = True
            item = result.get("item", "unknown")
            amount = result.get("amount", 1)
            renpy.notify("Gathered {} x{}".format(item, amount))
        elif result["type"] == "event":
            # Check if event has a dialogue label
            if "label" in result and result["label"]:
                # Set dialogue active flag to disable UI
                exploration_dialogue_active = True

                # Call dialogue label in new context (overlays exploration screen)
                renpy.call_in_new_context(result["label"])

                # Dialogue finished, re-enable UI
                exploration_dialogue_active = False
                renpy.restart_interaction()
            else:
                # No label, just show notification
                renpy.notify(result["message"])
        elif result["type"] == "teleporter":
            # Use the dedicated teleporter interaction handler
            handle_teleporter_interaction(x, y)

    def handle_stairs_interaction(direction, adj_x, adj_y):
        """Handle stairs interaction (change floors)."""
        global player_state, map_grid

        if not map_grid:
            return

        current_floor = map_grid.get_current_floor()
        if not current_floor:
            return

        # For now, just show a notification (only one floor exists)
        # TODO: Implement multi-floor navigation when more floors are added
        if direction == "up":
            renpy.notify("Stairs up (no destination floor)")
        else:
            renpy.notify("Stairs down (no destination floor)")

    def handle_door_interaction(adj_x, adj_y):
        """Handle door interaction (open door)."""
        global map_grid

        if not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        # Get icon at door position from dungeon icons
        icon = floor.get_dungeon_icon(adj_x, adj_y)
        if icon and icon.icon_type == "door_closed":
            # Change door to open
            icon.icon_type = "door_open"
            renpy.notify("Door opened")
            renpy.restart_interaction()

    def handle_teleporter_interaction(adj_x, adj_y):
        """Handle teleporter interaction (teleport to paired teleporter).

        Player must be standing on teleporter and facing correct direction.
        """
        global player_state, map_grid

        if not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        # Get icon at current teleporter position from dungeon icons
        # (adj_x, adj_y are actually the player's current position for on-tile interactions)
        icon = floor.get_dungeon_icon(adj_x, adj_y)
        if not icon or icon.icon_type != "teleporter":
            return

        # Get pair_id from teleporter metadata
        pair_id = icon.metadata.get("pair_id")

        if pair_id is not None:
            # Find matching teleporter with same pair_id
            target_pos = None

            # Search dungeon_icons for another teleporter with same pair_id
            if hasattr(floor, 'dungeon_icons'):
                for pos, other_icon in floor.dungeon_icons.items():
                    # Skip the current teleporter
                    if pos == (adj_x, adj_y):
                        continue

                    # Check if it's a teleporter with matching pair_id
                    if (other_icon.icon_type == "teleporter" and
                        other_icon.metadata.get("pair_id") == pair_id):
                        target_pos = pos
                        break

            if target_pos:
                # Teleport player to target position
                player_state.x, player_state.y = target_pos
                renpy.notify("Teleported to ({}, {})".format(target_pos[0], target_pos[1]))

                # Trigger auto-map reveal at new location if enabled
                if getattr(map_grid, 'auto_map_enabled', False):
                    auto_reveal_tile(floor, target_pos[0], target_pos[1])

                renpy.restart_interaction()
            else:
                renpy.notify("Teleporter pair not found (pair_id: {})".format(pair_id))
        else:
            renpy.notify("Teleporter has no pair_id")
