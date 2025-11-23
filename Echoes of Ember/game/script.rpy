# The script of the game goes in this file.

# Declare characters used by this game. The color argument colorizes the
# name of the character.

define e = Character("Eileen")


# The game starts here.

label start:

    # Initialize mapping system
    call start_mapping_system

    # Show a background. This uses a placeholder by default, but you can
    # add a file (named either "bg room.png" or "bg room.jpg") to the
    # images directory to show it.

    scene bg room

    # This shows a character sprite. A placeholder is used, but you can
    # replace it by adding a file named "eileen happy.png" to the images
    # directory.

    show eileen happy

    # These display lines of dialogue.

    e "You've created a new Ren'Py game."

    e "Once you add a story, pictures, and music, you can release it to the world!"

    e "The mapping system has been initialized. You can use it to create Etrian Odyssey-style dungeon maps!"

    # Initialize exploration system
    call start_exploration_system

    # Load the Prometheus Breach dungeon from Tiled JSON
    call load_dungeon_floor("maps/tiled/prom_breach_1f.json")

    # Show exploration screen
    call screen exploration_view

    # This ends the game.

    return
