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
                    map_data["floors"][floor_id] = {
                        "floor_id": floor.floor_id,
                        "floor_name": floor.floor_name,
                        "dimensions": floor.dimensions,
                        "current_dungeon_file": floor.current_dungeon_file,
                        "accessible": floor.accessible,
                        # Serialize tiles (player-drawn)
                        "tiles": [[{"type": tile.tile_type, "rotation": tile.rotation}
                                for tile in row] for row in floor.tiles],
                        # Serialize icons (player-placed)
                        "icons": {"{},{}".format(x, y): {"type": icon.icon_type,
                                                        "metadata": icon.metadata}
                                for (x, y), icon in floor.icons.items()},
                        # Serialize revealed tiles (auto-map)
                        "revealed_tiles": list(floor.revealed_tiles)
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
        Reloads dungeon_tiles and dungeon_icons from Tiled files after loading.

        This is called automatically whenever ANY load happens (regular, quick, or auto).
        The map_grid was already restored by Ren'Py's pickle system (without dungeon_tiles).
        We just need to reload dungeon_tiles from the Tiled files.
        """
        global map_grid, player_state

        try:
            # Reload dungeon layouts for all floors (dungeon_tiles/dungeon_icons)
            # These were excluded from pickling via __getstate__ to save space
            if map_grid and map_grid.floors:
                for floor_id, floor in map_grid.floors.items():
                    if hasattr(floor, 'current_dungeon_file') and floor.current_dungeon_file:
                        TiledImporter.reload_dungeon_layout(floor)

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
