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

# Sidebar content width ratio (for panels within the sidebar)
define SIDEBAR_CONTENT_WIDTH_RATIO = 0.314

# Minimap size ratio (relative to screen width)
define MINIMAP_SIZE_RATIO = 0.30

# ==========================================
# MAP GRID CONSTANTS
# Used in: exploration_screen.rpy, map_data.rpy, player_marker.rpy
# ==========================================

# Size of each map cell in pixels
define MAP_CELL_SIZE = 32

# Width of gridlines between map cells in pixels
define MAP_GRIDLINE_WIDTH = 2

# ==========================================
# PLAYER AND DUNGEON DEFAULTS
# Used in: map_data.rpy, exploration_init.rpy, exploration_screen.rpy
# Note: These are defaults - actual values loaded from Tiled files
# ==========================================

# Default starting position when no Tiled data available
define DEFAULT_STARTING_X = 10
define DEFAULT_STARTING_Y = 10
define DEFAULT_STARTING_ROTATION = 0

# Default view distance (how many tiles ahead player can see)
define DEFAULT_VIEW_DISTANCE = 3

# ==========================================
# UI COMPONENT CONSTANTS
# Used in: exploration_ui.rpy, player_marker.rpy
# ==========================================

# Player marker triangle size as ratio of cell size
define PLAYER_MARKER_SIZE_RATIO = 0.6

# ==========================================
# GAMEPLAY CONSTANTS
# Used in: exploration_handlers.rpy
# ==========================================

# Exploration percentage calculation weights
define EXPLORATION_TILES_WEIGHT = 0.7
define EXPLORATION_ITEMS_WEIGHT = 0.3

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

    # ==========================================
    # ROTATION AND DIRECTION MAPPING
    # Used in: interactions.rpy, exploration_state.rpy
    # ==========================================

    # Map player rotation degrees to direction letters
    ROTATION_TO_DIRECTION_MAP = {0: 'n', 90: 'e', 180: 's', 270: 'w'}
