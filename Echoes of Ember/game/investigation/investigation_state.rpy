## Investigation System - State Management
##
## This file manages the investigation state, including collected items,
## journal entries, and helper functions for story conditionals.

init python:

    class InvestigationState:
        """
        Manages the state of the investigation system.

        Attributes:
            collected_items: Set of collected item IDs
            journal_entries: List of JournalEntry objects
            terminals: Dictionary mapping terminal IDs to Terminal objects
            examinables: Dictionary mapping examinable IDs to ExaminableObject objects
            current_terminal: Currently open terminal (if any)
            current_terminal_category: Currently selected category in terminal
            current_terminal_entry_index: Currently viewing entry index in category
        """
        def __init__(self):
            self.collected_items = set()
            self.journal_entries = []
            self.terminals = {}
            self.examinables = {}
            self.current_terminal = None
            self.current_terminal_category = None
            self.current_terminal_entry_index = None

        def register_terminal(self, terminal):
            """Register a terminal in the system."""
            self.terminals[terminal.id] = terminal

        def register_examinable(self, examinable):
            """Register an examinable object in the system."""
            self.examinables[examinable.id] = examinable

        def get_terminal(self, terminal_id):
            """Get a terminal by ID."""
            return self.terminals.get(terminal_id)

        def get_examinable(self, examinable_id):
            """Get an examinable object by ID."""
            return self.examinables.get(examinable_id)

        def collect_item(self, item_id, item_title, item_content, location,
                        is_evidence=False, evidence_summary=""):
            """
            Collect an item and add it to the journal.

            Returns:
                True if item was newly collected, False if already collected
            """
            if item_id in self.collected_items:
                return False

            # Mark as collected
            self.collected_items.add(item_id)

            # Create journal entry
            entry = JournalEntry(
                source_id=item_id,
                title=item_title,
                content=item_content,
                location=location,
                timestamp=self._get_current_timestamp(),
                entry_type="evidence" if is_evidence else "data",
                evidence_summary=evidence_summary
            )

            # Add to journal
            self.journal_entries.append(entry)

            return True

        def has_collected(self, item_id):
            """Check if an item has been collected."""
            return item_id in self.collected_items

        def has_evidence(self, item_id):
            """Check if an evidence item has been collected."""
            if item_id not in self.collected_items:
                return False
            # Check if this item is marked as evidence in journal
            for entry in self.journal_entries:
                if entry.source_id == item_id and entry.entry_type == "evidence":
                    return True
            return False

        def has_data(self, item_id):
            """Check if a data item has been collected (any item)."""
            return self.has_collected(item_id)

        def has_all_evidence(self, item_ids):
            """
            Check if player has ALL of the evidence items.

            Args:
                item_ids: List of item IDs to check

            Returns:
                True if all items are collected as evidence, False otherwise
            """
            return all(self.has_evidence(item_id) for item_id in item_ids)

        def has_any_evidence(self, item_ids):
            """
            Check if player has ANY of the evidence items.

            Args:
                item_ids: List of item IDs to check

            Returns:
                True if at least one item is collected as evidence, False otherwise
            """
            return any(self.has_evidence(item_id) for item_id in item_ids)

        def get_collected_count(self):
            """
            Get total number of collected items.

            Returns:
                Integer count of collected items
            """
            return len(self.collected_items)

        def get_evidence_entries(self):
            """Get all evidence journal entries."""
            return [entry for entry in self.journal_entries if entry.entry_type == "evidence"]

        def get_all_entries(self):
            """Get all journal entries."""
            return self.journal_entries

        def add_terminal_entry(self, terminal_id, category, entry):
            """
            Dynamically add a new entry to a terminal.

            Args:
                terminal_id: ID of the terminal
                category: Category to add entry to
                entry: TerminalEntry object to add

            Returns:
                True if entry was added successfully, False otherwise
            """
            import sys

            terminal = self.get_terminal(terminal_id)
            if not terminal:
                print("Warning: Terminal '{}' not found, cannot add entry '{}'".format(terminal_id, entry.id), file=sys.stderr)
                return False

            # Validate category exists in TERMINAL_CATEGORIES
            if category not in TERMINAL_CATEGORIES:
                print("Warning: Invalid category '{}' for terminal '{}'. Valid categories: {}".format(
                    category, terminal_id, TERMINAL_CATEGORIES), file=sys.stderr)
                return False

            terminal.add_entry(entry)
            return True

        def remove_terminal_entry(self, terminal_id, entry_id):
            """
            Remove an entry from a terminal (for story events).

            Args:
                terminal_id: ID of the terminal
                entry_id: ID of the entry to remove

            Returns:
                True if entry was removed, False if not found
            """
            import sys

            terminal = self.get_terminal(terminal_id)
            if not terminal:
                print("Warning: Terminal '{}' not found, cannot remove entry '{}'".format(terminal_id, entry_id), file=sys.stderr)
                return False

            # Search through all categories
            for category, entries in terminal.entries.items():
                for i, entry in enumerate(entries):
                    if entry.id == entry_id:
                        del entries[i]
                        return True

            print("Warning: Entry '{}' not found in terminal '{}'".format(entry_id, terminal_id), file=sys.stderr)
            return False

        def clear_terminal_category(self, terminal_id, category):
            """
            Clear all entries in a category (for story events).

            Args:
                terminal_id: ID of the terminal
                category: Category to clear

            Returns:
                True if category was cleared, False if terminal not found
            """
            import sys

            terminal = self.get_terminal(terminal_id)
            if not terminal:
                print("Warning: Terminal '{}' not found, cannot clear category '{}'".format(terminal_id, category), file=sys.stderr)
                return False

            if category in terminal.entries:
                terminal.entries[category] = []

            return True

        def _get_current_timestamp(self):
            """Get current timestamp for journal entries."""
            # For now, just use a simple counter
            # Could be enhanced to use in-game time
            return "Recently"

        def to_dict(self):
            """Convert to dictionary for serialization."""
            return {
                "collected_items": list(self.collected_items),
                "journal_entries": [entry.to_dict() for entry in self.journal_entries],
                "terminals": {
                    terminal_id: terminal.to_dict()
                    for terminal_id, terminal in self.terminals.items()
                },
                "examinables": {
                    examinable_id: examinable.to_dict()
                    for examinable_id, examinable in self.examinables.items()
                }
            }

        @staticmethod
        def from_dict(data):
            """Create InvestigationState from dictionary."""
            state = InvestigationState()
            state.collected_items = set(data.get("collected_items", []))
            state.journal_entries = [
                JournalEntry.from_dict(entry_data)
                for entry_data in data.get("journal_entries", [])
            ]
            state.terminals = {
                terminal_id: Terminal.from_dict(terminal_data)
                for terminal_id, terminal_data in data.get("terminals", {}).items()
            }
            state.examinables = {
                examinable_id: ExaminableObject.from_dict(examinable_data)
                for examinable_id, examinable_data in data.get("examinables", {}).items()
            }
            return state


