# exploration_screen.rpy
# First-person dungeon exploration UI with integrated map view

# Colors for placeholder graphics
define color_wall = "#666666"
define color_floor = "#333333"
define color_ceiling = "#4D4D4D"
define color_door_closed = "#8B4513"
define color_door_open = "#D2B48C"
define color_interact = "#FFFF00"

# Global flag for dialogue state during exploration
default exploration_dialogue_active = False

screen exploration_view():
    """
    Main exploration screen with 2/3 left (first-person) + 1/3 right (map/controls) layout.
    """

    # Show area/floor popup when first entering
    on "show":
        action If(map_grid and map_grid.get_current_floor(),
            [Show("area_entry_popup",
                  area_name=getattr(map_grid.get_current_floor(), 'area_name', ''),
                  floor_name=getattr(map_grid.get_current_floor(), 'floor_name',
                                     map_grid.get_current_floor().floor_id if map_grid.get_current_floor() else ''))],
            None)

    # Get current floor and player state
    $ floor = map_grid.get_current_floor() if map_grid else None
    $ ps = player_state

    # Full screen container
    frame:
        xalign 0.0
        yalign 0.0
        xsize config.screen_width
        ysize config.screen_height
        padding (0, 0)
        background "#000000"

        hbox:
            spacing 0

            # LEFT 2/3: First-person view
            frame:
                xsize int(config.screen_width * 0.666)
                ysize config.screen_height
                background "#000000"
                padding (0, 0)

                if floor and ps:
                    # Get view data
                    $ view_data = FirstPersonView.get_view_data(
                        floor, ps.x, ps.y, ps.rotation,
                        view_distance=getattr(floor, 'view_distance', 3)
                    )

                    # Render first-person view
                    use render_first_person_view(view_data, floor, ps)

                    # Interaction sparkle/pulse overlay
                    $ icon, int_type, adj_x, adj_y = InteractionHandler.check_adjacent_trigger(
                        floor, ps.x, ps.y, ps.rotation
                    )

                    if icon:
                        # Show pulsing indicator in first-person view
                        add AnimatedInteractIndicator() xalign 0.5 yalign 0.7

                else:
                    text "No floor loaded" xalign 0.5 yalign 0.5 color "#FFFFFF"

            # RIGHT 1/3: Map + Controls (using existing map screen components)
            frame:
                xsize int(config.screen_width * 0.334)
                ysize config.screen_height
                background "#1A1A1A"
                padding (10, 10)

                vbox:
                    spacing 10
                    xpos 10  # Move right by 10 pixels

                    # SPACER - move everything down
                    null height 75

                    # MAP VIEW (using existing map_grid_display screen)
                    frame:
                        xsize int(config.screen_width * 0.25)
                        ysize int(config.screen_width * 0.25)  # Square viewport
                        background "#0066CC"  # Blue background
                        padding (10, 10)

                        if floor:
                            # Calculate cell size to match grid display
                            $ grid_w = floor.dimensions[0]
                            $ grid_h = floor.dimensions[1]
                            $ available_size = int(config.screen_width * 0.25) - 20
                            $ cell_size = min(available_size // grid_w, available_size // grid_h)

                            fixed:
                                # Show full map grid with tooltip info
                                use map_grid_display(floor, cell_size)

                                # Add player marker (red triangle) at player's grid position
                                if ps:
                                    add PlayerTriangleMarker(ps.x, ps.y, ps.rotation, cell_size) xpos (ps.x * cell_size) ypos (ps.y * cell_size)

                                # Display tooltip at note position (on top of everything)
                                $ tooltip_data = GetTooltip()
                                if tooltip_data:
                                    $ note_x, note_y, note_text = tooltip_data
                                    frame:
                                        xpos (note_x * cell_size)
                                        ypos (note_y * cell_size - 25)  # Above the note icon
                                        background "#000000DD"
                                        padding (5, 3)
                                        text note_text size 10 color "#FFFFFF"
                        else:
                            text "No map" xalign 0.5 yalign 0.5

                    # PALETTE - 6x4 grid with tiles and icons
                    frame:
                        xsize int(config.screen_width * 0.314)
                        ysize int(config.screen_height * 0.15)
                        background "#2A2A2A"
                        padding (10, 10)

                        # 6 columns x 4 rows
                        grid 6 4:
                            spacing 3
                            xalign 0.5

                            # Row 1: empty, corner_es, t_intersection_nes, wall_nes, door, stairs_up
                            # Row 2: cross, corner_ne, t_intersection_nws, wall_nws, enemy, stairs_down
                            # Row 3: hallway_ns, corner_wn, t_intersection_wne, wall_wne, event, teleporter
                            # Row 4: hallway_we, corner_ws, t_intersection_wse, wall_wse, gathering, note

                            for item in ["empty", "corner_es", "t_intersection_nes", "wall_nes", "door", "stairs_up",
                                        "cross", "corner_ne", "t_intersection_nws", "wall_nws", "enemy", "stairs_down",
                                        "hallway_ns", "corner_wn", "t_intersection_wne", "wall_wne", "event", "teleporter",
                                        "hallway_we", "corner_ws", "t_intersection_wse", "wall_wse", "gathering", "note"]:

                                # Determine if it's a tile or icon
                                $ is_icon = item in ["door", "stairs_up", "stairs_down", "enemy", "event", "teleporter", "gathering", "note"]

                                if is_icon:
                                    # Icon button
                                    $ icon_name = "door" if item == "door" else item
                                    $ icon_image = "images/maps/icons/{}.png".format(icon_name)
                                    $ icon_type = "door_closed" if item == "door" else item
                                    imagebutton:
                                        idle icon_image
                                        hover icon_image
                                        action Function(select_icon_for_placement, icon_type)
                                        xysize (32, 32)
                                        selected (map_grid.selected_icon_type == icon_type and map_grid.current_mode == "edit_icons" if map_grid else False)
                                        selected_background "#FFFF0080"
                                else:
                                    # Tile button
                                    $ tile_image = "images/maps/tiles/{}.png".format(item)
                                    imagebutton:
                                        idle tile_image
                                        hover tile_image
                                        action Function(select_tile_type, item)
                                        xysize (32, 32)
                                        selected (map_grid.selected_tile_type == item and map_grid.current_mode == "edit_tiles" if map_grid else False)
                                        selected_background "#FFFF0080"

                    # NAVIGATION CONTROLS
                    frame:
                        xsize int(config.screen_width * 0.314)
                        background "#2A2A2A"
                        padding (10, 10)

                        vbox:
                            spacing 8

                            # Calculate can_move for button sensitivity
                            if floor and ps:
                                $ new_x, new_y = ps.get_forward_position()
                                $ can_move, reason = MovementValidator.can_move_to(
                                    floor, ps.x, ps.y, new_x, new_y, ps.rotation
                                )
                            else:
                                $ can_move = False

                            # Forward button (text centered)
                            textbutton "Forward":
                                action Function(handle_move_forward)
                                xalign 0.5
                                xsize 100
                                ysize 40
                                text_xalign 0.5
                                sensitive (can_move and not exploration_dialogue_active)

                            # Empty line
                            null height 8

                            # Left and Right buttons (on same line, left and right aligned)
                            hbox:
                                xfill True

                                textbutton "Left":
                                    action Function(handle_turn_left)
                                    xalign 0.0
                                    xsize 100
                                    ysize 40
                                    sensitive (not exploration_dialogue_active)

                                null  # Spacer

                                textbutton "Right":
                                    action Function(handle_turn_right)
                                    xalign 1.0
                                    xsize 100
                                    ysize 40
                                    sensitive (not exploration_dialogue_active)

                            # Empty line
                            null height 8

                            # Back button (text centered)
                            textbutton "Back":
                                action Function(handle_move_backward)
                                xalign 0.5
                                xsize 100
                                ysize 40
                                text_xalign 0.5
                                sensitive (not exploration_dialogue_active)

                    # AUTO-MAP TOGGLE + LEAVE BUTTON (one line)
                    frame:
                        xsize int(config.screen_width * 0.314)
                        background "#2A2A2A"
                        padding (10, 10)

                        # Auto-Map on LEFT
                        textbutton "Auto-Map":
                            action ToggleField(map_grid, "auto_map_enabled")
                            xalign 0.0
                            xsize 200
                            ysize 35
                            selected_background "#FFFF00"
                            selected_hover_background "#FFDD00"
                            background "#444444"
                            hover_background "#555555"
                            selected (map_grid and getattr(map_grid, 'auto_map_enabled', False))
                            sensitive (not exploration_dialogue_active)

                        # Leave on RIGHT
                        textbutton "Leave":
                            action Return("exit")
                            xalign 1.0
                            xsize 90
                            ysize 35
                            sensitive (not exploration_dialogue_active)

                    # INTERACTION PROMPT (if any)
                    if floor and ps:
                        $ icon, int_type, adj_x, adj_y = InteractionHandler.check_adjacent_trigger(
                            floor, ps.x, ps.y, ps.rotation
                        )

                        if icon:
                            use compact_interaction_prompt(icon, int_type, adj_x, adj_y)


init python:
    def handle_map_click(x, y, floor, map_grid):
        """Handle clicking on a map cell to place tiles or icons."""
        if not map_grid:
            return

        if map_grid.current_mode == "edit_tiles" and map_grid.selected_tile_type:
            # Place selected tile
            tile = MapTile(map_grid.selected_tile_type, rotation=0)
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

    class PlayerTriangleMarker(renpy.Displayable):
        """Red triangle showing player position and facing direction."""

        def __init__(self, x, y, rotation, cell_size, **kwargs):
            super(PlayerTriangleMarker, self).__init__(**kwargs)
            self.x = x
            self.y = y
            self.rotation = rotation
            self.cell_size = cell_size

        def render(self, width, height, st, at):
            # Create a render the size of one cell
            render = renpy.Render(self.cell_size, self.cell_size)

            # Create simple red square as placeholder for triangle
            # (Actual triangle rendering would need more complex drawing)
            marker = Solid("#FF0000", xsize=int(self.cell_size*0.8), ysize=int(self.cell_size*0.8))
            marker_render = renpy.render(marker, int(self.cell_size*0.8), int(self.cell_size*0.8), st, at)

            # Center the marker in the cell
            render.blit(marker_render, (int(self.cell_size*0.1), int(self.cell_size*0.1)))

            return render

    class AnimatedInteractIndicator(renpy.Displayable):
        """Pulsing yellow indicator for interactions."""

        def render(self, width, height, st, at):
            # Pulse between 0.5 and 1.0 opacity
            alpha = 0.5 + 0.5 * abs(math.sin(st * 3.14))

            render = renpy.Render(100, 100)
            pulse = Solid(color_interact + "{:02x}".format(int(alpha * 255)), xsize=80, ysize=80)
            pulse_render = renpy.render(pulse, 80, 80, st, at)
            render.blit(pulse_render, (10, 10))

            renpy.redraw(self, 0.05)  # Update frequently for animation
            return render

    def get_tile_color(tile_type):
        """Get color for tile type on minimap."""
        colors = {
            "wall": "#888888",
            "hallway": "#CCCCCC",
            "corner": "#AAAAAA",
            "t_intersection": "#BBBBBB",
            "cross": "#DDDDDD",
            "empty": "#000000"
        }
        return colors.get(tile_type, "#666666")

    def get_icon_color(icon_type):
        """Get color for icon type on minimap."""
        colors = {
            "stairs_up": "#00FFFF",
            "stairs_down": "#FF00FF",
            "door_closed": "#8B4513",
            "door_open": "#D2B48C",
            "gathering": "#00FF00",
            "enemy": "#FF0000",
            "event": "#FFFF00",
            "teleporter": "#FF8800",
            "note": "#FFFFFF"
        }
        return colors.get(icon_type, "#FFFFFF")


screen map_grid_display(floor, cell_size):
    """
    Display the map grid with clickable tiles for drawing.
    This is the main map display that shows tiles, icons, and allows editing.
    """
    $ grid_w = floor.dimensions[0]
    $ grid_h = floor.dimensions[1]

    # Grid with tiles
    grid grid_w grid_h:
        spacing 0
        for y in range(grid_h):
            for x in range(grid_w):
                $ tile = floor.get_tile(x, y)
                $ icon = floor.icons.get((x, y))

                button:
                    xysize (cell_size, cell_size)
                    background "#444444"  # Grey cell background
                    action Function(handle_map_click, x, y, floor, map_grid)
                    padding (0, 0)

                    # Show tooltip for notes
                    if icon and icon.icon_type == "note":
                        tooltip (x, y, icon.metadata.get("note_text", ""))

                    # Tile (no rotation - causes offset issues)
                    if tile.tile_type != "empty":
                        add "images/maps/tiles/{}.png".format(tile.tile_type) xysize (cell_size, cell_size)

                    # Icon on top
                    if icon:
                        add "images/maps/icons/{}.png".format(icon.icon_type) xysize (cell_size, cell_size)


screen area_entry_popup(area_name, floor_name):
    """Display area and floor name when entering exploration."""

    modal True
    zorder 100

    frame:
        xalign 0.5
        yalign 0.3
        xsize 500
        background "#000000DD"
        padding (30, 30)

        vbox:
            spacing 20
            xalign 0.5

            # Area name (larger)
            if area_name:
                text area_name:
                    size 28
                    color "#FFFFFF"
                    xalign 0.5
                    text_align 0.5

            # Floor name
            if floor_name:
                text floor_name:
                    size 20
                    color "#CCCCCC"
                    xalign 0.5
                    text_align 0.5

            # Dismiss button
            textbutton "Continue":
                action Hide("area_entry_popup")
                xalign 0.5
                xsize 120
                ysize 40


screen note_input_popup(x, y, floor, map_grid):
    """Popup for entering note text when placing a note icon."""

    modal True

    default note_text = ""

    frame:
        xalign 0.5
        yalign 0.5
        xsize 400
        ysize 200
        background "#2A2A2A"
        padding (20, 20)

        vbox:
            spacing 15

            text "Enter Note (max 20 chars):" size 16 color "#FFFFFF"

            input:
                value ScreenVariableInputValue("note_text")
                length 20
                color "#FFFFFF"
                size 14
                xsize 360

            hbox:
                spacing 10
                xalign 0.5

                textbutton "OK":
                    action Function(confirm_note_placement, x, y, floor, map_grid, note_text)
                    xsize 80
                    ysize 35

                textbutton "Cancel":
                    action Hide("note_input_popup")
                    xsize 80
                    ysize 35


screen compact_interaction_prompt(icon, interaction_type, adj_x, adj_y):
    """Compact interaction prompt in right panel."""

    frame:
        xsize int(config.screen_width * 0.314)
        background "#FF0000AA"
        padding (10, 10)

        vbox:
            spacing 5

            if icon.icon_type == "stairs_up":
                text "Stairs Up" size 14 xalign 0.5
                textbutton "Climb Up":
                    action Function(handle_stairs_interaction, "up", adj_x, adj_y)
                    xalign 0.5
                    xsize 120
                    ysize 35
                    sensitive (not exploration_dialogue_active)

            elif icon.icon_type == "stairs_down":
                text "Stairs Down" size 14 xalign 0.5
                textbutton "Climb Down":
                    action Function(handle_stairs_interaction, "down", adj_x, adj_y)
                    xalign 0.5
                    xsize 120
                    ysize 35
                    sensitive (not exploration_dialogue_active)

            elif icon.icon_type == "door_closed":
                text "Closed Door" size 14 xalign 0.5
                textbutton "Open":
                    action Function(handle_door_interaction, adj_x, adj_y)
                    xalign 0.5
                    xsize 120
                    ysize 35
                    sensitive (not exploration_dialogue_active)

            elif icon.icon_type == "door_open":
                text "Open Door" size 14 xalign 0.5


screen render_first_person_view(view_data, floor, ps):
    """Render the first-person view based on view_data."""

    # Background (ceiling and floor)
    $ view_width = int(config.screen_width * 0.666)
    $ view_height = config.screen_height

    add Solid(color_ceiling) xpos 0 ypos 0 xsize view_width ysize int(view_height / 2)
    add Solid(color_floor) xpos 0 ypos int(view_height / 2) xsize view_width ysize int(view_height / 2)

    # Simple wall rendering if blocked
    if not view_data.get("can_move_forward", False):
        # Show wall ahead
        add Solid(color_wall) xpos int(view_width * 0.2) ypos int(view_height * 0.2) xsize int(view_width * 0.6) ysize int(view_height * 0.6)

    # Text overlay showing what's ahead (temporary placeholder)
    $ tiles = view_data.get("tiles", [])
    if tiles:
        text "Ahead: {} tiles visible".format(len(tiles)) xalign 0.5 ypos 20 color "#FFFFFF" size 16


# Navigation and interaction handlers (from original file, unchanged)
init python:
    import math  # For AnimatedInteractIndicator

    def calculate_exploration_percent(floor):
        """
        Calculate exploration percentage.

        Formula: (tiles_drawn / total_walkable) * 0.7 + (discovered_items / total_items) * 0.3
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

        # Weighted average (70% tiles, 30% items)
        exploration = (tile_pct * 0.7) + (item_pct * 0.3)

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

    def handle_turn_left():
        """Rotate player 90 degrees left"""
        global player_state
        if player_state:
            player_state.rotate_left()
            renpy.restart_interaction()

    def handle_turn_right():
        """Rotate player 90 degrees right"""
        global player_state
        if player_state:
            player_state.rotate_right()
            renpy.restart_interaction()

    def handle_move_forward():
        """Move player one tile forward"""
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
        """Move player one tile backward"""
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

    def auto_reveal_tile(floor, x, y):
        """Auto-reveal tile when walking on it - copy from dungeon to drawn map."""
        # Get the REAL tile from dungeon
        if hasattr(floor, 'dungeon_tiles') and floor.dungeon_tiles:
            if y < len(floor.dungeon_tiles) and x < len(floor.dungeon_tiles[y]):
                dungeon_tile = floor.dungeon_tiles[y][x]

                if dungeon_tile and dungeon_tile.tile_type != "empty":
                    # Copy dungeon tile to drawn map
                    import copy
                    floor.set_tile(x, y, copy.deepcopy(dungeon_tile))

                    # Initialize revealed_tiles set if it doesn't exist
                    if not hasattr(floor, 'revealed_tiles'):
                        floor.revealed_tiles = set()

                    # Add this tile to revealed tiles
                    floor.revealed_tiles.add((x, y))

    def handle_step_on_trigger(icon, floor, x, y):
        """Handle step-on interactions (gathering, event, teleporter, enemy)"""
        global player_state, exploration_dialogue_active

        result = InteractionHandler.handle_interaction(icon, "step_on", player_state, None)

        if result["type"] == "enemy":
            renpy.notify("You take {} damage! Health: {}".format(
                result["damage"], result["health"]
            ))
        elif result["type"] == "gathering":
            # Mark as discovered
            icon.metadata["discovered"] = True
            # Show debug notification with item and amount
            item = result.get("item", "unknown")
            amount = result.get("amount", 1)
            renpy.notify("DEBUG: Gathered {} x{} at ({}, {})".format(item, amount, x, y))
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
            # Get pair_id from teleporter metadata
            pair_id = result.get("metadata", {}).get("pair_id")

            if pair_id is not None:
                # Find matching teleporter with same pair_id
                target_teleporter = None
                target_pos = None

                # Search dungeon_icons for another teleporter with same pair_id
                if hasattr(floor, 'dungeon_icons'):
                    for pos, other_icon in floor.dungeon_icons.items():
                        # Skip the current teleporter
                        if pos == (x, y):
                            continue

                        # Check if it's a teleporter with matching pair_id
                        if (other_icon.icon_type == "teleporter" and
                            other_icon.metadata.get("pair_id") == pair_id):
                            target_teleporter = other_icon
                            target_pos = pos
                            break

                if target_pos:
                    # Teleport player to target position
                    player_state.x, player_state.y = target_pos
                    renpy.notify("Teleported to ({}, {})".format(target_pos[0], target_pos[1]))

                    # Trigger auto-map reveal at new location if enabled
                    if getattr(player_state, 'auto_map_enabled', False):
                        reveal_nearby_tiles(floor, target_pos[0], target_pos[1], player_state.rotation)

                    renpy.restart_interaction()
                else:
                    renpy.notify("Teleporter pair not found (pair_id: {})".format(pair_id))
            else:
                renpy.notify("Teleporter has no pair_id")

    def handle_stairs_interaction(direction, adj_x, adj_y):
        """Handle stairs interaction (change floors)"""
        global player_state, map_grid

        if not map_grid:
            return

        current_floor = map_grid.get_current_floor()
        if not current_floor:
            return

        # Get current floor ID and calculate target floor
        current_id = current_floor.floor_id

        # Extract numeric part of floor ID (e.g., "floor_1" -> 1)
        try:
            floor_num = int(current_id.split("_")[-1])
            if direction == "up":
                target_num = floor_num - 1
            else:  # down
                target_num = floor_num + 1

            target_id = "floor_{}".format(target_num)

            # Check if target floor exists
            if target_id in map_grid.floors:
                # Switch floor
                map_grid.switch_floor(target_id)
                player_state.current_floor_id = target_id

                # Get starting position for new floor
                new_floor = map_grid.get_floor(target_id)
                player_state.x = getattr(new_floor, 'starting_x', 10)
                player_state.y = getattr(new_floor, 'starting_y', 10)
                player_state.rotation = getattr(new_floor, 'starting_rotation', 0)

                renpy.notify("Moved to {}".format(new_floor.floor_name))
                renpy.restart_interaction()
            else:
                renpy.notify("No floor {} exists".format(target_id))
        except:
            renpy.notify("Cannot determine target floor")

    def handle_door_interaction(adj_x, adj_y):
        """Handle door interaction (open door)"""
        global map_grid

        if not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        # Get icon at door position
        icon = floor.icons.get((adj_x, adj_y))
        if icon and icon.icon_type == "door_closed":
            # Change door to open
            icon.icon_type = "door_open"
            renpy.notify("Door opened")
            renpy.restart_interaction()

    # Map editing functions (delegated to map_tools if available)
    def select_tile_type(tile_type):
        """Select tile type for placement."""
        global map_grid
        if map_grid:
            map_grid.selected_tile_type = tile_type
            map_grid.current_mode = "edit_tiles"
            renpy.restart_interaction()

    def select_icon_for_placement(icon_type):
        """Select icon type for placement."""
        global map_grid
        if map_grid:
            map_grid.selected_icon_type = icon_type
            map_grid.current_mode = "edit_icons"
            renpy.restart_interaction()

    def rotate_selected_tile():
        """Rotate the currently selected tile."""
        global map_grid
        if map_grid:
            map_grid.rotate_selected_tile()
            renpy.restart_interaction()
