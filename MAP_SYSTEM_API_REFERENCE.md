# Map System API Reference

Doxygen-style documentation for the Etrian Odyssey-style mapping system.

---

## File: `mapping.rpy` - Core Data Structures

### Class: `MapTile`

Represents a single tile on the map grid.

**Constants:**
- `VALID_TYPES`: List of valid tile types (empty, wall, hallway, corner, t_intersection, cross)

**Methods:**
- `__init__(tile_type="empty", rotation=0)` - Create a new map tile
  - Parameters: tile_type (str), rotation (int 0-270)
- `to_dict()` - Serialize tile to dictionary for JSON storage
  - Returns: dict
- `from_dict(data)` - [Static] Deserialize tile from dictionary
  - Parameters: data (dict)
  - Returns: MapTile instance
- `rotate_clockwise()` - Rotate tile 90 degrees clockwise
  - Modifies self.rotation

---

### Class: `MapIcon`

Represents an icon placed on a tile (stairs, doors, events, etc.).

**Constants:**
- `VALID_TYPES`: List of valid icon types (door, stairs_up, stairs_down, gathering, event, enemy, teleporter, note)

**Methods:**
- `__init__(icon_type, position, metadata=None)` - Create a new map icon
  - Parameters: icon_type (str), position (tuple x,y), metadata (dict, optional)
- `to_dict()` - Serialize icon to dictionary
  - Returns: dict
- `from_dict(data)` - [Static] Deserialize icon from dictionary
  - Parameters: data (dict)
  - Returns: MapIcon instance

---

### Class: `FloorMap`

Represents a single floor/level with tiles, icons, and notes.

**Attributes:**
- `floor_id` (str) - Unique identifier for the floor
- `floor_name` (str) - Display name
- `dimensions` (tuple) - Grid dimensions (width, height)
- `tiles` (2D list) - Grid of MapTile objects
- `icons` (dict) - Dictionary mapping (x,y) -> MapIcon
- `notes` (dict) - Dictionary mapping (x,y) -> note text (str)

**Methods:**
- `__init__(floor_id, floor_name, dimensions=(20, 20))` - Create a new floor
- `get_tile(x, y)` - Get tile at coordinates
  - Returns: MapTile or None if out of bounds
- `set_tile(x, y, tile)` - Set tile at coordinates
  - Parameters: x (int), y (int), tile (MapTile)
- `place_icon(x, y, icon)` - Place icon at coordinates
  - Parameters: x (int), y (int), icon (MapIcon)
- `remove_icon(x, y)` - Remove icon at coordinates
- `set_note(x, y, note_text)` - Set note text at coordinates
  - Parameters: note_text (str)
- `remove_note(x, y)` - Remove note at coordinates
- `to_dict()` - Serialize floor to dictionary
  - Returns: dict
- `from_dict(data)` - [Static] Deserialize floor from dictionary
  - Parameters: data (dict)
  - Returns: FloorMap instance

---

### Class: `MapGrid`

Container for all map data including multiple floors and editor state.

**Attributes:**
- `floors` (dict) - Dictionary mapping floor_id -> FloorMap
- `current_floor_id` (str) - ID of currently displayed floor
- `grid_size` (tuple) - Grid dimensions (width, height)
- `cell_size` (int) - Pixel size of each grid cell for rendering
- `current_mode` (str) - Editor mode: "view", "edit_tiles", or "edit_icons"
- `selected_tile_type` (str) - Currently selected tile type for placement
- `selected_tile_rotation` (int) - Rotation for selected tile (0, 90, 180, 270)
- `selected_icon_type` (str) - Currently selected icon type for placement
- `auto_map_enabled` (bool) - Whether auto-mapping is enabled

**Methods:**
- `__init__(grid_size=(20, 20), cell_size=64)` - Create new map grid
- `add_floor(floor_id, floor_name, dimensions=None)` - Add a new floor
  - Parameters: floor_id (str), floor_name (str), dimensions (tuple, optional)
  - Returns: FloorMap instance
- `get_floor(floor_id=None)` - Get floor by ID, or current floor if None
  - Returns: FloorMap or None
- `get_current_floor()` - Get the currently displayed floor
  - Returns: FloorMap or None
- `switch_floor(floor_id)` - Switch to different floor
  - Parameters: floor_id (str)
  - Returns: bool (success)
- `rotate_selected_tile()` - Rotate the currently selected tile 90 degrees
- `to_dict()` - Serialize entire map to dictionary
  - Returns: dict
- `from_dict(data)` - [Static] Deserialize map from dictionary
  - Parameters: data (dict)
  - Returns: MapGrid instance

**Global Variable:**
- `map_grid` (MapGrid) - The main map data object, initialized to None

---

## File: `map_persistence.rpy` - File I/O System

### Configuration

- `MAP_PERSISTENCE_DEBUG` (bool) - Set to False to reduce console output

### Function: `get_map_data_dir()`

