# exploration_persistence.rpy
# Save/load system for player-drawn maps and player state
# Uses Ren'Py's config.save_json_callbacks to store data within save files

init -1 python:
    import json
    import os

    def get_slot_tracker_path():
        """Get path to temp file for tracking which slot was loaded."""
        return os.path.join(renpy.config.gamedir, ".last_loaded_slot")

    def serialize_map_data_for_save(json_dict):
        """
        Callback for config.save_json_callbacks.
        Serializes map_grid and player_state into the save file's JSON metadata.

        This is called automatically whenever ANY save happens (regular, quick, or auto).
        The data is stored within the .save file itself, not as a separate file.
        """
        global map_grid, player_state

        try:
            import sys
            print("\n=== SERIALIZE DEBUG START ===", file=sys.stderr)
            print("map_grid exists: {}".format(map_grid is not None), file=sys.stderr)
            # Serialize map_grid if it exists
            if map_grid:
                map_data = {
                    "current_floor_id": map_grid.current_floor_id,
                    "auto_map_enabled": map_grid.auto_map_enabled,
                    "floors": {}
                }

                # Serialize each FloorMap (only player-drawn data and metadata)
                for floor_id, floor in map_grid.floors.items():
                    # Save only non-empty tiles with their positions (sparse)
                    tiles = {}
                    for y in range(floor.dimensions[1]):
                        for x in range(floor.dimensions[0]):
                            tile = floor.tiles[y][x]
                            if tile.tile_type != "empty":
                                tiles["{},{}".format(x, y)] = {"type": tile.tile_type}

                    map_data["floors"][floor_id] = {
                        "floor_id": floor.floor_id,
                        "floor_name": floor.floor_name,
                        "dimensions": floor.dimensions,
                        "current_dungeon_file": floor.current_dungeon_file,
                        "accessible": floor.accessible,
                        "tiles": tiles,
                        # Serialize icons (player-placed)
                        "icons": {"{},{}".format(x, y): {"type": icon.icon_type,
                                                        "metadata": icon.metadata}
                                for (x, y), icon in floor.icons.items()}
                    }
                json_dict["map_grid"] = map_data

                print("Serialized {} floors".format(len(map_data.get("floors", {}))), file=sys.stderr)
                for floor_id, floor_data in map_data.get("floors", {}).items():
                    tiles_count = len(floor_data.get("tiles", {}))
                    icons_count = len(floor_data.get("icons", {}))
                    print("  Floor {}: {} tiles, {} icons".format(floor_id, tiles_count, icons_count), file=sys.stderr)

            # Serialize player_state if it exists
            if player_state:
                json_dict["player_state"] = player_state.to_dict()
                print("Serialized player_state: pos=({}, {}), floor={}".format(
                    player_state.x, player_state.y, player_state.current_floor_id), file=sys.stderr)

            print("=== SERIALIZE DEBUG END ===\n", file=sys.stderr)

        except Exception as e:
            # If serialization fails, log but don't crash the save
            import sys
            print("!!! Error serializing map data: {}".format(e), file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)


    def deserialize_map_data_after_load():
        """
        Callback for config.after_load_callbacks.
        Restores map_grid and player_state from JSON (pickle can't handle nested structures).
        Then reloads dungeon_tiles from Tiled files.

        This is called automatically whenever ANY load happens (regular, quick, or auto).
        """
        try:
            import sys
            print("\n=== DESERIALIZE DEBUG START ===", file=sys.stderr)
            print("map_grid exists after pickle: {}".format(store.map_grid is not None), file=sys.stderr)

            # If pickle failed to restore map_grid, restore from JSON
            if not store.map_grid:
                print("Pickle failed - restoring from JSON", file=sys.stderr)

                # Read slot name from tracking file
                slot_name = None
                tracker_path = get_slot_tracker_path()
                if os.path.exists(tracker_path):
                    with open(tracker_path, 'r') as f:
                        slot_name = f.read().strip()
                    print("Loaded slot name from tracker: {}".format(slot_name), file=sys.stderr)
                else:
                    print("!!! No slot tracker file found!", file=sys.stderr)

                if slot_name:
                    # Get JSON data from the save file
                    json_data = renpy.slot_json(slot_name)
                    print("JSON data exists: {}".format(json_data is not None), file=sys.stderr)

                    if json_data:
                        # Restore map_grid from JSON
                        if "map_grid" in json_data:
                            map_data = json_data["map_grid"]
                            print("Restoring map_grid from JSON...", file=sys.stderr)

                            # Reconstruct MapGrid - update global store variable
                            store.map_grid = MapGrid()
                            store.map_grid.current_floor_id = map_data.get("current_floor_id")
                            store.map_grid.auto_map_enabled = map_data.get("auto_map_enabled", False)

                            # Reconstruct each floor
                            for floor_id, floor_data in map_data.get("floors", {}).items():
                                print("  Restoring floor: {}".format(floor_id), file=sys.stderr)

                                # Create FloorMap
                                dimensions = tuple(floor_data.get("dimensions", [20, 20]))
                                floor = FloorMap(
                                    floor_id=floor_data.get("floor_id", floor_id),
                                    floor_name=floor_data.get("floor_name", "Unknown"),
                                    dimensions=dimensions
                                )

                                # Restore metadata
                                floor.current_dungeon_file = floor_data.get("current_dungeon_file")
                                floor.accessible = floor_data.get("accessible", True)

                                # Restore tiles from sparse JSON data
                                tiles_data = floor_data.get("tiles", {})
                                for pos_key, tile_data in tiles_data.items():
                                    x, y = map(int, pos_key.split(","))
                                    floor.set_tile(x, y, MapTile(tile_data["type"], rotation=0))
                                print("    Restored {} tiles".format(len(tiles_data)), file=sys.stderr)

                                # Restore icons
                                icons_data = floor_data.get("icons", {})
                                for pos_key, icon_data in icons_data.items():
                                    x, y = map(int, pos_key.split(","))
                                    icon = MapIcon(icon_data["type"], (x, y), icon_data.get("metadata", {}))
                                    floor.icons[(x, y)] = icon
                                print("    Restored {} icons".format(len(icons_data)), file=sys.stderr)

                                store.map_grid.floors[floor_id] = floor

                        # Restore player_state from JSON - update global store variable
                        if "player_state" in json_data:
                            print("Restoring player_state from JSON...", file=sys.stderr)
                            store.player_state = PlayerState.from_dict(json_data["player_state"])
                            print("  Player at ({}, {}) on floor {}".format(
                                store.player_state.x, store.player_state.y, store.player_state.current_floor_id), file=sys.stderr)

            # Now reload dungeon_tiles from Tiled files (for movement validation)
            # These were excluded from JSON to save space
            if store.map_grid and store.map_grid.floors:
                print("Reloading dungeon_tiles from Tiled files...", file=sys.stderr)
                for floor_id, floor in store.map_grid.floors.items():
                    print("Processing floor: {}".format(floor_id), file=sys.stderr)

                    # Debug: Check what's in the floor
                    non_empty_tiles = 0
                    if hasattr(floor, 'tiles') and floor.tiles:
                        for row in floor.tiles:
                            for tile in row:
                                if tile.tile_type != "empty":
                                    non_empty_tiles += 1
                    print("  Non-empty tiles: {}".format(non_empty_tiles), file=sys.stderr)
                    print("  Icons count: {}".format(len(floor.icons) if hasattr(floor, 'icons') else 0), file=sys.stderr)

                    # Reload dungeon layout from Tiled
                    if hasattr(floor, 'current_dungeon_file') and floor.current_dungeon_file:
                        print("  Reloading dungeon from: {}".format(floor.current_dungeon_file), file=sys.stderr)
                        success = TiledImporter.reload_dungeon_layout(floor)
                        print("  Reload success: {}".format(success), file=sys.stderr)
                        print("  dungeon_tiles exists: {}".format(hasattr(floor, 'dungeon_tiles') and floor.dungeon_tiles is not None), file=sys.stderr)
                    else:
                        print("  No current_dungeon_file set!", file=sys.stderr)

            print("=== DESERIALIZE DEBUG END ===\n", file=sys.stderr)

        except Exception as e:
            # If deserialization fails, log but don't crash the load
            import sys
            print("!!! Error deserializing map data: {}".format(e), file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)


    # Register the callbacks with Ren'Py
    # These will be called automatically for ALL saves/loads (regular, quick, auto)
    config.save_json_callbacks.append(serialize_map_data_for_save)
    config.after_load_callbacks.append(deserialize_map_data_after_load)


    # Configure autosave and quicksave
    config.has_autosave = True
    config.has_quicksave = True

    # Wrapper actions for tracking which slot is being loaded
    class FileLoadWithTracking(Action):
        """Wrapper for FileLoad that tracks which slot is being loaded via temp file."""
        def __init__(self, name, **kwargs):
            self.name = name
            self.kwargs = kwargs

        def __call__(self):
            import sys
            # Write slot name to temp file before loading
            try:
                with open(get_slot_tracker_path(), 'w') as f:
                    f.write(self.name)
                print("Tracking load from slot: {}".format(self.name), file=sys.stderr)
            except Exception as e:
                print("!!! Error writing slot tracker: {}".format(e), file=sys.stderr)

            # Then perform the actual load
            return FileLoad(self.name, **self.kwargs)()


    class FileActionWithTracking(Action):
        """Wrapper for FileAction that tracks which slot is being loaded via temp file."""
        def __init__(self, name, **kwargs):
            self.name = name
            self.kwargs = kwargs

        def __call__(self):
            import sys
            # Construct full slot name
            if isinstance(self.name, int):
                # It's a slot number - need to add page prefix
                page = persistent._file_page if hasattr(persistent, '_file_page') and persistent._file_page else "1"
                full_slot_name = "{}-{}".format(page, self.name)
                print("Tracking action on slot: {} (converted to {})".format(self.name, full_slot_name), file=sys.stderr)
            else:
                # It's already a full slot name (like "auto-1", "quick-1")
                full_slot_name = str(self.name)
                print("Tracking action on slot: {}".format(full_slot_name), file=sys.stderr)

            # Write full slot name to temp file before loading (if loading)
            try:
                with open(get_slot_tracker_path(), 'w') as f:
                    f.write(full_slot_name)
            except Exception as e:
                print("!!! Error writing slot tracker: {}".format(e), file=sys.stderr)

            # Then perform the actual action (save or load)
            return FileAction(self.name, **self.kwargs)()