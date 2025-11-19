# Echoes of Ember - Map Data Persistence
# Map data is saved WITH Ren'Py save files (using default, NOT persistent)
# This ensures each save file has independent map data

init -1 python:
    import json
    import os

    def get_map_data_dir():
        """Get the directory for map data files"""
        # Use Ren'Py's savegame directory
        print("MapPersistence - config.savedir = {}".format(config.savedir))
        map_dir = os.path.join(config.savedir, "map_data")
        print("MapPersistence - map_data dir = {}".format(map_dir))
        if not os.path.exists(map_dir):
            try:
                os.makedirs(map_dir)
                print("MapPersistence - Created directory: {}".format(map_dir))
            except Exception as e:
                print("MapPersistence - Error creating directory: {}".format(e))
        return map_dir

    def get_map_data_path(slot_name):
        """Get file path for map data for a given save slot"""
        if not slot_name:
            return None
        map_dir = get_map_data_dir()
        # Sanitize slot name for filename
        safe_name = str(slot_name).replace("/", "_").replace("\\", "_").replace("-", "_")
        return os.path.join(map_dir, "{}.json".format(safe_name))

    def save_map_data_to_file(slot_name):
        """Save current map_grid to external JSON file"""
        global map_grid

        print("MapPersistence - save_map_data_to_file called with slot: {}".format(slot_name))
        print("MapPersistence - map_grid exists: {}".format(map_grid is not None))

        if not slot_name:
            print("MapPersistence - Error: No slot_name provided")
            return False

        if not map_grid:
            print("MapPersistence - Error: map_grid is None")
            return False

        path = get_map_data_path(slot_name)
        if not path:
            print("MapPersistence - Error: Could not get path for slot")
            return False

        print("MapPersistence - Full save path: {}".format(path))

        try:
            # Serialize map_grid to dict
            data = map_grid.to_dict()
            print("MapPersistence - Serialized data, {} floors".format(len(data.get("floors", {}))))

            # Write to file
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print("MapPersistence - SUCCESS! Saved map data to: {}".format(path))
            print("MapPersistence - File size: {} bytes".format(os.path.getsize(path)))
            return True
        except Exception as e:
            print("MapPersistence Error - Save failed: {}".format(e))
            import traceback
            traceback.print_exc()
            return False

    def load_map_data_from_file(slot_name):
        """Load map data from external JSON file into map_grid"""
        global map_grid

        if not slot_name:
            return False

        path = get_map_data_path(slot_name)
        if not path or not os.path.exists(path):
            # No map data for this slot - initialize fresh
            print("MapPersistence - No map data file found for slot: {}".format(slot_name))
            map_grid = MapGrid()
            # Add default floor for new game
            map_grid.add_floor("floor_1", "Entrance Hall", (20, 20))
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Deserialize into MapGrid object
            map_grid = MapGrid.from_dict(data)

            print("MapPersistence - Loaded map data from: {}".format(path))
            print("  Floors: {}".format(len(map_grid.floors)))
            return True
        except Exception as e:
            print("MapPersistence Error - Load failed: {}".format(e))
            # Initialize fresh on error
            map_grid = MapGrid()
            map_grid.add_floor("floor_1", "Entrance Hall", (20, 20))
            return False

    def delete_map_data_file(slot_name):
        """Delete map data file for a given slot"""
        if not slot_name:
            return False

        path = get_map_data_path(slot_name)
        if path and os.path.exists(path):
            try:
                os.remove(path)
                print("MapPersistence - Deleted map data file: {}".format(path))
                return True
            except Exception as e:
                print("MapPersistence Error - Delete failed: {}".format(e))
                return False
        return False


# File I/O based map data persistence
# ============================================================
# Ren'Py's default system doesn't work - it wipes map_grid
# So we use external JSON files, one per save slot
# ============================================================

