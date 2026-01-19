# Investigation & Evidence Collection System

## Overview

The Investigation System allows players to examine objects during exploration and collect evidence/data that is stored in a journal. The system supports two types of investigation objects:

1. **Terminals** - Complex multi-level navigation with categories and entries (emails, logs, notices, etc.)
2. **Examinable Objects** - Simple objects like books and boxes with text descriptions and optional images

## File Structure

```
investigation/
├── investigation_data.rpy           # Core data classes
├── investigation_state.rpy          # State management & helper functions
├── investigation_screens.rpy        # All UI screens
├── investigation_handlers.rpy       # Interaction handlers
├── investigation_persistence.rpy    # Save/load system
├── variables.rpy                    # Configuration constants
├── terminal_content.rpy            # Terminal definitions
├── object_content.rpy              # Examinable object definitions
├── README.md                       # This file
└── text/                          # Content text files
    ├── emails/
    ├── logs/
    ├── notices/
    └── objects/
```

## Creating Terminals

### Step 1: Define Terminal Content

Create or edit `terminal_content.rpy`:

```python
def create_my_terminal():
    terminal = Terminal(
        id="my_terminal_id",
        welcome_message="Terminal Online",
        metadata_text="Location: Research Lab\nTerminal ID: LAB-01",
        empty_category_message={
            "Logs": "Access Denied",
            "Personnel Files": "No Records"
        }
    )

    # Add entries to categories
    terminal.entries["Email"] = [
        TerminalEntry(
            id="my_email_id",
            category="Email",
            title="Important Message",
            content_file="investigation/text/emails/my_email.txt",
            is_evidence=True,
            evidence_summary="Short summary for Evidence tab",
            timestamp="2 days ago",
            preview="FROM: John Doe - This is a preview..."
        )
    ]

    return terminal

# Register terminal
init python:
    investigation_state.register_terminal(create_my_terminal())
```

### Step 2: Create Content Text Files

Create `investigation/text/emails/my_email.txt`:

```
FROM: John Doe
TO: Research Team
DATE: March 15, 2087
SUBJECT: Important Message

This is the full content of the email.
Multiple paragraphs are supported.

Just use plain text for now.
```

### Step 3: Place Terminal in Map

In Tiled, add an object to the Object Layer:

- **Type:** (leave empty or set to object type)
- **Name:** (descriptive name)
- **Custom Properties:**
  - `icon_type` (string): "terminal"
  - `content_id` (string): "my_terminal_id"
  - `facing_direction` (int): 0, 90, 180, or 270 (direction player must face)

## Creating Examinable Objects

### Step 1: Define Object Content

Create or edit `object_content.rpy`:

```python
my_book = ExaminableObject(
    id="my_book_id",
    title="My Book Title",
    image="images/investigation/books/my_book.png",
    content_file="investigation/text/objects/my_book.txt",
    interaction_range="adjacent",  # or "same_tile"
    is_evidence=True,
    evidence_summary="Short summary for Evidence tab"
)

# Register object
init python:
    investigation_state.register_examinable(my_book)
```

### Step 2: Create Content Text File

Create `investigation/text/objects/my_book.txt`:

```
This is the content of the book.

Multiple paragraphs work fine.

The player will see this when they examine the book.
```

### Step 3: Create Image

Create your image at `images/investigation/books/my_book.png`:

- PNG format recommended
- Size: 400x300 to 800x600 pixels works well
- Will be scaled based on distance in FPV

### Step 4: Place Object in Map

In Tiled, add an object to the Object Layer:

- **Custom Properties:**
  - `icon_type` (string): "examinable"
  - `content_id` (string): "my_book_id"

## Global Categories

Terminal categories are defined globally in `variables.rpy`:

```python
define TERMINAL_CATEGORIES = [
    "Email",
    "Notices",
    "Logs",
    "Personnel Files",
    "Research Notes"
]
```

To add a new category, add it to this list. If a terminal doesn't have entries for a category, it will be greyed out with the empty message.

## Dynamic Content Updates

You can add entries to terminals during the story:

```python
label my_story_event:
    $ add_terminal_entry("my_terminal_id", "Email", {
        "id": "new_email_id",
        "category": "Email",
        "title": "New Email",
        "content_file": "investigation/text/emails/new_email.txt",
        "is_evidence": False,
        "evidence_summary": "",
        "timestamp": "Just now",
        "preview": "This just arrived..."
    })
```

## Story Conditionals

Use these helper functions in your story:

```python
# Check if player has collected evidence
if has_evidence("security_keycard"):
    "You use the keycard to unlock the door."

# Check if player has collected any data
if has_data("maintenance_log"):
    "You remember reading about this in the maintenance log."

# Count collected items
$ evidence_total = evidence_count()
$ data_total = data_count()
```

## Journal System

The journal has two tabs:

1. **Evidence Tab**: Shows only items with `is_evidence=True`, displays `evidence_summary`
2. **Data Tab**: Shows all collected items, displays full content

Both tabs show where each item was found (floor name and location).

## Configuration

Edit `investigation/variables.rpy` to customize:

- Terminal styling colors (retro amber theme by default)
- FPV scaling factors
- Category list
- Notification messages
- UI dimensions

## Integration with Exploration

The system is fully integrated with the exploration system:

- **FPV Display**: Investigation objects appear as clickable images in first-person view
- **Distance Scaling**: Objects scale based on distance (visible up to view_distance)
- **Interaction Prompts**: Green prompts appear in right panel when player can interact
- **Journal Button**: Available in exploration navigation and VN quick menu
- **Save/Load**: All collected data persists through save files

## Example Content

See the example content included in the system:

- **Terminal**: `security_terminal_1f` with emails and notices
- **Book**: `research_journal` (Dr. Chen's journal)
- **Box**: `medical_supplies` (medical crate)
- **Book**: `security_manual` (security protocols)

## Notes

- All text content should be plain text for now (no Ren'Py tags)
- Images are required for FPV display but system will handle missing images gracefully
- Terminal entries are collected when first viewed (individual entries, not terminal itself)
- Examinable objects are collected when examined
- Re-examining collected items doesn't trigger notification again
- Investigation interactions take priority over exploration interactions
