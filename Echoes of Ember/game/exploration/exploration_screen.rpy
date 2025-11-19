# exploration_screen.rpy
# First-person dungeon exploration UI

# Colors for placeholder graphics
define color_wall = "#666666"
define color_floor = "#333333"
define color_ceiling = "#4D4D4D"
define color_door_closed = "#8B4513"
define color_door_open = "#D2B48C"
define color_interact = "#FFFF00"

screen exploration_view():
    """
    Main exploration screen with first-person view and navigation controls.
    """

    # Get current floor and player state
    $ floor = map_grid.get_current_floor() if map_grid else None
    $ ps = player_state

    # Background
    frame:
        xalign 0.5
        yalign 0.5
        xsize 1280
        ysize 720
        background "#000000"

        vbox:
            spacing 20
            xalign 0.5
            yalign 0.5

            # First-person view area
            frame:
                xsize 800
                ysize 600
                xalign 0.5
                background "#000000"

                if floor and ps:
                    # Get view data
                    $ view_data = FirstPersonView.get_view_data(
                        floor, ps.x, ps.y, ps.rotation,
                        view_distance=getattr(floor, 'view_distance', 3)
                    )

                    # Render first-person view
                    use render_first_person_view(view_data, floor, ps)
                else:
                    text "No floor loaded" xalign 0.5 yalign 0.5

            # Navigation controls
            hbox:
                spacing 20
                xalign 0.5

                # Turn Left
                textbutton "Turn Left":
                    action Function(handle_turn_left)
                    xsize 150
                    ysize 60

                vbox:
                    spacing 10
                    xalign 0.5

                    # Forward
                    if floor and ps:
                        $ view_data = FirstPersonView.get_view_data(
                            floor, ps.x, ps.y, ps.rotation,
                            view_distance=getattr(floor, 'view_distance', 3)
                        )
                        $ can_move = view_data.get("can_move_forward", False)
                    else:
                        $ can_move = False

                    textbutton "Forward":
                        action Function(handle_move_forward)
                        xsize 150
                        ysize 60
                        sensitive can_move

                    # Backward
                    textbutton "Backward":
                        action Function(handle_move_backward)
                        xsize 150
                        ysize 60

                # Turn Right
                textbutton "Turn Right":
                    action Function(handle_turn_right)
                    xsize 150
                    ysize 60

            # Status info
            hbox:
                spacing 40
                xalign 0.5

                if ps:
                    text "Position: ({}, {})".format(ps.x, ps.y)
                    text "Facing: {}".format(ps.get_facing_direction_name())
                    text "Health: {}/{}".format(ps.health, ps.max_health)

            # Map toggle
            textbutton "Toggle Map (M)":
                action ToggleScreen("map_view")
                xalign 0.5

    # Interaction prompt (if any)
    if floor and ps:
        $ icon, int_type, adj_x, adj_y = InteractionHandler.check_adjacent_trigger(
            floor, ps.x, ps.y, ps.rotation
        )

        if icon:
            use interaction_prompt(icon, int_type, adj_x, adj_y)

    # Keyboard shortcuts
    key "m" action ToggleScreen("map_view")
    key "M" action ToggleScreen("map_view")


screen render_first_person_view(view_data, floor, ps):
    """
    Render the first-person view based on view_data.
    """

    # Background (ceiling and floor)
    add Solid(color_ceiling) xpos 0 ypos 0 xsize 800 ysize 300
    add Solid(color_floor) xpos 0 ypos 300 xsize 800 ysize 300

    # Render tiles from farthest to nearest (painter's algorithm)
    $ tiles = view_data.get("tiles", [])
    $ icons = view_data.get("icons", [])

    python:
        # Render tiles by distance (farthest first)
        for tile_x, tile_y, tile, dist in reversed(tiles):
            # Calculate render position and size based on distance
            # Distance 1 (closest): large, distance 3 (far): small
            scale = 1.0 / dist
            width = int(600 * scale)
            height = int(400 * scale)
            x_offset = (800 - width) // 2
            y_offset = (600 - height) // 2

            # Determine what to render based on tile type
            tile_type = tile.tile_type

            # Check if there's a wall ahead
            walls = FirstPersonView.get_wall_configuration(floor, tile_x, tile_y)

            # If looking at a wall face, render wall
            if dist == 1:
                # Check if forward is blocked
                if not view_data.get("can_move_forward", False):
                    # Render wall
                    renpy.display.render.render(
                        Solid(color_wall, xsize=width, ysize=height),
                        width, height, 0, 0
                    )

            # Check for icons at this tile
            for icon_x, icon_y, icon, icon_dist in icons:
                if icon_x == tile_x and icon_y == tile_y:
                    # Render icon
                    if icon.icon_type == "door_closed":
                        # Render door
                        pass  # Placeholder
                    elif icon.icon_type == "door_open":
                        pass  # Placeholder


