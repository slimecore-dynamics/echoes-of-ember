## Investigation System - UI Screens
##
## This file contains all UI screens for the investigation system:
## - Simple object examination popup
## - Terminal interface (3 levels)
## - Journal screen
## - FPV overlays for clickable investigation objects
## - Investigation interaction prompts

## ==============================================================================
## SIMPLE OBJECT EXAMINATION POPUP
## ==============================================================================

screen examination_popup(examinable_obj):
    """
    Shows a popup for examining simple objects (books, boxes, etc.)

    Args:
        examinable_obj: ExaminableObject instance to display
    """
    modal True
    zorder 200

    # Dim background
    add "#000000c0"

    # Main popup frame
    frame:
        xalign 0.5
        yalign 0.5
        xmaximum 800
        ymaximum 600
        padding (30, 30)
        background "#1a1a1a"

        vbox:
            spacing 20
            xfill True

            # Title
            text examinable_obj.title:
                size 32
                xalign 0.5
                color "#ffffff"

            # Image (if present)
            if examinable_obj.image:
                image examinable_obj.image:
                    xalign 0.5
                    fit "contain"
                    xmaximum INVESTIGATION_MAX_IMAGE_WIDTH
                    ymaximum 300

            # Content (scrollable)
            viewport:
                xfill True
                ymaximum 300
                scrollbars "vertical"
                mousewheel True

                text examinable_obj.get_content():
                    size 18
                    color "#e0e0e0"
                    xfill True

            # Close button
            textbutton "Close":
                xalign 0.5
                action Hide("examination_popup")


## ==============================================================================
## TERMINAL INTERFACE
## ==============================================================================

screen terminal_interface(terminal):
    """
    Main terminal interface screen (Level 1).
    Shows categories in left sidebar and main content area.

    Args:
        terminal: Terminal instance to display
    """
    modal True
    zorder 200

    # Dim background
    add "#000000c0"

    # Calculate terminal dimensions based on FPV area
    $ fpv_width = int(config.screen_width * 0.666)
    $ terminal_width = int(fpv_width * TERMINAL_SCREEN_WIDTH_RATIO)
    $ terminal_height = int(config.screen_height * TERMINAL_SCREEN_HEIGHT_RATIO)
    $ terminal_x = int((fpv_width - terminal_width) / 2)
    $ terminal_y = int((config.screen_height - terminal_height) / 2)

    # Main terminal frame
    frame:
        xpos terminal_x
        ypos terminal_y
        xsize terminal_width
        ysize terminal_height
        background TERMINAL_BG_COLOR
        padding (0, 0)

        # Border
        add Solid(TERMINAL_BORDER_COLOR, xsize=terminal_width, ysize=terminal_height)

        # Inner content with padding
        frame:
            xpos 2
            ypos 2
            xsize terminal_width - 4
            ysize terminal_height - 4
            background TERMINAL_BG_COLOR
            padding (0, 0)

            hbox:
                spacing 0
                xfill True
                yfill True

                # Left sidebar - Categories
                frame:
                    xsize int(terminal_width * TERMINAL_SIDEBAR_WIDTH_RATIO)
                    yfill True
                    background TERMINAL_BG_COLOR
                    padding (5, 5)

                    vbox:
                        spacing 0
                        xfill True
                        yfill True

                        for category in TERMINAL_CATEGORIES:
                            $ has_content = terminal.has_content_in_category(category)
                            $ is_selected = (investigation_state.current_terminal_category == category)

                            frame:
                                xfill True
                                ysize int((terminal_height - 20) / len(TERMINAL_CATEGORIES))
                                background (TERMINAL_HIGHLIGHT_COLOR if is_selected else TERMINAL_BG_COLOR)
                                padding (TERMINAL_CATEGORY_PADDING, TERMINAL_CATEGORY_PADDING)

                                button:
                                    xfill True
                                    yfill True
                                    background None
                                    action [
                                        SetVariable("investigation_state.current_terminal_category", category),
                                        If(has_content,
                                           SetVariable("investigation_state.current_terminal_entry_index", None),
                                           NullAction())
                                    ]
                                    sensitive has_content

                                    text category:
                                        xalign 0.5
                                        yalign 0.5
                                        size 20
                                        color (TERMINAL_TEXT_COLOR if has_content else TERMINAL_DISABLED_COLOR)

                # Vertical divider
                add Solid(TERMINAL_BORDER_COLOR, xsize=2)

                # Main content area
                frame:
                    xfill True
                    yfill True
                    background TERMINAL_BG_COLOR
                    padding (20, 20)

                    # Determine what to show based on state
                    if investigation_state.current_terminal_category is None:
                        # Level 1: Welcome screen
                        use terminal_welcome_screen(terminal)
                    elif investigation_state.current_terminal_entry_index is None:
                        # Level 2: Category list
                        use terminal_category_list(terminal, investigation_state.current_terminal_category)
                    else:
                        # Level 3: Individual entry view
                        use terminal_entry_view(terminal, investigation_state.current_terminal_category,
                                               investigation_state.current_terminal_entry_index)

        # Close button (top right)
        textbutton "X":
            xalign 0.98
            yalign 0.02
            action [
                SetVariable("investigation_state.current_terminal", None),
                SetVariable("investigation_state.current_terminal_category", None),
                SetVariable("investigation_state.current_terminal_entry_index", None),
                Hide("terminal_interface")
            ]
            text_size 24
            text_color TERMINAL_TEXT_COLOR


