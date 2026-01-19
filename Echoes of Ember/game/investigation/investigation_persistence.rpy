## Investigation System - Persistence (Save/Load)
##
## This file handles saving and loading investigation data with game saves.

init python:

    def serialize_investigation_data(data):
        """
        Serialize investigation state to JSON for saving.

        Called by Ren'Py when saving the game.
        """
        try:
            investigation_data = investigation_state.to_dict()
            data["investigation_state"] = investigation_data
        except Exception as e:
            renpy.notify("Error saving investigation data: {}".format(str(e)))

    def deserialize_investigation_data():
        """
        Deserialize investigation state from JSON after loading.

        Called by Ren'Py when loading the game.
        Note: This is called with no arguments by after_load_callbacks.
        """
        global investigation_state

        try:
            # Get the slot tracker to find which slot was loaded
            tracker_path = get_slot_tracker_path()
            slot_name = None

            import os
            if os.path.exists(tracker_path):
                with open(tracker_path, 'r') as f:
                    slot_name = f.read().strip()

            if slot_name:
                # Get JSON data from the save file
                json_data = renpy.slot_json(slot_name)

                if json_data and "investigation_state" in json_data:
                    investigation_state = InvestigationState.from_dict(json_data["investigation_state"])
                else:
                    # No investigation data in save file - use default
                    investigation_state = InvestigationState()
            else:
                # No slot tracker - use default
                investigation_state = InvestigationState()

        except Exception as e:
            import sys
            print("!!! Error loading investigation data: {}".format(e), file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            investigation_state = InvestigationState()

## Register callbacks with Ren'Py
init python:
    # Register save callback
    config.save_json_callbacks.append(serialize_investigation_data)

    # Register load callback
    config.after_load_callbacks.append(deserialize_investigation_data)
