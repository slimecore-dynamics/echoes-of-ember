# Echoes of Ember - Mapping System Initialization and Utilities
# Map data initialization, labels, and helper functions
# Based on: mapping_implementation_plan.md v3.0

# Initialize mapping system on game start (new game only)
label start_mapping_system:
    python:
        # Ensure required directories exist
        MapIO.ensure_directories()

        # Only initialize fresh map if map_grid doesn't already exist
        # (it will exist if we just loaded a save file)
        global map_grid
        if map_grid is None:
            map_grid = MapGrid()
            floor = map_grid.add_floor("floor_1", "Entrance Hall", (20, 20))
            print("MapSystem - Created new map with default floor: {}".format(floor.floor_name))
        else:
            print("MapSystem - Map already exists (loaded from save), skipping initialization")

    return


# Save map changes (call this label after any map modification)
# NOTE: No longer needed - map_grid is automatically saved with game saves
label save_map_changes:
    # Map data is now automatically saved with Ren'Py's save system
    # This label is kept for compatibility but does nothing
    return


# Create a new floor
label create_new_floor(floor_id, floor_name, width=20, height=20):
    python:
        if map_grid:
            floor = map_grid.add_floor(floor_id, floor_name, (width, height))
            renpy.notify("Floor created: {}".format(floor_name))
            print("MapSystem - Created floor: {} ({})".format(floor_name, floor_id))
    return


# Switch to a different floor
label switch_to_floor(floor_id):
    python:
        if map_grid and map_grid.switch_floor(floor_id):
            renpy.notify("Switched to: {}".format(map_grid.get_floor().floor_name))
            print("MapSystem - Switched to floor: {}".format(floor_id))
        else:
            renpy.notify("Floor not found!")
    return


# Auto-reveal tile at location (for auto-mapping during exploration)
label auto_reveal_tile(x, y, tile_type="empty", rotation=0):
    python:
        if map_grid and map_grid.auto_map_enabled:
            current_floor = map_grid.get_floor()
            if current_floor:
                tile = MapTile(tile_type, rotation)
                current_floor.set_tile(x, y, tile)
                print("MapSystem - Auto-revealed tile at ({}, {}): {}".format(x, y, tile_type))
    return


