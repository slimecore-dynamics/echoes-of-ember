## Investigation System - Terminal Content Definitions
##
## This file contains definitions for all terminals in the game.

init python:

    # Example Security Terminal
    def create_security_terminal_1f():
        """Create the security terminal on floor 1F."""
        terminal = Terminal(
            id="security_terminal_1f",
            welcome_message="Security Terminal Online",
            metadata_text="Prometheus Breach - Security Network\nTerminal ID: SEC-1F-01\nAccess Level: 3",
            empty_category_message={
                "Logs": "Access Denied",
                "Personnel Files": "Database Corrupted",
                "Research Notes": "No Records Found"
            }
        )

        # Email category entries
        terminal.entries["Email"] = [
            TerminalEntry(
                id="email_security_breach",
                category="Email",
                title="Security Breach Alert",
                content_file="investigation/text/emails/security_breach.txt",
                is_evidence=True,
                evidence_summary="Security breach detected on March 15th, 2087",
                timestamp="3 days ago",
                preview="FROM: Dr. Sarah Chen - URGENT: Unauthorized access detected..."
            ),
            TerminalEntry(
                id="email_maintenance",
                category="Email",
                title="Scheduled Maintenance",
                content_file="investigation/text/emails/maintenance.txt",
                is_evidence=False,
                evidence_summary="",
                timestamp="1 week ago",
                preview="FROM: Maintenance Dept - All systems will be offline on..."
            ),
        ]

        # Notices category entries
        terminal.entries["Notices"] = [
            TerminalEntry(
                id="notice_evacuation",
                category="Notices",
                title="Evacuation Protocol",
                content_file="investigation/text/notices/evacuation.txt",
                is_evidence=True,
                evidence_summary="Emergency evacuation was ordered",
                timestamp="2 days ago",
                preview="EMERGENCY NOTICE: All personnel must evacuate immediately..."
            ),
        ]

        return terminal


## Initialize example terminals
init python:
    # Register terminals with investigation system
    investigation_state.register_terminal(create_security_terminal_1f())