init -10 python:
    # Wrapper functions that handle both game save/load AND map data file I/O

    def save_game_with_map(name, extra_info='', screenshot=None, **kwargs):
        """Save game AND map data to external JSON file"""
        print("=" * 60)
        print("MapPersistence - save_game_with_map called for: {}".format(name))

        # Convert slot number to string for renpy.save()
        # FileAction uses format like "1-1" for page 1, slot 1
        # But we just have the slot number, so convert to string
        slot_name = str(name)

        # First save the game normally
        renpy.save(slot_name, extra_info=extra_info, **kwargs)

        # Then save map data to external file (use same name)
        save_map_data_to_file(slot_name)
        print("=" * 60)

        return True

    def load_game_with_map(name, **kwargs):
        """Load game AND map data from external JSON file"""
        print("=" * 60)
        print("MapPersistence - load_game_with_map called for: {}".format(name))

        # Convert slot number to string
        slot_name = str(name)

        # Write slot name to a temporary file that survives renpy.load()
        temp_file = os.path.join(config.savedir, "_loading_slot.tmp")
        try:
            with open(temp_file, 'w') as f:
                f.write(slot_name)
            print("MapPersistence - Wrote slot to temp file: {}".format(temp_file))
        except Exception as e:
            print("MapPersistence - ERROR writing temp file: {}".format(e))

        # Load the game - after_load will read the temp file
        renpy.load(slot_name, **kwargs)
        print("=" * 60)

init python:
    # Store reference to original FileAction before we modify anything
    OriginalFileAction = FileAction

    # Custom FileAction that wraps the original and adds map data save/load
    class FileActionWithMapData(Action):
        """Wraps FileAction to add map data persistence to external files"""

        def __init__(self, name, page=None, **kwargs):
            self.name = name
            self.page = page
            self.kwargs = kwargs
            # Create an instance of the original FileAction
            self.original_action = OriginalFileAction(name, page, **kwargs)

        def __call__(self):
            # Determine if we're on save or load screen (robust method)
            # Check which screen is currently displayed
            is_save_screen = renpy.get_screen("save") is not None
            is_load_screen = renpy.get_screen("load") is not None

            if is_save_screen:
                # SAVE: Call original FileAction first (handles screenshot, etc.)
                self.original_action()

                # Then save map data to external file
                slot_name = str(self.name)
                print("MapPersistence - Saving map data for slot: {}".format(slot_name))
                save_map_data_to_file(slot_name)

            elif is_load_screen:
                # LOAD: Write slot to temp file, then call original FileAction
                slot_name = str(self.name)
                temp_file = os.path.join(config.savedir, "_loading_slot.tmp")
                try:
                    with open(temp_file, 'w') as f:
                        f.write(slot_name)
                    print("MapPersistence - Wrote slot to temp file for load: {}".format(slot_name))
                except Exception as e:
                    print("MapPersistence - ERROR writing temp file: {}".format(e))

                # Call original FileAction to load the game
                # after_load label will then load the map data
                self.original_action()

            else:
                # Unknown screen - just call original action
                print("MapPersistence - Warning: FileAction called from unknown screen, delegating to original")
                self.original_action()

        def get_sensitive(self):
            # Delegate to original FileAction
            return self.original_action.get_sensitive()

        def get_selected(self):
            # Delegate to original FileAction
            return self.original_action.get_selected()

    print("MapPersistence - File I/O persistence system initialized")
    print("MapPersistence - Wrapped FileAction to add map data save/load")


# Label that runs AFTER loading a save file
label after_load:
    python:
        import os

        print("MapPersistence - after_load triggered")

        # Read slot name from temporary file
        temp_file = os.path.join(config.savedir, "_loading_slot.tmp")
        slot = None

        if os.path.exists(temp_file):
            try:
                with open(temp_file, 'r') as f:
                    slot = f.read().strip()
                print("MapPersistence - Read slot from temp file: {}".format(slot))

                # Delete temp file
                os.remove(temp_file)
            except Exception as e:
                print("MapPersistence - ERROR reading temp file: {}".format(e))

        if slot:
            print("=" * 60)
            print("MapPersistence - after_load: Loading map for slot {}".format(slot))

            # Load map data from JSON file
            # This happens AFTER renpy.load() restored variables
            load_map_data_from_file(slot)

            print("=" * 60)
        else:
            print("MapPersistence - after_load: No temp file found, skipping map load")

    return
