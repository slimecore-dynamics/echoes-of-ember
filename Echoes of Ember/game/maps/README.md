# Map Files Directory

This directory contains Tiled map editor files for dungeon layouts in Echoes of Ember.

## Directory Structure

- **tiled/** - Dungeon layouts created in Tiled Map Editor (JSON format)

## File Format

Dungeon layouts use Tiled JSON format. These define the actual dungeon structure, not player-drawn maps.

### Tiled JSON Maps
Contains tile layers and object layers with dungeon layout and interaction points.
```json
{
  "width": 20,
  "height": 20,
  "layers": [...],
  "tilesets": [...],
  "properties": {
    "floor_id": "floor_1",
    "starting_x": 10,
    "starting_y": 10,
    ...
  }
}
```

## Creating Dungeons

1. Design your dungeon in Tiled Map Editor
2. Export as JSON format
3. Place the file in `maps/tiled/`
4. Load in game with: `call load_dungeon_floor("maps/tiled/your_dungeon.json")`

## Map Data Persistence

Player-drawn map data (not dungeon layouts) is automatically saved with game saves in:
`<savedir>/map_data/<slot>_mapgrid.json`

This includes:
- Player-drawn tiles
- Player-placed icons and notes
- Revealed tiles (auto-map)

These files are managed automatically by the save/load system.
