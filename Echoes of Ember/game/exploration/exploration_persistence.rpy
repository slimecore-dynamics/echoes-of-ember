# exploration_persistence.rpy
# Extends map save/load system to include player state

init -1 python:
    def save_player_state_to_file(slot_name):
        """
        Save player_state to external JSON file (same location as map data).

        File: <savedir>/map_data/<slot>_player.json
        """
        global player_state

        if not slot_name or not player_state:
            return False

        try:
            # Get map data directory
            map_dir = get_map_data_dir()

            # Sanitize slot name
            safe_name = str(slot_name).replace("/", "_").replace("\\", "_").replace("-", "_")

            # Player state file path
            player_path = os.path.join(map_dir, "{}_player.json".format(safe_name))

            # Serialize player state
            data = player_state.to_dict()

            # Write to JSON
            with open(player_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print("Error saving player state: {}".format(e))
            return False


    def load_player_state_from_file(slot_name):
        """
        Load player_state from external JSON file.

        Returns: True if loaded, False if file not found
        """
        global player_state

        if not slot_name:
            return False

        try:
            # Get map data directory
            map_dir = get_map_data_dir()

            # Sanitize slot name
            safe_name = str(slot_name).replace("/", "_").replace("\\", "_").replace("-", "_")

            # Player state file path
            player_path = os.path.join(map_dir, "{}_player.json".format(safe_name))

            # Check if file exists
            if not os.path.exists(player_path):
                # Don't create a default player state - let the dungeon load handle it
                return False

            # Load JSON
            with open(player_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Deserialize player state
            player_state = PlayerState.from_dict(data)

            return True

        except Exception as e:
            print("Error loading player state: {}".format(e))
            # Don't create a default player state on error - let the dungeon load handle it
            return False


# NOTE: save_map_data_to_file extension disabled - mapping module was removed
# Player state is saved/loaded independently via save_player_state_to_file

