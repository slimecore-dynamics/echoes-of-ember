# Echoes of Ember

A Ren'Py visual novel featuring an Etrian Odyssey-style dungeon exploration system.

## Features

### Dungeon Exploration System
- **First-person navigation** with tile-based movement
- **Player-drawn mapping** system with tile and icon placement
- **Tiled Map Editor** integration for dungeon design
- **Auto-mapping** support for automatic map reveal
- **Save/load system** with per-slot map data persistence

### Tile-Based Movement
- Hallways, corners, T-intersections, and cross intersections
- Movement constraints based on tile type and rotation
- Collision detection and pathfinding

### Interactive Elements
- Stairs, doors, teleporters
- Gathering points and events
- Enemy encounters
- Player notes on map

## Project Structure

```
Echoes of Ember/game/
├── exploration/          # Dungeon exploration system
│   ├── exploration_state.rpy      # Player state and position
│   ├── movement.rpy                # Movement validation
│   ├── first_person_view.rpy      # View rendering
│   ├── interactions.rpy            # Icon interactions
│   ├── exploration_screen.rpy      # UI and controls
│   ├── tiled_importer.rpy          # Tiled JSON import
│   ├── exploration_persistence.rpy # Save/load system
│   ├── exploration_init.rpy        # Initialization
│   ├── map_data.rpy                # Core data structures
│   └── player_marker.rpy           # Map marker display
├── maps/                # Dungeon layouts
│   └── tiled/          # Tiled JSON files
├── images/             # Graphics assets
│   └── maps/          # Map tiles and icons
└── script.rpy         # Main game script
```

## Getting Started

See `EXPLORATION_SYSTEM_GUIDE.md` for complete documentation on the dungeon exploration system.

## Development

Built with [Ren'Py](https://www.renpy.org/) visual novel engine.

Map dungeons designed with [Tiled Map Editor](https://www.mapeditor.org/).

## Save Data

Map data is saved per-slot in: `<savedir>/map_data/<slot>_mapgrid.json`

Player state is saved in: `<savedir>/map_data/<slot>_player.json`