screen terminal_welcome_screen(terminal):
    """Terminal Level 1: Welcome/main screen."""
    vbox:
        spacing 20
        xfill True
        yalign 0.5

        # Welcome message
        text terminal.welcome_message:
            xalign 0.5
            size 28
            color TERMINAL_HIGHLIGHT_COLOR

        # Metadata
        if terminal.metadata_text:
            text terminal.metadata_text:
                xalign 0.5
                size 18
                color TERMINAL_TEXT_COLOR


screen terminal_category_list(terminal, category):
    """Terminal Level 2: List of entries in a category."""
    $ entries = terminal.get_category_entries(category)

    vbox:
        spacing 10
        xfill True
        yfill True

        # Category header
        text category:
            size 24
            color TERMINAL_HIGHLIGHT_COLOR

        add Solid(TERMINAL_BORDER_COLOR, xsize=9999, ysize=1)

        if len(entries) == 0:
            # No entries - show empty message
            text terminal.get_empty_message(category):
                xalign 0.5
                yalign 0.5
                size 20
                color TERMINAL_DISABLED_COLOR
        else:
            # Show scrollable list of entries
            viewport:
                xfill True
                yfill True
                scrollbars "vertical"
                mousewheel True
                draggable True
                pagekeys True

                vbox:
                    spacing 15
                    xfill True

                    for i, entry in enumerate(entries):
                        button:
                            xfill True
                            background Frame(Solid(TERMINAL_BG_COLOR), 10, 10)
                            hover_background Frame(Solid(TERMINAL_HIGHLIGHT_COLOR + "40"), 10, 10)
                            action SetVariable("investigation_state.current_terminal_entry_index", i)
                            padding (10, 10)

                            vbox:
                                spacing 5
                                xfill True

                                # Title
                                text entry.title:
                                    size 20
                                    color TERMINAL_HIGHLIGHT_COLOR

                                # Preview
                                if entry.preview:
                                    text entry.preview:
                                        size 16
                                        color TERMINAL_TEXT_COLOR
                                        text_align 0.0

                                # Timestamp
                                text entry.timestamp:
                                    size 14
                                    color TERMINAL_DISABLED_COLOR
                                    xalign 1.0


