import math
import customtkinter


class CanvasRenderer:
    """Handles all canvas drawing operations (scale, legend, roads)."""
    
    def __init__(self, map_widget):
        self.map_widget = map_widget
        self.canvas = map_widget.canvas
    
    def draw_scale(self):
        """Draw scale bar on canvas."""
        self.canvas.delete("scale")
        w, h = self.map_widget.winfo_width(), self.map_widget.winfo_height()
        if w < 10 or h < 10:
            return False
        
        x1, y1, x2, y2 = 20, h - 30, 120, h - 30
        meters = self._pixels_to_meters(100)
        self.canvas.create_line(x1, y1, x2, y2, fill="white", width=3, tags="scale")
        self.canvas.create_line(x1, y1 - 5, x1, y1 + 5, fill="white", width=3, tags="scale")
        self.canvas.create_line(x2, y2 - 5, x2, y2 + 5, fill="white", width=3, tags="scale")
        self.canvas.create_text(
            (x1 + x2) // 2, y1 - 10, 
            text=f"{meters:.0f} m",
            fill="white", font=("Arial", 10, "bold"), tags="scale"
        )
        return True
    
    def draw_legend(self, legend_items, legend_config):
        """Draw legend with specified items."""
        self.canvas.delete("legend")
        w, h = self.map_widget.winfo_width(), self.map_widget.winfo_height()
        
        if w < 10 or h < 10 or not legend_items:
            return False
        
        start_x = 20
        current_y = h - 180
        line_length = 40
        spacing = 30
        amount_to_draw = len(legend_items)
        
        # Draw background box
        box_left = start_x - 15
        box_right = start_x + line_length + 130
        box_top = current_y - 20
        box_bottom = current_y + (spacing * amount_to_draw) +10
        
        self.canvas.create_rectangle(
            box_left, box_top, box_right, box_bottom,
            fill="#1e1e1e", outline="black", width=3, tags="legend"
        )
        
        # Draw title
        title_x = (box_left + box_right) / 2
        self.canvas.create_text(
            title_x, box_top + 10,
            text="Legenda", fill="white", font=("Arial", 10, "bold"),
            tags="legend"
        )
        
        current_y += spacing
        
        # Draw legend items
        for item in legend_items:
            current_y = self._draw_legend_item(item, start_x, current_y, line_length, 
                                              spacing, legend_config)
        
        return True
    
    def _draw_legend_item(self, item, start_x, current_y, line_length, spacing, legend_config):
        """Draw a single legend item."""
        nwb_line = legend_config.get("NWBLine")
        help_line = legend_config.get("helpLine")
        calc_marker = legend_config.get("calcMarker")
        pos_marker = legend_config.get("posMarker")
        nwb_settings = legend_config.get("NWBLineSettings", {1: "#FFD700", 2: 5})
        help_settings = legend_config.get("helpLineSettings", {1: "#FF6600", 2: 5})
        
        if item == nwb_line:
            self._draw_line_legend(start_x, current_y, line_length, 
                                  nwb_settings[1], nwb_settings[2], "= Wegvak lijn")
            return current_y + spacing
        
        elif item == help_line:
            self._draw_line_legend(start_x, current_y, line_length,
                                  help_settings[1], help_settings[2], "= Hulplijn berekening")
            return current_y + spacing
        
        elif item == calc_marker:
            self._draw_marker_legend(start_x, current_y, "blue", "= Berekende posities")
            return current_y + spacing
        
        elif item == pos_marker:
            self._draw_marker_legend(start_x, current_y, "red", "= Positie kegelrobot")
            return current_y + spacing
        
        return current_y
    
    def _draw_line_legend(self, x, y, length, color, width, text):
        """Draw line legend item."""
        self.canvas.create_line(x, y, x + length, y, fill=color, width=width, tags="legend")
        self.canvas.create_text(x + length + 10, y, text=text, anchor="w", 
                               fill="white", tags="legend")
    
    def _draw_marker_legend(self, x, y, color, text):
        """Draw marker legend item."""
        self.canvas.create_oval(x, y - 8, x + 16, y + 8, fill=color, 
                               outline="black", width=2, tags="legend")
        self.canvas.create_text(x + 25, y, text=text, anchor="w", 
                               fill="white", tags="legend")
    
    def draw_roads(self, polylines, tag, color, width):
        """Draw road polylines on canvas."""
        self.canvas.delete(tag)
        
        if not polylines:
            return False
        
        for polyline in polylines:
            pts = []
            for lat, lon in polyline:
                try:
                    cx, cy = self._latlon_to_canvas(lat, lon)
                    pts.extend([cx, cy])
                except Exception:
                    pass
            
            if len(pts) >= 4:
                self.canvas.create_line(
                    *pts, fill=color, width=width, tags=tag,
                    capstyle="round", joinstyle="round"
                )
        
        self.canvas.tag_raise(tag)
        return True
    
    def draw_marker_arrows(self, marker, direction, tag, arrow_length=50):
        """Draw direction arrow for marker."""
        try:
            cx, cy = marker.get_canvas_pos(marker.position)
            self.canvas.delete(tag)
            angle_rad = math.radians(direction)
            self.canvas.create_line(
                cx, cy,
                cx + arrow_length * math.cos(angle_rad),
                cy + arrow_length * math.sin(angle_rad),
                fill="green", width=5, tags=tag, arrow=customtkinter.LAST
            )
            return True
        except Exception:
            return False
    
    def clear_canvas_tag(self, tag):
        """Clear all items with given tag."""
        self.canvas.delete(tag)
    
    def _pixels_to_meters(self, pixels):
        """Convert pixel distance to meters based on zoom and latitude."""
        zoom = self.map_widget.zoom
        lat = self.map_widget.get_position()[0]
        return pixels * (156543.03 * math.cos(math.radians(lat))) / (2 ** zoom)
    
    def _latlon_to_canvas(self, lat, lon):
        """Convert lat/lon to canvas coordinates."""
        zoom = self.map_widget.zoom
        tile_x = (lon + 180) / 360 * (2 ** zoom)
        sin_lat = math.sin(math.radians(lat))
        tile_y = (1 - math.log((1 + sin_lat) / (1 - sin_lat)) / (2 * math.pi)) / 2 * (2 ** zoom)
        upper_left_x, upper_left_y = self.map_widget.upper_left_tile_pos
        cx = (tile_x - upper_left_x) * self.map_widget.tile_size
        cy = (tile_y - upper_left_y) * self.map_widget.tile_size
        return cx, cy
