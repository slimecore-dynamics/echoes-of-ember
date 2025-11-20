# exploration_init.rpy
# Initialization and utility functions for dungeon exploration

label start_exploration_system:
    """
    Initialize the exploration system.

    Call this after start_mapping_system to set up player state.
    """

    python:
        global player_state, map_grid

        # Only initialize if player_state is None (new game)
        if player_state is None:
            # Get current floor
            if map_grid and map_grid.floors:
                floor = map_grid.get_current_floor()

                if floor:
                    # Use floor's starting position if available
                    start_x = getattr(floor, 'starting_x', 10)
                    start_y = getattr(floor, 'starting_y', 10)
                    start_rot = getattr(floor, 'starting_rotation', 0)
                    floor_id = floor.floor_id
                else:
                    # Default position
                    start_x, start_y = 10, 10
                    start_rot = 0
                    floor_id = None

                # Create player state
                player_state = PlayerState(
                    x=start_x,
                    y=start_y,
                    rotation=start_rot,
                    floor_id=floor_id
                )

                print("ExplorationInit - Created new player state at ({}, {}) facing {}".format(
                    start_x, start_y, player_state.get_facing_direction_name()
                ))
            else:
                # No map grid, create default player state
                player_state = PlayerState(x=10, y=10, rotation=0)
                print("ExplorationInit - Created default player state (no map grid)")
        else:
            # Player state already exists (loaded from save)
            print("ExplorationInit - Player state already exists (loaded from save)")

    return


label load_dungeon_floor(floor_filepath, floor_id=None):
    """
    Load a dungeon floor from a Tiled JSON file.

    Args:
        floor_filepath: Path to Tiled JSON file (relative to game directory)
        floor_id: Optional floor ID (defaults to filename)
    """

    python:
        global map_grid, player_state

        # Ensure map_grid exists
        if not map_grid:
            map_grid = MapGrid()

        # Load floor using Tiled importer
        floor = TiledImporter.load_tiled_map(floor_filepath, floor_id=floor_id)

        if floor:
            # Add floor to map grid
            map_grid.floors[floor.floor_id] = floor
            map_grid.current_floor_id = floor.floor_id

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

            renpy.notify("Loaded floor: {}".format(floor.floor_name))
        else:
            renpy.notify("Failed to load floor from: {}".format(floor_filepath))

    return


init python:
    def create_test_dungeon():
        """
        Create a simple test dungeon programmatically (no Tiled file needed).

        This creates a small dungeon for testing the exploration system.
        """
        global map_grid, player_state

        # Ensure map_grid exists
        if not map_grid:
            map_grid = MapGrid()

        # Create floor
        floor_id = "test_floor_1"
        floor_name = "Test Dungeon - Level 1"
        floor = FloorMap(floor_id, floor_name, dimensions=(20, 20))

        # Set exploration metadata
        floor.starting_x = 10
        floor.starting_y = 10
        floor.starting_rotation = 0  # Facing North
        floor.view_distance = 3

        # Create a simple dungeon layout:
        # Row 10: 4 horizontal hallways from (8,10) to (12,10)
        for x in range(8, 13):
            floor.set_tile(x, 10, MapTile("hallway", rotation=0))

        # Add t_intersection at (13, 10) with rotation 0 (wall at north)
        floor.set_tile(13, 10, MapTile("t_intersection", rotation=0))

        # Add vertical hallway going south from t_intersection
        for y in range(11, 15):
            floor.set_tile(13, y, MapTile("hallway", rotation=90))

        # Add some walls around the corridor
        for x in range(7, 14):
            if x != 10:  # Don't block starting position
                floor.set_tile(x, 9, MapTile("wall", rotation=180))  # North wall
                floor.set_tile(x, 11, MapTile("wall", rotation=0))   # South wall (except at junction)

        # Add a door at (11, 10)
        floor.place_icon(11, 10, MapIcon("door_closed", (11, 10)))

        # Add gathering point at (13, 14)
        floor.place_icon(13, 14, MapIcon("gathering", (13, 14), metadata={"item": "data", "amount": 1}))

        # Add enemy at (12, 10)
        floor.place_icon(12, 10, MapIcon("enemy", (12, 10), metadata={"damage": 5}))

        # Add stairs down at (13, 15)
        # (This would lead to floor_2 if it existed)
        floor.place_icon(13, 15, MapIcon("stairs_down", (13, 15)))

        # Add floor to map grid
        map_grid.floors[floor_id] = floor
        map_grid.current_floor_id = floor_id

        # Initialize player state
        if not player_state:
            player_state = PlayerState(
                x=floor.starting_x,
                y=floor.starting_y,
                rotation=floor.starting_rotation,
                floor_id=floor_id
            )
        else:
            player_state.x = floor.starting_x
            player_state.y = floor.starting_y
            player_state.rotation = floor.starting_rotation
            player_state.current_floor_id = floor_id

        print("Test dungeon created: {} tiles, {} icons".format(
            sum(1 for row in floor.tiles for tile in row if tile.tile_type != "empty"),
            len(floor.icons)
        ))

        return floor


# Entry/Exit labels for exploration mode
label enter_exploration_mode(floor_id):
    """
    Enter exploration mode for a specific floor.

    Args:
        floor_id: ID of the floor to explore (must exist in map_grid)

    Returns:
        "exit_exploration" when player leaves
    """

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
            print("ExplorationInit - Deleted floor: {}".format(floor_id))

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
                print("ExplorationInit - Updated save file: {}".format(slot_name))
            except Exception as e:
                print("ExplorationInit - Error updating save: {}".format(e))

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
