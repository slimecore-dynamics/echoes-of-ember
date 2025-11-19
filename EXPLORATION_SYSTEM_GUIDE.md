# Dungeon Exploration System Guide

## Overview

This system adds first-person dungeon exploration to the Etrian Odyssey-style mapping system. Players navigate through dungeons tile-by-tile, with movement constraints based on tile types and rotations.

---

## Quick Start

### 1. Initialize the System

In your `script.rpy`:

```renpy
label start:
    # Initialize mapping system (already exists)
    call start_mapping_system

    # Initialize exploration system (new)
    call start_exploration_system

    # Option A: Load a dungeon from Tiled JSON
    call load_dungeon_floor("maps/dungeon_floor1.json", "floor_1")

    # Option B: Create a test dungeon programmatically
    $ create_test_dungeon()

    # Show exploration view
    call screen exploration_view

    return
```

### 2. Create a Dungeon in Tiled

1. Open Tiled Map Editor
2. Create a new map (20×20 tiles recommended)
3. Create a tileset with tiles numbered:
   - Tile 0: Empty (void)
   - Tile 1: Wall
   - Tile 2: Hallway
   - Tile 3: Corner
   - Tile 4: T-Intersection
   - Tile 5: Cross Intersection

4. Add custom properties to the map:
   - `starting_x` (int): Player starting X coordinate
   - `starting_y` (int): Player starting Y coordinate
   - `starting_rotation` (int): 0, 90, 180, or 270
   - `view_distance` (int): How many tiles ahead the player can see (default: 3)

5. Create an Object Layer for icons:
   - Add objects with types: `stairs_up`, `stairs_down`, `door`, `gathering`, `enemy`, `event`, `teleporter`, `note`
   - For gathering objects, add custom properties:
     - `item` (string): "metal scrap", "electronics", "psionic capsule", or "data"
     - `amount` (int): How many to gather
   - For enemy objects, add:
     - `damage` (int): Damage dealt to player

6. Export as JSON (File → Export As → JSON)

7. Place in `game/maps/` directory

---

## Tile Types & Movement

### Hallway
- **Rotation 0/180** (horizontal): Can only move East/West
- **Rotation 90/270** (vertical): Can only move North/South

### Corner
- **Rotation 0**: Can move East and South
- **Rotation 90**: Can move South and West
- **Rotation 180**: Can move West and North
- **Rotation 270**: Can move North and East

### T-Intersection
- **Rotation 0** (wall at North): Can move South/East/West
- **Rotation 90** (wall at East): Can move North/South/West
- **Rotation 180** (wall at South): Can move North/East/West
- **Rotation 270** (wall at West): Can move North/South/East

### Cross Intersection
- Can move in all 4 directions

### Wall
- **Rotation 0** (solid face North): Can move South/East/West
- **Rotation 90** (solid face East): Can move North/South/West
- **Rotation 180** (solid face South): Can move North/East/West
- **Rotation 270** (solid face West): Can move North/South/East

### Empty
- Unreachable void (no movement)

---

## Icon Interactions

### Passable Icons (can walk on)
- **gathering**: Step on → prompt → collect item
- **event**: Step on → prompt → trigger event
- **teleporter**: Step on → prompt → teleport
- **enemy**: Step on → automatic damage (no blocking)
- **note**: Step on → nothing (visual marker for player)
- **door_open**: Can walk through

### Blocking Icons (must be adjacent + facing)
- **stairs_up**: Face and interact → go to previous floor
- **stairs_down**: Face and interact → go to next floor
- **door_closed**: Face and interact → open door (changes to door_open)

---

## Navigation Controls

### Buttons
- **Forward**: Move one tile in facing direction (if valid)
- **Backward**: Move one tile behind (if valid)
- **Turn Left**: Rotate 90° counter-clockwise
- **Turn Right**: Rotate 90° clockwise

### Keyboard
- **M**: Toggle map view
- Map view shows player position as a red triangle pointing in facing direction

---

## File Structure

```
Echoes of Ember/game/
├── exploration/
│   ├── exploration_state.rpy        # PlayerState class
│   ├── movement.rpy                 # Movement validation & collision
│   ├── first_person_view.rpy        # View calculation with occlusion
│   ├── interactions.rpy             # Icon interaction handling
│   ├── exploration_screen.rpy       # UI & navigation
│   ├── tiled_importer.rpy           # Tiled JSON importer
│   ├── exploration_persistence.rpy  # Save/load player state
│   ├── exploration_init.rpy         # Initialization & test dungeon
│   └── player_marker.rpy            # Map marker overlay
│
├── maps/                            # Place Tiled JSON files here
│   └── dungeon_floor1.json
│
└── images/exploration/
    └── first_person/                # First-person view images
        ├── wall.png
        ├── floor.png
        ├── ceiling.png
        ├── door_closed.png
        ├── door_open.png
        └── interact_highlight.png
```

