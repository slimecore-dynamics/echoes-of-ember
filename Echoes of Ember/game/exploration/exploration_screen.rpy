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

default map_grid = None

screen exploration_view():
    # Main exploration screen with 2/3 left (first-person) + 1/3 right (map/controls) layout.

    # Show floor notification when first entering
    on "show":
        action If(map_grid and map_grid.get_current_floor(),
            Function(renpy.notify, "{}\n{}".format(
                getattr(map_grid.get_current_floor(), 'area_name', 'Unknown Area'),
                getattr(map_grid.get_current_floor(), 'floor_name', map_grid.get_current_floor().floor_id if map_grid.get_current_floor() else ''))),
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
                    python:
                        # Check for adjacent triggers (stairs, doors)
                        icon, int_type, adj_x, adj_y = InteractionHandler.check_adjacent_trigger(
                            floor, ps.x, ps.y, ps.rotation
                        )

                        # If no adjacent trigger, check for on-tile interactions (teleporter)
                        if not icon:
                            icon, int_type, tile_x, tile_y = InteractionHandler.check_on_tile_interact(
                                floor, ps.x, ps.y, ps.rotation
                            )
                            if icon:
                                adj_x, adj_y = tile_x, tile_y

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

                    # MAP VIEW - Three layers: black border, blue background, grid with gridlines
                    if floor:
                        # Grid dimensions from floor
                        $ grid_w = floor.dimensions[0]
                        $ grid_h = floor.dimensions[1]

                        # Calculate sizes accounting for gridlines
                        $ gridline_width = 2
                        $ border_thickness = 3
                        $ available_size = int(config.screen_width * 0.30) - 20 - (border_thickness * 2)

                        # Cell size accounting for gridlines between cells
                        $ cell_size = min(
                            (available_size - gridline_width * (grid_w - 1)) // grid_w,
                            (available_size - gridline_width * (grid_h - 1)) // grid_h
                        )

                        # Actual grid size (cells + gridlines)
                        $ grid_width = cell_size * grid_w + gridline_width * (grid_w - 1)
                        $ grid_height = cell_size * grid_h + gridline_width * (grid_h - 1)

                        # Black border frame (slightly larger than grid)
                        frame:
                            xsize (grid_width + border_thickness * 2)
                            ysize (grid_height + border_thickness * 2)
                            xalign 0.5  # Center horizontally in right third
                            background "#000000"  # Black border
                            padding (border_thickness, border_thickness)

                            # Blue background frame (exact grid size)
                            frame:
                                xsize grid_width
                                ysize grid_height
                                background "#0066CC"  # Blue background
                                padding (0, 0)

                                fixed:
                                    xysize (grid_width, grid_height)

                                    # Show full map grid with gridlines
                                    use map_grid_display(floor, cell_size, gridline_width)

                                    # Add player marker (red triangle) at player's grid position
                                    if ps:
                                        # Position accounting for gridlines
                                        $ marker_x = ps.x * (cell_size + gridline_width)
                                        $ marker_y = ps.y * (cell_size + gridline_width)
                                        add PlayerTriangleMarker(ps.x, ps.y, ps.rotation, cell_size) xpos marker_x ypos marker_y

                                    # Display tooltip at note position (on top of everything)
                                    $ tooltip_data = GetTooltip()
                                    if tooltip_data:
                                        $ note_x, note_y, note_text = tooltip_data
                                        $ tooltip_x = note_x * (cell_size + gridline_width)
                                        $ tooltip_y = note_y * (cell_size + gridline_width) - 25
                                        frame:
                                            xpos tooltip_x
                                            ypos tooltip_y
                                            background "#000000DD"
                                            padding (5, 3)
                                            text note_text size 10 color "#FFFFFF"
                    else:
                        # No floor loaded placeholder
                        frame:
                            xsize int(config.screen_width * 0.30)
                            ysize int(config.screen_width * 0.30)
                            xalign 0.5
                            background "#000000"
                            padding (10, 10)
                            text "No map" xalign 0.5 yalign 0.5

                    # PALETTE - Two grids: tiles (left) and icons (right)
                    frame:
                        xsize int(config.screen_width * 0.314)
                        background "#2A2A2A"
                        padding (10, 10)

                        hbox:
                            spacing 10
                            xfill True

                            # TILES GRID (left-aligned): 8 columns x 2 rows
                            grid 8 2:
                                spacing 6
                                xalign 0.0

                                # Row 1: empty | corner_es | corner_wn | hallway_ns | t_intersection_nes | t_intersection_wne | wall_nes | wall_wne
                                # Row 2: cross | corner_ne | corner_ws | hallway_we | t_intersection_nws | t_intersection_wse | wall_nws | wall_wse
                                for tile_type in ["empty", "corner_es", "corner_wn", "hallway_ns", "t_intersection_nes", "t_intersection_wne", "wall_nes", "wall_wne",
                                                "cross", "corner_ne", "corner_ws", "hallway_we", "t_intersection_nws", "t_intersection_wse", "wall_nws", "wall_wse"]:
                                    $ tile_image = "images/maps/tiles/{}.png".format(tile_type)
                                    button:
                                        xysize (36, 36)
                                        padding (2, 2)
                                        action Function(select_tile_type, tile_type)
                                        selected (map_grid.selected_tile_type == tile_type and map_grid.current_mode == "edit_tiles" if map_grid else False)
                                        selected_background "#FFFF00"
                                        background "#00000000"
                                        hover_background "#FFFFFF40"

                                        # Use fixed container to prevent image from blocking clicks
                                        fixed:
                                            fit_first True
                                            add tile_image xysize (32, 32)

                            # ICONS GRID (right-aligned): 5 columns x 2 rows
                            grid 5 2:
                                spacing 6
                                xalign 1.0

                                # Row 1: door_open | enemy | gathering | stairs_down | note
                                # Row 2: door_closed | event | teleporter | stairs_up | (empty slot)
                                for icon_type in ["door_open", "enemy", "gathering", "stairs_down", "note",
                                                "door_closed", "event", "teleporter", "stairs_up"]:
                                    $ icon_image = "images/maps/icons/{}.png".format(icon_type)
                                    button:
                                        xysize (36, 36)
                                        padding (2, 2)
                                        action Function(select_icon_for_placement, icon_type)
                                        selected (map_grid.selected_icon_type == icon_type and map_grid.current_mode == "edit_icons" if map_grid else False)
                                        selected_background "#FFFF00"
                                        background "#00000000"
                                        hover_background "#FFFFFF40"

                                        # Use fixed container to prevent image from blocking clicks
                                        fixed:
                                            fit_first True
                                            add icon_image xysize (32, 32)

                                # Empty slot for grid layout
                                null xysize (36, 36)

                    # NAVIGATION CONTROLS
                    frame:
                        xsize int(config.screen_width * 0.314)
                        background "#2A2A2A"
                        padding (10, 10)

                        vbox:
                            spacing 4
                            xfill True

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
                                padding (20, 8)
                                text_xalign 0.5
                                background "#444444"
                                hover_background "#555555"
                                sensitive (can_move and not exploration_dialogue_active)

                            # Left and Right buttons (on same line, left and right aligned)
                            hbox:
                                xfill True

                                textbutton "Left":
                                    action Function(handle_turn_left)
                                    xalign 0.0
                                    padding (20, 8)
                                    background "#444444"
                                    hover_background "#555555"
                                    sensitive (not exploration_dialogue_active)

                                null  # Spacer

                                textbutton "Right":
                                    action Function(handle_turn_right)
                                    xalign 1.0
                                    padding (20, 8)
                                    background "#444444"
                                    hover_background "#555555"
                                    sensitive (not exploration_dialogue_active)

                            # Back button (text centered)
                            textbutton "Back":
                                action Function(handle_move_backward)
                                xalign 0.5
                                padding (20, 8)
                                text_xalign 0.5
                                background "#444444"
                                hover_background "#555555"
                                sensitive (not exploration_dialogue_active)

                    # AUTO-MAP TOGGLE + LEAVE BUTTON (one line)
                    frame:
                        xsize int(config.screen_width * 0.314)
                        background "#2A2A2A"
                        padding (10, 10)

                        hbox:
                            spacing 10
                            xfill True

                            # Auto-Map on LEFT
                            textbutton "Auto-Map":
                                action ToggleField(map_grid, "auto_map_enabled")
                                xalign 0.0
                                padding (20, 8)
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
                                padding (20, 8)
                                background "#444444"
                                hover_background "#555555"
                                sensitive (not exploration_dialogue_active)

                    # INTERACTION PROMPT (if any)
                    if floor and ps:
                        python:
                            # Check for adjacent triggers (stairs, doors)
                            icon, int_type, adj_x, adj_y = InteractionHandler.check_adjacent_trigger(
                                floor, ps.x, ps.y, ps.rotation
                            )

                            # If no adjacent trigger, check for on-tile interactions (teleporter)
                            if not icon:
                                icon, int_type, tile_x, tile_y = InteractionHandler.check_on_tile_interact(
                                    floor, ps.x, ps.y, ps.rotation
                                )
                                if icon:
                                    adj_x, adj_y = tile_x, tile_y

                        if icon:
                            use compact_interaction_prompt(icon, int_type, adj_x, adj_y)


init python:
    def handle_map_click(x, y, floor, map_grid):
        # Handle clicking on a map cell to place tiles or icons.
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
        # Confirm note placement with text from input.
        # Hide the popup
        renpy.hide_screen("note_input_popup")

        # Create note icon with text in metadata
        icon = MapIcon("note", (x, y), metadata={"note_text": note_text})
        floor.place_icon(x, y, icon)

        renpy.restart_interaction()

    def select_tile_type(tile_type):
        # Select a tile type from the palette.
        if map_grid:
            map_grid.selected_tile_type = tile_type
            map_grid.selected_icon_type = None
            map_grid.current_mode = "edit_tiles"
            renpy.restart_interaction()

    def select_icon_for_placement(icon_type):
        # Select an icon type from the palette.
        if map_grid:
            map_grid.selected_icon_type = icon_type
            map_grid.selected_tile_type = None
            map_grid.current_mode = "edit_icons"
            renpy.restart_interaction()

    class PlayerTriangleMarker(renpy.Displayable):
        # Red triangle showing player position and facing direction.

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


screen map_grid_display(floor, cell_size, gridline_width):
    # Display the map grid with clickable tiles for drawing.
    # Grid has dark grey background that shows through spacing as gridlines.
    # Tiles fit exactly within cells with no gaps.
    $ grid_w = floor.dimensions[0]
    $ grid_h = floor.dimensions[1]

    # Calculate exact grid size including gridlines
    $ total_grid_w = cell_size * grid_w + gridline_width * (grid_w - 1)
    $ total_grid_h = cell_size * grid_h + gridline_width * (grid_h - 1)

    # Dark grey container for gridlines (explicitly sized)
    frame:
        xsize total_grid_w
        ysize total_grid_h
        background "#555555"  # Dark grey gridlines
        padding (0, 0)

        # Grid with spacing for gridlines
        grid grid_w grid_h:
            spacing gridline_width
            for y in range(grid_h):
                for x in range(grid_w):
                    $ tile = floor.get_tile(x, y)
                    $ icon = floor.icons.get((x, y))

                    button:
                        xysize (cell_size, cell_size)
                        background "#0066CC"  # Blue cell background
                        action Function(handle_map_click, x, y, floor, map_grid)
                        padding (0, 0)

                        # Show tooltip for notes
                        if icon and icon.icon_type == "note":
                            tooltip (x, y, icon.metadata.get("note_text", ""))

                        # Tile image (fills cell exactly)
                        if tile.tile_type != "empty":
                            add "images/maps/tiles/{}.png".format(tile.tile_type):
                                xysize (cell_size, cell_size)

                        # Icon on top (fills cell exactly)
                        if icon:
                            add "images/maps/icons/{}.png".format(icon.icon_type):
                                xysize (cell_size, cell_size)


screen note_input_popup(x, y, floor, map_grid):
    # Popup for entering note text when placing a note icon.

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
    # Compact interaction prompt in right panel.

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

            elif icon.icon_type == "teleporter":
                text "Teleporter" size 14 xalign 0.5
                textbutton "Use":
                    action Function(handle_teleporter_interaction, adj_x, adj_y)
                    xalign 0.5
                    xsize 120
                    ysize 35
                    sensitive (not exploration_dialogue_active)


screen render_first_person_view(view_data, floor, ps):
    # Render the first-person view based on view_data.

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

        # For now, just show a notification (only one floor exists)
        # TODO: Implement multi-floor navigation when more floors are added
        if direction == "up":
            renpy.notify("Stairs up (no destination floor)")
        else:
            renpy.notify("Stairs down (no destination floor)")

    def handle_door_interaction(adj_x, adj_y):
        """Handle door interaction (open door)"""
        global map_grid

        if not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        # Get icon at door position from dungeon icons
        icon = floor.dungeon_icons.get((adj_x, adj_y)) if hasattr(floor, 'dungeon_icons') else floor.icons.get((adj_x, adj_y))
        if icon and icon.icon_type == "door_closed":
            # Change door to open
            icon.icon_type = "door_open"
            renpy.notify("Door opened")
            renpy.restart_interaction()

    def handle_teleporter_interaction(adj_x, adj_y):
        """
        Handle teleporter interaction (teleport to paired teleporter).
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
        icon = floor.dungeon_icons.get((adj_x, adj_y)) if hasattr(floor, 'dungeon_icons') else floor.icons.get((adj_x, adj_y))
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
                if getattr(player_state, 'auto_map_enabled', False):
                    reveal_nearby_tiles(floor, target_pos[0], target_pos[1], player_state.rotation)

                renpy.restart_interaction()
            else:
                renpy.notify("Teleporter pair not found (pair_id: {})".format(pair_id))
        else:
            renpy.notify("Teleporter has no pair_id")

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
        # Rotate the currently selected tile.
        global map_grid
        if map_grid:
            map_grid.rotate_selected_tile()
            renpy.restart_interaction()
