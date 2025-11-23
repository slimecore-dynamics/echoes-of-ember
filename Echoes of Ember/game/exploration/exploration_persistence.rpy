# exploration_persistence.rpy
# Extends map save/load system to include player state

init -1 python:
    import os
    import json

    def get_map_data_dir():
        # Get the directory where map data files are stored
        # Returns: path to <savedir>/map_data/
        # Creates the directory if it doesn't exist

        # Get Ren'Py's save directory
        save_dir = renpy.config.savedir
        print("DEBUG get_map_data_dir: save_dir = {}".format(save_dir))

        # Create map_data subdirectory
        map_dir = os.path.join(save_dir, "map_data")
        print("DEBUG get_map_data_dir: map_dir = {}".format(map_dir))

        # Ensure directory exists
        if not os.path.exists(map_dir):
            print("DEBUG get_map_data_dir: Creating directory")
            os.makedirs(map_dir)
        else:
            print("DEBUG get_map_data_dir: Directory already exists")

        return map_dir

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


    def save_map_data_to_file(slot_name):
        # Save player-drawn map data to external JSON file
        # File: <savedir>/map_data/<slot>_mapgrid.json
        #
        # Saves ONLY player-drawn data:
        # - floor.tiles (player drawings, NOT dungeon_tiles)
        # - floor.icons (player-placed icons, NOT dungeon_icons)
        # - floor.revealed_tiles (auto-map)
        # - map_grid.current_floor_id
        # - map_grid.auto_map_enabled
        global map_grid

        if not slot_name or not map_grid:
            return False

        try:
            # Get map data directory
            map_dir = get_map_data_dir()

            # Sanitize slot name
            safe_name = str(slot_name).replace("/", "_").replace("\\", "_").replace("-", "_")

            # Map grid file path
            map_path = os.path.join(map_dir, "{}_mapgrid.json".format(safe_name))

            # Serialize MapGrid to dict
            data = {
                "current_floor_id": map_grid.current_floor_id,
                "auto_map_enabled": map_grid.auto_map_enabled,
                "floors": {}
            }

            # Serialize each FloorMap (only player-drawn data)
            for floor_id, floor in map_grid.floors.items():
                data["floors"][floor_id] = {
                    "floor_id": floor.floor_id,
                    "floor_name": floor.floor_name,
                    "dimensions": floor.dimensions,
                    # Serialize tiles (player-drawn)
                    "tiles": [[{"type": tile.tile_type, "rotation": tile.rotation}
                              for tile in row] for row in floor.tiles],
                    # Serialize icons (player-placed)
                    "icons": {"{},{}".format(x, y): {"type": icon.icon_type,
                                                      "metadata": icon.metadata}
                             for (x, y), icon in floor.icons.items()},
                    # Serialize revealed tiles (auto-map)
                    "revealed_tiles": list(floor.revealed_tiles)
                }

            # Write to JSON
            with open(map_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print("Error saving map data: {}".format(e))
            return False


    def load_map_data_from_file(slot_name):
        # Load player-drawn map data from external JSON file
        # Returns: True if loaded, False if file not found
        #
        # Restores ONLY player-drawn data:
        # - floor.tiles (player drawings)
        # - floor.icons (player-placed icons)
        # - floor.revealed_tiles (auto-map)
        # - map_grid.current_floor_id
        # - map_grid.auto_map_enabled
        #
        # Does NOT restore dungeon_tiles or dungeon_icons
        # (those come from Tiled JSON via load_dungeon_floor)
        global map_grid

        if not slot_name:
            return False

        try:
            # Get map data directory
            map_dir = get_map_data_dir()

            # Sanitize slot name
            safe_name = str(slot_name).replace("/", "_").replace("\\", "_").replace("-", "_")

            # Map grid file path
            map_path = os.path.join(map_dir, "{}_mapgrid.json".format(safe_name))

            # Check if file exists
            if not os.path.exists(map_path):
                return False

            # Load JSON
            with open(map_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Create new MapGrid
            map_grid = MapGrid()
            map_grid.current_floor_id = data.get("current_floor_id")
            map_grid.auto_map_enabled = data.get("auto_map_enabled", False)

            # Deserialize each FloorMap
            for floor_id, floor_data in data.get("floors", {}).items():
                floor = FloorMap(
                    floor_data["floor_id"],
                    floor_data["floor_name"],
                    tuple(floor_data["dimensions"])
                )

                # Restore tiles (player-drawn)
                for y, row in enumerate(floor_data["tiles"]):
                    for x, tile_data in enumerate(row):
                        floor.tiles[y][x] = MapTile(tile_data["type"], tile_data["rotation"])

                # Restore icons (player-placed)
                for pos_str, icon_data in floor_data.get("icons", {}).items():
                    x, y = map(int, pos_str.split(","))
                    floor.icons[(x, y)] = MapIcon(icon_data["type"], (x, y), icon_data.get("metadata", {}))

                # Restore revealed tiles (auto-map)
                floor.revealed_tiles = set(tuple(pos) for pos in floor_data.get("revealed_tiles", []))

                map_grid.floors[floor_id] = floor

            return True

        except Exception as e:
            print("Error loading map data: {}".format(e))
            return False


    class FileActionWithMapData(Action):
        # Ren'Py action that wraps FileAction and adds map data persistence
        # Saves/loads both game state AND player-drawn map data

        def __init__(self, slot):
            self.slot = slot
            self.file_action = FileAction(slot)
            print("DEBUG FileActionWithMapData: Created for slot {}".format(slot))

        def __call__(self):
            print("DEBUG FileActionWithMapData: __call__ invoked for slot {}".format(self.slot))

            # Delegate to standard FileAction first (handles game state save/load)
            result = self.file_action()
            print("DEBUG FileActionWithMapData: FileAction result = {}".format(result))

            # Then handle map data and player state
            screen_name = renpy.current_screen().screen_name[0]
            print("DEBUG FileActionWithMapData: screen_name = {}".format(screen_name))

            if screen_name == "save":
                print("DEBUG FileActionWithMapData: Saving map data and player state")
                # On save: persist map data and player state
                save_result = save_map_data_to_file(self.slot)
                print("DEBUG FileActionWithMapData: save_map_data result = {}".format(save_result))
                player_result = save_player_state_to_file(self.slot)
                print("DEBUG FileActionWithMapData: save_player_state result = {}".format(player_result))
            else:  # load
                print("DEBUG FileActionWithMapData: Loading map data and player state")
                # On load: restore map data and player state
                load_result = load_map_data_from_file(self.slot)
                print("DEBUG FileActionWithMapData: load_map_data result = {}".format(load_result))
                player_result = load_player_state_from_file(self.slot)
                print("DEBUG FileActionWithMapData: load_player_state result = {}".format(player_result))

            return result

