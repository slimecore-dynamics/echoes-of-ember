# Echoes of Ember - Map Screen
# Map viewing screen for the Etrian Odyssey-style mapping system

# Main map viewing/editing screen
screen map_view():
    modal True
    zorder 100

    # Keybindings
    key "m" action Hide("map_view")
    key "M" action Hide("map_view")
    key "r" action Function(rotate_selected_tile)
    key "R" action Function(rotate_selected_tile)
    key "K_ESCAPE" action Hide("map_view")

    # Semi-transparent background
    frame:
        background "#000000cc"
        xfill True
        yfill True

    # Main map container
    frame:
        xalign 0.5
        yalign 0.5
        xsize 1200
        ysize 800
        background "#1a1a1a"

        # Map content centered in window
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 10

            # Map name centered over canvas
            if map_grid and map_grid.get_floor():
                $ current_floor = map_grid.get_floor()
                text "Map - [current_floor.floor_name]":
                    size 32
                    color "#cc0000"
                    xalign 0.5
            else:
                text "Map - No Floor":
                    size 32
                    color "#cc0000"
                    xalign 0.5

            if map_grid and map_grid.get_floor():
                # Map canvas
                use map_grid_display(current_floor)

                # Palette under canvas
                use combined_selector_panel()

                # Rotation note under palette
                text "Press R to rotate":
                    size 12
                    color "#ffffff"
                    xalign 0.5
            else:
                text "No map data available" xalign 0.5

        # Close button overlaid at top right
        textbutton "Close":
            xalign 1.0
            yalign 0.0
            xoffset -10
            yoffset 10
            action Hide("map_view")
            text_size 24

    # Tooltip display for notes
    $ tooltip_text = GetTooltip()
    if tooltip_text:
        nearrect:
            focus "tooltip"
            prefer_top True

            frame:
                background "#000000dd"
                padding (10, 10)
                xmaximum 400

                text tooltip_text:
                    size 18
                    color "#ffffff"


# Map grid display
screen map_grid_display(floor):
    $ cell_size = 32
    $ grid_width = floor.dimensions[0]
    $ grid_height = floor.dimensions[1]
    $ grid_pixel_width = grid_width * cell_size
    $ grid_pixel_height = grid_height * cell_size

    # Container with black border
    frame:
        background "#000000"
        padding (5, 5)
        xalign 0.5
        yalign 0.5

        # Blue background container
        frame:
            background "#4682b4"
            padding (0, 0)
            xsize grid_pixel_width
            ysize grid_pixel_height

            # Grid with backgrounds and borders
            grid grid_width grid_height:
                spacing 0
                for y in range(grid_height):
                    for x in range(grid_width):
                        $ tile = floor.get_tile(x, y)
                        $ icon = floor.get_icon(x, y)
                        $ note = floor.get_note(x, y)

                        # Each cell is a fixed container
                        fixed:
                            xysize (cell_size, cell_size)

                            # Cell clickable button (background layer)
                            button:
                                xysize (cell_size, cell_size)
                                background None
                                hover_background None
                                action Function(handle_grid_click, x, y)
                                if note:
                                    tooltip note

                            # Tile layer
                            if tile and tile.tile_type != "empty":
                                $ tile_image = "images/maps/tiles/{}.png".format(tile.tile_type)
                                add Transform(tile_image, xysize=(cell_size, cell_size), rotate=tile.rotation, anchor=(0.0, 0.0), offset=(-5, -5)):
                                    pos (0, 0)

                            # Grid border layer
                            add Solid("#666666", xysize=(cell_size, 1)):
                                pos (0, 0)  # Top
                            add Solid("#666666", xysize=(1, cell_size)):
                                pos (0, 0)  # Left
                            add Solid("#666666", xysize=(cell_size, 1)):
                                pos (0, cell_size - 1)  # Bottom
                            add Solid("#666666", xysize=(1, cell_size)):
                                pos (cell_size - 1, 0)  # Right

                            # Icon layer (on top)
                            if icon:
                                $ icon_image = "images/maps/icons/{}.png".format(icon.icon_type)
                                add Transform(icon_image, xysize=(cell_size, cell_size), anchor=(0.0, 0.0)):
                                    pos (0, 0)


# Combined tile and icon selector panel (horizontal palette)
screen combined_selector_panel():
    frame:
        xalign 0.5
        background "#888888"
        padding (10, 10)

        hbox:
            spacing 15

            # Tiles
            hbox:
                spacing 5
                for tile_type in TILE_TYPES:
                    $ tile_img = "images/maps/tiles/{}.png".format(tile_type)
                    $ is_selected = map_grid and map_grid.selected_tile_type == tile_type and map_grid.current_mode == "edit_tiles"

                    button:
                        xysize (38, 38)
                        background Solid("#ffff00" if is_selected else "#666666")
                        padding (3, 3)
                        action Function(select_tile_type, tile_type)

                        add tile_img:
                            xysize (32, 32)

            # Icons
            hbox:
                spacing 5
                for icon_type in ICON_TYPES:
                    $ icon_img = "images/maps/icons/{}.png".format(icon_type)
                    $ is_selected = map_grid and map_grid.selected_icon_type == icon_type and map_grid.current_mode == "edit_icons"

                    button:
                        xysize (38, 38)
                        background Solid("#ffff00" if is_selected else "#666666")
                        padding (3, 3)
                        action Function(select_icon_for_placement, icon_type)

                        add icon_img:
                            xysize (32, 32)


# Note input screen (modal)
screen add_note_input(grid_x, grid_y):
    modal True
    zorder 200

    default note_text = ""

    # Semi-transparent background
    frame:
        background "#000000dd"
        xfill True
        yfill True

    # Note input dialog
    frame:
        xalign 0.5
        yalign 0.5
        xsize 600
        ysize 300
        background "#1a1a1a"
        padding (20, 20)

        vbox:
            spacing 20
            xfill True
            yfill True

            # Title
            text "Add Note for Tile ([grid_x], [grid_y])":
                size 24
                color "#cc0000"
                xalign 0.5

            # Input field
            frame:
                background "#2a2a2a"
                xfill True
                padding (10, 10)

                input:
                    id "note_input"
                    color "#ffffff"
                    size 20
                    xfill True
                    length 200
                    value ScreenVariableInputValue("note_text")

            # Buttons
            hbox:
                spacing 20
                xalign 0.5

                textbutton "OK":
                    action [Function(confirm_note_input, grid_x, grid_y, note_text), Hide("add_note_input")]
                    text_size 24

                textbutton "Cancel":
                    action Hide("add_note_input")
                    text_size 24


# Add 'M' key to open/close map
init python:
    config.keymap['toggle_map'] = ['m', 'M']
    config.underlay.append(renpy.Keymap(toggle_map=ToggleScreen("map_view")))
