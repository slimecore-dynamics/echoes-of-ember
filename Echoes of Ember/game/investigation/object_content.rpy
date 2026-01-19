## Investigation System - Examinable Object Content Definitions
##
## This file contains definitions for all examinable objects (books, boxes, etc.) in the game.

init python:

    # Example Book - Research Journal
    research_journal = ExaminableObject(
        id="research_journal",
        title="Dr. Chen's Research Journal",
        image="images/investigation/books/research_journal.png",
        content_file="investigation/text/objects/research_journal.txt",
        interaction_range="adjacent",
        is_evidence=True,
        evidence_summary="Dr. Chen was researching an unknown artifact before the breach"
    )

    # Example Box - Medical Supplies
    medical_supplies_box = ExaminableObject(
        id="medical_supplies",
        title="Medical Supply Crate",
        image="images/investigation/boxes/medical_crate.png",
        content_file="investigation/text/objects/medical_supplies.txt",
        interaction_range="adjacent",
        is_evidence=False,
        evidence_summary=""
    )

    # Example Book on Bookshelf - Security Manual
    security_manual = ExaminableObject(
        id="security_manual",
        title="Security Protocols Manual",
        image="images/investigation/books/security_manual.png",
        content_file="investigation/text/objects/security_manual.txt",
        interaction_range="same_tile",
        is_evidence=False,
        evidence_summary=""
    )


## Register examinable objects with investigation system
init python:
    investigation_state.register_examinable(research_journal)
    investigation_state.register_examinable(medical_supplies_box)
    investigation_state.register_examinable(security_manual)
