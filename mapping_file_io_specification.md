# Mapping System File I/O Specification

 

## Project: Echoes of Ember - Etrian Odyssey Mapping System

 

**Version:** 2.0 (Updated to reflect final implementation)

**Date:** 2025-11-19

**Related:** mapping_implementation_plan.md v3.0

 

---

 

## Overview

 

This document defines the file I/O approach for the Etrian Odyssey-style mapping system in Echoes of Ember. The implementation uses **external JSON files** (one per save slot) to ensure each save file has independent map data.

 

### Key Design Decisions

 

1. **External JSON Files** - Map data stored separately from Ren'Py save files

2. **Per-Save Independence** - Each save slot gets its own `<savedir>/map_data/<slot>.json` file

3. **Wrapper Pattern** - `FileActionWithMapData` wraps Ren'Py's FileAction to inject map save/load

4. **Temp File Approach** - Uses temporary file to pass slot name through `renpy.load()` state restoration

 

### Why Not Persistent Storage?

 

- **Problem:** Ren'Py's `persistent` storage is shared across ALL save files

- **Problem:** Ren'Py's `default` variables get wiped when opening console

- **Solution:** External JSON files provide true per-save-slot independence

 

---

 

## 1. Storage Architecture

 

### Storage Strategy

 

```

┌─────────────────────────────────────────────────┐

│          Application Layer (Ren'Py)             │

│     (mapping.rpy, map_screen.rpy, etc.)         │

└────────────────┬────────────────────────────────┘

                 │

┌────────────────▼────────────────────────────────┐

│      FileActionWithMapData (Wrapper)            │

│   - Intercepts save/load operations             │

│   - Calls original FileAction                   │

│   - Adds map data save/load on top              │

└────────────────┬────────────────────────────────┘

                 │

        ┌────────┴────────┐

        │                 │

┌───────▼──────┐  ┌──────▼──────────────────────┐

│  Ren'Py Save │  │  External JSON Files        │

│  Files       │  │  <savedir>/map_data/        │

│  (game data, │  │  - 1.json                   │

│  screenshot) │  │  - 2.json                   │

└──────────────┘  │  - auto_1.json              │

                  │  - _loading_slot.tmp (temp) │

                  └─────────────────────────────┘

```

 

### File Structure

 

```

<savedir>/                                  # Ren'Py save directory

  ├── 1-1.save                              # Ren'Py save file (slot 1)

  ├── 2-1.save                              # Ren'Py save file (slot 2)

  ├── auto-1.save                           # Autosave

  ├── map_data/                             # Map data directory

  │   ├── 1.json                            # Map for slot 1

  │   ├── 2.json                            # Map for slot 2

  │   ├── auto_1.json                       # Map for autosave

  │   └── _loading_slot.tmp                 # Temp file (transient)

  └── persistent                            # Ren'Py persistent (NOT used for maps)

 

/Echoes of Ember/game/

  ├── mapping/

  │   ├── mapping.rpy                       # Core data classes

  │   ├── map_persistence.rpy               # File I/O save/load (MAIN LOGIC)

  │   ├── map_data.rpy                      # Initialization

  │   ├── map_io.rpy                        # Export/import for sharing

  │   ├── map_tools.rpy                     # Editing handlers

  │   └── map_screen.rpy                    # UI screens

  ├── screens.rpy                           # Modified to use FileActionWithMapData

  └── script.rpy                            # Calls start_mapping_system

```

 

---

 

## 2. Data Structures

 

### Core Classes (with Serialization Methods)

 

