## Investigation System - JSON Data Loader
##
## Loads terminal and examinable object data from JSON files.

init python:
    import json

    class InvestigationDataLoader:
        """Loads investigation data from JSON files."""

        @staticmethod
        def load_terminal(file_path):
            """
            Load a terminal from a JSON file.

            Args:
                file_path: Path to JSON file (e.g., "investigation/data/security_terminal_1f.json")

            Returns:
                Terminal object or None if loading fails
            """
            try:
                # Load JSON file
                json_text = renpy.file(file_path).read().decode('utf-8')
                data = json.loads(json_text)

                # Create terminal
                terminal = Terminal(
                    id=data.get("id"),
                    welcome_message=data.get("welcome_message", "Terminal Online"),
                    metadata_text=data.get("metadata_text", ""),
                    empty_category_message=data.get("empty_category_messages", {}),
                    fpv_position=tuple(data["fpv_position"]) if "fpv_position" in data else None
                )

                # Load entries by category
                entries_data = data.get("entries", {})
                for category, entry_list in entries_data.items():
                    terminal.entries[category] = []
                    for entry_data in entry_list:
                        entry = TerminalEntry(
                            id=entry_data.get("id"),
                            category=category,
                            title=entry_data.get("title"),
                            content_file=entry_data.get("content_file"),
                            is_evidence=entry_data.get("is_evidence", False),
                            evidence_summary=entry_data.get("evidence_summary", ""),
                            timestamp=entry_data.get("timestamp", "Unknown"),
                            preview=entry_data.get("preview", "")
                        )
                        terminal.entries[category].append(entry)

                return terminal

            except Exception as e:
                renpy.notify("Error loading terminal from {}: {}".format(file_path, str(e)))
                return None

        @staticmethod
        def load_examinable(file_path):
            """
            Load an examinable object from a JSON file.

            Args:
                file_path: Path to JSON file (e.g., "investigation/data/research_journal.json")

            Returns:
                ExaminableObject or None if loading fails
            """
            try:
                # Load JSON file
                json_text = renpy.file(file_path).read().decode('utf-8')
                data = json.loads(json_text)

                # Create examinable object
                examinable = ExaminableObject(
                    id=data.get("id"),
                    title=data.get("title"),
                    image=data.get("image"),
                    content_file=data.get("content_file"),
                    interaction_range=data.get("interaction_range", "adjacent"),
                    is_evidence=data.get("is_evidence", False),
                    evidence_summary=data.get("evidence_summary", ""),
                    fpv_position=tuple(data["fpv_position"]) if "fpv_position" in data else None
                )

                return examinable

            except Exception as e:
                renpy.notify("Error loading examinable from {}: {}".format(file_path, str(e)))
                return None

        @staticmethod
        def prompt_facing_to_rotation(facing):
            """
            Convert prompt_facing direction letter to rotation degrees.

            Args:
                facing: "n", "s", "e", or "w"

            Returns:
                Rotation in degrees (0, 90, 180, 270) or None
            """
            facing_map = {
                "n": 0,
                "e": 90,
                "s": 180,
                "w": 270
            }
            return facing_map.get(facing.lower() if facing else None)

        @staticmethod
        def validate_content_files():
            """
            Validate that all content files referenced in terminals and examinables exist.

            Returns:
                Tuple of (success: bool, errors: list of error messages)
            """
            import os
            import sys

            errors = []
            success = True

            # Validate terminals
            for terminal_id, terminal in investigation_state.terminals.items():
                for category, entries in terminal.entries.items():
                    for entry in entries:
                        # Check if content file exists
                        try:
                            renpy.file(entry.content_file)
                        except:
                            errors.append("Terminal '{}' entry '{}': Content file not found: {}".format(
                                terminal_id, entry.id, entry.content_file))
                            success = False

            # Validate examinables
            for examinable_id, examinable in investigation_state.examinables.items():
                # Check if content file exists
                try:
                    renpy.file(examinable.content_file)
                except:
                    errors.append("Examinable '{}': Content file not found: {}".format(
                        examinable_id, examinable.content_file))
                    success = False

                # Check if image file exists (if specified)
                if examinable.image:
                    try:
                        renpy.loadable(examinable.image)
                    except:
                        errors.append("Examinable '{}': Image file not found: {}".format(
                            examinable_id, examinable.image))
                        success = False

            # Print errors to stderr
            if errors:
                print("\n=== Investigation Content Validation Errors ===", file=sys.stderr)
                for error in errors:
                    print("ERROR: {}".format(error), file=sys.stderr)
                print("==============================================\n", file=sys.stderr)

            return (success, errors)
