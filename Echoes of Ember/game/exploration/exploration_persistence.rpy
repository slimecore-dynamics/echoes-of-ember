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
        Reloads dungeon_tiles from Tiled files (excluded from pickle to save space).
        Player-drawn tiles, icons, and revealed_tiles are already restored via pickle.

        This is called automatically whenever ANY load happens (regular, quick, or auto).
        """
        global map_grid

        try:
            import sys
            print("\n=== DESERIALIZE DEBUG START ===", file=sys.stderr)
            print("map_grid exists: {}".format(map_grid is not None), file=sys.stderr)

            if map_grid:
                print("map_grid.floors count: {}".format(len(map_grid.floors)), file=sys.stderr)
                print("current_floor_id: {}".format(map_grid.current_floor_id), file=sys.stderr)

            # Reload dungeon_tiles from Tiled files (for movement validation)
            # These were excluded from pickling via __getstate__ to save space
            if map_grid and map_grid.floors:
                for floor_id, floor in map_grid.floors.items():
                    print("Processing floor: {}".format(floor_id), file=sys.stderr)

                    # Debug: Check what's in the floor after pickle restore
                    non_empty_tiles = 0
                    if hasattr(floor, 'tiles') and floor.tiles:
                        for row in floor.tiles:
                            for tile in row:
                                if tile.tile_type != "empty":
                                    non_empty_tiles += 1
                    print("  Non-empty tiles after pickle: {}".format(non_empty_tiles), file=sys.stderr)
                    print("  Icons count: {}".format(len(floor.icons) if hasattr(floor, 'icons') else 0), file=sys.stderr)
                    print("  Revealed tiles: {}".format(len(floor.revealed_tiles) if hasattr(floor, 'revealed_tiles') else 0), file=sys.stderr)

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


    # Configure single-slot autosave and quicksave
    config.has_autosave = True
    config.autosave_slots = 1  # Only one autosave slot
    config.has_quicksave = True
    # Note: config.quicksave_slots doesn't exist, but QuickSave action handles this