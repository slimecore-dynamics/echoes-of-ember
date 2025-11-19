# exploration_example.rpy
# Example script demonstrating dungeon exploration system

# This label shows how to start exploration with a test dungeon
label start_dungeon_exploration_example:
    """
    Example: Start dungeon exploration with test dungeon.

    To use this example, call this label from your script.rpy:

    label start:
        call start_mapping_system
        call start_dungeon_exploration_example
        return
    """

    # Initialize exploration system
    call start_exploration_system

    # Create test dungeon (or load from Tiled)
    $ create_test_dungeon()

    # Optional: Show intro message
    "Welcome to the dungeon!"
    "Use the navigation buttons to explore."
    "Press M to toggle the map view."

    # Show exploration screen
    call screen exploration_view

    # When player exits exploration screen, return here
    "You have exited the dungeon."

    return


# This label shows how to load a custom dungeon from Tiled JSON
label start_custom_dungeon_example:
    """
    Example: Load a custom dungeon from Tiled JSON file.

    Prerequisites:
    1. Create a dungeon in Tiled Map Editor
    2. Export as JSON to game/maps/your_dungeon.json
    3. Update the filepath below
    """

    call start_mapping_system
    call start_exploration_system

    # Load dungeon from Tiled JSON file
    # Replace "maps/your_dungeon.json" with your actual file path
    call load_dungeon_floor("maps/dungeon_floor1.json", "floor_1")

    "Welcome to [floor.floor_name]!" with dissolve

    # Show exploration screen
    call screen exploration_view

    return


# This label shows how to create a multi-floor dungeon
label multi_floor_dungeon_example:
    """
    Example: Create a multi-floor dungeon with stairs.
    """

    call start_mapping_system
    call start_exploration_system

    python:
        # Create Floor 1
        floor1 = FloorMap("floor_1", "Entrance Hall", dimensions=(20, 20))
        floor1.starting_x = 10
        floor1.starting_y = 10
        floor1.starting_rotation = 0
        floor1.view_distance = 3

        # Simple corridor
        for x in range(8, 13):
            floor1.set_tile(x, 10, MapTile("hallway", rotation=0))

        # Stairs down at end
        floor1.place_icon(12, 10, MapIcon("stairs_down", (12, 10)))

        # Add to map
        map_grid.floors["floor_1"] = floor1

        # Create Floor 2
        floor2 = FloorMap("floor_2", "Lower Level", dimensions=(20, 20))
        floor2.starting_x = 10
        floor2.starting_y = 10
        floor2.starting_rotation = 180  # Facing south
        floor2.view_distance = 2  # Darker floor, less visibility

        # Simple room
        for x in range(9, 12):
            for y in range(9, 12):
                floor2.set_tile(x, y, MapTile("cross", rotation=0))

        # Stairs up at entrance
        floor2.place_icon(10, 10, MapIcon("stairs_up", (10, 10)))

        # Enemy in room
        floor2.place_icon(11, 11, MapIcon("enemy", (11, 11),
            metadata={"damage": 10}))

        # Add to map
        map_grid.floors["floor_2"] = floor2

        # Start on floor 1
        map_grid.current_floor_id = "floor_1"
        player_state = PlayerState(x=10, y=10, rotation=0, floor_id="floor_1")

    "You enter the dungeon entrance..."

    call screen exploration_view

    return


# This label shows how to use gathering items
label gathering_example:
    """
    Example: Gathering system with inventory.
    """

    # Initialize inventory
    $ inventory = {
        "metal scrap": 0,
        "electronics": 0,
        "psionic capsule": 0,
        "data": 0
    }

    call start_mapping_system
    call start_exploration_system

    python:
        # Create floor with gathering points
        floor = FloorMap("gather_test", "Resource Room", dimensions=(20, 20))
        floor.starting_x = 10
        floor.starting_y = 10
        floor.starting_rotation = 0
        floor.view_distance = 3

        # Corridor
        for x in range(8, 15):
            floor.set_tile(x, 10, MapTile("hallway", rotation=0))

        # Place gathering points
        floor.place_icon(9, 10, MapIcon("gathering", (9, 10),
            metadata={"item": "metal scrap", "amount": 3}))

        floor.place_icon(11, 10, MapIcon("gathering", (11, 10),
            metadata={"item": "electronics", "amount": 2}))

        floor.place_icon(13, 10, MapIcon("gathering", (13, 10),
            metadata={"item": "data", "amount": 1}))

        map_grid.floors["gather_test"] = floor
        map_grid.current_floor_id = "gather_test"
        player_state = PlayerState(x=10, y=10, rotation=0, floor_id="gather_test")

    "Collect resources to proceed..."

    call screen exploration_view

    # Show inventory
    "You collected:"
    $ total_items = sum(inventory.values())
    if total_items > 0:
        python:
            for item, amount in inventory.items():
                if amount > 0:
                    renpy.say(None, "- {} x{}".format(item, amount))
    else:
        "Nothing yet."

    return


# Note: To actually collect items in gathering_example, you'd need to
# extend handle_step_on_trigger() in exploration_screen.rpy to update
# the inventory dict. Example:
#
# def handle_step_on_trigger_with_inventory(icon):
#     global player_state, inventory
#
#     result = InteractionHandler.handle_interaction(icon, "step_on", player_state, None)
#
#     if result["type"] == "gathering":
#         item = result.get("item", "unknown")
#         amount = result.get("amount", 0)
#
#         if item in inventory:
#             inventory[item] += amount
#             renpy.notify("Gathered {} {}".format(amount, item))
#         else:
#             renpy.notify("Unknown item: {}".format(item))
#     # ... rest of handling ...