Get the directory where map data JSON files are stored.

- **Returns:** str - Path to `<savedir>/map_data/`
- **Side Effects:** Creates directory if it doesn't exist

### Function: `get_map_data_path(slot_name)`

Get the full file path for a specific save slot's map data.

- **Parameters:** slot_name (str) - Save slot identifier
- **Returns:** str - Path to `<savedir>/map_data/<slot>.json`
- **Note:** Sanitizes slot name (replaces /, \, - with _)

### Function: `save_map_data_to_file(slot_name)`

Save current map_grid to external JSON file.

- **Parameters:** slot_name (str) - Save slot identifier
- **Returns:** bool - True on success, False on failure
- **Side Effects:** Writes JSON file, modifies global map_grid
- **Called By:** FileActionWithMapData when saving

### Function: `load_map_data_from_file(slot_name)`

Load map data from external JSON file into map_grid.

- **Parameters:** slot_name (str) - Save slot identifier
- **Returns:** bool - True on success, False if file not found
- **Side Effects:** Sets global map_grid, creates fresh map if file missing
- **Called By:** `after_load` label after game loads

### Function: `delete_map_data_file(slot_name)`

Delete map data file for a specific save slot.

- **Parameters:** slot_name (str) - Save slot identifier
- **Returns:** bool - True on success, False on failure
- **Use Case:** Cleanup when deleting save files

### Function: `save_game_with_map(name, extra_info='', screenshot=None, **kwargs)`

**DEPRECATED** - No longer used by FileActionWithMapData.

Save both game and map data. Kept for backwards compatibility.

- **Parameters:** name (str/int), extra_info (str), screenshot, kwargs
- **Returns:** bool - True on success

### Function: `load_game_with_map(name, **kwargs)`

**DEPRECATED** - No longer used by FileActionWithMapData.

Load both game and map data. Kept for backwards compatibility.

- **Parameters:** name (str/int), kwargs
- **Side Effects:** Writes temp file, calls renpy.load()

---

### Class: `FileActionWithMapData(Action)`

Wraps Ren'Py's FileAction to add map data persistence.

**Purpose:** Intercepts save/load operations to add external JSON file I/O

**Methods:**

- `__init__(name, page=None, **kwargs)` - Create action
  - Parameters: name (int) - slot number, page (str, optional), kwargs
  - Creates instance of original FileAction

- `__call__()` - Execute the action (save or load)
  - **Save Flow:**
    1. Calls original FileAction (saves game + screenshot)
    2. Calls `save_map_data_to_file()` to save map to JSON
  - **Load Flow:**
    1. Writes slot name to temp file
    2. Calls original FileAction (loads game)
    3. `after_load` label reads temp file and loads map

- `get_sensitive()` - Check if action is clickable
  - Returns: bool - Delegates to original FileAction

- `get_selected()` - Check if action represents selected slot
  - Returns: bool - Delegates to original FileAction

---

### Label: `after_load`

Ren'Py label that runs automatically after loading a save file.

**Execution Flow:**
1. Checks for temporary file at `<savedir>/_loading_slot.tmp`
2. If found, reads slot name from file
3. Deletes temp file
4. Calls `load_map_data_from_file(slot)` to restore map data
5. If no temp file, skips map loading (new game scenario)

**Why Temp File:** `renpy.load()` wipes all variables, so temp file survives the state restoration

---

## File: `map_data.rpy` - Initialization

### Label: `start_mapping_system`

Initialize the mapping system for new games.

**Called By:** `script.rpy` at game start

**Logic:**
1. Ensures map directories exist via `MapIO.ensure_directories()`
2. Checks if `map_grid` is None
3. If None: Creates fresh MapGrid with default floor (new game)
4. If exists: Skips initialization (loaded game - map already loaded by `after_load`)

**Why Check None:** Prevents overwriting map data that was just loaded from a save file

---

### Utility Functions

- `place_map_icon(x, y, icon_type, metadata=None)` - Place icon on current floor
- `add_map_note(x, y, note_text)` - Add note to current floor
- `set_map_tile(x, y, tile_type, rotation=0)` - Set tile on current floor
- `toggle_auto_map()` - Toggle auto-mapping feature
- `create_test_floor()` - Create a test floor with sample data

---

## File: `map_screen.rpy` - User Interface

### Screen: `map_view()`

Main map viewing and editing interface.

**Features:**
- M key to toggle map on/off
- R key to rotate selected tile
- Displays current floor grid
- Shows tile and icon selection palette

### Screen: `map_grid_display(floor)`

Renders the map grid with tiles and icons.

**Parameters:** floor (FloorMap) - Floor to display

**Rendering:**
- 32×32 pixel cells
- Tile layer with rotation support
- Icon layer on top of tiles
- Click handlers for editing

### Screen: `combined_selector_panel()`

Palette showing tile and icon options for editing.

**Features:**
- Horizontal layout with 6 tile types + 8 icon types
- Yellow highlight for selected option
- Click to select tile/icon for placement

