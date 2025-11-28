# map_data.rpy
# Core data structures for dungeon mapping and exploration

init -2 python:
    class MapTile:
        """Represents a single tile on the map."""
        def __init__(self, tile_type):
            self.tile_type = tile_type  # "empty", "hallway", "corner", etc.

    class MapIcon:
        """Represents an icon placed on the map (stairs, doors, enemies, etc.).

        WARNING: Position Duplication Issue
        ------------------------------------
        The position data is stored in TWO places:
        1. As self.position attribute in this MapIcon instance
        2. As the dictionary key in floor.icons: {(x, y): MapIcon}

        This duplication can lead to inconsistencies if:
        - An icon's position attribute is modified without updating the dict key
        - An icon is moved to a new position without removing the old dict entry

        Current usage patterns that avoid this issue:
        - Icons are created with position and never moved
        - Icons are removed via floor.remove_icon(x, y) which uses the dict key
        - Icon position is read from the dict key, not from icon.position

        Future refactoring options:
        - Remove self.position attribute, always use dict key
        - Add a move_icon() method that maintains consistency
        - Make position a read-only property that reads from parent floor
        """
        def __init__(self, icon_type, position, metadata=None):
            self.icon_type = icon_type  # "stairs_up", "door_closed", "enemy", etc.
            self.position = position    # (x, y) tuple - WARNING: duplicates dict key!
            self.metadata = metadata or {}  # Additional data

    class FloorMap:
        """Represents a single floor/level of a dungeon."""
        def __init__(self, floor_id, floor_name, dimensions):
            self.floor_id = floor_id
            self.floor_name = floor_name
            self.dimensions = dimensions  # (width, height)

            # Drawn map (player-created) - starts empty
            self.tiles = []
            for y in range(dimensions[1]):
                row = []
                for x in range(dimensions[0]):
                    row.append(MapTile("empty"))
                self.tiles.append(row)

            # Real dungeon tiles (from Tiled JSON) - for movement validation
            # This is the actual dungeon layout that the player navigates
            self.dungeon_tiles = None

            # Player-drawn icons (visible on map)
            self.icons = {}  # {(x, y): MapIcon}

            # Real dungeon icons (from Tiled JSON) - for collision and interaction
            # This is separate from player-drawn icons
            self.dungeon_icons = {}  # {(x, y): MapIcon}

            # Revealed tiles (for auto-map)
            self.revealed_tiles = set()  # {(x, y), ...}

            # Metadata from Tiled JSON
            self.starting_x = 10
            self.starting_y = 10
            self.starting_rotation = 0
            self.view_distance = 3
            self.area_name = ""
            self.sub_area_name = ""
            self.description = ""

            # Path to Tiled JSON file for reloading dungeon layout
            # This gets pickled so we can reload dungeon_tiles after loading saves
            self.current_dungeon_file = None

            # Whether this floor is accessible (for story progression)
            # When False, story should not allow entering this floor
            # But map data is preserved for potential gallery/review features
            self.accessible = True

        def get_tile(self, x, y):
            """Get tile at position (returns drawn map tile)."""
            if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
                return self.tiles[y][x]
            return MapTile("empty")

        def set_tile(self, x, y, tile):
            """Set tile at position (updates drawn map)."""
            if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
                self.tiles[y][x] = tile

        def place_icon(self, x, y, icon):
            """Place an icon at position."""
            self.icons[(x, y)] = icon

        def remove_icon(self, x, y):
            """Remove icon at position."""
            if (x, y) in self.icons:
                del self.icons[(x, y)]

        def get_dungeon_icon(self, x, y):
            """Get real dungeon icon at position (for collision/interaction).

            Returns dungeon icon if it exists, otherwise returns None.
            Dungeon icons represent the actual game world, not player-drawn icons.
            """
            if hasattr(self, 'dungeon_icons') and self.dungeon_icons:
                return self.dungeon_icons.get((x, y))
            return None

        def get_dungeon_tile(self, x, y):
            """Get real dungeon tile at position (for movement validation).

            Returns dungeon tile if it exists, falls back to drawn map.
            """
            if hasattr(self, 'dungeon_tiles') and self.dungeon_tiles:
                if 0 <= y < len(self.dungeon_tiles) and 0 <= x < len(self.dungeon_tiles[y]):
                    return self.dungeon_tiles[y][x]
            return self.get_tile(x, y)  # Fallback to drawn map

        def __getstate__(self):
            """Custom pickle: exclude dungeon_tiles and dungeon_icons from saves.

            These are large and should be reloaded from Tiled files, not pickled.
            This prevents bloating save files with dungeon layout data.
            """
            state = self.__dict__.copy()
            del state['dungeon_tiles']
            state['dungeon_icons'] = {}
            return state

        def __setstate__(self, state):
            """Custom unpickle: restore attributes."""
            self.__dict__.update(state)
            # dungeon_tiles won't exist after unpickling (will be set by callback)
            # dungeon_icons will be {} after unpickling

    class MapGrid:
        """Container for all floors and mapping state."""
        def __init__(self):
            self.floors = {}  # {floor_id: FloorMap}
            self.current_floor_id = None
            self.cell_size = MAP_CELL_SIZE  # Defined in variables.rpy
            self.auto_map_enabled = False

            # Palette selection state
            self.selected_tile_type = "empty"
            self.selected_icon_type = None
            self.current_mode = "edit_tiles"  # "edit_tiles" or "edit_icons"

        def get_current_floor(self):
            """Get the currently active floor."""
            if self.current_floor_id and self.current_floor_id in self.floors:
                return self.floors[self.current_floor_id]
            return None
