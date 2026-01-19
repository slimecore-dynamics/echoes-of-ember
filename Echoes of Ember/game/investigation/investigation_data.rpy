## Investigation System - Core Data Classes
##
## This file defines the core data structures for the investigation system,
## including examinable objects, terminal entries, and journal entries.

init python:

    class ExaminableObject:
        """
        Represents a simple examinable object (book, box, etc.)

        Attributes:
            id: Unique identifier for this object
            title: Display name
            image: Path to image file for FPV display
            content_file: Path to text file containing description
            interaction_range: "same_tile" or "adjacent"
            is_evidence: Whether this is marked as evidence
            evidence_summary: Short summary for Evidence tab (if is_evidence)
            fpv_position: Optional (x, y) tuple for FPV overlay position
        """
        def __init__(self, id, title, image, content_file, interaction_range="adjacent",
                     is_evidence=False, evidence_summary="", fpv_position=None):
            self.id = id
            self.title = title
            self.image = image
            self.content_file = content_file
            self.interaction_range = interaction_range
            self.is_evidence = is_evidence
            self.evidence_summary = evidence_summary
            self.fpv_position = fpv_position
            self._cached_content = None

        def get_content(self):
            """Load and return content from file, caching it."""
            if self._cached_content is None:
                try:
                    self._cached_content = renpy.file(self.content_file).read().decode('utf-8')
                except:
                    self._cached_content = "[Content file not found: {}]".format(self.content_file)
            return self._cached_content

        def to_dict(self):
            """Convert to dictionary for serialization."""
            return {
                "id": self.id,
                "title": self.title,
                "image": self.image,
                "content_file": self.content_file,
                "interaction_range": self.interaction_range,
                "is_evidence": self.is_evidence,
                "evidence_summary": self.evidence_summary,
                "fpv_position": self.fpv_position
            }

        @staticmethod
        def from_dict(data):
            """Create ExaminableObject from dictionary."""
            return ExaminableObject(**data)


    class TerminalEntry:
        """
        Represents a single entry in a terminal (email, log, notice, etc.)

        Attributes:
            id: Unique identifier
            category: Category this entry belongs to
            title: Title shown in list view
            content_file: Path to text file with full content
            is_evidence: Whether this is marked as evidence
            evidence_summary: Short summary for Evidence tab (if is_evidence)
            timestamp: Display timestamp (e.g., "235 days ago", "1 hour ago")
            preview: Short preview text for list view
        """
        def __init__(self, id, category, title, content_file, is_evidence=False,
                     evidence_summary="", timestamp="Unknown", preview=""):
            self.id = id
            self.category = category
            self.title = title
            self.content_file = content_file
            self.is_evidence = is_evidence
            self.evidence_summary = evidence_summary
            self.timestamp = timestamp
            self.preview = preview
            self._cached_content = None

        def get_content(self):
            """Load and return content from file, caching it."""
            if self._cached_content is None:
                try:
                    self._cached_content = renpy.file(self.content_file).read().decode('utf-8')
                except:
                    self._cached_content = "[Content file not found: {}]".format(self.content_file)
            return self._cached_content

        def to_dict(self):
            """Convert to dictionary for serialization."""
            return {
                "id": self.id,
                "category": self.category,
                "title": self.title,
                "content_file": self.content_file,
                "is_evidence": self.is_evidence,
                "evidence_summary": self.evidence_summary,
                "timestamp": self.timestamp,
                "preview": self.preview
            }

        @staticmethod
        def from_dict(data):
            """Create TerminalEntry from dictionary."""
            return TerminalEntry(**data)


    class Terminal:
        """
        Represents a terminal with multiple categories of entries.

        Attributes:
            id: Unique identifier for this terminal
            welcome_message: Message shown on terminal main screen
            metadata_text: Additional info shown on main screen
            empty_category_message: Message for categories with no content (per-category dict)
            entries: Dictionary mapping category names to lists of TerminalEntry objects
            fpv_position: Optional (x, y) tuple for FPV overlay position
        """
        def __init__(self, id, welcome_message="Terminal Unlocked", metadata_text="",
                     empty_category_message=None, entries=None, fpv_position=None):
            self.id = id
            self.welcome_message = welcome_message
            self.metadata_text = metadata_text
            self.empty_category_message = empty_category_message or {}
            self.entries = entries or {}
            self.fpv_position = fpv_position

        def get_category_entries(self, category):
            """Get all entries for a category."""
            return self.entries.get(category, [])

        def has_content_in_category(self, category):
            """Check if category has any entries."""
            return len(self.get_category_entries(category)) > 0

        def get_empty_message(self, category):
            """Get the empty message for a category."""
            return self.empty_category_message.get(category, "Data Corrupted")

        def add_entry(self, entry):
            """Add a new entry to this terminal."""
            if entry.category not in self.entries:
                self.entries[entry.category] = []
            self.entries[entry.category].append(entry)

        def to_dict(self):
            """Convert to dictionary for serialization."""
            return {
                "id": self.id,
                "welcome_message": self.welcome_message,
                "metadata_text": self.metadata_text,
                "empty_category_message": self.empty_category_message,
                "entries": {
                    category: [entry.to_dict() for entry in entries]
                    for category, entries in self.entries.items()
                },
                "fpv_position": self.fpv_position
            }

        @staticmethod
        def from_dict(data):
            """Create Terminal from dictionary."""
            terminal = Terminal(
                id=data["id"],
                welcome_message=data.get("welcome_message", "Terminal Unlocked"),
                metadata_text=data.get("metadata_text", ""),
                empty_category_message=data.get("empty_category_message", {}),
                fpv_position=data.get("fpv_position")
            )
            # Reconstruct entries
            for category, entries_data in data.get("entries", {}).items():
                terminal.entries[category] = [
                    TerminalEntry.from_dict(entry_data)
                    for entry_data in entries_data
                ]
            return terminal


    class JournalEntry:
        """
        Represents an entry in the player's journal.

        Attributes:
            source_id: ID of the source object/terminal entry
            title: Display title
            content: Full content text
            location: Where this was found (e.g., "Prometheus Breach - 1F")
            timestamp: When collected (game time or real time)
            entry_type: "evidence" or "data"
            evidence_summary: Short summary (for evidence entries)
        """
        def __init__(self, source_id, title, content, location, timestamp,
                     entry_type="data", evidence_summary=""):
            self.source_id = source_id
            self.title = title
            self.content = content
            self.location = location
            self.timestamp = timestamp
            self.entry_type = entry_type
            self.evidence_summary = evidence_summary

        def to_dict(self):
            """Convert to dictionary for serialization."""
            return {
                "source_id": self.source_id,
                "title": self.title,
                "content": self.content,
                "location": self.location,
                "timestamp": self.timestamp,
                "entry_type": self.entry_type,
                "evidence_summary": self.evidence_summary
            }

        @staticmethod
        def from_dict(data):
            """Create JournalEntry from dictionary."""
            return JournalEntry(**data)
