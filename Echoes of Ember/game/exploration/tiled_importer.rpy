# tiled_importer.rpy
# Import dungeon layouts from Tiled JSON format

init python:
    import json
    import os

    class TiledImporter:
        # Import dungeon maps from Tiled Map Editor JSON format.
        # Tiled Format: https://doc.mapeditor.org/en/stable/reference/json-map-format/

        # Tile type parsing based on image filenames
        @staticmethod
        def parse_tile_from_image(image_path):
            # Parse tile type from image filename.
            # Rotation is no longer used - always returns 0.
            # Returns: (tile_type, rotation)
            import os
            filename = os.path.basename(image_path).replace(".png", "")

            # Return the full filename as tile_type (no suffix stripping)
            # Examples: hallway_we, corner_ws, t_intersection_nws, wall_nes, cross, empty
            return (filename, 0)

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
            # Load a Tiled JSON map and convert to FloorMap.
            #
            # Args:
            #     filepath: Path to Tiled JSON file (relative to game directory)
            #     floor_id: Optional floor ID (defaults to filename)
            #     floor_name: Optional floor name (defaults to Tiled map name)
            #
            # Returns:
            #     FloorMap instance, or None on failure
            # Resolve path relative to game directory
            full_path = os.path.join(renpy.config.gamedir, filepath)

            if not os.path.exists(full_path):
                return None

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    tiled_data = json.load(f)
            except Exception as e:
                return None

            # Extract map properties
            width = tiled_data.get("width", 20)
            height = tiled_data.get("height", 20)

            # Extract custom properties for exploration
            raw_props = tiled_data.get("properties", [])
            properties = TiledImporter._extract_properties(raw_props)

            # Use floor_id from properties, or parameter, or derive from filename
            if not floor_id:
                floor_id = properties.get("floor_id", os.path.splitext(os.path.basename(filepath))[0])

            # Use floor_name from properties, or parameter
            if not floor_name:
                floor_name = properties.get("floor_name", floor_id)

            # Create FloorMap
            floor = FloorMap(floor_id, floor_name, (width, height))

            # Store source file path for reloading dungeon layout after loading saves
            floor.current_dungeon_file = filepath

            # Store exploration metadata on floor
            floor.starting_x = properties.get("starting_x", 10)
            floor.starting_y = properties.get("starting_y", 10)
            floor.starting_rotation = properties.get("starting_rotation", 0)
            floor.view_distance = properties.get("view_distance", 3)
            floor.area_name = properties.get("area_name", "")
            floor.sub_area_name = properties.get("sub_area_name", "")
            floor.description = properties.get("description", "")

            # Build tile ID mapping from tilesets
            tile_id_map = TiledImporter._build_tile_id_map(tiled_data.get("tilesets", []))

            # Process tile layers
            layers = tiled_data.get("layers", [])
            for layer in layers:
                if layer.get("type") == "tilelayer":
                    TiledImporter._process_tile_layer(layer, floor, tile_id_map)
                elif layer.get("type") == "objectgroup":
                    TiledImporter._process_object_layer(layer, floor, tile_id_map)

            # CRITICAL: Dual map system - separate real dungeon from player-drawn map
            # The loaded tiles represent the real dungeon that the player navigates.
            # We copy these to dungeon_tiles (for movement validation) and clear the
            # visible map so the player starts with a blank canvas to draw on.
            import copy
            floor.dungeon_tiles = copy.deepcopy(floor.tiles)

            # Clear the drawn map (player starts with blank map to fill in)
            for y in range(height):
                for x in range(width):
                    floor.set_tile(x, y, MapTile("empty", rotation=0))

            # CRITICAL: Dual icon system - separate real icons from player-drawn icons
            # The loaded icons represent the real dungeon objects (for collision/interaction).
            # We copy these to dungeon_icons (for game logic) and clear the visible icons
            # so they don't appear on the player's map until discovered.
            floor.dungeon_icons = copy.deepcopy(floor.icons)
            floor.icons = {}  # Player starts with no icons marked on map

            return floor

        @staticmethod
        def _build_tile_id_map(tilesets):
            # Build mapping from Tiled tile IDs to (tile_type, rotation).
            #
            # Args:
            #     tilesets: List of tileset objects from Tiled JSON
            #
            # Returns:
            #     dict: {tiled_gid: (tile_type, rotation)}
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
            # Extract custom properties from Tiled format.
            # Tiled properties are in array format: [{"name": "x", "type": "int", "value": 10}, ...]
            props = {}

            # Check if it's a dict first
            if isinstance(properties, dict):
                props = properties
            # Use duck typing for list check (Ren'Py type compatibility)
            elif hasattr(properties, '__iter__') and not isinstance(properties, str):
                for i, prop in enumerate(properties):
                    # Use duck typing for dict check too (isinstance doesn't work in Ren'Py)
                    if hasattr(prop, 'get'):
                        name = prop.get("name")
                        value = prop.get("value")
                        props[name] = value
            return props

        @staticmethod
        def _process_tile_layer(layer, floor, tile_id_map):
            # Process a Tiled tile layer and populate FloorMap tiles.
            #
            # Args:
            #     layer: Tiled layer object
            #     floor: FloorMap to populate
            #     tile_id_map: Mapping from Tiled GID to (tile_type, rotation)
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
                            tile_type = "empty"
                            rotation = 0

                    # Create and set tile
                    tile = MapTile(tile_type, rotation)
                    floor.set_tile(x, y, tile)

        @staticmethod
        def _process_object_layer(layer, floor, tile_id_map):
            # Process a Tiled object layer and populate FloorMap icons.
            # Objects represent stairs, doors, enemies, etc.
            objects = layer.get("objects", [])

            for obj in objects:
                # Get object position (Tiled uses pixel coordinates, convert to grid)
                pixel_x = obj.get("x", 0)
                pixel_y = obj.get("y", 0)
                tile_width = obj.get("width", 32)  # Assuming 32px tiles
                tile_height = obj.get("height", 32)

                # Convert pixel to grid coordinates
                # NOTE: Tiled y-coordinate is at BOTTOM of tile, so subtract height first
                grid_x = int(pixel_x / 32)
                grid_y = int((pixel_y - tile_height) / 32)

                # Get object type - try multiple sources
                obj_type = obj.get("type", "").lower()
                if not obj_type:
                    obj_name = obj.get("name", "").lower()
                    obj_type = obj_name

                # If still no type, check if object has a gid (tile object)
                if not obj_type and "gid" in obj:
                    gid = obj.get("gid")
                    if gid in tile_id_map:
                        # Get tile name from gid
                        tile_name, _ = tile_id_map[gid]
                        obj_type = tile_name.lower()

                # Map to our icon type
                icon_type = TiledImporter.OBJECT_TYPE_MAP.get(obj_type)
                if not icon_type:
                    continue

                # Extract custom properties
                properties = TiledImporter._extract_properties(obj.get("properties", []))

                # Create icon
                icon = MapIcon(icon_type, (grid_x, grid_y), metadata=properties)
                floor.place_icon(grid_x, grid_y, icon)

        @staticmethod
        def reload_dungeon_layout(floor):
            # Reload dungeon_tiles and dungeon_icons from source file.
            # Does NOT affect player-drawn tiles, icons, or revealed_tiles.
            # Used after loading a save to restore dungeon layout.
            #
            # Args:
            #     floor: FloorMap instance with current_dungeon_file attribute set
            #
            # Returns:
            #     True if reloaded successfully, False otherwise
            if not floor or not floor.current_dungeon_file:
                return False

            # Load the Tiled map fresh
            temp_floor = TiledImporter.load_tiled_map(floor.current_dungeon_file)
            if not temp_floor:
                return False

            # Copy only dungeon layout (NOT player-drawn data)
            floor.dungeon_tiles = temp_floor.dungeon_tiles
            floor.dungeon_icons = temp_floor.dungeon_icons

            # Also refresh metadata in case Tiled file was updated
            floor.starting_x = temp_floor.starting_x
            floor.starting_y = temp_floor.starting_y
            floor.starting_rotation = temp_floor.starting_rotation
            floor.view_distance = temp_floor.view_distance
            floor.area_name = temp_floor.area_name
            floor.sub_area_name = temp_floor.sub_area_name
            floor.description = temp_floor.description

            return True
