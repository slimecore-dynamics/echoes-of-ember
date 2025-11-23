# map_data.rpy
# Core data structures for dungeon mapping and exploration

init -2 python:
    class MapTile:
        # Represents a single tile on the map.
        def __init__(self, tile_type, rotation=0):
            self.tile_type = tile_type  # "empty", "hallway", "corner", etc.
            self.rotation = rotation    # 0, 90, 180, 270

    class MapIcon:
        # Represents an icon placed on the map (stairs, doors, enemies, etc.).
        def __init__(self, icon_type, position, metadata=None):
            self.icon_type = icon_type  # "stairs_up", "door_closed", "enemy", etc.
            self.position = position    # (x, y) tuple
            self.metadata = metadata or {}  # Additional data

    class FloorMap:
        # Represents a single floor/level of a dungeon.
        def __init__(self, floor_id, floor_name, dimensions):
            self.floor_id = floor_id
            self.floor_name = floor_name
            self.dimensions = dimensions  # (width, height)

            # Drawn map (player-created) - starts empty
            self.tiles = []
            for y in range(dimensions[1]):
                row = []
                for x in range(dimensions[0]):
                    row.append(MapTile("empty", 0))
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

        def get_tile(self, x, y):
            # Get tile at position (returns drawn map tile).
            if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
                return self.tiles[y][x]
            return MapTile("empty", 0)

        def set_tile(self, x, y, tile):
            # Set tile at position (updates drawn map).
            if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
                self.tiles[y][x] = tile

        def place_icon(self, x, y, icon):
            # Place an icon at position.
            self.icons[(x, y)] = icon

        def remove_icon(self, x, y):
            # Remove icon at position.
            if (x, y) in self.icons:
                del self.icons[(x, y)]

    class MapGrid:
        # Container for all floors and mapping state.
        def __init__(self):
            self.floors = {}  # {floor_id: FloorMap}
            self.current_floor_id = None
            self.cell_size = 32
            self.auto_map_enabled = False

            # Palette selection state
            self.selected_tile_type = "empty"
            self.selected_icon_type = None
            self.current_mode = "edit_tiles"  # "edit_tiles" or "edit_icons"

        def get_current_floor(self):
            # Get the currently active floor.
            if self.current_floor_id and self.current_floor_id in self.floors:
                return self.floors[self.current_floor_id]
            return None
