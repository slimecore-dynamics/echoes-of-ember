# player_marker.rpy
# Adds player position marker to the map view

init python:
    def draw_player_marker(canvas_obj, x, y, rotation, cell_size=32):
        """
        Draw a triangle marker showing player position and rotation on the map.

        Args:
            canvas_obj: Ren'Py Canvas object
            x, y: Grid coordinates
            rotation: Player rotation (0, 90, 180, 270)
            cell_size: Size of map grid cells in pixels
        """
        import math

        # Calculate center of the cell
        center_x = x * cell_size + (cell_size // 2)
        center_y = y * cell_size + (cell_size // 2)

        # Triangle size
        tri_size = cell_size * 0.6

        # Calculate triangle points based on rotation
        # Rotation 0 = pointing North (up)
        # Rotation 90 = pointing East (right)
        # Rotation 180 = pointing South (down)
        # Rotation 270 = pointing West (left)

        if rotation == 0:  # North
            points = [
                (center_x, center_y - tri_size / 2),  # Top point
                (center_x - tri_size / 3, center_y + tri_size / 3),  # Bottom left
                (center_x + tri_size / 3, center_y + tri_size / 3)   # Bottom right
            ]
        elif rotation == 90:  # East
            points = [
                (center_x + tri_size / 2, center_y),  # Right point
                (center_x - tri_size / 3, center_y - tri_size / 3),  # Top left
                (center_x - tri_size / 3, center_y + tri_size / 3)   # Bottom left
            ]
        elif rotation == 180:  # South
            points = [
                (center_x, center_y + tri_size / 2),  # Bottom point
                (center_x - tri_size / 3, center_y - tri_size / 3),  # Top left
                (center_x + tri_size / 3, center_y - tri_size / 3)   # Top right
            ]
        else:  # 270 = West
            points = [
                (center_x - tri_size / 2, center_y),  # Left point
                (center_x + tri_size / 3, center_y - tri_size / 3),  # Top right
                (center_x + tri_size / 3, center_y + tri_size / 3)   # Bottom right
            ]

        # Draw filled triangle
        canvas_obj.polygon(points, "#FF0000")  # Red triangle

        # Draw outline
        canvas_obj.polygon(points, "#FFFFFF", width=2, fill=False)  # White outline


screen player_marker_overlay():
    """
    Overlay that draws the player marker on top of the map view.

    This should be shown when the map is visible and player_state exists.
    """

    if map_grid and player_state:
        $ floor = map_grid.get_current_floor()

        if floor:
            # Create canvas to draw marker
            $ cell_size = map_grid.cell_size if hasattr(map_grid, 'cell_size') else 32

            # Only draw if player is on current floor
            if player_state.current_floor_id == floor.floor_id:
                fixed:
                    # Position marker on map grid
                    # This assumes the map grid starts at some offset
                    # Adjust based on actual map_view screen layout
                    add CanvasMarker(player_state.x, player_state.y, player_state.rotation, cell_size)


init python:
    from renpy.display.layout import Fixed
    from renpy.display.im import Image as RenpyImage

    class CanvasMarker(renpy.Displayable):
        """
        Custom displayable that draws the player marker triangle.
        """

        def __init__(self, grid_x, grid_y, rotation, cell_size=32, **kwargs):
            super(CanvasMarker, self).__init__(**kwargs)
            self.grid_x = grid_x
            self.grid_y = grid_y
            self.rotation = rotation
            self.cell_size = cell_size

        def render(self, width, height, st, at):
            # Create render surface
            render_obj = renpy.Render(width, height)

            # Calculate position
            center_x = self.grid_x * self.cell_size + (self.cell_size // 2)
            center_y = self.grid_y * self.cell_size + (self.cell_size // 2)

            # Triangle size
            tri_size = self.cell_size * 0.6

            # Calculate triangle points based on rotation
            if self.rotation == 0:  # North
                points = [
                    (center_x, center_y - tri_size / 2),
                    (center_x - tri_size / 3, center_y + tri_size / 3),
                    (center_x + tri_size / 3, center_y + tri_size / 3)
                ]
            elif self.rotation == 90:  # East
                points = [
                    (center_x + tri_size / 2, center_y),
                    (center_x - tri_size / 3, center_y - tri_size / 3),
                    (center_x - tri_size / 3, center_y + tri_size / 3)
                ]
            elif self.rotation == 180:  # South
                points = [
                    (center_x, center_y + tri_size / 2),
                    (center_x - tri_size / 3, center_y - tri_size / 3),
                    (center_x + tri_size / 3, center_y - tri_size / 3)
                ]
            else:  # 270 = West
                points = [
                    (center_x - tri_size / 2, center_y),
                    (center_x + tri_size / 3, center_y - tri_size / 3),
                    (center_x + tri_size / 3, center_y + tri_size / 3)
                ]

            # Draw triangle using Ren'Py polygon
            # Note: This is a simplified version - actual implementation
            # may need to use canvas or solid shapes

            # For now, use a simple colored square as placeholder
            # Real triangle drawing would require more complex rendering
            marker = renpy.display.render.Solid("#FF0000", xsize=int(tri_size), ysize=int(tri_size))
            marker_render = renpy.display.render.render(marker, int(tri_size), int(tri_size), st, at)

            render_obj.blit(marker_render, (int(center_x - tri_size/2), int(center_y - tri_size/2)))

            return render_obj

        def event(self, ev, x, y, st):
            return None