```python

class MapTile:

    """Individual grid cell tile"""

    def __init__(self, tile_type="empty", rotation=0):

        self.tile_type = tile_type  # "empty", "wall", "hallway", "corner", "t_intersection", "cross"

        self.rotation = rotation     # 0, 90, 180, 270

 

    def to_dict(self):

        """Serialize to dictionary for JSON storage"""

        return {

            "type": self.tile_type,

            "rotation": self.rotation

        }

 

    @staticmethod

    def from_dict(data):

        """Deserialize from dictionary"""

        return MapTile(

            tile_type=data.get("type", "empty"),

            rotation=data.get("rotation", 0)

        )

 

class MapIcon:

    """Map marker/icon"""

    def __init__(self, icon_type, position, metadata=None):

        self.icon_type = icon_type  # "door", "stairs_up", "enemy", etc.

        self.position = position     # (x, y) tuple

        self.metadata = metadata or {}  # Additional data (optional)

 

    def to_dict(self):

        return {

            "type": self.icon_type,

            "position": list(self.position),  # Convert tuple to list for JSON

            "metadata": self.metadata

        }

 

    @staticmethod

    def from_dict(data):

        return MapIcon(

            icon_type=data["type"],

            position=tuple(data["position"]),

            metadata=data.get("metadata", {})

        )

 

class FloorMap:

    """Individual floor/level map data"""

    def __init__(self, floor_id, floor_name, dimensions=(20, 20)):

        self.floor_id = floor_id

        self.floor_name = floor_name

        self.dimensions = dimensions  # (width, height) in cells

        self.tiles = self._initialize_tiles()

        self.icons = {}  # {(x,y): MapIcon}

        self.notes = {}  # {(x,y): "note text"}

 

    def _initialize_tiles(self):

        """Create empty 2D tile array"""

        width, height = self.dimensions

        return [[MapTile() for _ in range(width)] for _ in range(height)]

 

    def to_dict(self):

        """Serialize floor to dictionary"""

        return {

            "floor_id": self.floor_id,

            "floor_name": self.floor_name,

            "dimensions": list(self.dimensions),

            "tiles": [

                [tile.to_dict() for tile in row]

                for row in self.tiles

            ],

            "icons": {

                f"{x},{y}": icon.to_dict()

                for (x, y), icon in self.icons.items()

            },

            "notes": {

                f"{x},{y}": note

                for (x, y), note in self.notes.items()

            }

        }

 

    @staticmethod

    def from_dict(data):

        """Deserialize floor from dictionary"""

        floor = FloorMap(

            floor_id=data["floor_id"],

            floor_name=data["floor_name"],

            dimensions=tuple(data["dimensions"])

        )

 

        # Restore tiles

        floor.tiles = [

            [MapTile.from_dict(tile_data) for tile_data in row]

            for row in data["tiles"]

        ]

 

        # Restore icons

        floor.icons = {

            tuple(map(int, pos.split(','))): MapIcon.from_dict(icon_data)

            for pos, icon_data in data.get("icons", {}).items()

        }

 

        # Restore notes

        floor.notes = {

            tuple(map(int, pos.split(','))): note

            for pos, note in data.get("notes", {}).items()

        }

 

        return floor

 

class MapGrid:

    """Container for all map data"""

    def __init__(self, grid_size=(20, 20), cell_size=64):

        self.grid_size = grid_size       # Default dimensions for new floors

        self.cell_size = cell_size       # Pixel size for rendering

        self.floors = {}                 # {floor_id: FloorMap}

        self.current_floor_id = None     # Active floor ID

        self.auto_map_enabled = True     # Auto-reveal toggle

        self.version = "1.0"             # Data format version

 

        # Editor state

        self.current_mode = "view"       # "view", "edit_tiles", "edit_icons"

        self.selected_tile_type = "hallway"

        self.selected_tile_rotation = 0

        self.selected_icon_type = None

 

    def to_dict(self):

        """Serialize entire map grid to dictionary"""

        return {

            "version": self.version,

            "grid_size": list(self.grid_size),

            "cell_size": self.cell_size,

            "auto_map_enabled": self.auto_map_enabled,

            "current_floor": self.current_floor_id,

            "floors": {

                floor_id: floor.to_dict()

                for floor_id, floor in self.floors.items()

            }

        }

 

    @staticmethod

    def from_dict(data):

        """Deserialize map grid from dictionary"""

        grid = MapGrid(

            grid_size=tuple(data.get("grid_size", (20, 20))),

            cell_size=data.get("cell_size", 64)

        )

 

        grid.version = data.get("version", "1.0")

        grid.auto_map_enabled = data.get("auto_map_enabled", True)

        grid.current_floor_id = data.get("current_floor")

 

        # Restore all floors

        grid.floors = {

            floor_id: FloorMap.from_dict(floor_data)

            for floor_id, floor_data in data.get("floors", {}).items()

        }

 

        return grid

```

 

**Global Variable:**

```python

default map_grid = None  # Initialized by start_mapping_system, NOT saved by Ren'Py

```

 

---

 

## 3. File I/O System (map_persistence.rpy)

 

### Core Functions

 

