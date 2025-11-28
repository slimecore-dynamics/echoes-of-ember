# variables.rpy
# Central location for all exploration system constants and configuration values

# ==========================================
# SCREEN LAYOUT CONSTANTS
# Used in: exploration_screen.rpy
# ==========================================

# First-person view takes up 2/3 of screen width
define FIRST_PERSON_VIEW_WIDTH_RATIO = 0.666

# Map sidebar takes up 1/3 of screen width
define MAP_VIEW_WIDTH_RATIO = 0.334

# ==========================================
# MAP GRID CONSTANTS
# Used in: exploration_screen.rpy, map_data.rpy, player_marker.rpy
# ==========================================

# Size of each map cell in pixels
define MAP_CELL_SIZE = 32

# Width of gridlines between map cells in pixels
define MAP_GRIDLINE_WIDTH = 2

# ==========================================
# LEGACY COLOR DEFINES
# Used in: exploration_screen.rpy (for compatibility)
# Note: New code should use color palettes below
# ==========================================

define color_wall = "#666666"
define color_floor = "#333333"
define color_ceiling = "#4D4D4D"
define color_door_closed = "#8B4513"
define color_door_open = "#D2B48C"
define color_interact = "#FFFF00"

# ==========================================
# COLOR PALETTES
# Used in: exploration_ui.rpy, exploration_screen.rpy
# ==========================================

init python:
    # First-Person View Colors
    # Used for rendering walls, floors, ceilings in FPV
    FPV_COLORS = {
        "wall": "#666666",
        "floor": "#333333",
        "ceiling": "#4D4D4D",
        "door_closed": "#8B4513",
        "door_open": "#D2B48C",
        "interact": "#FFFF00"
    }

    # Map Tile Colors
    # Used for rendering tile types on the minimap
    TILE_COLORS = {
        "wall": "#888888",
        "hallway": "#CCCCCC",
        "corner": "#AAAAAA",
        "t_intersection": "#BBBBBB",
        "cross": "#DDDDDD",
        "empty": "#000000"
    }

    # Map Icon Colors
    # Used for rendering icon types on the minimap
    ICON_COLORS = {
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

    # UI Colors
    # Used throughout exploration screens for consistent theming
    UI_COLORS = {
        "background": "#000000",
        "sidebar": "#1A1A1A",
        "panel": "#2A2A2A",
        "button": "#444444",
        "button_hover": "#555555",
        "button_selected": "#FFFF00",
        "button_selected_hover": "#FFDD00",
        "hover_transparent": "#FFFFFF40",
        "transparent": "#00000000",
        "text": "#FFFFFF",
        "border": "#000000",
        "minimap_bg": "#0066CC",
        "tooltip_bg": "#000000DD",
        "gridlines": "#555555",
        "cell_highlight": "#0066CC",
        "interaction_warning": "#FF0000AA"
    }