screen interaction_prompt(icon, interaction_type, adj_x, adj_y):
    """
    Show interaction prompt for adjacent icons.
    """

    frame:
        xalign 0.5
        yalign 0.2
        xpadding 40
        ypadding 30
        background "#000000CC"

        vbox:
            spacing 15
            xalign 0.5

            if icon.icon_type == "stairs_up":
                text "Stairs leading up" xalign 0.5
                textbutton "Climb Up":
                    action Function(handle_stairs_interaction, "up", adj_x, adj_y)
                    xalign 0.5

            elif icon.icon_type == "stairs_down":
                text "Stairs leading down" xalign 0.5
                textbutton "Climb Down":
                    action Function(handle_stairs_interaction, "down", adj_x, adj_y)
                    xalign 0.5

            elif icon.icon_type == "door_closed":
                text "A closed door" xalign 0.5
                textbutton "Open":
                    action Function(handle_door_interaction, adj_x, adj_y)
                    xalign 0.5

            elif icon.icon_type == "door_open":
                text "An open door" xalign 0.5

            textbutton "Cancel":
                action NullAction()
                xalign 0.5


# Navigation handler functions
init python:
    def handle_turn_left():
        """Rotate player 90 degrees left"""
        global player_state
        if player_state:
            player_state.rotate_left()
            renpy.restart_interaction()

    def handle_turn_right():
        """Rotate player 90 degrees right"""
        global player_state
        if player_state:
            player_state.rotate_right()
            renpy.restart_interaction()

    def handle_move_forward():
        """Move player one tile forward"""
        global player_state, map_grid

        if not player_state or not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        # Get forward position
        new_x, new_y = player_state.get_forward_position()

        # Validate movement
        can_move, reason = MovementValidator.can_move_to(
            floor, player_state.x, player_state.y, new_x, new_y, player_state.rotation
        )

        if can_move:
            # Move player
            player_state.set_position(new_x, new_y)

            # Check for step-on triggers
            icon, trigger_type = InteractionHandler.check_step_on_trigger(floor, new_x, new_y)
            if icon:
                handle_step_on_trigger(icon)

            renpy.restart_interaction()
        else:
            renpy.notify("Cannot move: {}".format(reason))

    def handle_move_backward():
        """Move player one tile backward"""
        global player_state, map_grid

        if not player_state or not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        # Get backward position
        new_x, new_y = player_state.get_backward_position()

        # Validate movement
        can_move, reason = MovementValidator.can_move_to(
            floor, player_state.x, player_state.y, new_x, new_y, player_state.rotation
        )

        if can_move:
            # Move player
            player_state.set_position(new_x, new_y)

            # Check for step-on triggers
            icon, trigger_type = InteractionHandler.check_step_on_trigger(floor, new_x, new_y)
            if icon:
                handle_step_on_trigger(icon)

            renpy.restart_interaction()
        else:
            renpy.notify("Cannot move: {}".format(reason))

    def handle_step_on_trigger(icon):
        """Handle step-on interactions (gathering, event, teleporter, enemy)"""
        global player_state

        result = InteractionHandler.handle_interaction(icon, "step_on", player_state, None)

        if result["type"] == "enemy":
            renpy.notify("You take {} damage! Health: {}".format(
                result["damage"], result["health"]
            ))
        elif result["type"] == "gathering":
            renpy.notify(result["message"])
        elif result["type"] == "event":
            renpy.notify(result["message"])
        elif result["type"] == "teleporter":
            renpy.notify(result["message"])

    def handle_stairs_interaction(direction, adj_x, adj_y):
        """Handle stairs interaction (change floors)"""
        global player_state, map_grid

        if not map_grid:
            return

        current_floor = map_grid.get_current_floor()
        if not current_floor:
            return

        # Get current floor ID and calculate target floor
        current_id = current_floor.floor_id

        # Extract numeric part of floor ID (e.g., "floor_1" -> 1)
        try:
            floor_num = int(current_id.split("_")[-1])
            if direction == "up":
                target_num = floor_num - 1
            else:  # down
                target_num = floor_num + 1

            target_id = "floor_{}".format(target_num)

            # Check if target floor exists
            if target_id in map_grid.floors:
                # Switch floor
                map_grid.switch_floor(target_id)
                player_state.current_floor_id = target_id

                # Get starting position for new floor
                new_floor = map_grid.get_floor(target_id)
                player_state.x = getattr(new_floor, 'starting_x', 10)
                player_state.y = getattr(new_floor, 'starting_y', 10)
                player_state.rotation = getattr(new_floor, 'starting_rotation', 0)

                renpy.notify("Moved to {}".format(new_floor.floor_name))
                renpy.restart_interaction()
            else:
                renpy.notify("No floor {} exists".format(target_id))
        except:
            renpy.notify("Cannot determine target floor")

    def handle_door_interaction(adj_x, adj_y):
        """Handle door interaction (open door)"""
        global map_grid

        if not map_grid:
            return

        floor = map_grid.get_current_floor()
        if not floor:
            return

        # Get icon at door position
        icon = floor.icons.get((adj_x, adj_y))
        if icon and icon.icon_type == "door_closed":
            # Change door to open
            icon.icon_type = "door_open"
            renpy.notify("Door opened")
            renpy.restart_interaction()
