## Investigation System - Configuration Variables
##
## This file contains all configuration constants for the investigation system.

## Global terminal categories (in display order)
define TERMINAL_CATEGORIES = [
    "Email",
    "Notices",
    "Logs",
    "Personnel Files",
    "Research Notes"
]

## FPV Image Scaling Configuration
## Scale factor at minimum distance (adjacent/same tile = distance 1)
define INVESTIGATION_FPV_SCALE_MIN = 1.0

## Scale factor at maximum view distance
define INVESTIGATION_FPV_SCALE_MAX = 0.0

## Terminal UI Configuration
define TERMINAL_SIDEBAR_WIDTH_RATIO = 0.25  # 25% of terminal width
define TERMINAL_CATEGORY_PADDING = 10  # Pixels padding for category buttons
define TERMINAL_SCREEN_WIDTH_RATIO = 0.80  # 80% of FPV area width
define TERMINAL_SCREEN_HEIGHT_RATIO = 0.80  # 80% of screen height

## Terminal Styling (Retro Amber Theme)
define TERMINAL_BG_COLOR = "#000000"  # Black background
define TERMINAL_TEXT_COLOR = "#ffb000"  # Amber text
define TERMINAL_HIGHLIGHT_COLOR = "#ffd700"  # Bright amber for highlights
define TERMINAL_DISABLED_COLOR = "#664400"  # Dimmed amber for disabled items
define TERMINAL_BORDER_COLOR = "#ffb000"  # Amber border

## Journal Configuration
define JOURNAL_BUTTON_WIDTH = 150  # Width of journal button in exploration
define JOURNAL_BUTTON_HEIGHT = 40  # Height of journal button

## Notification Messages
define NOTIFICATION_EVIDENCE_SECURED = "Evidence secured"
define NOTIFICATION_DATA_SECURED = "Data secured"

## FPV Default Positions (x, y coordinates for center of image)
## These are offsets from the FPV area, will be calculated based on distance
define INVESTIGATION_FPV_DEFAULT_Y_OFFSET = {
    1: 0.6,   # Distance 1 (adjacent/same tile) - lower on screen
    2: 0.45,  # Distance 2 - middle
    3: 0.3    # Distance 3 - upper
}

define INVESTIGATION_FPV_DEFAULT_X_CENTER = 0.5  # Centered horizontally

## Image Maximum Dimensions (for safety)
define INVESTIGATION_MAX_IMAGE_WIDTH = 800
define INVESTIGATION_MAX_IMAGE_HEIGHT = 600

## Journal Tab Names
define JOURNAL_TAB_EVIDENCE = "Evidence"
define JOURNAL_TAB_DATA = "Data"
