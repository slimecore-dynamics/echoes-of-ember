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


# This label shows VN dialogue DURING exploration
label dialogue_during_exploration_example:
    """
    Example: Show VN dialogue during exploration (overlays exploration screen).

    Demonstrates:
    - Event triggers dialogue label
    - Dialogue appears over exploration UI
    - Choices affect variables
    - Returns to exploration after dialogue
    """

    call start_mapping_system
    call start_exploration_system

    # Character definitions (if not already defined)
    define survivor = Character("Survivor", color="#00FF00")
    define ai = Character("AI Voice", color="#00FFFF")

    python:
        # Create floor with event triggers
        floor = FloorMap("wreck_floor", "Crashed Ship", dimensions=(20, 20))
        floor.starting_x = 10
        floor.starting_y = 10
        floor.starting_rotation = 0
        floor.view_distance = 3

        # Corridor
        for x in range(8, 15):
            floor.set_tile(x, 10, MapTile("hallway", rotation=0))

        # Event 1: Survivor at (9, 10)
        floor.place_icon(9, 10, MapIcon("event", (9, 10),
            metadata={"label": "found_survivor", "message": "You see someone..."}))

        # Event 2: AI console at (12, 10)
        floor.place_icon(12, 10, MapIcon("event", (12, 10),
            metadata={"label": "ai_console", "message": "A console flickers..."}))

        # Gathering point
        floor.place_icon(14, 10, MapIcon("gathering", (14, 10),
            metadata={"item": "data", "amount": 1}))

        # Variables to track story
        saved_survivor = False
        got_ai_data = False

        map_grid.floors["wreck_floor"] = floor
        map_grid.current_floor_id = "wreck_floor"
        player_state = PlayerState(x=10, y=10, rotation=0, floor_id="wreck_floor")

    "You enter the crashed ship..."
    "Explore and find what you can."

    # Enter exploration mode
    call enter_exploration_mode("wreck_floor")

    # Player has exited exploration

    # Check what happened during exploration
    if saved_survivor and got_ai_data:
        "You rescued the survivor and recovered the AI data."
        "This will be very valuable."
    elif saved_survivor:
        "You rescued the survivor, but missed the AI data."
    elif got_ai_data:
        "You recovered the AI data, but left the survivor behind..."
    else:
        "You left empty-handed."

    return


# Dialogue labels that get called during exploration

label found_survivor:
    """Triggered when stepping on survivor event icon."""

    # This dialogue appears OVER the exploration screen
    # Map interaction is disabled during dialogue

    show survivor at center with dissolve

    survivor "Help! I've been trapped here for days!"
    survivor "The ship's AI went haywire and locked me in."

    menu:
        "Will you help them?"

        "Yes, I'll help you escape":
            survivor "Thank you! Follow me, I know a way out."
            $ saved_survivor = True
            "The survivor escapes with you."

        "Sorry, I can't risk it":
            survivor "Please... don't leave me here..."
            "You leave them behind."

    hide survivor with dissolve

    # Returns to exploration
    return


label ai_console:
    """Triggered when stepping on AI console event icon."""

    show screen console_screen

    ai "Access granted. Data retrieval in progress."

    menu:
        "What do you do?"

        "Download all data":
            ai "Warning: This will alert security systems."

            menu:
                "Continue anyway":
                    $ got_ai_data = True
                    ai "Download complete. Intruder alert activated."
                    "You got the data, but security is now active!"

                "Cancel download":
                    ai "Download cancelled."

        "Leave it alone":
            ai "Session terminated."

    hide screen console_screen

    return


# Simple console screen overlay
screen console_screen:
    frame:
        xalign 0.5
        yalign 0.3
        xpadding 40
        ypadding 30
        background "#000088DD"

        text "AI CONSOLE ACTIVE" xalign 0.5 color "#00FFFF" size 24
