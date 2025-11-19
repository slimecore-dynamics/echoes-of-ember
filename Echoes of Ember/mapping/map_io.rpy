# Echoes of Ember - Mapping System File I/O
# MapIO Class for Save/Load/Import/Export Operations
# Based on: mapping_file_io_specification.md v1.0

init python:
    import json
    import os
    import time

    class MapIO:
        """
        Handles all file I/O operations for the mapping system

        NOTE: Map data is now automatically saved with Ren'Py save files.
        The persistent storage methods are DEPRECATED and should not be used.

        This class provides methods for:
        - Exporting maps to JSON files for sharing and backups
        - Importing maps from JSON files
        - Data validation and error handling

        DEPRECATED:
        - save_to_persistent() - Map data saves automatically
        - load_from_persistent() - Map data loads automatically
        """

        # Directory paths (relative to game directory)
        PERSISTENT_KEY = "map_data"
        EXPORT_DIR = "maps/exports"
        IMPORT_DIR = "maps/imports"
        BACKUP_DIR = "maps/backups"

        @staticmethod
        def save_to_persistent(map_grid):
            """
            DEPRECATED: Map data is now automatically saved with Ren'Py save files.
            This function does nothing and always returns True.

            Previously saved map data to Ren'Py persistent storage, but this
            caused map data to be shared across all save files.

            Args:
                map_grid: MapGrid object (ignored)

            Returns:
                True (always)
            """
            # DEPRECATED: Do nothing, map saves automatically with game saves
            return True

        @staticmethod
        def load_from_persistent():
            """
            DEPRECATED: Map data is now automatically loaded with Ren'Py save files.
            This function just returns a fresh MapGrid.

            Previously loaded map data from Ren'Py persistent storage, but this
            caused map data to be shared across all save files.

            Returns:
                Fresh MapGrid object
            """
            # DEPRECATED: Just return fresh grid, map loads automatically with game saves
            return MapGrid()

        @staticmethod
        def export_to_json(map_grid, filename=None):
            """
            Export map data to JSON file
            Used for sharing maps or creating backups

            Args:
                map_grid: MapGrid object to export
                filename: Optional custom filename (auto-generated if None)

            Returns:
                filepath: Path to exported file, or None if failed
            """
            try:
                # Ensure export directory exists
                export_path = os.path.join(renpy.config.gamedir, MapIO.EXPORT_DIR)
                if not os.path.exists(export_path):
                    os.makedirs(export_path)

                # Generate filename if not provided
                if not filename:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = "map_export_{}.json".format(timestamp)

                # Ensure .json extension
                if not filename.endswith('.json'):
                    filename += '.json'

                filepath = os.path.join(export_path, filename)

                # Serialize and save
                data = map_grid.to_dict()
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print("MapIO - Exported map to: {}".format(filepath))
                return filepath

            except Exception as e:
                print("MapIO Error - Export failed: {}".format(e))
                return None

        @staticmethod
        def import_from_json(filepath):
            """
            Import map data from JSON file

            Args:
                filepath: Path to JSON file (relative to game directory or absolute)

            Returns:
                MapGrid object or None if import failed
            """
            try:
                # Handle relative paths
                if not os.path.isabs(filepath):
                    filepath = os.path.join(renpy.config.gamedir, filepath)

                # Check file exists
                if not os.path.exists(filepath):
                    print("MapIO Error - File not found: {}".format(filepath))
                    return None

                # Load and parse JSON
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Validate data
                is_valid, error_msg = MapIO.validate_map_data(data)
                if not is_valid:
                    print("MapIO Error - Invalid map data: {}".format(error_msg))
                    return None

                # Deserialize
                map_grid = MapGrid.from_dict(data)
                print("MapIO - Imported map from: {}".format(filepath))
                return map_grid

            except json.JSONDecodeError as e:
                print("MapIO Error - Invalid JSON format: {}".format(e))
                return None
            except Exception as e:
                print("MapIO Error - Import failed: {}".format(e))
                return None

        @staticmethod
        def export_floor_to_json(floor_map, filename=None):
            """
            Export a single floor to JSON file

            Args:
                floor_map: FloorMap object to export
                filename: Optional custom filename

            Returns:
                filepath: Path to exported file, or None if failed
            """
            try:
                export_path = os.path.join(renpy.config.gamedir, MapIO.EXPORT_DIR)
                if not os.path.exists(export_path):
                    os.makedirs(export_path)

                if not filename:
                    # Generate filename from floor name
                    safe_name = floor_map.floor_name.lower().replace(' ', '_')
                    filename = "{}_{}.json".format(floor_map.floor_id, safe_name)

                if not filename.endswith('.json'):
                    filename += '.json'

                filepath = os.path.join(export_path, filename)

                # Serialize and save
                data = floor_map.to_dict()
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print("MapIO - Exported floor to: {}".format(filepath))
                return filepath

            except Exception as e:
                print("MapIO Error - Floor export failed: {}".format(e))
                return None

        @staticmethod
        def import_floor_from_json(filepath):
            """
            Import a single floor from JSON file

            Args:
                filepath: Path to JSON file

            Returns:
                FloorMap object or None if import failed
            """
            try:
                if not os.path.isabs(filepath):
                    filepath = os.path.join(renpy.config.gamedir, filepath)

                if not os.path.exists(filepath):
                    print("MapIO Error - File not found: {}".format(filepath))
                    return None

                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Basic validation for floor data
                required_keys = ["floor_id", "floor_name", "dimensions", "tiles"]
                for key in required_keys:
                    if key not in data:
                        print("MapIO Error - Missing required key: {}".format(key))
                        return None

                floor = FloorMap.from_dict(data)
                print("MapIO - Imported floor: {}".format(floor.floor_name))
                return floor

            except Exception as e:
                print("MapIO Error - Floor import failed: {}".format(e))
                return None

        @staticmethod
        def create_backup(map_grid):
            """
            Create automatic backup of current map state

            Args:
                map_grid: MapGrid to backup

            Returns:
                filepath: Path to backup file, or None if failed
            """
            try:
                backup_path = os.path.join(renpy.config.gamedir, MapIO.BACKUP_DIR)
                if not os.path.exists(backup_path):
                    os.makedirs(backup_path)

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = "map_backup_{}.json".format(timestamp)
                filepath = os.path.join(backup_path, filename)

                data = map_grid.to_dict()
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print("MapIO - Created backup: {}".format(filepath))
                return filepath

            except Exception as e:
                print("MapIO Error - Backup creation failed: {}".format(e))
                return None

        @staticmethod
        def _backup_corrupted_data(data):
            """
            Internal method to backup corrupted persistent data for analysis

            Args:
                data: Corrupted data to backup
            """
            try:
                backup_path = os.path.join(renpy.config.gamedir, MapIO.BACKUP_DIR)
                if not os.path.exists(backup_path):
                    os.makedirs(backup_path)

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = "corrupted_backup_{}.json".format(timestamp)
                filepath = os.path.join(backup_path, filename)

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print("MapIO - Backed up corrupted data to: {}".format(filepath))

            except Exception as e:
                print("MapIO Error - Could not backup corrupted data: {}".format(e))

        @staticmethod
        def list_exported_maps():
            """
            Get list of all exported map files

            Returns:
                List of filenames in exports directory
            """
            try:
                export_path = os.path.join(renpy.config.gamedir, MapIO.EXPORT_DIR)
                if not os.path.exists(export_path):
                    return []

                files = [f for f in os.listdir(export_path) if f.endswith('.json')]
                return sorted(files, reverse=True)  # Most recent first

            except Exception as e:
                print("MapIO Error - Could not list exports: {}".format(e))
                return []

        @staticmethod
        def list_importable_maps():
            """
            Get list of all importable map files

            Returns:
                List of filenames in imports directory
            """
            try:
                import_path = os.path.join(renpy.config.gamedir, MapIO.IMPORT_DIR)
                if not os.path.exists(import_path):
                    return []

                files = [f for f in os.listdir(import_path) if f.endswith('.json')]
                return sorted(files)

            except Exception as e:
                print("MapIO Error - Could not list imports: {}".format(e))
                return []

        @staticmethod
        def list_backups():
            """
            Get list of all backup files

            Returns:
                List of filenames in backups directory
            """
            try:
                backup_path = os.path.join(renpy.config.gamedir, MapIO.BACKUP_DIR)
                if not os.path.exists(backup_path):
                    return []

                files = [f for f in os.listdir(backup_path) if f.endswith('.json')]
                return sorted(files, reverse=True)  # Most recent first

            except Exception as e:
                print("MapIO Error - Could not list backups: {}".format(e))
                return []

        @staticmethod
        def validate_map_data(data):
            """
            Validate map data structure

            Args:
                data: Dictionary to validate

            Returns:
                (is_valid, error_message) tuple
            """
            try:
                # Check if data is a dictionary
                if not isinstance(data, dict):
                    return (False, "Data must be a dictionary")

                # Check required keys
                required_keys = ["version", "floors"]
                for key in required_keys:
                    if key not in data:
                        return (False, "Missing required key: {}".format(key))

                # Validate version
                if not isinstance(data["version"], (str, unicode)):
                    return (False, "Invalid version format")

                # Validate floors
                if not isinstance(data["floors"], dict):
                    return (False, "Floors must be a dictionary")

                # Validate each floor
                for floor_id, floor_data in data["floors"].items():
                    floor_required = ["floor_id", "floor_name", "dimensions", "tiles"]
                    for key in floor_required:
                        if key not in floor_data:
                            return (False, "Floor {} missing key: {}".format(floor_id, key))

                    # Validate dimensions
                    if not isinstance(floor_data["dimensions"], list) or len(floor_data["dimensions"]) != 2:
                        return (False, "Floor {} has invalid dimensions".format(floor_id))

                    # Validate tiles is a 2D array
                    if not isinstance(floor_data["tiles"], list):
                        return (False, "Floor {} tiles must be a list".format(floor_id))

                return (True, "")

            except Exception as e:
                return (False, str(e))

        @staticmethod
        def ensure_directories():
            """
            Ensure all required directories exist
            Called on initialization
            """
            try:
                directories = [
                    MapIO.EXPORT_DIR,
                    MapIO.IMPORT_DIR,
                    MapIO.BACKUP_DIR
                ]

                for dir_path in directories:
                    full_path = os.path.join(renpy.config.gamedir, dir_path)
                    if not os.path.exists(full_path):
                        os.makedirs(full_path)
                        print("MapIO - Created directory: {}".format(full_path))

            except Exception as e:
                print("MapIO Error - Could not create directories: {}".format(e))


# Helper functions for easy access

init python:
    def save_map():
        """Quick save current map to persistent storage"""
        if map_grid:
            return MapIO.save_to_persistent(map_grid)
        return False

    def load_map():
        """Quick load map from persistent storage"""
        global map_grid
        map_grid = MapIO.load_from_persistent()
        return map_grid

    def export_map(filename=None):
        """Quick export current map to JSON"""
        if map_grid:
            filepath = MapIO.export_to_json(map_grid, filename)
            if filepath:
                renpy.notify("Map exported successfully!")
                return filepath
        renpy.notify("Export failed!")
        return None

    def import_map(filename):
        """Quick import map from JSON file"""
        global map_grid
        filepath = os.path.join(MapIO.IMPORT_DIR, filename)
        imported = MapIO.import_from_json(filepath)
        if imported:
            map_grid = imported
            MapIO.save_to_persistent(map_grid)
            renpy.notify("Map imported successfully!")
            return True
        renpy.notify("Import failed!")
        return False

    def backup_map():
        """Quick create backup of current map"""
        if map_grid:
            filepath = MapIO.create_backup(map_grid)
            if filepath:
                renpy.notify("Backup created!")
                return filepath
        renpy.notify("Backup failed!")
        return None
