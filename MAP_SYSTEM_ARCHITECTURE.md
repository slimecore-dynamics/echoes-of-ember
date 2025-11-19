# Map System Architecture - Complete Walkthrough

This document explains the complete structure of the Etrian Odyssey-style mapping system with file I/O persistence.

---

## File Overview

```
Echoes of Ember/game/mapping/
├── mapping.rpy           - Core data classes (MapTile, MapIcon, FloorMap, MapGrid)
├── map_persistence.rpy   - File I/O save/load system (MAIN PERSISTENCE LOGIC)
├── map_data.rpy          - Initialization and utility functions
├── map_io.rpy           - Export/import for sharing maps (bonus features)
├── map_tools.rpy        - Editing interaction handlers
└── map_screen.rpy       - UI screens for viewing/editing

Echoes of Ember/game/
├── script.rpy           - Calls start_mapping_system on new game
└── screens.rpy          - Modified to use FileActionWithMapData
```

---

## Core Architecture

### The Big Picture

**Problem We're Solving:**
- Ren'Py's `persistent` storage shares data across ALL save files (bad for maps)
- Ren'Py's `default` variables get wiped when opening console or loading (also bad)
- **Solution**: External JSON files, one per save slot

**How It Works:**
1. Each save slot gets its own `<savedir>/map_data/<slot>.json` file
2. When saving: Game saves normally + map data writes to JSON
3. When loading: Game loads normally + `after_load` label reads JSON
4. Result: Each save file has independent map data

---

## File-by-File Breakdown

### 1. `mapping.rpy` - Core Data Classes

**Purpose**: Define the map data structures and serialization

**Key Classes:**

#### `MapTile`
```python
class MapTile:
    VALID_TYPES = ["empty", "wall", "hallway", "corner", "t_intersection", "cross"]

    def __init__(self, tile_type="empty", rotation=0)
    def to_dict()          # Serialize to dictionary
    @staticmethod from_dict(data)  # Deserialize from dictionary
    def rotate_clockwise()
```
- Represents a single tile on the map grid
- Has type (wall, hallway, etc.) and rotation (0°, 90°, 180°, 270°)
- Serializable to/from JSON

#### `MapIcon`
```python
class MapIcon:
    VALID_TYPES = ["door", "stairs_up", "stairs_down", "gathering",
                   "event", "enemy", "teleporter", "note"]

    def __init__(self, icon_type, position, metadata=None)
    def to_dict()
    @staticmethod from_dict(data)
```
- Represents icons placed on tiles (stairs, doors, etc.)
- Has position (x, y) and optional metadata (for notes, etc.)
- Serializable to/from JSON

#### `FloorMap`
```python
class FloorMap:
    def __init__(self, floor_id, floor_name, dimensions=(20, 20))

    # Data storage
    self.tiles = [[MapTile() for x in range(width)] for y in range(height)]
    self.icons = {}  # Dictionary: (x,y) -> MapIcon
    self.notes = {}  # Dictionary: (x,y) -> "note text"

    # Methods
    def get_tile(x, y)
    def set_tile(x, y, tile)
    def place_icon(x, y, icon)
    def remove_icon(x, y)
    def set_note(x, y, note_text)
    def to_dict()
    @staticmethod from_dict(data)
```
- Represents a single floor/level
- Contains 2D grid of tiles + dictionaries of icons and notes
- Serializable to/from JSON

#### `MapGrid`
```python
class MapGrid:
    def __init__(self, grid_size=(20, 20), cell_size=64)

    # Data storage
    self.floors = {}  # Dictionary: floor_id -> FloorMap
    self.current_floor_id = None

    # Editor state
    self.current_mode = "view"  # or "edit_tiles" or "edit_icons"
    self.selected_tile_type = "hallway"
    self.selected_tile_rotation = 0
    self.selected_icon_type = None
    self.auto_map_enabled = True

    # Methods
    def add_floor(floor_id, floor_name, dimensions)
    def get_floor(floor_id=None)
    def get_current_floor()
    def switch_floor(floor_id)
    def rotate_selected_tile()
    def to_dict()
    @staticmethod from_dict(data)
```
- Container for all map data (multiple floors, editor state, etc.)
- This is the main object that gets saved/loaded
- Serializable to/from JSON

