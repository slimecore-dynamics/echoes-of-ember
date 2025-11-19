# Echoes of Ember - Mapping System
# Interaction Handlers and Tool Functions

init python:
    # Available tile types
    TILE_TYPES = ["empty", "wall", "hallway", "corner", "t_intersection", "cross"]

    # Available icon types
    ICON_TYPES = ["door", "stairs_up", "stairs_down", "gathering", "event", "enemy", "teleporter", "note"]

    def select_tile_type(tile_type):
        """Select a tile type for placement"""
        global map_grid
        if map_grid and tile_type in TILE_TYPES:
            map_grid.selected_tile_type = tile_type
            map_grid.current_mode = "edit_tiles"
            renpy.restart_interaction()

    def rotate_selected_tile():
        """Rotate the currently selected tile"""
        global map_grid
        if map_grid:
            map_grid.rotate_selected_tile()
            renpy.restart_interaction()

    def handle_grid_click(x, y):
        """Handle clicking on a grid cell"""
        global map_grid
        if not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        if map_grid.current_mode == "edit_tiles":
            # Place the selected tile
            tile = MapTile(map_grid.selected_tile_type, map_grid.selected_tile_rotation)
            floor.set_tile(x, y, tile)
            # Map data is automatically saved with game saves (no explicit save needed)
            renpy.restart_interaction()

        elif map_grid.current_mode == "edit_icons":
            # Place the selected icon
            if map_grid.selected_icon_type:
                # If placing a note icon, show note dialog instead
                if map_grid.selected_icon_type == "note":
                    renpy.show_screen("add_note_input", grid_x=x, grid_y=y)
                else:
                    # Place other icons normally
                    icon = MapIcon(map_grid.selected_icon_type, (x, y))
                    floor.place_icon(x, y, icon)
                    # Map data is automatically saved with game saves (no explicit save needed)
                    renpy.restart_interaction()

    def confirm_note_input(x, y, note_text):
        """Confirm and save note input"""
        global map_grid
        if not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        # Save the note if text was entered
        if note_text and note_text.strip():
            floor.set_note(x, y, note_text.strip())
            # Also place a note icon automatically
            note_icon = MapIcon("note", (x, y))
            floor.place_icon(x, y, note_icon)
            # Map data is automatically saved with game saves (no explicit save needed)

        renpy.restart_interaction()

    def select_icon_for_placement(icon_type):
        """Select an icon type and switch to icon placement mode"""
        global map_grid
        if map_grid and icon_type in ICON_TYPES:
            map_grid.current_mode = "edit_icons"
            map_grid.selected_icon_type = icon_type
            renpy.restart_interaction()

    def remove_tile_at(x, y):
        """Clear/remove a tile at the specified position"""
        global map_grid
        if not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        tile = MapTile("empty", 0)
        floor.set_tile(x, y, tile)
        renpy.restart_interaction()

    def set_map_mode(mode):
        """Set the current map interaction mode"""
        global map_grid
        if map_grid and mode in ["view", "edit_tiles", "edit_icons", "edit_notes"]:
            map_grid.current_mode = mode
            renpy.restart_interaction()