## Initialize global investigation state
default investigation_state = InvestigationState()


## Helper Functions for Story Conditionals

init python:

    def has_evidence(item_id):
        """
        Check if player has collected a specific evidence item.

        Args:
            item_id: ID of the item to check

        Returns:
            True if collected and is evidence, False otherwise
        """
        return investigation_state.has_evidence(item_id)

    def has_data(item_id):
        """
        Check if player has collected a specific data item.

        Args:
            item_id: ID of the item to check

        Returns:
            True if collected, False otherwise
        """
        return investigation_state.has_data(item_id)

    def has_all_evidence(item_ids):
        """
        Check if player has collected ALL of the specified evidence items.

        Args:
            item_ids: List of item IDs to check

        Returns:
            True if all items are collected as evidence, False otherwise

        Example:
            if has_all_evidence(["email_breach", "journal_virus", "security_log"]):
                "You've gathered all the evidence."
        """
        return investigation_state.has_all_evidence(item_ids)

    def has_any_evidence(item_ids):
        """
        Check if player has collected ANY of the specified evidence items.

        Args:
            item_ids: List of item IDs to check

        Returns:
            True if at least one item is collected as evidence, False otherwise

        Example:
            if has_any_evidence(["email_breach", "journal_virus"]):
                "You've found some evidence."
        """
        return investigation_state.has_any_evidence(item_ids)

    def get_collected_count():
        """
        Get the total number of collected items (both evidence and data).

        Returns:
            Integer count of collected items

        Example:
            if get_collected_count() >= 10:
                "You've been thorough in your investigation."
        """
        return investigation_state.get_collected_count()

    def add_terminal_entry(terminal_id, category, entry_dict):
        """
        Add a new entry to a terminal dynamically.

        Args:
            terminal_id: ID of the terminal
            category: Category to add entry to
            entry_dict: Dictionary with entry data (id, title, content_file, etc.)

        Example:
            $ add_terminal_entry("security_terminal_1f", "Email", {
                "id": "emergency_email",
                "category": "Email",
                "title": "Emergency Protocol",
                "content_file": "investigation/text/emails/emergency.txt",
                "is_evidence": True,
                "evidence_summary": "Emergency protocol activated",
                "timestamp": "1 hour ago",
                "preview": "URGENT: All personnel..."
            })
        """
        entry = TerminalEntry.from_dict(entry_dict)
        investigation_state.add_terminal_entry(terminal_id, category, entry)

    def evidence_count():
        """Get the number of evidence items collected."""
        return len(investigation_state.get_evidence_entries())

    def data_count():
        """Get the total number of items collected."""
        return len(investigation_state.get_all_entries())