screen terminal_entry_view(terminal, category, entry_index):
    """Terminal Level 3: Individual entry view with navigation."""
    $ entries = terminal.get_category_entries(category)
    $ entry = entries[entry_index]
    $ has_prev = entry_index > 0
    $ has_next = entry_index < len(entries) - 1

    # Collect this entry when viewed (if not already collected)
    on "show":
        action Function(handle_terminal_entry_collection, terminal.id, entry.id)

    vbox:
        spacing 10
        xfill True
        yfill True

        # Navigation bar
        hbox:
            xfill True
            spacing 10

            # Previous button
            textbutton "<":
                action SetVariable("investigation_state.current_terminal_entry_index", entry_index - 1)
                sensitive has_prev
                text_size 24
                text_color (TERMINAL_TEXT_COLOR if has_prev else TERMINAL_DISABLED_COLOR)

            # Title (centered, takes remaining space)
            text entry.title:
                xalign 0.5
                size 22
                color TERMINAL_HIGHLIGHT_COLOR
                xfill True

            # Next button
            textbutton ">":
                action SetVariable("investigation_state.current_terminal_entry_index", entry_index + 1)
                sensitive has_next
                text_size 24
                text_color (TERMINAL_TEXT_COLOR if has_next else TERMINAL_DISABLED_COLOR)

        add Solid(TERMINAL_BORDER_COLOR, xsize=9999, ysize=1)

        # Content (scrollable)
        viewport:
            xfill True
            yfill True
            scrollbars "vertical"
            mousewheel True
            draggable True
            pagekeys True

            text entry.get_content():
                size 18
                color TERMINAL_TEXT_COLOR
                xfill True


## ==============================================================================
## JOURNAL SCREEN
## ==============================================================================

screen journal_screen():
    """
    Journal screen with Evidence and Data tabs.
    Shows all collected items with their content and locations.
    """
    modal True
    zorder 200

    # Which tab is currently selected
    default current_tab = JOURNAL_TAB_DATA

    # Dim background
    add "#000000c0"

    # Main journal frame
    frame:
        xalign 0.5
        yalign 0.5
        xmaximum 900
        ymaximum 700
        padding (20, 20)
        background "#1a1a1a"

        vbox:
            spacing 15
            xfill True
            yfill True

            # Title and tabs
            hbox:
                spacing 20
                xfill True

                text "Journal":
                    size 32
                    color "#ffffff"

                # Spacer
                null width 20

                # Evidence tab
                textbutton JOURNAL_TAB_EVIDENCE:
                    action SetScreenVariable("current_tab", JOURNAL_TAB_EVIDENCE)
                    text_size 24
                    text_color ("#ffd700" if current_tab == JOURNAL_TAB_EVIDENCE else "#808080")

                # Data tab
                textbutton JOURNAL_TAB_DATA:
                    action SetScreenVariable("current_tab", JOURNAL_TAB_DATA)
                    text_size 24
                    text_color ("#ffd700" if current_tab == JOURNAL_TAB_DATA else "#808080")

            add Solid("#404040", xsize=9999, ysize=2)

            # Content based on selected tab
            if current_tab == JOURNAL_TAB_EVIDENCE:
                use journal_evidence_tab()
            else:
                use journal_data_tab()

            # Close button
            textbutton "Close":
                xalign 0.5
                action Hide("journal_screen")


screen journal_evidence_tab():
    """Evidence tab - shows only evidence items with summaries."""
    $ evidence_entries = investigation_state.get_evidence_entries()

    if len(evidence_entries) == 0:
        text "No evidence collected yet.":
            xalign 0.5
            yalign 0.5
            size 20
            color "#808080"
    else:
        viewport:
            xfill True
            yfill True
            scrollbars "vertical"
            mousewheel True

            vbox:
                spacing 20
                xfill True

                # Group by location
                $ current_location = None
                for entry in evidence_entries:
                    if entry.location != current_location:
                        $ current_location = entry.location

                        # Location header
                        text current_location:
                            size 22
                            color "#ffd700"
                            bold True

                        add Solid("#404040", xsize=9999, ysize=1)

                    # Entry
                    frame:
                        xfill True
                        background "#2a2a2a"
                        padding (15, 15)

                        vbox:
                            spacing 8
                            xfill True

                            # Title
                            text entry.title:
                                size 20
                                color "#ffffff"
                                bold True

                            # Evidence summary
                            text entry.evidence_summary:
                                size 16
                                color "#d0d0d0"
                                xfill True


