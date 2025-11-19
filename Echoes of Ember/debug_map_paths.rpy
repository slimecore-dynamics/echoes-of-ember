# Debug script to show where map data is being saved

label debug_show_renpy_save_callbacks:
    python:
        print("=" * 60)
        print("AVAILABLE SAVE/LOAD CALLBACKS IN CONFIG")
        print("=" * 60)

        # Check what save-related config variables exist
        save_related = [attr for attr in dir(config) if 'save' in attr.lower() or 'load' in attr.lower()]

        print("\nAll save/load related config attributes:")
        for attr in sorted(save_related):
            try:
                value = getattr(config, attr)
                print("  config.{} = {} (type: {})".format(attr, repr(value)[:80], type(value).__name__))
            except:
                print("  config.{} = <error accessing>".format(attr))

        print("\n" + "=" * 60)

    return

label debug_show_map_paths:
    python:
        import os

        print("=" * 60)
        print("MAP DATA FILE LOCATIONS DEBUG")
        print("=" * 60)

        # Show config.savedir
        print("\nRen'Py Save Directory (config.savedir):")
        print("  {}".format(config.savedir))

        # Show map data directory
        map_data_dir = get_map_data_dir()
        print("\nMap Data Directory:")
        print("  {}".format(map_data_dir))

        # Check if directory exists
        print("\nDirectory exists: {}".format(os.path.exists(map_data_dir)))

        # List files if directory exists
        if os.path.exists(map_data_dir):
            files = os.listdir(map_data_dir)
            print("\nFiles in map_data directory:")
            if files:
                for f in files:
                    full_path = os.path.join(map_data_dir, f)
                    size = os.path.getsize(full_path)
                    print("  - {} ({} bytes)".format(f, size))
            else:
                print("  (no files)")

        # Show what the path would be for slot "1-1"
        test_slot = "1-1"
        test_path = get_map_data_path(test_slot)
        print("\nExample save path for slot '{}':".format(test_slot))
        print("  {}".format(test_path))

        # Show current map_grid status
        print("\nCurrent map_grid status:")
        if map_grid:
            print("  Initialized: Yes")
            print("  Floors: {}".format(len(map_grid.floors)))
            if map_grid.floors:
                for floor_id, floor in map_grid.floors.items():
                    stats = get_floor_stats(floor_id)
                    print("    - {}: {} tiles placed".format(
                        floor.floor_name,
                        stats["tiles_placed"] if stats else 0
                    ))
        else:
            print("  Initialized: No (map_grid is None)")

        print("=" * 60)

    return
