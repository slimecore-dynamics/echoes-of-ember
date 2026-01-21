## code_input_screen.rpy
## Code input interface for locked doors and terminals

init python:
    class CodeInputState:
        """Manages state for code input validation and lockout."""

        def __init__(self):
            self.current_object = None  # (x, y, icon_type) tuple
            self.current_code = ""
            self.failed_attempts = 0
            self.is_locked_out = False
            self.lockout_end_time = 0
            self.is_flashing = False
            self.flash_success = False  # True for green, False for red

        def start_code_input(self, x, y, icon_type):
            """Initialize state for a new code input session."""
            # If switching to different object, reset state
            if self.current_object != (x, y, icon_type):
                self.current_object = (x, y, icon_type)
                self.current_code = ""
                self.failed_attempts = 0
                self.is_locked_out = False
                self.lockout_end_time = 0

        def reset(self):
            """Reset all state."""
            self.current_object = None
            self.current_code = ""
            self.failed_attempts = 0
            self.is_locked_out = False
            self.lockout_end_time = 0
            self.is_flashing = False
            self.flash_success = False

        def check_lockout(self):
            """Check if lockout has expired."""
            if self.is_locked_out:
                import time
                if time.time() >= self.lockout_end_time:
                    self.is_locked_out = False
                    self.failed_attempts = 0
                    return False
                return True
            return False

        def get_remaining_lockout_time(self):
            """Get remaining lockout time in seconds."""
            import time
            if self.is_locked_out:
                remaining = max(0, self.lockout_end_time - time.time())
                return int(remaining)
            return 0

        def can_input(self):
            """Check if player can currently input code."""
            return not self.is_locked_out and not self.is_flashing

    # Global code input state
    code_input_state = CodeInputState()


def handle_code_submission(passcode, x, y, icon_type, is_door=True):
    """
    Handle code submission and validation.

    Args:
        passcode: The correct passcode
        x, y: Grid coordinates of the object
        icon_type: Type of icon (for fetching)
        is_door: True if door, False if terminal
    """
    import time

    # Get the player's input
    player_code = code_input_state.current_code.strip()

    # Check if code is correct (case-sensitive exact match)
    if player_code == passcode:
        # Success! Flash green and unlock
        code_input_state.is_flashing = True
        code_input_state.flash_success = True
        renpy.restart_interaction()

        # Flash green 3 times (0.2s on, 0.2s off, repeat)
        for i in range(3):
            renpy.pause(0.2, hard=True)
            renpy.restart_interaction()
            renpy.pause(0.2, hard=True)
            renpy.restart_interaction()

        code_input_state.is_flashing = False

        # Unlock the object
        floor = map_grid.get_floor(player_state.current_floor_id)
        if floor:
            icon = floor.get_dungeon_icon(x, y)
            if icon and icon.metadata:
                icon.metadata["unlocked"] = True

                # For doors, change to door_open
                if is_door:
                    icon.icon_type = "door_open"

        # Reset state and close interface
        code_input_state.reset()
        renpy.hide_screen("code_input_interface")

        # If it was a door, show success message
        if is_door:
            renpy.notify("Door unlocked")
        else:
            # For terminals, open the terminal interface
            if icon and icon.metadata:
                content_id = icon.metadata.get("content_id")
                if content_id:
                    handle_terminal_interaction(content_id)
    else:
        # Failed attempt - flash red
        code_input_state.is_flashing = True
        code_input_state.flash_success = False
        code_input_state.failed_attempts += 1
        renpy.restart_interaction()

        # Flash red 3 times
        for i in range(3):
            renpy.pause(0.2, hard=True)
            renpy.restart_interaction()
            renpy.pause(0.2, hard=True)
            renpy.restart_interaction()

        code_input_state.is_flashing = False

        # Clear input field
        code_input_state.current_code = ""

        # Check if we should lock out
        if code_input_state.failed_attempts >= 3:
            code_input_state.is_locked_out = True
            code_input_state.lockout_end_time = time.time() + LOCKOUT_TIMEOUT_SECONDS

        renpy.restart_interaction()


def get_code_input_from_player(prompt_text, is_numeric):
    """
    Get code input from player using renpy.input().

    Args:
        prompt_text: Prompt to show player
        is_numeric: If True, only allow numbers

    Returns:
        String input from player
    """
    if is_numeric:
        return renpy.input(prompt_text, allow="0123456789", length=20)
    else:
        return renpy.input(prompt_text, length=50)


