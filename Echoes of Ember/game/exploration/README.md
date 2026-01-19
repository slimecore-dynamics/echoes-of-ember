# Dungeon Exploration System

Etrian Odyssey-style first-person dungeon exploration for Ren'Py.

## Features

✅ **First-Person Navigation**
- Step-by-step tile movement (Forward/Backward)
- 90° rotation (Turn Left/Right)
- View distance with occlusion (walls block sight)

✅ **Tile-Based Movement Constraints**
- Hallways restrict movement to 2 directions based on rotation
- Corners allow 2 perpendicular directions
- T-intersections allow 3 directions
- Cross intersections allow all 4 directions
- Walls block one direction based on rotation

✅ **Icon Interactions**
- **Passable**: gathering, event, teleporter, enemy, note, door_open
- **Blocking**: stairs_up, stairs_down, door_closed
- Step-on triggers vs adjacent-facing triggers

✅ **Tiled Map Editor Support**
- Load dungeon layouts from Tiled JSON files
- Custom properties for starting position, rotation, view distance
- Object layers for icons with metadata

✅ **Save/Load Integration**
- Player state (position, rotation, health) saved with map data
- External JSON files (per save slot)
- Compatible with existing map save/load system

✅ **Map Integration**
- Player marker (red triangle) on map showing position & rotation
- Toggle map view with M key
- Auto-mapping support (if enabled)

✅ **Placeholder Graphics**
- Colored rectangles for first-person view (replace with actual images)
- Wall, floor, ceiling, doors
- Interaction highlights

## Quick Start

```renpy
label start:
    call start_mapping_system
    call start_exploration_system
    $ create_test_dungeon()
    call screen exploration_view
    return
```

## Files

- `exploration_state.rpy` - PlayerState class (position, rotation, health)
- `movement.rpy` - Movement validation & collision detection
- `first_person_view.rpy` - View calculation with occlusion
- `interactions.rpy` - Icon interaction handling (gathering, stairs, doors)
- `exploration_screen.rpy` - UI & navigation controls
- `tiled_importer.rpy` - Tiled JSON map importer
- `exploration_persistence.rpy` - Save/load player state to JSON
- `exploration_init.rpy` - Initialization & test dungeon generator
- `player_marker.rpy` - Map overlay showing player position
- `README.md` - This file

## Documentation

See `/EXPLORATION_SYSTEM_GUIDE.md` for complete documentation.

## Example Usage

See `/game/exploration_example.rpy` for examples:
- Test dungeon
- Loading Tiled maps
- Multi-floor dungeons
- Gathering items

## Next Steps

1. **Replace placeholder graphics**
   - Create first-person wall/floor/ceiling images
   - Add door sprites
   - Add interaction highlights

2. **Design your dungeon in Tiled**
   - Export as JSON
   - Place in `game/maps/`
   - Call `load_dungeon_floor("maps/your_dungeon.json")`

3. **Extend functionality**
   - Add inventory system for gathering
   - Implement teleporter logic
   - Add random encounters
   - Create puzzle events

## Version

1.0 - Initial implementation (2025-11-19)
