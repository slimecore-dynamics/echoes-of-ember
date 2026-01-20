## Investigation System - Interaction Handlers
##
## This file handles interactions with investigation objects (terminals, books, boxes).

init python:
    import sys

    class InvestigationInteractionHandler:
        """
        Handles interactions with investigation objects.

        Two types of investigation interactions:
        1. Terminal: Must be on same tile AND facing correct direction
        2. Examinable (book/box): Either same tile OR adjacent (configurable per object)
        """

        # Investigation icon types
        TERMINAL_ICON = "terminal"
        EXAMINABLE_ICON = "examinable"

        @staticmethod
        def check_investigation_interaction(floor, x, y, rotation):
            """
            Check if there's an investigation object the player can interact with.

            Returns: tuple (icon, interaction_type, pos_x, pos_y, content_id)
                     or (None, None, None, None, None)
            """
            # First check same tile
            icon = floor.get_dungeon_icon(x, y)

            if icon and icon.icon_type == InvestigationInteractionHandler.TERMINAL_ICON:
                # Terminal requires facing direction
                metadata = getattr(icon, 'metadata', {})
                facing_direction = metadata.get('facing_direction', None)

                if facing_direction is not None and rotation != facing_direction:
                    # Not facing the terminal
                    pass
                else:
                    content_id = metadata.get('content_id', None)
                    if content_id:
                        return (icon, "terminal", x, y, content_id)

            if icon and icon.icon_type == InvestigationInteractionHandler.EXAMINABLE_ICON:
                # Examinable object - check interaction range
                metadata = getattr(icon, 'metadata', {})
                content_id = metadata.get('content_id', None)

                if not content_id:
                    return (None, None, None, None, None)

                # Get the examinable object to check interaction range
                examinable = investigation_state.get_examinable(content_id)
                if not examinable:
                    return (None, None, None, None, None)

                # If interaction range is "same_tile", we're good
                if examinable.interaction_range == "same_tile":
                    return (icon, "examinable", x, y, content_id)

            # Check adjacent tile for examinable objects
            adj_pos = InvestigationInteractionHandler._get_adjacent_position(x, y, rotation)
            if adj_pos:
                adj_x, adj_y = adj_pos

                # Check bounds
                width, height = floor.dimensions
                if adj_x >= 0 and adj_x < width and adj_y >= 0 and adj_y < height:
                    icon = floor.get_dungeon_icon(adj_x, adj_y)

                    if icon and icon.icon_type == InvestigationInteractionHandler.EXAMINABLE_ICON:
                        metadata = getattr(icon, 'metadata', {})
                        content_id = metadata.get('content_id', None)

                        if content_id:
                            # Get the examinable object to check interaction range
                            examinable = investigation_state.get_examinable(content_id)
                            if examinable and examinable.interaction_range == "adjacent":
                                return (icon, "examinable", adj_x, adj_y, content_id)

            return (None, None, None, None, None)

        @staticmethod
        def _get_adjacent_position(x, y, rotation):
            """Get position adjacent to (x, y) based on rotation."""
            if rotation == 0:    # North
                return (x, y - 1)
            elif rotation == 90:  # East
                return (x + 1, y)
            elif rotation == 180: # South
                return (x, y + 1)
            elif rotation == 270: # West
                return (x - 1, y)
            return None

        @staticmethod
        def calculate_fpv_position(distance, view_distance, fpv_width, fpv_height, custom_position=None):
            """
            Calculate the position for an investigation object in the first-person view.

            Args:
                distance: Distance from player (1, 2, 3, etc.)
                view_distance: Maximum view distance
                fpv_width: Width of FPV area
                fpv_height: Height of FPV area
                custom_position: Optional (x, y) tuple for custom position

            Returns:
                tuple (x, y, scale) or None if object is beyond view distance
            """
            # If beyond view distance, don't render
            if distance > view_distance:
                return None

            # Calculate scale based on distance
            if distance == view_distance:
                scale = INVESTIGATION_FPV_SCALE_MAX  # 0.0 (invisible)
            else:
                # Linear interpolation between min and max scale
                scale_range = INVESTIGATION_FPV_SCALE_MIN - INVESTIGATION_FPV_SCALE_MAX
                scale = INVESTIGATION_FPV_SCALE_MIN - (scale_range * (distance - 1) / (view_distance - 1))

            if scale <= 0:
                return None

            # If custom position provided, use it
            if custom_position:
                return (custom_position[0], custom_position[1], scale)

            # Calculate default position based on distance
            y_offset = INVESTIGATION_FPV_DEFAULT_Y_OFFSET.get(distance, 0.5)
            x_center = INVESTIGATION_FPV_DEFAULT_X_CENTER

            x = int(fpv_width * x_center)
            y = int(fpv_height * y_offset)

            return (x, y, scale)