### Screen: `add_note_input(grid_x, grid_y)`

Modal dialog for entering note text.

**Parameters:** grid_x (int), grid_y (int) - Coordinates for note

---

## File: `map_tools.rpy` - Editing Handlers

### Constants

- `TILE_TYPES` - List of available tile types
- `ICON_TYPES` - List of available icon types

### Functions

- `select_tile_type(tile_type)` - Select tile for placement, enter edit mode
  - Sets map_grid.current_mode = "edit_tiles"

- `select_icon_for_placement(icon_type)` - Select icon for placement, enter edit mode
  - Sets map_grid.current_mode = "edit_icons"

- `handle_grid_click(x, y)` - Handle click on grid cell
  - If edit_tiles mode: Places selected tile
  - If edit_icons mode: Places selected icon (or shows note dialog)
  - If view mode: Does nothing

- `confirm_note_input(x, y, note_text)` - Save note text to map
  - Creates note icon and stores text

- `rotate_selected_tile()` - Rotate the selected tile 90 degrees clockwise

---

## File: `map_io.rpy` - Export/Import (Bonus)

### Class: `MapIO`

Handles export/import of maps for sharing between players.

**Note:** Not used for save/load - only for manual export/import

**Static Methods:**

- `export_to_json(map_grid, filename=None)` - Export map to file
  - Exports to: `game/maps/exports/<filename>.json`
  - Returns: filepath or None

- `import_from_json(filepath)` - Import map from file
  - Imports from: `game/maps/imports/<filename>.json`
  - Returns: MapGrid instance or None

- `export_floor_to_json(floor_map, filename=None)` - Export single floor
  - Returns: filepath or None

- `import_floor_from_json(filepath)` - Import single floor
  - Returns: FloorMap instance or None

- `create_backup(map_grid)` - Create timestamped backup
  - Saves to: `game/maps/backups/map_backup_<timestamp>.json`
  - Returns: filepath or None

- `list_exported_maps()` - Get list of exported map files
  - Returns: List of filenames

- `list_importable_maps()` - Get list of importable map files
  - Returns: List of filenames

- `list_backups()` - Get list of backup files
  - Returns: List of filenames

- `validate_map_data(data)` - Validate map data structure
  - Parameters: data (dict)
  - Returns: (bool, str) - (is_valid, error_message)

- `ensure_directories()` - Create required directories if missing

---

## Data Flow Summary

### Saving a Game

1. User clicks save button
2. `FileActionWithMapData.__call__()` executes
3. Calls `original_action()` → game saves, screenshot captured
4. Calls `save_map_data_to_file(slot)` → map saved to JSON

**Result:** Both game data and map data saved, thumbnail updated

---

### Loading a Game

1. User clicks load button
2. `FileActionWithMapData.__call__()` executes
3. Writes slot name to temp file: `<savedir>/_loading_slot.tmp`
4. Calls `original_action()` → `renpy.load()` restores game state
5. `label after_load` runs automatically
6. Reads slot from temp file, deletes temp file
7. Calls `load_map_data_from_file(slot)` → map loaded from JSON
8. `label start_mapping_system` checks if map exists, skips initialization

**Result:** Both game data and map data restored correctly

---

## File Locations

**Map Data:**
- Windows: `C:/Users/<user>/AppData/Roaming/RenPy/EchoesofEmber-<id>/map_data/`
- macOS: `~/Library/RenPy/EchoesofEmber-<id>/map_data/`
- Linux: `~/.renpy/EchoesofEmber-<id>/map_data/`

**File Format:** `<slot>.json` where slot characters `/`, `\`, `-` are replaced with `_`

**JSON Structure:**
```
{
  "version": "1.0",
  "grid_size": [width, height],
  "cell_size": 64,
  "auto_map_enabled": true,
  "current_floor": "floor_id",
  "floors": {
    "floor_id": {
      "floor_id": "...",
      "floor_name": "...",
      "dimensions": [width, height],
      "tiles": [[{tile}, ...], ...],
      "icons": {"x,y": {icon}, ...},
      "notes": {"x,y": "text", ...}
    }
  }
}
```

---

## Design Decisions

**Why External JSON Files?**
- Ren'Py's `persistent` shares data across ALL save files
- Ren'Py's `default` variables get wiped on console open
- External files provide true per-save-slot independence

**Why Temp File for Loading?**
- `renpy.load()` wipes ALL Python variables when restoring state
- Filesystem survives state restoration
- Temp file passes slot name through the load operation

**Why Wrapper Pattern for FileAction?**
- Preserves all FileAction features (screenshots, thumbnails, metadata)
- Adds map persistence on top without breaking existing functionality
- Delegates to original for sensitivity and selection checks

**Why Check `map_grid is None`?**
- `label start` runs for both new games and loaded games
- Prevents overwriting map data that was just loaded by `after_load`
- Only creates fresh map when truly starting a new game