---

## Save/Load System

Player state is automatically saved/loaded with map data:

- **Save file**: `<savedir>/map_data/<slot>_player.json`
- **Data saved**:
  - Position (x, y)
  - Rotation (0, 90, 180, 270)
  - Current floor ID
  - Health / Max Health

When loading a save, player state is restored to the exact position and rotation.

---

## Programmatic Dungeon Creation

Instead of using Tiled, you can create dungeons in code:

```python
def create_my_dungeon():
    global map_grid, player_state

    # Create floor
    floor = FloorMap("my_floor", "My Dungeon", dimensions=(20, 20))

    # Set metadata
    floor.starting_x = 10
    floor.starting_y = 10
    floor.starting_rotation = 0
    floor.view_distance = 3

    # Place tiles
    floor.set_tile(10, 10, MapTile("hallway", rotation=0))
    floor.set_tile(11, 10, MapTile("hallway", rotation=0))

    # Place icons
    floor.place_icon(11, 10, MapIcon("door_closed", (11, 10)))
    floor.place_icon(12, 10, MapIcon("gathering", (12, 10),
        metadata={"item": "data", "amount": 1}))

    # Add to map grid
    map_grid.floors["my_floor"] = floor
    map_grid.current_floor_id = "my_floor"

    # Initialize player
    player_state = PlayerState(x=10, y=10, rotation=0, floor_id="my_floor")
```

---

## Extending the System

### Custom Tile Types

1. Add to `MapTile.VALID_TYPES` in mapping.rpy
2. Add movement rules in `MovementValidator._get_allowed_directions()`
3. Create tile image in `game/images/maps/tiles/`

### Custom Icon Types

1. Add to `MapIcon.VALID_TYPES` in mapping.rpy
2. Add to `InteractionHandler.STEP_ON_ICONS` or `ADJACENT_ICONS`
3. Add handler in `InteractionHandler.handle_interaction()`
4. Create icon image in `game/images/maps/icons/`

### Custom First-Person View

Replace placeholder graphics in `exploration_screen.rpy`:
- Update `screen render_first_person_view()` to use actual images
- Add depth-based scaling for perspective effect
- Add animated elements (torches, water, etc.)

---

## Testing

### Test Dungeon

Run the built-in test dungeon:

```renpy
label start:
    call start_mapping_system
    call start_exploration_system
    $ create_test_dungeon()
    call screen exploration_view
    return
```

The test dungeon includes:
- 4 horizontal hallways
- T-intersection
- Vertical corridor
- Closed door
- Gathering point (data)
- Enemy (5 damage)
- Stairs down

### Debugging

Enable debug output by checking console for:
- `ExplorationInit - ...` (initialization messages)
- `ExplorationPersistence - ...` (save/load messages)
- `TiledImporter - ...` (map loading messages)
- `MapPersistence - ...` (map save/load messages)

---

## Common Issues

### "Cannot move" notification
- Check tile type and rotation allow movement in that direction
- Check for blocking icons (door_closed, stairs, etc.)
- Check map bounds

### Player not visible on map
- Ensure `player_state.current_floor_id` matches `map_grid.current_floor_id`
- Check player coordinates are within floor dimensions

### Door won't open
- Ensure you're facing the door (adjacent + correct rotation)
- Interaction prompt should appear automatically

### Gathering not working
- Ensure metadata includes `"item"` and `"amount"` properties
- Check that icon type is exactly `"gathering"`

---

## Next Steps

1. **Create your dungeon in Tiled**
   - Design layout with tile types and rotations
   - Place icons for interactions
   - Set custom properties (starting position, view distance)
   - Export as JSON

2. **Add first-person graphics**
   - Create wall/floor/ceiling textures
   - Create door sprites
   - Add interaction highlights

3. **Extend interactions**
   - Add custom event handlers
   - Implement teleporter logic
   - Add gathering inventory system

4. **Add gameplay features**
   - Random encounters
   - Puzzles
   - Story events
   - Fast travel system

---

## API Reference

See `MAP_SYSTEM_API_REFERENCE.md` for detailed class/function documentation.

### Key Classes

- `PlayerState` - Player position, rotation, health
- `MovementValidator` - Validates tile-based movement
- `FirstPersonView` - Calculates visible tiles with occlusion
- `InteractionHandler` - Handles icon interactions
- `TiledImporter` - Loads Tiled JSON maps

### Key Functions

- `create_test_dungeon()` - Create programmatic test dungeon
- `handle_move_forward()` - Move player forward
- `handle_turn_left()` / `handle_turn_right()` - Rotate player
- `handle_stairs_interaction()` - Change floors
- `handle_door_interaction()` - Open doors

---

## Version

- **System Version**: 1.0
- **Last Updated**: 2025-11-19
- **Compatible with**: Ren'Py 7.0+, Tiled 1.0+