```python

def get_map_data_dir():

    """Get the directory for map data files"""

    # Returns: <savedir>/map_data/

    map_dir = os.path.join(config.savedir, "map_data")

    if not os.path.exists(map_dir):

        os.makedirs(map_dir)

    return map_dir

 

def get_map_data_path(slot_name):

    """Get file path for a specific save slot's map data"""

    # Input: "1" -> Output: <savedir>/map_data/1.json

    # Input: "auto-1" -> Output: <savedir>/map_data/auto_1.json

    map_dir = get_map_data_dir()

    # Sanitize slot name (replace /, \, - with _)

    safe_name = str(slot_name).replace("/", "_").replace("\\", "_").replace("-", "_")

    return os.path.join(map_dir, "{}.json".format(safe_name))

 

def save_map_data_to_file(slot_name):

    """Save current map_grid to external JSON file"""

    global map_grid

 

    if not slot_name or not map_grid:

        return False

 

    path = get_map_data_path(slot_name)

 

    # Serialize map_grid to dict

    data = map_grid.to_dict()

 

    # Write to JSON file

    with open(path, 'w', encoding='utf-8') as f:

        json.dump(data, f, indent=2, ensure_ascii=False)

 

    print("MapPersistence - Saved map data to: {}".format(path))

    return True

 

def load_map_data_from_file(slot_name):

    """Load map data from external JSON file into map_grid"""

    global map_grid

 

    path = get_map_data_path(slot_name)

 

    # If no file exists, create fresh map

    if not os.path.exists(path):

        map_grid = MapGrid()

        map_grid.add_floor("floor_1", "Entrance Hall", (20, 20))

        return False

 

    # Load and deserialize JSON

    with open(path, 'r', encoding='utf-8') as f:

        data = json.load(f)

 

    map_grid = MapGrid.from_dict(data)

    print("MapPersistence - Loaded map data from: {}".format(path))

    return True

 

def delete_map_data_file(slot_name):

    """Delete map data file for a specific save slot"""

    path = get_map_data_path(slot_name)

    if os.path.exists(path):

        os.remove(path)

        return True

    return False

```

 

### FileActionWithMapData Wrapper

 

```python

class FileActionWithMapData(Action):

    """Wraps FileAction to add map data persistence to external files"""

 

    def __init__(self, name, page=None, **kwargs):

        self.name = name  # Slot number (1, 2, 3, etc.)

        self.page = page

        self.kwargs = kwargs

        # Create instance of original FileAction

        self.original_action = OriginalFileAction(name, page, **kwargs)

 

    def __call__(self):

        # Check which screen is currently displayed (robust method)

        is_save_screen = renpy.get_screen("save") is not None

        is_load_screen = renpy.get_screen("load") is not None

 

        if is_save_screen:

            # SAVE FLOW:

            # 1. Call original FileAction (saves game + screenshot)

            self.original_action()

 

            # 2. Save map data to external file

            slot_name = str(self.name)

            save_map_data_to_file(slot_name)

 

        elif is_load_screen:

            # LOAD FLOW:

            # 1. Write slot name to temp file

            slot_name = str(self.name)

            temp_file = os.path.join(config.savedir, "_loading_slot.tmp")

            with open(temp_file, 'w') as f:

                f.write(slot_name)

 

            # 2. Call original FileAction (loads game)

            self.original_action()

 

            # 3. after_load label will read temp file and load map

 

        else:

            # Unknown screen - delegate to original

            print("MapPersistence - Warning: FileAction called from unknown screen")

            self.original_action()

 

    def get_sensitive(self):

        # Delegate to original FileAction

        return self.original_action.get_sensitive()

 

    def get_selected(self):

        # Delegate to original FileAction

        return self.original_action.get_selected()

```

 

### after_load Label

 

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

            # This happens AFTER renpy.load() restored variables

            load_map_data_from_file(slot)

 

    return

```

 

---

 

## 4. Save/Load Flow

 

### Save Operation Flow

 

```

User clicks "Save" button

    ↓

FileActionWithMapData.__call__()

    ↓

Detects: renpy.get_screen("save") is not None

    ↓

Calls: self.original_action()

    ├─→ Saves game to slot

    ├─→ Captures screenshot

    └─→ Updates save thumbnail

    ↓

Calls: save_map_data_to_file(slot)

    ├─→ Serializes map_grid to dict

    ├─→ Writes to <savedir>/map_data/<slot>.json

    └─→ Returns True

    ↓

Save complete! Game + map + thumbnail all saved ✓

```

 

### Load Operation Flow

 

```

User clicks "Load" button

    ↓

FileActionWithMapData.__call__()

    ↓

Detects: renpy.get_screen("load") is not None

    ↓

Writes slot name to temp file: _loading_slot.tmp

    ↓