screen journal_data_tab():
    """Data tab - shows all collected items with full content."""
    $ all_entries = investigation_state.get_all_entries()

    if len(all_entries) == 0:
        text "No data collected yet.":
            xalign 0.5
            yalign 0.5
            size 20
            color "#808080"
    else:
        viewport:
            xfill True
            yfill True
            scrollbars "vertical"
            mousewheel True

            vbox:
                spacing 20
                xfill True

                # Group by location
                $ current_location = None
                for entry in all_entries:
                    if entry.location != current_location:
                        $ current_location = entry.location

                        # Location header
                        text current_location:
                            size 22
                            color "#ffd700"
                            bold True

                        add Solid("#404040", xsize=9999, ysize=1)

                    # Entry
                    frame:
                        xfill True
                        background "#2a2a2a"
                        padding (15, 15)

                        vbox:
                            spacing 8
                            xfill True

                            # Title
                            text entry.title:
                                size 20
                                color "#ffffff"
                                bold True

                            # Full content (limited height)
                            viewport:
                                xfill True
                                ymaximum 150
                                scrollbars "vertical"
                                mousewheel True

                                text entry.content:
                                    size 16
                                    color "#d0d0d0"
                                    xfill True


## ==============================================================================
## FPV OVERLAYS FOR INVESTIGATION OBJECTS
## ==============================================================================

screen render_investigation_fpv_overlays(view_data, floor, ps):
    """
    Render clickable investigation object overlays in the first-person view.

    Args:
        view_data: View data from FirstPersonView.get_view_data()
        floor: Current floor
        ps: Player state
    """
    $ fpv_width = int(config.screen_width * 0.666)
    $ fpv_height = config.screen_height
    $ view_distance = view_data.get("view_distance", 3)

    # Check each visible icon for investigation objects
    for icon_data in view_data.get("icons", []):
        $ x, y, icon, distance = icon_data

        # Check if this is an investigation object
        if icon.icon_type in ["terminal", "examinable"]:
            $ metadata = getattr(icon, 'metadata', {})
            $ content_id = metadata.get('content_id', None)

            if content_id:
                # Get the content object to retrieve image
                python:
                    content_obj = None
                    if icon.icon_type == "terminal":
                        content_obj = investigation_state.get_terminal(content_id)
                    elif icon.icon_type == "examinable":
                        content_obj = investigation_state.get_examinable(content_id)

                if content_obj and hasattr(content_obj, 'image') and content_obj.image:
                    # Calculate FPV position for this object
                    $ fpv_pos = InvestigationInteractionHandler.calculate_fpv_position(
                        distance, view_distance, fpv_width, fpv_height,
                        custom_position=content_obj.fpv_position
                    )

                    if fpv_pos:
                        $ pos_x, pos_y, scale = fpv_pos

                        # Render clickable image button
                        imagebutton:
                            xpos pos_x
                            ypos pos_y
                            xanchor 0.5
                            yanchor 0.5
                            idle content_obj.image
                            hover content_obj.image
                            at transform:
                                zoom scale
                            action [
                                If(icon.icon_type == "terminal",
                                   Function(handle_terminal_interaction, content_id),
                                   Function(handle_examinable_interaction, content_id))
                            ]


## ==============================================================================
## INVESTIGATION INTERACTION PROMPT
## ==============================================================================

screen investigation_interaction_prompt(inv_icon, inv_type, content_id):
    """
    Compact investigation interaction prompt in right panel.

    Args:
        inv_icon: Icon object
        inv_type: "terminal" or "examinable"
        content_id: ID of the content to display
    """
    frame:
        xsize int(config.screen_width * 0.314)
        background "#00FF00AA"  # Green background (different from red exploration prompts)
        padding (10, 10)

        vbox:
            spacing 5

            if inv_type == "terminal":
                text "Terminal" size 14 xalign 0.5 color "#FFFFFF"
                textbutton "Access":
                    action Function(handle_terminal_interaction, content_id)
                    xalign 0.5
                    xsize 120
                    ysize 35
                    sensitive True

            elif inv_type == "examinable":
                $ examinable = investigation_state.get_examinable(content_id)
                if examinable:
                    text examinable.title size 14 xalign 0.5 color "#FFFFFF"
                    textbutton "Examine":
                        action Function(handle_examinable_interaction, content_id)
                        xalign 0.5
                        xsize 120
                        ysize 35
                        sensitive True
