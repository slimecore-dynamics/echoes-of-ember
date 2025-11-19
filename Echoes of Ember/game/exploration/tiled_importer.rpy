# tiled_importer.rpy
# Import dungeon layouts from Tiled JSON format

init python:
    import json
    import os

    class TiledImporter:
        """
        Import dungeon maps from Tiled Map Editor JSON format.

        Tiled Format: https://doc.mapeditor.org/en/stable/reference/json-map-format/
        """

        # Mapping from Tiled tile IDs to our tile types
        # These can be customized based on your Tiled tileset
        TILE_ID_MAP = {
            0: "empty",
            1: "wall",
            2: "hallway",
            3: "corner",
            4: "t_intersection",
            5: "cross"
        }

        # Mapping from Tiled object types to icon types
        OBJECT_TYPE_MAP = {
            "stairs_up": "stairs_up",
            "stairs_down": "stairs_down",
            "door": "door_closed",
            "door_closed": "door_closed",
            "door_open": "door_open",
            "teleporter": "teleporter",
            "gathering": "gathering",
            "event": "event",
            "enemy": "enemy",
            "note": "note"
        }

        @staticmethod
        def load_tiled_map(filepath, floor_id=None, floor_name=None):
            """
            Load a Tiled JSON map and convert to FloorMap.

            Args:
                filepath: Path to Tiled JSON file (relative to game directory)
                floor_id: Optional floor ID (defaults to filename)
                floor_name: Optional floor name (defaults to Tiled map name)

            Returns:
                FloorMap instance, or None on failure
            """
            # Resolve path relative to game directory
            full_path = os.path.join(renpy.config.gamedir, filepath)

            if not os.path.exists(full_path):
                print("TiledImporter - File not found: {}".format(full_path))
                return None

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    tiled_data = json.load(f)
            except Exception as e:
                print("TiledImporter - Failed to load JSON: {}".format(e))
                return None

            # Extract map properties
            width = tiled_data.get("width", 20)
            height = tiled_data.get("height", 20)

            # Use floor_id or derive from filename
            if not floor_id:
                floor_id = os.path.splitext(os.path.basename(filepath))[0]

            # Use floor_name or Tiled map name
            if not floor_name:
                floor_name = tiled_data.get("properties", {}).get("name", floor_id)

            # Create FloorMap
            floor = FloorMap(floor_id, floor_name, (width, height))

            # Extract custom properties for exploration
            properties = TiledImporter._extract_properties(tiled_data.get("properties", []))

            # Store exploration metadata on floor (extend FloorMap)
            floor.starting_x = properties.get("starting_x", 10)
            floor.starting_y = properties.get("starting_y", 10)
            floor.starting_rotation = properties.get("starting_rotation", 0)
            floor.view_distance = properties.get("view_distance", 3)

            # Process tile layers
            layers = tiled_data.get("layers", [])
            for layer in layers:
                if layer.get("type") == "tilelayer":
                    TiledImporter._process_tile_layer(layer, floor)
                elif layer.get("type") == "objectgroup":
                    TiledImporter._process_object_layer(layer, floor)

            print("TiledImporter - Loaded map: {} ({}x{})".format(floor_name, width, height))
            return floor

        @staticmethod
        def _extract_properties(properties):
            """
            Extract custom properties from Tiled format.

            Tiled properties are in array format: [{"name": "x", "type": "int", "value": 10}, ...]
            """
            props = {}
            if isinstance(properties, list):
                for prop in properties:
                    name = prop.get("name")
                    value = prop.get("value")
                    props[name] = value
            elif isinstance(properties, dict):
                # Some Tiled versions use dict format
                props = properties
            return props

        @staticmethod
        def _process_tile_layer(layer, floor):
            """
            Process a Tiled tile layer and populate FloorMap tiles.

            Tiled data format: {"data": [tile_id, tile_id, ...], "width": w, "height": h}
            """
            data = layer.get("data", [])
            width = layer.get("width", floor.dimensions[0])
            height = layer.get("height", floor.dimensions[1])

            for y in range(height):
                for x in range(width):
                    idx = y * width + x
                    if idx >= len(data):
                        continue

                    tile_id = data[idx]

                    # Handle rotation/flipping flags (Tiled encodes these in high bits)
                    # Extract actual tile ID (lower 28 bits)
                    FLIPPED_HORIZONTALLY_FLAG = 0x80000000
                    FLIPPED_VERTICALLY_FLAG = 0x40000000
                    FLIPPED_DIAGONALLY_FLAG = 0x20000000

                    flipped_h = bool(tile_id & FLIPPED_HORIZONTALLY_FLAG)
                    flipped_v = bool(tile_id & FLIPPED_VERTICALLY_FLAG)
                    flipped_d = bool(tile_id & FLIPPED_DIAGONALLY_FLAG)

                    # Clear flags to get actual tile ID
                    tile_id = tile_id & ~(FLIPPED_HORIZONTALLY_FLAG | FLIPPED_VERTICALLY_FLAG | FLIPPED_DIAGONALLY_FLAG)

                    # Convert Tiled tile ID to our tile type
                    # Tiled uses 0 for "no tile", we use 1+ for actual tiles
                    if tile_id == 0:
                        tile_type = "empty"
                        rotation = 0
                    else:
                        # Subtract 1 because Tiled uses 1-indexed tiles
                        adjusted_id = tile_id - 1
                        tile_type = TiledImporter.TILE_ID_MAP.get(adjusted_id, "empty")

                        # Calculate rotation from flip flags
                        rotation = TiledImporter._calculate_rotation(flipped_h, flipped_v, flipped_d)

                    # Create and set tile
                    tile = MapTile(tile_type, rotation)
                    floor.set_tile(x, y, tile)

        @staticmethod
        def _calculate_rotation(flipped_h, flipped_v, flipped_d):
            """
            Calculate rotation from Tiled flip flags.

            Tiled uses flip flags for rotation. Common mappings:
            - No flip: 0°
            - Diagonal flip: 90°
            - H+V flip: 180°
            - H+V+D flip: 270°
            """
            if flipped_d and not flipped_h and not flipped_v:
                return 90
            elif flipped_h and flipped_v and not flipped_d:
                return 180
            elif flipped_d and flipped_h and flipped_v:
                return 270
            else:
                return 0

        @staticmethod
        def _process_object_layer(layer, floor):
            """
            Process a Tiled object layer and populate FloorMap icons.

            Objects represent stairs, doors, enemies, etc.
            """
            objects = layer.get("objects", [])

            for obj in objects:
                # Get object position (Tiled uses pixel coordinates, convert to grid)
                pixel_x = obj.get("x", 0)
                pixel_y = obj.get("y", 0)
                tile_width = obj.get("width", 32)  # Assuming 32px tiles
                tile_height = obj.get("height", 32)

                # Convert pixel to grid coordinates
                grid_x = int(pixel_x / 32)
                grid_y = int(pixel_y / 32)

                # Get object type
                obj_type = obj.get("type", "").lower()
                if not obj_type:
                    obj_name = obj.get("name", "").lower()
                    obj_type = obj_name

                # Map to our icon type
                icon_type = TiledImporter.OBJECT_TYPE_MAP.get(obj_type)
                if not icon_type:
                    print("TiledImporter - Unknown object type: {}".format(obj_type))
                    continue

                # Extract custom properties
                properties = TiledImporter._extract_properties(obj.get("properties", []))

                # Create icon
                icon = MapIcon(icon_type, (grid_x, grid_y), metadata=properties)
                floor.place_icon(grid_x, grid_y, icon)

        @staticmethod
        def save_floor_as_tiled_json(floor, filepath):
            """
            Export FloorMap to Tiled JSON format (for round-tripping).

            This is optional - allows editing in Tiled after generation.
            """
            # TODO: Implement if needed for level editor workflows
            pass