screen code_input_interface(x, y, icon, is_door=True):
    """
    Code input interface for locked doors and terminals.

    Args:
        x, y: Grid coordinates of the locked object
        icon: MapIcon instance
        is_door: True if door, False if terminal
    """
    modal True
    zorder 200

    # Extract properties from icon metadata
    $ metadata = icon.metadata if icon.metadata else {}
    $ passcode = metadata.get("passcode", "")
    $ hint_text = metadata.get("hint_text", "")
    $ keycode = metadata.get("keycode", False)
    $ examine_text = metadata.get("examine_text", "This is locked.")

    # Initialize code input state for this object
    $ code_input_state.start_code_input(x, y, icon.icon_type)

    # Check if lockout expired
    $ code_input_state.check_lockout()

    # Dim background
    add "#000000c0"

    # Main popup frame
    frame:
        xalign 0.5
        yalign 0.5
        xmaximum 600
        padding (30, 30)
        background "#1a1a1a"

        vbox:
            spacing 20
            xfill True

            # Title
            text ("Locked Door" if is_door else "Locked Terminal"):
                size 28
                xalign 0.5
                color "#ffffff"

            # Examination text
            if examine_text:
                text examine_text:
                    size 18
                    color "#d0d0d0"
                    xalign 0.5
                    text_align 0.5

            add Solid("#404040", xalign=0.0, xsize=540, ysize=2)

            # Code input prompt
            text ("Enter Code:" if not code_input_state.is_locked_out else "Access Denied"):
                size 20
                xalign 0.5
                color ("#ff0000" if code_input_state.is_locked_out else "#ffd700")

            # Input display frame
            frame:
                xalign 0.5
                xsize 400
                ysize 60
                background ("#ff000040" if code_input_state.is_flashing and not code_input_state.flash_success
                           else "#00ff0040" if code_input_state.is_flashing and code_input_state.flash_success
                           else "#2a2a2a")
                padding (10, 10)

                if code_input_state.is_locked_out:
                    # Show lockout countdown
                    $ remaining = code_input_state.get_remaining_lockout_time()
                    text "Locked out for [remaining] seconds":
                        size 18
                        xalign 0.5
                        yalign 0.5
                        color "#ff0000"
                else:
                    # Show current input (masked or visible based on preference)
                    text code_input_state.current_code:
                        size 20
                        xalign 0.5
                        yalign 0.5
                        color "#ffffff"

            # Hint text (if provided)
            if hint_text:
                text "Hint: [hint_text]":
                    size 16
                    color "#808080"
                    xalign 0.5
                    italic True

            # Buttons
            hbox:
                spacing 20
                xalign 0.5

                # Input button
                textbutton "Enter Code":
                    action [
                        Function(lambda: setattr(code_input_state, "current_code",
                                get_code_input_from_player("Enter code:", keycode))),
                        Function(renpy.restart_interaction)
                    ]
                    sensitive code_input_state.can_input()
                    xsize 150
                    ysize 40

                # Submit button
                textbutton "Submit":
                    action Function(handle_code_submission, passcode, x, y, icon.icon_type, is_door)
                    sensitive (code_input_state.can_input() and len(code_input_state.current_code) > 0)
                    xsize 150
                    ysize 40

                # Cancel button
                textbutton "Cancel":
                    action [
                        Function(code_input_state.reset),
                        Hide("code_input_interface")
                    ]
                    xsize 150
                    ysize 40

    # Timer to update lockout countdown
    if code_input_state.is_locked_out:
        timer 1.0 repeat True action [
            Function(code_input_state.check_lockout),
            Function(renpy.restart_interaction)
        ]


screen locked_object_examination(x, y, icon, is_door=True):
    """
    Examination screen for locked doors/terminals.
    Shows examine text and option to try code.

    Args:
        x, y: Grid coordinates of the locked object
        icon: MapIcon instance
        is_door: True if door, False if terminal
    """
    modal True
    zorder 200

    # Extract properties from icon metadata
    $ metadata = icon.metadata if icon.metadata else {}
    $ examine_text = metadata.get("examine_text", "This is locked. You'll need a code to access it.")

    # Dim background
    add "#000000c0"

    # Main popup frame
    frame:
        xalign 0.5
        yalign 0.5
        xmaximum 600
        padding (30, 30)
        background "#1a1a1a"

        vbox:
            spacing 20
            xfill True

            # Title
            text ("Locked Door" if is_door else "Locked Terminal"):
                size 28
                xalign 0.5
                color "#ffffff"

            # Examination text
            text examine_text:
                size 18
                color "#d0d0d0"
                xalign 0.5
                text_align 0.5

            # Buttons
            hbox:
                spacing 20
                xalign 0.5

                # Try Code button
                textbutton "Try Code":
                    action [
                        Hide("locked_object_examination"),
                        Show("code_input_interface", x=x, y=y, icon=icon, is_door=is_door)
                    ]
                    xsize 150
                    ysize 40

                # Cancel button
                textbutton "Cancel":
                    action Hide("locked_object_examination")
                    xsize 150
                    ysize 40