Calls: self.original_action()

    ├─→ Calls renpy.load(slot)

    ├─→ Restores all game variables

    ├─→ map_grid is restored to None

    └─→ Triggers label after_load

    ↓

label after_load executes

    ├─→ Reads slot from temp file

    ├─→ Deletes temp file

    ├─→ Calls load_map_data_from_file(slot)

    └─→ Loads JSON and sets map_grid

    ↓

script.rpy continues

    ├─→ Calls start_mapping_system

    ├─→ Checks if map_grid is None

    └─→ If not None: skips initialization (loaded game)

    ↓

Game continues with loaded map! ✓

```

 

**Why Temp File?**

- `renpy.load()` wipes ALL Python variables when restoring state

- Can't pass slot name via variables (they get wiped)

- Filesystem survives state restoration

- Temp file passes slot name through the load operation

 

---

 

## 5. JSON File Format

 

### Complete Map Export Format

 

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

      "floor_name": "Forest Entrance",

      "dimensions": [20, 20],

      "tiles": [

        [

          {"type": "empty", "rotation": 0},

          {"type": "wall", "rotation": 0},

          {"type": "hallway", "rotation": 90}

        ]

      ],

      "icons": {

        "5,5": {

          "type": "enemy",

          "position": [5, 5],

          "metadata": {}

        },

        "10,10": {

          "type": "stairs_up",

          "position": [10, 10],

          "metadata": {"leads_to": "floor_2"}

        }

      },

      "notes": {

        "3,7": "Secret passage to the west",

        "12,15": "Boss room - bring healing items"

      }

    }

  }

}

```

 

---

 

## 6. Integration with Ren'Py Game Flow

 

### Initialization (map_data.rpy)

 

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

            print("MapSystem - Created new map with default floor")

        else:

            # Map already exists (loaded from save file)

            print("MapSystem - Map already exists (loaded from save), skipping initialization")

 

    return

```

 

**Why Check `if map_grid is None`?**

- `label start` runs for BOTH new games AND loaded games

- For loaded games, `after_load` already loaded map data

- This check prevents overwriting the loaded map

 

### Screen Integration (screens.rpy)

 

```python

screen file_slots(title):

    # ... existing code ...

 

    for i in range(gui.file_slot_cols * gui.file_slot_rows):

        $ slot = i + 1

 

        button:

            action FileActionWithMapData(slot)  # ← Changed from FileAction(slot)

 

            # ... rest of button code ...

```

 

---

 

## 7. MapIO Class (Bonus Export/Import)

 

The `MapIO` class provides export/import functionality for sharing maps with other players. This is separate from the main save/load system.

 

```python

class MapIO:

    """Handles export/import of maps for sharing between players"""

 

    EXPORT_DIR = "maps/exports"

    IMPORT_DIR = "maps/imports"

    BACKUP_DIR = "maps/backups"

 

    @staticmethod

    def export_to_json(map_grid, filename=None):

        """Export map to game/maps/exports/ for sharing"""

        # ... implementation ...

 

    @staticmethod

    def import_from_json(filepath):

        """Import map from game/maps/imports/"""

        # ... implementation ...

 

    @staticmethod

    def create_backup(map_grid):

        """Create timestamped backup in game/maps/backups/"""

        # ... implementation ...

```

 

**Note:** These methods are NOT used for save/load. They're for:

- Sharing maps with other players

- Creating manual backups

- Exporting maps for external editing

 

---

 

## 8. File Locations Reference

 

### Directory Structure

 

```

# Windows Example

C:/Users/[user]/AppData/Roaming/RenPy/EchoesofEmber-[id]/

  ├── 1-1.save                    # Ren'Py save file

  ├── 2-1.save

  ├── auto-1.save

  ├── map_data/                   # Map data directory (created automatically)

  │   ├── 1.json                  # Map for slot 1

  │   ├── 2.json                  # Map for slot 2

  │   ├── auto_1.json             # Map for autosave (dash → underscore)

  │   └── _loading_slot.tmp       # Temp file (transient, deleted after load)

  └── persistent                  # Ren'Py persistent (NOT used for maps)

 

# Game Directory

/Echoes of Ember/game/

  ├── mapping/

  │   ├── mapping.rpy

  │   ├── map_persistence.rpy     # ← Main save/load logic

  │   ├── map_data.rpy

  │   ├── map_io.rpy              # ← Export/import for sharing

  │   ├── map_tools.rpy

  │   └── map_screen.rpy

  └── maps/                        # ← Export/import directory (manual sharing)

      ├── exports/

      ├── imports/

      └── backups/

