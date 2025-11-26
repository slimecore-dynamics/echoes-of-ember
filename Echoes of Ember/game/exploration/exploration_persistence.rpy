# exploration_persistence.rpy
# Save/load system for player-drawn maps and player state
# Uses Ren'Py's config.save_json_callbacks to store data within save files

init -1 python:
    import json

    def serialize_map_data_for_save(json_dict):
        """
        Callback for config.save_json_callbacks.
        Serializes map_grid and player_state into the save file's JSON metadata.

        This is called automatically whenever ANY save happens (regular, quick, or auto).
        The data is stored within the .save file itself, not as a separate file.
        """
        global map_grid, player_state

        try:
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

            # Serialize player_state if it exists
            if player_state:
                json_dict["player_state"] = player_state.to_dict()

        except Exception as e:
            # If serialization fails, log but don't crash the save
            import sys
            print("Error serializing map data: {}".format(e), file=sys.stderr)


    def deserialize_map_data_after_load():
        """
        Callback for config.after_load_callbacks.
        Reloads dungeon_tiles from Tiled files and player-drawn map from JSON.

        This is called automatically whenever ANY load happens (regular, quick, or auto).
        """
        global map_grid

        try:
            # Step 1: Reload dungeon_tiles from Tiled files (for movement)
            # These were excluded from pickling via __getstate__ to save space
            if map_grid and map_grid.floors:
                for floor_id, floor in map_grid.floors.items():
                    if hasattr(floor, 'current_dungeon_file') and floor.current_dungeon_file:
                        TiledImporter.reload_dungeon_layout(floor)

            # Step 2: Read JSON and restore player-drawn map (for display)
            if hasattr(persistent, '_loaded_slot') and persistent._loaded_slot:
                slot_name = persistent._loaded_slot
                json_data = renpy.slot_json(slot_name)

                if json_data and "map_grid" in json_data:
                    map_data = json_data["map_grid"]

                    # Restore each floor's player-drawn data
                    for floor_id, floor_data in map_data.get("floors", {}).items():
                        if floor_id in map_grid.floors:
                            floor = map_grid.floors[floor_id]

                            # Clear existing drawn tiles (start fresh)
                            for y in range(floor.dimensions[1]):
                                for x in range(floor.dimensions[0]):
                                    floor.set_tile(x, y, MapTile("empty", rotation=0))

                            # Reconstruct tiles from sparse JSON data
                            tiles_data = floor_data.get("tiles", {})
                            for pos_key, tile_data in tiles_data.items():
                                x, y = map(int, pos_key.split(","))
                                floor.set_tile(x, y, MapTile(tile_data["type"], rotation=0))

                            # Reconstruct icons
                            icons_data = floor_data.get("icons", {})
                            floor.icons = {}
                            for pos_key, icon_data in icons_data.items():
                                x, y = map(int, pos_key.split(","))
                                icon = MapIcon(icon_data["type"], (x, y), icon_data.get("metadata", {}))
                                floor.icons[(x, y)] = icon

        except Exception as e:
            # If deserialization fails, log but don't crash the load
            import sys
            print("Error deserializing map data: {}".format(e), file=sys.stderr)


    # Register the callbacks with Ren'Py
    # These will be called automatically for ALL saves/loads (regular, quick, auto)
    config.save_json_callbacks.append(serialize_map_data_for_save)
    config.after_load_callbacks.append(deserialize_map_data_after_load)


    # Configure single-slot autosave and quicksave
    config.has_autosave = True
    config.autosave_slots = 1  # Only one autosave slot
    config.has_quicksave = True
    # Note: config.quicksave_slots doesn't exist, but QuickSave action handles this

    # Wrapper actions for tracking which slot is being loaded
    class FileLoadWithTracking(Action):
        """Wrapper for FileLoad that tracks which slot is being loaded."""
        def __init__(self, name, **kwargs):
            self.name = name
            self.kwargs = kwargs

        def __call__(self):
            # Store slot name in persistent (survives the load!)
            persistent._loaded_slot = self.name
            return FileLoad(self.name, **self.kwargs)()


    class FileActionWithTracking(Action):
        """Wrapper for FileAction that tracks which slot is being loaded."""
        def __init__(self, name, **kwargs):
            self.name = name
            self.kwargs = kwargs

        def __call__(self):
            # Store slot name in persistent (survives the load!)
            persistent._loaded_slot = self.name
            return FileAction(self.name, **self.kwargs)()