# Utility functions accessible from Python code
init python:
    def get_current_floor():
        """Get the currently active floor"""
        if map_grid:
            return map_grid.get_floor()
        return None

    def place_map_icon(x, y, icon_type, metadata=None):
        """
        Place an icon on the current floor

        Args:
            x, y: Grid coordinates
            icon_type: Type of icon to place
            metadata: Optional metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        if map_grid:
            current_floor = map_grid.get_floor()
            if current_floor:
                icon = MapIcon(icon_type, (x, y), metadata)
                current_floor.place_icon(x, y, icon)
                return True
        return False

    def remove_map_icon(x, y):
        """Remove icon at coordinates on current floor"""
        if map_grid:
            current_floor = map_grid.get_floor()
            if current_floor:
                success = current_floor.remove_icon(x, y)
                return success
        return False

    def add_map_note(x, y, note_text):
        """
        Add or update a note on the current floor

        Args:
            x, y: Grid coordinates
            note_text: Text content of the note

        Returns:
            True if successful, False otherwise
        """
        if map_grid:
            current_floor = map_grid.get_floor()
            if current_floor:
                current_floor.add_note(x, y, note_text)
                return True
        return False

    def remove_map_note(x, y):
        """Remove note at coordinates on current floor"""
        if map_grid:
            current_floor = map_grid.get_floor()
            if current_floor:
                success = current_floor.remove_note(x, y)
                return success
        return False

    def set_map_tile(x, y, tile_type="empty", rotation=0):
        """
        Set a tile on the current floor

        Args:
            x, y: Grid coordinates
            tile_type: Type of tile to place
            rotation: Rotation in degrees (0, 90, 180, 270)

        Returns:
            True if successful, False otherwise
        """
        if map_grid:
            current_floor = map_grid.get_floor()
            if current_floor:
                tile = MapTile(tile_type, rotation)
                success = current_floor.set_tile(x, y, tile)
                return success
        return False

    def get_map_tile(x, y):
        """
        Get tile at coordinates on current floor

        Args:
            x, y: Grid coordinates

        Returns:
            MapTile object or None
        """
        if map_grid:
            current_floor = map_grid.get_floor()
            if current_floor:
                return current_floor.get_tile(x, y)
        return None

    def toggle_auto_map():
        """Toggle auto-mapping on/off"""
        if map_grid:
            map_grid.auto_map_enabled = not map_grid.auto_map_enabled
            status = "enabled" if map_grid.auto_map_enabled else "disabled"
            renpy.notify("Auto-map {}".format(status))
            return map_grid.auto_map_enabled
        return False

    def get_floor_list():
        """
        Get list of all floors

        Returns:
            List of tuples: [(floor_id, floor_name), ...]
        """
        if map_grid:
            return [
                (floor_id, floor.floor_name)
                for floor_id, floor in map_grid.floors.items()
            ]
        return []

    def get_floor_stats(floor_id=None):
        """
        Get statistics for a floor

        Args:
            floor_id: Floor ID (uses current floor if None)

        Returns:
            Dictionary with stats or None
        """
        if map_grid:
            floor = map_grid.get_floor(floor_id)
            if floor:
                # Count non-empty tiles
                tile_count = 0
                for row in floor.tiles:
                    for tile in row:
                        if tile.tile_type != "empty":
                            tile_count += 1

                return {
                    "name": floor.floor_name,
                    "dimensions": floor.dimensions,
                    "tiles_placed": tile_count,
                    "icons": len(floor.icons),
                    "notes": len(floor.notes)
                }
        return None

    def export_current_floor(filename=None):
        """Export the current floor to JSON"""
        if map_grid:
            current_floor = map_grid.get_floor()
            if current_floor:
                filepath = MapIO.export_floor_to_json(current_floor, filename)
                if filepath:
                    renpy.notify("Floor exported!")
                    return filepath
        renpy.notify("Export failed!")
        return None

    def import_floor_and_add(filepath, new_floor_id=None):
        """
        Import a floor from JSON and add it to the current map

        Args:
            filepath: Path to JSON file
            new_floor_id: Optional new ID for the floor (uses original if None)

        Returns:
            True if successful, False otherwise
        """
        if map_grid:
            floor = MapIO.import_floor_from_json(filepath)
            if floor:
                # Use new ID if provided
                if new_floor_id:
                    floor.floor_id = new_floor_id

                # Add to map grid
                map_grid.floors[floor.floor_id] = floor
                renpy.notify("Floor imported: {}".format(floor.floor_name))
                return True
        renpy.notify("Import failed!")
        return False


# Test/Debug functions
init python:
    def create_test_floor():
        """Create a test floor with some sample data (for testing purposes)"""
        if map_grid:
            # Create test floor
            floor = map_grid.add_floor("test_floor", "Test Dungeon", (15, 15))

            # Place some test tiles
            floor.set_tile(5, 5, MapTile("hallway", 0))
            floor.set_tile(6, 5, MapTile("corner", 90))
            floor.set_tile(7, 5, MapTile("hallway", 0))
            floor.set_tile(5, 6, MapTile("wall", 0))
            floor.set_tile(7, 6, MapTile("t_intersection", 180))

            # Place some icons
            floor.place_icon(5, 5, MapIcon("stairs_down", (5, 5)))
            floor.place_icon(10, 10, MapIcon("enemy", (10, 10)))
            floor.place_icon(12, 8, MapIcon("door", (12, 8)))

            # Add some notes
            floor.add_note(10, 10, "Boss encounter here!")
            floor.add_note(12, 8, "Locked door - need key")

            print("MapSystem - Created test floor with sample data")
            return floor
        return None

    def print_map_info():
        """Print current map information (for debugging)"""
        if map_grid:
            print("=== Map Grid Info ===")
            print("Version: {}".format(map_grid.version))
            print("Grid Size: {}".format(map_grid.grid_size))
            print("Cell Size: {}px".format(map_grid.cell_size))
            print("Auto-map: {}".format("Enabled" if map_grid.auto_map_enabled else "Disabled"))
            print("Current Floor: {}".format(map_grid.current_floor))
            print("Total Floors: {}".format(len(map_grid.floors)))

            for floor_id, floor in map_grid.floors.items():
                stats = get_floor_stats(floor_id)
                print("\nFloor: {} ({})".format(floor.floor_name, floor_id))
                print("  Dimensions: {}".format(stats["dimensions"]))
                print("  Tiles placed: {}".format(stats["tiles_placed"]))
                print("  Icons: {}".format(stats["icons"]))
                print("  Notes: {}".format(stats["notes"]))
        else:
            print("No map grid initialized")


# Default persistent value
default persistent.map_data = None