## Handler Functions for UI Actions

init python:

    def handle_terminal_interaction(content_id):
        """Open a terminal interface."""
        terminal = investigation_state.get_terminal(content_id)
        if not terminal:
            renpy.notify("Terminal not found: {}".format(content_id))
            return

        # Set current terminal
        investigation_state.current_terminal = terminal
        investigation_state.current_terminal_category = None
        investigation_state.current_terminal_entry_index = None

        # Show terminal screen
        renpy.show_screen("terminal_interface", terminal)

    def handle_examinable_interaction(content_id):
        """Examine a simple object (book, box, etc.)."""
        examinable = investigation_state.get_examinable(content_id)
        if not examinable:
            renpy.notify("Object not found: {}".format(content_id))
            return

        # Get current location for journal entry
        floor = map_grid.get_current_floor() if map_grid else None
        if floor:
            location = "{} - {}".format(
                getattr(floor, 'area_name', 'Unknown Area'),
                getattr(floor, 'floor_name', floor.floor_id)
            )
        else:
            location = "Unknown Location"

        # Collect the item
        newly_collected = investigation_state.collect_item(
            item_id=examinable.id,
            item_title=examinable.title,
            item_content=examinable.get_content(),
            location=location,
            is_evidence=examinable.is_evidence,
            evidence_summary=examinable.evidence_summary
        )

        # Show notification if newly collected
        if newly_collected:
            if examinable.is_evidence:
                renpy.notify(NOTIFICATION_EVIDENCE_SECURED)
            else:
                renpy.notify(NOTIFICATION_DATA_SECURED)

        # Show examination popup
        renpy.show_screen("examination_popup", examinable)

    def handle_terminal_entry_collection(terminal_id, entry_id):
        """Collect a terminal entry when first viewed."""
        terminal = investigation_state.get_terminal(terminal_id)
        if not terminal:
            print("Warning: Terminal not found: {}".format(terminal_id), file=sys.stderr)
            return

        # Find the entry
        entry = None
        for category, entries in terminal.entries.items():
            for e in entries:
                if e.id == entry_id:
                    entry = e
                    break
            if entry:
                break

        if not entry:
            print("Warning: Entry not found: {} in terminal {}".format(entry_id, terminal_id), file=sys.stderr)
            return

        # Get current location for journal entry
        floor = map_grid.get_current_floor() if map_grid else None
        if floor:
            location = "{} - {}".format(
                getattr(floor, 'area_name', 'Unknown Area'),
                getattr(floor, 'floor_name', floor.floor_id)
            )
        else:
            location = "Unknown Location"

        # Collect the entry
        newly_collected = investigation_state.collect_item(
            item_id=entry.id,
            item_title=entry.title,
            item_content=entry.get_content(),
            location=location,
            is_evidence=entry.is_evidence,
            evidence_summary=entry.evidence_summary
        )

        # Show notification if newly collected
        if newly_collected:
            if entry.is_evidence:
                renpy.notify(NOTIFICATION_EVIDENCE_SECURED)
            else:
                renpy.notify(NOTIFICATION_DATA_SECURED)

    def open_journal():
        """Open the journal screen."""
        renpy.show_screen("journal_screen")
