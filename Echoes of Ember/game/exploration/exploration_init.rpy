# exploration_init.rpy
# Initialization and utility functions for dungeon exploration

label start_exploration_system:
    # Initialize the exploration system.
    # Call this after start_mapping_system to set up player state.

    python:
        global player_state, map_grid

        # Ensure map_grid exists (will be populated by load_dungeon_floor)
        # Player state is created by load_dungeon_floor, not here
        if not map_grid:
            map_grid = MapGrid()

    return


label load_dungeon_floor(floor_filepath, floor_id=None):
    # Load a dungeon floor from a Tiled JSON file.
    #
    # Args:
    #     floor_filepath: Path to Tiled JSON file (relative to game directory)
    #     floor_id: Optional floor ID (defaults to filename)

    python:
        global map_grid, player_state

        print("=" * 80)
        print("DEBUG [LOAD_DUNGEON START] load_dungeon_floor('{}')".format(floor_filepath))

        # Ensure map_grid exists
        if not map_grid:
            map_grid = MapGrid()

        # Check if floor already exists (from save load)
        floor_id_to_check = floor_id if floor_id else "unknown"
        if floor_id_to_check in map_grid.floors:
            existing_floor = map_grid.floors[floor_id_to_check]
            existing_tile = existing_floor.get_tile(0, 0)
            print("DEBUG [LOAD_DUNGEON BEFORE] Floor '{}' already exists! tile(0,0) = '{}'".format(floor_id_to_check, existing_tile.tile_type))
        else:
            print("DEBUG [LOAD_DUNGEON BEFORE] Floor '{}' does not exist yet".format(floor_id_to_check))

        # Load floor using Tiled importer
        floor = TiledImporter.load_tiled_map(floor_filepath, floor_id=floor_id)

        if floor:
            # Check tile in newly loaded floor
            new_tile = floor.get_tile(0, 0)
            print("DEBUG [LOAD_DUNGEON MIDDLE] Tiled importer returned floor '{}' with tile(0,0) = '{}'".format(floor.floor_id, new_tile.tile_type))

            # Add floor to map grid (THIS OVERWRITES EXISTING FLOOR!)
            map_grid.floors[floor.floor_id] = floor
            map_grid.current_floor_id = floor.floor_id

            # Verify after overwrite
            final_tile = map_grid.floors[floor.floor_id].get_tile(0, 0)
            print("DEBUG [LOAD_DUNGEON AFTER] Overwrote floor '{}', tile(0,0) now = '{}'".format(floor.floor_id, final_tile.tile_type))
            print("=" * 80)

            # Initialize or reset player state for this floor
            if not player_state:
                player_state = PlayerState(
                    x=getattr(floor, 'starting_x', 10),
                    y=getattr(floor, 'starting_y', 10),
                    rotation=getattr(floor, 'starting_rotation', 0),
                    floor_id=floor.floor_id
                )
            else:
                # Move player to starting position
                player_state.x = getattr(floor, 'starting_x', 10)
                player_state.y = getattr(floor, 'starting_y', 10)
                player_state.rotation = getattr(floor, 'starting_rotation', 0)
                player_state.current_floor_id = floor.floor_id

        else:
            renpy.notify("Failed to load floor from: {}".format(floor_filepath))

    return


# Entry/Exit labels for exploration mode
label enter_exploration_mode(floor_id):
    # Enter exploration mode for a specific floor.
    #
    # Args:
    #     floor_id: ID of the floor to explore (must exist in map_grid)
    #
    # Returns:
    #     "exit_exploration" when player leaves

    python:
        global map_grid, player_state

        # Ensure systems are initialized
        if not map_grid:
            renpy.notify("Error: Map system not initialized")
            renpy.return_statement(value="error")

        # Check if floor exists
        if floor_id not in map_grid.floors:
            renpy.notify("Error: Floor {} not found".format(floor_id))
            renpy.return_statement(value="error")

        # Switch to floor
        map_grid.switch_floor(floor_id)
        floor = map_grid.get_floor(floor_id)

        # Initialize or update player state
        if not player_state:
            player_state = PlayerState(
                x=getattr(floor, 'starting_x', 10),
                y=getattr(floor, 'starting_y', 10),
                rotation=getattr(floor, 'starting_rotation', 0),
                floor_id=floor_id
            )
        else:
            # Move player to starting position
            player_state.x = getattr(floor, 'starting_x', 10)
            player_state.y = getattr(floor, 'starting_y', 10)
            player_state.rotation = getattr(floor, 'starting_rotation', 0)
            player_state.current_floor_id = floor_id

        # Auto-reveal starting tile if auto-map is enabled
        if getattr(map_grid, 'auto_map_enabled', False):
            if not hasattr(floor, 'revealed_tiles'):
                floor.revealed_tiles = set()
            floor.revealed_tiles.add((player_state.x, player_state.y))

    # Show exploration screen (this will block until player exits)
    call screen exploration_view

    # When we get here, player has exited exploration

    # Autosave
    $ renpy.save("auto-1")

    return


init python:
    def delete_exploration_floor(floor_id, slot_name=None):
        """
        Delete a floor from the map grid and optionally from save files.

        Args:
            floor_id: ID of the floor to delete
            slot_name: Optional slot name to delete map data from

        Use this when story prevents returning to a location.
        """
        global map_grid

        if not map_grid:
            return False

        # Remove floor from map grid
        if floor_id in map_grid.floors:
            del map_grid.floors[floor_id]

        # If we're currently on this floor, switch to another floor
        if map_grid.current_floor_id == floor_id:
            if map_grid.floors:
                # Switch to first available floor
                map_grid.current_floor_id = list(map_grid.floors.keys())[0]
            else:
                map_grid.current_floor_id = None

        # Optionally delete from save file
        if slot_name:
            try:
                # Save the updated map grid (without the deleted floor)
                save_map_data_to_file(slot_name)
            except Exception as e:
                print("Error updating save: {}".format(e))

        return True

    def get_exploration_percent_for_floor(floor_id):
        """
        Get exploration percentage for a specific floor.

        Returns: int (0-100)
        """
        global map_grid

        if not map_grid or floor_id not in map_grid.floors:
            return 0

        floor = map_grid.floors[floor_id]
        return calculate_exploration_percent(floor)
