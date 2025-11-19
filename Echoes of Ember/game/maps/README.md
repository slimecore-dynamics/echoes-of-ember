# Map Files Directory

This directory contains map data files for the Etrian Odyssey-style mapping system in Echoes of Ember.

## Directory Structure

- **exports/** - Maps exported by the player (JSON format)
- **imports/** - Place JSON map files here to import them into the game
- **backups/** - Automatic backups of map data

## File Format

All map files use JSON format for human readability and easy sharing between players.

### Full Map Export
Contains all floors and complete map grid data.
```json
{
  "version": "1.0",
  "floors": {...},
  "current_floor": "floor_1",
  ...
}
```

### Single Floor Export
Contains data for one floor only.
```json
{
  "floor_id": "floor_1",
  "floor_name": "Entrance Hall",
  "dimensions": [20, 20],
  "tiles": [...],
  "icons": {...},
  "notes": {...}
}
```

## Importing Maps

1. Place a JSON map file in the `imports/` directory
2. Use the in-game import function to load the map
3. The map will be merged with or replace your current map data

## Exporting Maps

Use the in-game export function to save your maps as JSON files. These will appear in the `exports/` directory.

## Sharing Maps

You can share exported JSON files with other players. Simply copy the file from your `exports/` directory and send it to others, who can place it in their `imports/` directory.

## Backups

Automatic backups are created in the `backups/` directory. These can be used to restore your map if something goes wrong.