```

 

### Platform-Specific Save Locations

 

- **Windows:** `%APPDATA%/RenPy/EchoesofEmber-{id}/map_data/`

- **macOS:** `~/Library/RenPy/EchoesofEmber-{id}/map_data/`

- **Linux:** `~/.renpy/EchoesofEmber-{id}/map_data/`

 

---

 

## 9. Error Handling

 

### Validation and Recovery

 

```python

def load_map_data_from_file(slot_name):

    """Load with error handling"""

    global map_grid

 

    path = get_map_data_path(slot_name)

 

    if not os.path.exists(path):

        # No map data for this slot - initialize fresh

        map_grid = MapGrid()

        map_grid.add_floor("floor_1", "Entrance Hall", (20, 20))

        return False

 

    try:

        with open(path, 'r', encoding='utf-8') as f:

            data = json.load(f)

 

        # Deserialize into MapGrid object

        map_grid = MapGrid.from_dict(data)

        return True

 

    except Exception as e:

        print("MapPersistence Error - Load failed: {}".format(e))

        # Initialize fresh on error

        map_grid = MapGrid()

        map_grid.add_floor("floor_1", "Entrance Hall", (20, 20))

        return False

```

 

### Common Error Scenarios

 

1. **Missing JSON file** → Creates fresh map automatically

2. **Corrupted JSON** → Logs error, creates fresh map

3. **Temp file missing** → Gracefully skips map load

4. **Unknown screen context** → Delegates to original FileAction

 

---

 

## 10. Testing Strategy

 

### Manual Test Cases

 

1. **New Game → Save → Load**

   - Start new game

   - Edit map (place tiles)

   - Save to slot 1

   - Load slot 1 → Map should persist

 

2. **Multiple Independent Saves**

   - New game, edit map, save slot 1

   - New game, edit differently, save slot 2

   - Load slot 1 → Shows slot 1's map

   - Load slot 2 → Shows slot 2's map

 

3. **Console Open/Close**

   - Edit map, open console (Shift+O), close console

   - Map should NOT be wiped (external file survives)

 

4. **Autosave/Load**

   - Edit map, trigger autosave

   - Load autosave → Map should persist

 

### Verification Checklist

 

- ✅ Each save has independent map data

- ✅ Screenshots/thumbnails update correctly

- ✅ Console opening doesn't wipe map

- ✅ JSON files created in `<savedir>/map_data/`

- ✅ Temp file cleaned up after load

- ✅ Fresh map created for new games

- ✅ Corrupted JSON handled gracefully

 

---

 

## 11. Design Rationale

 

### Why FileActionWithMapData Wrapper?

 

**Alternatives Considered:**

1. ❌ Custom save/load functions → Breaks screenshots/thumbnails

2. ❌ Override renpy.save()/load() → Too invasive, risky

3. ✅ **Wrapper pattern** → Preserves all FileAction features, adds map I/O on top

 

**Benefits:**

- All FileAction features preserved (screenshots, metadata, sensitivity checks)

- Clean separation of concerns

- Easy to debug (clear interception point)

- Future-proof (delegates to original for unknown behavior)

 

### Why Temp File for Loading?

 

**Alternatives Considered:**

1. ❌ Module-level variable → Gets reset when `renpy.load()` re-runs init blocks

2. ❌ Store variable → Gets wiped when `renpy.load()` restores state

3. ❌ Built-in `_file_name` → Not reliably set in all contexts

4. ✅ **Temp file** → Survives state restoration, reliable

 

**Benefits:**

- Guaranteed to survive `renpy.load()` state restoration

- Self-cleaning (deleted after read)

- Simple and predictable

 

### Why External JSON Not Persistent?

 

**Ren'Py Persistent Issues:**

- Shared across ALL save files (not per-save)

- Survives game uninstall (confusing for users)

- No clear way to export/share

 

**Default Variable Issues:**

- Gets wiped on console open

- Wiped during `renpy.load()` before `after_load` runs

 

**External JSON Benefits:**

- True per-save independence

- Survives console operations

- Easy to backup/share/edit

- Human-readable format

 

---

 

## Document Metadata

 

- **Version:** 2.0 (Final Implementation)

- **Date:** 2025-11-19

- **Author:** Claude (AI Assistant)

- **Related Documents:**

  - MAP_SYSTEM_API_REFERENCE.md

- **Status:** Implemented and Verified