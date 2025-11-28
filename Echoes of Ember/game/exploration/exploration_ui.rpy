# exploration_ui.rpy
# UI components: displayables and UI helper functions
# Color palettes are defined in variables.rpy

init python:
    import math

    class PlayerTriangleMarker(renpy.Displayable):
        """Red triangle showing player position and facing direction."""

        def __init__(self, x, y, rotation, cell_size, **kwargs):
            super(PlayerTriangleMarker, self).__init__(**kwargs)
            self.x = x
            self.y = y
            self.rotation = rotation
            self.cell_size = cell_size

        def render(self, width, height, st, at):
            """Render actual triangle pointing in player's facing direction."""
            import math

            render = renpy.Render(self.cell_size, self.cell_size)

            # Triangle size
            tri_size = self.cell_size * 0.6
            half_size = tri_size / 2.0

            # Center of cell
            center_x = self.cell_size / 2.0
            center_y = self.cell_size / 2.0

            # Calculate triangle points based on rotation
            # 0 = North (point up), 90 = East (point right), etc.
            angle_rad = math.radians(self.rotation - 90)  # Adjust so 0 points up

            # Three points of equilateral triangle
            points = []
            for i in range(3):
                point_angle = angle_rad + (i * 2.0 * math.pi / 3.0)
                px = center_x + (half_size * math.cos(point_angle))
                py = center_y + (half_size * math.sin(point_angle))
                points.append((int(px), int(py)))

            # Draw triangle using Canvas
            canvas = renpy.display.draw.Canvas()
            canvas.polygon("#FF0000", points)
            canvas_render = renpy.render(canvas, self.cell_size, self.cell_size, st, at)
            render.blit(canvas_render, (0, 0))

            return render

    class AnimatedInteractIndicator(renpy.Displayable):
        """Pulsing yellow indicator for interactions."""

        def render(self, width, height, st, at):
            """Pulse between 0.5 and 1.0 opacity."""
            alpha = 0.5 + 0.5 * abs(math.sin(st * 3.14))

            render = renpy.Render(100, 100)
            pulse = Solid(color_interact + "{:02x}".format(int(alpha * 255)), xsize=80, ysize=80)
            pulse_render = renpy.render(pulse, 80, 80, st, at)
            render.blit(pulse_render, (10, 10))

            renpy.redraw(self, 0.05)  # Update frequently for animation
            return render

    def get_tile_color(tile_type):
        """Get color for tile type on minimap."""
        return TILE_COLORS.get(tile_type, "#666666")

    def get_icon_color(icon_type):
        """Get color for icon type on minimap."""
        return ICON_COLORS.get(icon_type, "#FFFFFF")
