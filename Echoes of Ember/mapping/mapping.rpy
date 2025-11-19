# Echoes of Ember - Mapping System
# Core Data Classes with Serialization Support
# Based on: mapping_implementation_plan.md v3.0 and mapping_file_io_specification.md v1.0

init python:
    import json

    class MapTile:
        """
        Individual grid cell tile

        Attributes:
            tile_type: Type of tile ("empty", "wall", "hallway", "corner", "t_intersection", "cross")
            rotation: Rotation in degrees (0, 90, 180, 270)
        """

        VALID_TYPES = ["empty", "wall", "hallway", "corner", "t_intersection", "cross"]
        VALID_ROTATIONS = [0, 90, 180, 270]

        def __init__(self, tile_type="empty", rotation=0):
            # Validate inputs
            if tile_type not in self.VALID_TYPES:
                tile_type = "empty"
            if rotation not in self.VALID_ROTATIONS:
                rotation = 0

            self.tile_type = tile_type
            self.rotation = rotation

        def to_dict(self):
            """Serialize to dictionary for JSON/persistent storage"""
            return {
                "type": self.tile_type,
                "rotation": self.rotation
            }

        @staticmethod
        def from_dict(data):
            """Deserialize from dictionary"""
            return MapTile(
                tile_type=data.get("type", "empty"),
                rotation=data.get("rotation", 0)
            )

        def rotate_clockwise(self):
            """Rotate tile 90 degrees clockwise"""
            rotation_cycle = [0, 90, 180, 270]
            current_index = rotation_cycle.index(self.rotation)
            next_index = (current_index + 1) % len(rotation_cycle)
            self.rotation = rotation_cycle[next_index]

        def rotate_counterclockwise(self):
            """Rotate tile 90 degrees counterclockwise"""
            rotation_cycle = [0, 90, 180, 270]
            current_index = rotation_cycle.index(self.rotation)
            prev_index = (current_index - 1) % len(rotation_cycle)
            self.rotation = rotation_cycle[prev_index]

        def __repr__(self):
            return f"MapTile(type={self.tile_type}, rotation={self.rotation}°)"


    class MapIcon:
        """
        Map marker/icon for points of interest

        Attributes:
            icon_type: Type of icon ("door", "stairs_up", "stairs_down", "enemy", etc.)
            position: (x, y) tuple coordinates on grid
            metadata: Optional dictionary for additional data
        """

        VALID_TYPES = [
            "door", "stairs_up", "stairs_down", "gathering",
            "event", "enemy", "teleporter", "note"
        ]

        def __init__(self, icon_type, position, metadata=None):
            if icon_type not in self.VALID_TYPES:
                icon_type = "event"  # Default fallback

            self.icon_type = icon_type
            self.position = tuple(position)  # Ensure tuple
            self.metadata = metadata or {}

        def to_dict(self):
            """Serialize to dictionary"""
            return {
                "type": self.icon_type,
                "position": list(self.position),  # Convert tuple to list for JSON
                "metadata": self.metadata
            }

        @staticmethod
        def from_dict(data):
            """Deserialize from dictionary"""
            return MapIcon(
                icon_type=data.get("type", "event"),
                position=tuple(data.get("position", (0, 0))),
                metadata=data.get("metadata", {})
            )

        def __repr__(self):
            return f"MapIcon(type={self.icon_type}, pos={self.position})"


    class FloorMap:
        """
        Individual floor/level map data

        Attributes:
            floor_id: Unique identifier string
            floor_name: Display name string
            dimensions: (width, height) tuple in cells
            tiles: 2D array of MapTile objects
            icons: Dictionary mapping (x,y) to MapIcon objects
            notes: Dictionary mapping (x,y) to note text strings
        """

        def __init__(self, floor_id, floor_name, dimensions=(20, 20)):
            self.floor_id = floor_id
            self.floor_name = floor_name
            self.dimensions = tuple(dimensions)
            self.tiles = self._initialize_tiles()
            self.icons = {}  # {(x,y): MapIcon}
            self.notes = {}  # {(x,y): "note text"}

        def _initialize_tiles(self):
            """Create empty 2D tile array"""
            width, height = self.dimensions
            return [[MapTile() for _ in range(width)] for _ in range(height)]

        def get_tile(self, x, y):
            """Get tile at coordinates (with bounds checking)"""
            width, height = self.dimensions
            if 0 <= x < width and 0 <= y < height:
                return self.tiles[y][x]
            return None

        def set_tile(self, x, y, tile):
            """Set tile at coordinates (with bounds checking)"""
            width, height = self.dimensions
            if 0 <= x < width and 0 <= y < height:
                self.tiles[y][x] = tile
                return True
            return False

        def place_icon(self, x, y, icon):
            """Place icon at coordinates"""
            self.icons[(x, y)] = icon

        def remove_icon(self, x, y):
            """Remove icon at coordinates"""
            if (x, y) in self.icons:
                del self.icons[(x, y)]
                return True
            return False

        def get_icon(self, x, y):
            """Get icon at coordinates"""
            return self.icons.get((x, y))

        def add_note(self, x, y, note_text):
            """Add or update note at coordinates"""
            self.notes[(x, y)] = note_text

        def set_note(self, x, y, note_text):
            """Alias for add_note - set or update note at coordinates"""
            self.add_note(x, y, note_text)

        def remove_note(self, x, y):
            """Remove note at coordinates"""
            if (x, y) in self.notes:
                del self.notes[(x, y)]
                return True
            return False

        def get_note(self, x, y):
            """Get note at coordinates"""
            return self.notes.get((x, y))

        def to_dict(self):
            """Serialize floor to dictionary"""
            return {
                "floor_id": self.floor_id,
                "floor_name": self.floor_name,
                "dimensions": list(self.dimensions),
                "tiles": [
                    [tile.to_dict() for tile in row]
                    for row in self.tiles
                ],
                "icons": {
                    "{},{}".format(x, y): icon.to_dict()
                    for (x, y), icon in self.icons.items()
                },
                "notes": {
                    "{},{}".format(x, y): note
                    for (x, y), note in self.notes.items()
                }
            }

        @staticmethod
        def from_dict(data):
            """Deserialize floor from dictionary"""
            floor = FloorMap(
                floor_id=data["floor_id"],
                floor_name=data["floor_name"],
                dimensions=tuple(data["dimensions"])
            )

            # Restore tiles
            floor.tiles = [
                [MapTile.from_dict(tile_data) for tile_data in row]
                for row in data["tiles"]
            ]

            # Restore icons
            floor.icons = {
                tuple(map(int, pos.split(','))): MapIcon.from_dict(icon_data)
                for pos, icon_data in data.get("icons", {}).items()
            }

            # Restore notes
            floor.notes = {
                tuple(map(int, pos.split(','))): note
                for pos, note in data.get("notes", {}).items()
            }

            return floor

        def __repr__(self):
            return f"FloorMap(id={self.floor_id}, name='{self.floor_name}', size={self.dimensions})"


    class MapGrid:
        """
        Container for all map data

        Attributes:
            grid_size: Default (width, height) for new floors
            cell_size: Pixel size for rendering each cell
            floors: Dictionary of {floor_id: FloorMap}
            current_floor: ID of active floor
            auto_map_enabled: Boolean for auto-reveal feature
            version: Data format version string
        """

        DATA_VERSION = "1.0"

        def __init__(self, grid_size=(20, 20), cell_size=64):
            self.grid_size = tuple(grid_size)
            self.cell_size = cell_size
            self.floors = {}  # {floor_id: FloorMap}
            self.current_floor = None
            self.auto_map_enabled = True
            self.version = self.DATA_VERSION

            # Editor state
            self.current_mode = "view"  # "view", "edit_tiles", "edit_icons", "edit_notes"
            self.selected_tile_type = "hallway"
            self.selected_tile_rotation = 0
            self.selected_icon_type = None

        def add_floor(self, floor_id, floor_name, dimensions=None):
            """
            Add a new floor to the map

            Args:
                floor_id: Unique identifier
                floor_name: Display name
                dimensions: Optional (width, height) tuple, uses grid_size if None

            Returns:
                The created FloorMap object
            """
            if dimensions is None:
                dimensions = self.grid_size

            floor = FloorMap(floor_id, floor_name, dimensions)
            self.floors[floor_id] = floor

            # Set as current if first floor
            if self.current_floor is None:
                self.current_floor = floor_id

            return floor

        def remove_floor(self, floor_id):
            """Remove a floor from the map"""
            if floor_id in self.floors:
                del self.floors[floor_id]

                # Update current_floor if needed
                if self.current_floor == floor_id:
                    if self.floors:
                        self.current_floor = list(self.floors.keys())[0]
                    else:
                        self.current_floor = None

                return True
            return False

        def get_floor(self, floor_id=None):
            """
            Get floor by ID, or current floor if no ID provided

            Args:
                floor_id: Optional floor ID, uses current_floor if None

            Returns:
                FloorMap object or None
            """
            if floor_id is None:
                floor_id = self.current_floor

            return self.floors.get(floor_id)

        def switch_floor(self, floor_id):
            """Switch to a different floor"""
            if floor_id in self.floors:
                self.current_floor = floor_id
                return True
            return False

        def get_current_floor(self):
            """Get the currently active floor (convenience method)"""
            return self.get_floor()

        def rotate_selected_tile(self):
            """Rotate the selected tile 90 degrees clockwise"""
            rotation_cycle = [0, 90, 180, 270]
            current_index = rotation_cycle.index(self.selected_tile_rotation)
            next_index = (current_index + 1) % len(rotation_cycle)
            self.selected_tile_rotation = rotation_cycle[next_index]

        def to_dict(self):
            """Serialize entire map grid to dictionary"""
            return {
                "version": self.version,
                "grid_size": list(self.grid_size),
                "cell_size": self.cell_size,
                "auto_map_enabled": self.auto_map_enabled,
                "current_floor": self.current_floor,
                "floors": {
                    floor_id: floor.to_dict()
                    for floor_id, floor in self.floors.items()
                }
            }

        @staticmethod
        def from_dict(data):
            """Deserialize map grid from dictionary"""
            grid = MapGrid(
                grid_size=tuple(data.get("grid_size", (20, 20))),
                cell_size=data.get("cell_size", 64)
            )

            grid.version = data.get("version", MapGrid.DATA_VERSION)
            grid.auto_map_enabled = data.get("auto_map_enabled", True)
            grid.current_floor = data.get("current_floor")

            # Restore all floors
            grid.floors = {
                floor_id: FloorMap.from_dict(floor_data)
                for floor_id, floor_data in data.get("floors", {}).items()
            }

            return grid

        def __repr__(self):
            floor_count = len(self.floors)
            return f"MapGrid(floors={floor_count}, current={self.current_floor})"


# Global map grid instance
# Will be initialized in start_mapping_system or loaded from save
# NOTE: This is NOT automatically saved by Ren'Py - we use external JSON files
default map_grid = None
