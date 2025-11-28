# exploration_screen.rpy
# First-person dungeon exploration UI with integrated map view
# Constants are defined in variables.rpy

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

    # Check for interactions ONCE per frame (used by both indicator and prompt)
    python:
        current_interaction = None
        interaction_pos = (0, 0)
        if floor and ps:
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
                current_interaction = (icon, int_type, adj_x, adj_y)
                interaction_pos = (adj_x, adj_y)

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
                xsize int(config.screen_width * FIRST_PERSON_VIEW_WIDTH_RATIO)
                ysize config.screen_height
                background UI_COLORS["background"]
                padding (0, 0)

                if floor and ps:
                    # Get view data
                    $ view_data = FirstPersonView.get_view_data(
                        floor, ps.x, ps.y, ps.rotation,
                        view_distance=getattr(floor, 'view_distance', DEFAULT_VIEW_DISTANCE)
                    )

                    # Render first-person view
                    use render_first_person_view(view_data, floor, ps)

                    # Show pulsing indicator if there's an interaction available
                    if current_interaction:
                        add AnimatedInteractIndicator() xalign 0.5 yalign 0.7

                else:
                    text "No floor loaded" xalign 0.5 yalign 0.5 color "#FFFFFF"

            # RIGHT 1/3: Map + Controls (using existing map screen components)
            frame:
                xsize int(config.screen_width * MAP_VIEW_WIDTH_RATIO)
                ysize config.screen_height
                background UI_COLORS["sidebar"]
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
                        $ available_size = int(config.screen_width * MINIMAP_SIZE_RATIO) - 20 - (border_thickness * 2)

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
                            xsize int(config.screen_width * MINIMAP_SIZE_RATIO)
                            ysize int(config.screen_width * MINIMAP_SIZE_RATIO)
                            xalign 0.5
                            background "#000000"
                            padding (10, 10)
                            text "No map" xalign 0.5 yalign 0.5

                    # PALETTE - Two grids: tiles (left) and icons (right)
                    frame:
                        xsize int(config.screen_width * SIDEBAR_CONTENT_WIDTH_RATIO)
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
                        xsize int(config.screen_width * SIDEBAR_CONTENT_WIDTH_RATIO)
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
                        xsize int(config.screen_width * SIDEBAR_CONTENT_WIDTH_RATIO)
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
                    if current_interaction:
                        $ icon, int_type, adj_x, adj_y = current_interaction
                        use compact_interaction_prompt(icon, int_type, adj_x, adj_y)



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
    $ view_width = int(config.screen_width * FIRST_PERSON_VIEW_WIDTH_RATIO)
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

