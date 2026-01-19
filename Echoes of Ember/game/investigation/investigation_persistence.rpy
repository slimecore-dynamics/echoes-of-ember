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

    def deserialize_investigation_data(data):
        """
        Deserialize investigation state from JSON after loading.

        Called by Ren'Py when loading the game.
        """
        global investigation_state

        try:
            if "investigation_state" in data:
                investigation_state = InvestigationState.from_dict(data["investigation_state"])
            else:
                # No investigation data in save file - use default
                investigation_state = InvestigationState()
        except Exception as e:
            renpy.notify("Error loading investigation data: {}".format(str(e)))
            investigation_state = InvestigationState()

## Register callbacks with Ren'Py
init python:
    # Register save callback
    config.save_json_callbacks.append(serialize_investigation_data)

    # Register load callback
    config.after_load_callbacks.append(deserialize_investigation_data)