**Global Variable:**
```python
default map_grid = None
```
- Starts as `None`, initialized by `start_mapping_system`
- NOT saved by Ren'Py's system (it's `None` in save files)
- Actual map data saved to external JSON files

---

### 2. `map_persistence.rpy` - File I/O System (MAIN LOGIC)

**Purpose**: Handle saving/loading map data to external JSON files

This file has THREE init blocks that run at different priorities:

#### **Block 1: `init -1 python:` (Lines 5-119)**
**Runs**: Very early in Ren'Py initialization (before most things)

**Functions Defined:**

##### `get_map_data_dir()`
```python
def get_map_data_dir():
    map_dir = os.path.join(config.savedir, "map_data")
    if not os.path.exists(map_dir):
        os.makedirs(map_dir)
    return map_dir
```
- Returns: `C:/Users/[user]/AppData/Roaming/RenPy/EchoesofEmber-[id]/map_data/`
- Creates directory if it doesn't exist
- Called every time we need to save/load

##### `get_map_data_path(slot_name)`
```python
def get_map_data_path(slot_name):
    map_dir = get_map_data_dir()
    safe_name = str(slot_name).replace("/", "_").replace("\\", "_").replace("-", "_")
    return os.path.join(map_dir, "{}.json".format(safe_name))
```
- Input: `"1"` → Output: `<savedir>/map_data/1.json`
- Input: `"auto-1"` → Output: `<savedir>/map_data/auto_1.json`
- Sanitizes slot name for filesystem

##### `save_map_data_to_file(slot_name)`
```python
def save_map_data_to_file(slot_name):
    global map_grid

    # Validation checks
    if not slot_name or not map_grid:
        return False

    # Get file path
    path = get_map_data_path(slot_name)

    # Serialize map_grid to dictionary
    data = map_grid.to_dict()

    # Write to JSON file
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True
```
- **Core save function**: Writes map data to external JSON file
- Called when saving a game (by `FileActionWithMapData`)
- Returns `True` on success, `False` on failure

##### `load_map_data_from_file(slot_name)`
```python
def load_map_data_from_file(slot_name):
    global map_grid

    path = get_map_data_path(slot_name)

    # If no file exists, create fresh map
    if not path or not os.path.exists(path):
        map_grid = MapGrid()
        map_grid.add_floor("floor_1", "Entrance Hall", (20, 20))
        return False

    # Load and parse JSON
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Deserialize into MapGrid object
    map_grid = MapGrid.from_dict(data)

    return True
```
- **Core load function**: Reads map data from external JSON file
- Called after loading a game (by `after_load` label)
- Creates fresh map if file doesn't exist
- Returns `True` on success, `False` if file not found

##### `delete_map_data_file(slot_name)`
```python
def delete_map_data_file(slot_name):
    path = get_map_data_path(slot_name)
    if path and os.path.exists(path):
        os.remove(path)
        return True
    return False
```
- Deletes map data file for a slot
- Not currently used, but available for cleanup

---

#### **Block 2: `init -10 python:` (Lines 128-169)**
**Runs**: Even earlier than block 1 (priority -10 < -1)

**Functions Defined:**

##### `save_game_with_map(name, extra_info='', screenshot=None, **kwargs)`
```python
def save_game_with_map(name, extra_info='', screenshot=None, **kwargs):
    slot_name = str(name)

    # First save the game normally
    renpy.save(slot_name, extra_info=extra_info, **kwargs)

    # Then save map data to external file
    save_map_data_to_file(slot_name)

    return True
```
- **DEPRECATED**: No longer called by `FileActionWithMapData`
- Kept for backwards compatibility and manual saves
- Calls Ren'Py's save, then saves map data

##### `load_game_with_map(name, **kwargs)`
```python
def load_game_with_map(name, **kwargs):
    slot_name = str(name)

    # Write slot name to temp file
    temp_file = os.path.join(config.savedir, "_loading_slot.tmp")
    with open(temp_file, 'w') as f:
        f.write(slot_name)

    # Load the game - after_load will read temp file
    renpy.load(slot_name, **kwargs)
```
- **DEPRECATED**: No longer called by `FileActionWithMapData`
- Kept for backwards compatibility and manual loads
- Writes slot to temp file, then calls Ren'Py's load

---

#### **Block 3: `init python:` (Lines 171-223)**
**Runs**: Normal initialization priority

**Class Defined:**

##### `FileActionWithMapData(Action)`
```python
class FileActionWithMapData(Action):
    """Wraps FileAction to add map data persistence to external files"""

    def __init__(self, name, page=None, **kwargs):
        self.name = name  # Slot number (1, 2, 3, etc.)
        self.page = page  # Page name (optional)
        self.kwargs = kwargs

        # Create instance of original FileAction
        self.original_action = OriginalFileAction(name, page, **kwargs)

    def __call__(self):
        current_screen_name = renpy.current_screen().screen_name[0]

        if current_screen_name == "save":
            # SAVE FLOW:
            # 1. Call original FileAction (saves game + screenshot)
            self.original_action()

            # 2. Save map data to external file
            slot_name = str(self.name)
            save_map_data_to_file(slot_name)

        else:
            # LOAD FLOW:
            # 1. Write slot name to temp file
            slot_name = str(self.name)
            temp_file = os.path.join(config.savedir, "_loading_slot.tmp")
            with open(temp_file, 'w') as f:
                f.write(slot_name)

            # 2. Call original FileAction (loads game)
            self.original_action()

            # 3. after_load label will read temp file and load map

    def get_sensitive(self):
        # Delegate to original FileAction
        return self.original_action.get_sensitive()

    def get_selected(self):
        # Delegate to original FileAction
        return self.original_action.get_selected()
```

**How It Works:**

1. **Wraps Original FileAction**: Stores reference to original, delegates most methods
2. **Adds Map Save**: After original FileAction saves, saves map to JSON
3. **Adds Map Load**: Writes slot to temp file, then loads game (after_load reads temp file)
4. **Preserves All Features**: Screenshots, thumbnails, metadata all still work

**Why Wrapper Pattern:**
- Original approach: Replaced FileAction completely → broke screenshots
- New approach: Wraps FileAction → preserves all features + adds map save

---

#### **Block 4: `label after_load:` (Lines 226-244)**
**Runs**: After a save file is loaded

```python
label after_load:
    python:
        import os

        # Read slot name from temporary file
        temp_file = os.path.join(config.savedir, "_loading_slot.tmp")
        slot = None

        if os.path.exists(temp_file):
            # Read slot name
            with open(temp_file, 'r') as f:
                slot = f.read().strip()

            # Delete temp file (cleanup)
            os.remove(temp_file)

        if slot:
            # Load map data from JSON file
            load_map_data_from_file(slot)
        else:
            # No temp file found (probably a new game)
            # Do nothing

    return
```

**How It Works:**

1. **Triggered**: Runs automatically after `renpy.load()` completes
2. **Reads Temp File**: Gets the slot name that was just loaded
3. **Loads Map Data**: Calls `load_map_data_from_file(slot)`
4. **Cleans Up**: Deletes temp file

**Why Temp File?**
- Problem: `renpy.load()` wipes ALL variables when it restores save state
- Solution: Write slot name to filesystem before load, read it after
- Files survive `renpy.load()`, variables don't

---

### 3. `map_data.rpy` - Initialization

**Purpose**: Initialize map system for new games

#### `label start_mapping_system:`
```python
label start_mapping_system:
    python:
        # Ensure map directories exist
        MapIO.ensure_directories()

        # Only initialize if map_grid is None
        global map_grid
        if map_grid is None:
            # Create fresh map for new game
            map_grid = MapGrid()
            floor = map_grid.add_floor("floor_1", "Entrance Hall", (20, 20))
        else:
            # Map already exists (loaded from save file)
            # Skip initialization

    return
```

**When Called:**
- From `script.rpy` on `label start:` (beginning of game)
- Runs both for NEW games and LOADED games

**Why Check `if map_grid is None:`**
- New game: `map_grid` is `None` → create fresh map
- Loaded game: `map_grid` was loaded by `after_load` → skip initialization
- Prevents overwriting loaded map data

---

### 4. `map_screen.rpy` - UI

**Purpose**: Display and edit the map

#### `screen map_view():`
- Main map viewing/editing screen
- Shows grid, tiles, icons
- Handles M key to toggle, R key to rotate

#### `screen map_grid_display(floor):`
- Renders the actual map grid
- 32×32 pixel cells
- Clickable for editing

#### `screen combined_selector_panel():`
- Palette with tile and icon buttons
- Yellow highlight for selected

#### `screen add_note_input(grid_x, grid_y):`
- Modal dialog for entering note text

---

### 5. `map_tools.rpy` - Editing

**Purpose**: Handle user interactions

```python
def handle_grid_click(x, y):
    # User clicked a grid cell
    if map_grid.current_mode == "edit_tiles":
        # Place selected tile
        tile = MapTile(map_grid.selected_tile_type, map_grid.selected_tile_rotation)
        floor.set_tile(x, y, tile)

    elif map_grid.current_mode == "edit_icons":
        # Place selected icon
        if map_grid.selected_icon_type == "note":
            # Show note input dialog
            renpy.show_screen("add_note_input", grid_x=x, grid_y=y)
        else:
            # Place icon
            icon = MapIcon(map_grid.selected_icon_type, (x, y))
            floor.place_icon(x, y, icon)

def select_tile_type(tile_type):
    map_grid.selected_tile_type = tile_type
    map_grid.current_mode = "edit_tiles"

def select_icon_for_placement(icon_type):
    map_grid.selected_icon_type = icon_type
    map_grid.current_mode = "edit_icons"

def rotate_selected_tile():
    map_grid.rotate_selected_tile()
```

---

### 6. `map_io.rpy` - Export/Import

**Purpose**: Share maps between players (bonus feature)

```python
class MapIO:
    @staticmethod
    def export_to_json(map_grid, filename=None):
        # Export entire map to game/maps/exports/

    @staticmethod
    def import_from_json(filepath):
        # Import map from game/maps/imports/

    @staticmethod
    def create_backup(map_grid):
        # Create backup in game/maps/backups/
```

**Not Used for Save/Load**: These are for sharing maps with other players or backing up

---

## Complete Save/Load Flow

### **SAVING A GAME**

```
User clicks "Save" button on slot 1
    ↓
screens.rpy: FileActionWithMapData(1) is called
    ↓
map_persistence.rpy: FileActionWithMapData.__call__()
    ↓
Detects we're on "save" screen
    ↓
Calls self.original_action()  [THIS IS THE ORIGINAL FileAction]
    ↓
    ├─→ Original FileAction saves game to slot "1"
    ├─→ Captures screenshot
    ├─→ Updates save slot thumbnail
    └─→ Writes save metadata
    ↓
After original save completes...
    ↓
Calls save_map_data_to_file("1")
    ↓
    ├─→ Gets path: <savedir>/map_data/1.json
    ├─→ Serializes map_grid to dictionary
    ├─→ Writes JSON to file
    └─→ Returns True
    ↓
Save complete! Game saved + map saved + thumbnail updated ✓
```

### **LOADING A GAME**

```
User clicks "Load" button on slot 1
    ↓
screens.rpy: FileActionWithMapData(1) is called
    ↓
map_persistence.rpy: FileActionWithMapData.__call__()
    ↓
Detects we're NOT on "save" screen (must be load)
    ↓
Writes "1" to temp file: <savedir>/_loading_slot.tmp
    ↓
Calls self.original_action()  [THIS IS THE ORIGINAL FileAction]
    ↓
    ├─→ Original FileAction loads save from slot "1"
    ├─→ Ren'Py loads save file
    ├─→ Restores all game variables
    ├─→ map_grid is restored to None (because that's what's in save)
    └─→ Triggers label after_load
    ↓
map_persistence.rpy: label after_load runs
    ↓
Checks if temp file exists
    ↓
Reads "1" from <savedir>/_loading_slot.tmp
    ↓
Deletes temp file (cleanup)
    ↓
Calls load_map_data_from_file("1")
    ↓
    ├─→ Gets path: <savedir>/map_data/1.json
    ├─→ Reads JSON from file
    ├─→ Deserializes to MapGrid object
    └─→ Sets global map_grid to loaded data
    ↓
script.rpy: Game continues with label start
    ↓
Calls start_mapping_system
    ↓
Checks if map_grid is None
    ↓
    ├─→ If None: Create fresh map (new game)
    └─→ If exists: Skip initialization (loaded game) ✓
    ↓
Game continues with loaded map! ✓
```

---

## Key Design Decisions

### Why External JSON Files?
- **Problem**: Ren'Py's `persistent` shares data across ALL saves
- **Problem**: Ren'Py's `default` variables get wiped on console open
- **Solution**: External files, one per save slot, independent of Ren'Py's save system

### Why Temp File for Loading?
- **Problem**: `renpy.load()` wipes ALL variables when restoring state
- **Problem**: Can't pass slot name to `after_load` via Python variables
- **Solution**: Write to filesystem before load, read after load

### Why Wrapper Pattern for FileAction?
- **Problem**: Original approach replaced FileAction → broke screenshots
- **Solution**: Wrap FileAction → call original + add map save/load

### Why Three Init Blocks?
- `init -10`: Runs earliest, defines wrapper functions
- `init -1`: Runs early, defines core save/load functions
- `init`: Normal priority, defines FileAction wrapper class

### Why Check `map_grid is None` in start_mapping_system?
- **Problem**: `label start` runs for both new games AND loaded games
- **Problem**: Would overwrite loaded map if we always created fresh map
- **Solution**: Only create fresh map if `map_grid` is still `None`

---

## Testing Checklist

✅ **New Game**: Fresh map created
✅ **Save Slot 1**: Map data saved to `1.json`, thumbnail updated
✅ **Save Slot 2**: Map data saved to `2.json`, thumbnail updated
✅ **Load Slot 1**: Correct map loaded from `1.json`
✅ **Load Slot 2**: Correct map loaded from `2.json`
✅ **Open Console**: Map data NOT wiped (external file survives)
✅ **Return to Main Menu**: Each new game starts fresh
✅ **Delete Save**: Can manually delete map JSON if needed

---

## File Locations

### Save Files
```
Windows: C:/Users/[user]/AppData/Roaming/RenPy/EchoesofEmber-[id]/
  ├── 1-1.save          # Ren'Py save file
  ├── 2-1.save          # Ren'Py save file
  └── map_data/         # Our external map data
      ├── 1.json        # Map for slot 1
      ├── 2.json        # Map for slot 2
      └── auto_1.json   # Map for autosave
```

### JSON Format
```json
{
  "version": "1.0",
  "grid_size": [20, 20],
  "cell_size": 64,
  "auto_map_enabled": true,
  "current_floor": "floor_1",
  "floors": {
    "floor_1": {
      "floor_id": "floor_1",
      "floor_name": "Entrance Hall",
      "dimensions": [20, 20],
      "tiles": [
        [{"type": "empty", "rotation": 0}, ...],
        ...
      ],
      "icons": {
        "5,5": {"type": "stairs_down", "position": [5, 5], "metadata": {}}
      },
      "notes": {
        "5,5": "Stairs to floor 2"
      }
    }
  }
}
```

---

## Summary

The mapping system uses **external JSON files** to store map data independently for each save slot. The `FileActionWithMapData` wrapper intercepts save/load operations and adds map data persistence on top of Ren'Py's normal save system. A temporary file passes the slot name through the `renpy.load()` operation to the `after_load` label, which then loads the correct map data from the external JSON file.

This approach ensures:
- Each save file has independent map data
- Map data survives console opening
- Screenshots and thumbnails still work
- Clean separation of concerns
