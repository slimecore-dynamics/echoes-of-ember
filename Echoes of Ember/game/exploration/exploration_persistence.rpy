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

            print("ExplorationPersistence - Saved player state to: {}".format(player_path))
            return True

        except Exception as e:
            print("ExplorationPersistence - Error saving player state: {}".format(e))
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
                print("ExplorationPersistence - No player state file found")
                # Don't create a default player state - let the dungeon load handle it
                return False

            # Load JSON
            with open(player_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Deserialize player state
            player_state = PlayerState.from_dict(data)

            print("ExplorationPersistence - Loaded player state from: {}".format(player_path))
            return True

        except Exception as e:
            print("ExplorationPersistence - Error loading player state: {}".format(e))
            # Don't create a default player state on error - let the dungeon load handle it
            return False


# Hook into existing save/load system
# We need to extend FileActionWithMapData to also save player state
# NOTE: This must run AFTER map_persistence.rpy (init -1), so we use init 1

init 1 python:
    # Store reference to original save function
    _original_save_map_data_to_file = save_map_data_to_file
    _original_load_map_data_from_file = load_map_data_from_file

    def save_map_data_to_file_extended(slot_name):
        """Extended version that saves both map and player state"""
        # Call original map save
        result = _original_save_map_data_to_file(slot_name)

        # Also save player state
        save_player_state_to_file(slot_name)

        return result

    def load_map_data_from_file_extended(slot_name):
        """Extended version that loads both map and player state"""
        # Call original map load
        result = _original_load_map_data_from_file(slot_name)

        # Also load player state
        load_player_state_from_file(slot_name)

        return result

    # Replace the functions
    save_map_data_to_file = save_map_data_to_file_extended
    load_map_data_from_file = load_map_data_from_file_extended
