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

        # Tile type and rotation mappings based on image filenames
        @staticmethod
        def parse_tile_from_image(image_path):
            """
            Parse tile type and rotation from image filename.

            Returns: (tile_type, rotation)
            """
            import os
            filename = os.path.basename(image_path).replace(".png", "")

            # Handle different tile types
            if filename == "empty":
                return ("empty", 0)
            elif filename == "cross":
                return ("cross", 0)
            elif filename.startswith("hallway_"):
                # hallway_we = horizontal (W-E) = 0 degrees
                # hallway_ns = vertical (N-S) = 90 degrees
                if "we" in filename:
                    return ("hallway", 0)
                elif "ns" in filename:
                    return ("hallway", 90)
            elif filename.startswith("corner_"):
                # corner_es = E+S openings = 0 degrees
                # corner_ne = N+E openings = 270 degrees
                # corner_wn = W+N openings = 180 degrees
                # corner_ws = W+S openings = 90 degrees
                if "es" in filename:
                    return ("corner", 0)
                elif "ne" in filename:
                    return ("corner", 270)
                elif "wn" in filename:
                    return ("corner", 180)
                elif "ws" in filename:
                    return ("corner", 90)
            elif filename.startswith("t_intersection_"):
                # t_intersection_wse = W+S+E openings (blocks N) = 0 degrees
                # t_intersection_nws = N+W+S openings (blocks E) = 90 degrees
                # t_intersection_wne = W+N+E openings (blocks S) = 180 degrees
                # t_intersection_nes = N+E+S openings (blocks W) = 270 degrees
                if "wse" in filename:
                    return ("t_intersection", 0)
                elif "nws" in filename:
                    return ("t_intersection", 90)
                elif "wne" in filename:
                    return ("t_intersection", 180)
                elif "nes" in filename:
                    return ("t_intersection", 270)
            elif filename.startswith("wall_"):
                # wall_wse = W+S+E openings (blocks N) = 0 degrees
                # wall_nws = N+W+S openings (blocks E) = 90 degrees
                # wall_wne = W+N+E openings (blocks S) = 180 degrees
                # wall_nes = N+E+S openings (blocks W) = 270 degrees
                if "wse" in filename:
                    return ("wall", 0)
                elif "nws" in filename:
                    return ("wall", 90)
                elif "wne" in filename:
                    return ("wall", 180)
                elif "nes" in filename:
                    return ("wall", 270)

            # Default fallback
            return ("empty", 0)

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

            # Extract custom properties for exploration
            raw_props = tiled_data.get("properties", [])
            print("TiledImporter - Raw properties from JSON: {}".format(raw_props))
            properties = TiledImporter._extract_properties(raw_props)
            print("TiledImporter - Extracted properties dict: {}".format(properties))

            # Use floor_id from properties, or parameter, or derive from filename
            if not floor_id:
                floor_id = properties.get("floor_id", os.path.splitext(os.path.basename(filepath))[0])

            # Use floor_name from properties, or parameter
            if not floor_name:
                floor_name = properties.get("floor_name", floor_id)

            # Create FloorMap
            floor = FloorMap(floor_id, floor_name, (width, height))

            # Store exploration metadata on floor
            floor.starting_x = properties.get("starting_x", 10)
            floor.starting_y = properties.get("starting_y", 10)
            floor.starting_rotation = properties.get("starting_rotation", 0)
            floor.view_distance = properties.get("view_distance", 3)
            floor.area_name = properties.get("area_name", "")
            floor.sub_area_name = properties.get("sub_area_name", "")
            floor.description = properties.get("description", "")

            print("TiledImporter - Floor properties set: start=({},{}) rot={} view_dist={}".format(
                floor.starting_x, floor.starting_y, floor.starting_rotation, floor.view_distance
            ))

            # Build tile ID mapping from tilesets
            tile_id_map = TiledImporter._build_tile_id_map(tiled_data.get("tilesets", []))

            # Process tile layers
            layers = tiled_data.get("layers", [])
            for layer in layers:
                if layer.get("type") == "tilelayer":
                    TiledImporter._process_tile_layer(layer, floor, tile_id_map)
                elif layer.get("type") == "objectgroup":
                    TiledImporter._process_object_layer(layer, floor)

            # CRITICAL: Separate dungeon from drawn map
            # floor.tiles currently has the real dungeon from Tiled
            # We need to copy it to dungeon_tiles and clear tiles
            import copy
            floor.dungeon_tiles = copy.deepcopy(floor.tiles)

            # Clear the drawn map (player starts with blank map)
            for y in range(height):
                for x in range(width):
                    floor.set_tile(x, y, MapTile("empty", rotation=0))

            print("TiledImporter - Loaded map: {} ({}x{})".format(floor_name, width, height))
            print("TiledImporter - Dungeon tiles stored, drawn map cleared")
            return floor

        @staticmethod
        def _build_tile_id_map(tilesets):
            """
            Build mapping from Tiled tile IDs to (tile_type, rotation).

            Args:
                tilesets: List of tileset objects from Tiled JSON

            Returns:
                dict: {tiled_gid: (tile_type, rotation)}
            """
            tile_map = {}

            for tileset in tilesets:
                firstgid = tileset.get("firstgid", 1)
                tiles = tileset.get("tiles", [])

                for tile_data in tiles:
                    tile_id = tile_data.get("id", 0)
                    image_path = tile_data.get("image", "")

                    # Parse tile type and rotation from image filename
                    tile_type, rotation = TiledImporter.parse_tile_from_image(image_path)

                    # Global tile ID = firstgid + tile_id
                    gid = firstgid + tile_id
                    tile_map[gid] = (tile_type, rotation)

            return tile_map

        @staticmethod
        def _extract_properties(properties):
            """
            Extract custom properties from Tiled format.

            Tiled properties are in array format: [{"name": "x", "type": "int", "value": 10}, ...]
            """
            props = {}
            print("_extract_properties - Input type: {}".format(type(properties)))

            # Check if it's a dict first
            if isinstance(properties, dict):
                print("_extract_properties - Using dict format")
                props = properties
            # Use duck typing for list check (Ren'Py type compatibility)
            elif hasattr(properties, '__iter__') and not isinstance(properties, str):
                print("_extract_properties - Processing iterable with {} items".format(len(properties)))
                for i, prop in enumerate(properties):
                    # Use duck typing for dict check too (isinstance doesn't work in Ren'Py)
                    if hasattr(prop, 'get'):
                        name = prop.get("name")
                        value = prop.get("value")
                        print("_extract_properties - Item {}: name='{}' value='{}'".format(i, name, value))
                        props[name] = value
                    else:
                        print("_extract_properties - WARNING: Item {} has no get method: {}".format(i, prop))
                print("_extract_properties - Final props dict: {}".format(props))
            else:
                print("_extract_properties - WARNING: Unknown type!")
            return props

        @staticmethod
        def _process_tile_layer(layer, floor, tile_id_map):
            """
            Process a Tiled tile layer and populate FloorMap tiles.

            Args:
                layer: Tiled layer object
                floor: FloorMap to populate
                tile_id_map: Mapping from Tiled GID to (tile_type, rotation)
            """
            data = layer.get("data", [])
            width = layer.get("width", floor.dimensions[0])
            height = layer.get("height", floor.dimensions[1])

            for y in range(height):
                for x in range(width):
                    idx = y * width + x
                    if idx >= len(data):
                        continue

                    gid = data[idx]

                    # Tiled uses 0 for "no tile"
                    if gid == 0:
                        tile_type = "empty"
                        rotation = 0
                    else:
                        # Look up tile type and rotation from map
                        if gid in tile_id_map:
                            tile_type, rotation = tile_id_map[gid]
                        else:
                            print("TiledImporter - Warning: Unknown tile GID {} at ({}, {})".format(gid, x, y))
                            tile_type = "empty"
                            rotation = 0

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
