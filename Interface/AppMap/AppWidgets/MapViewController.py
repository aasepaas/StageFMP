

class MapViewController:
    """Manages map pan, zoom, and viewport operations."""
    
    def __init__(self, map_widget):
        self.map_widget = map_widget
        self.max_zoom = 21
    
    def set_tile_server(self, tile_type):
        """Change tile server based on type."""
        if tile_type == "Map normaal":
            self.max_zoom = 20
            self.map_widget.set_tile_server(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
                max_zoom=20
            )
        elif tile_type == "Map satelliet":
            self.max_zoom = 21
            self.map_widget.set_tile_server(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                max_zoom=21
            )
    
    def enforce_zoom(self):
        """Enforce maximum zoom level to prevent zooming in too far."""
        if self.map_widget.zoom > self.max_zoom:
            self.map_widget.set_zoom(self.max_zoom)
    
    def get_viewport_bbox(self):
        """Get bounding box of current viewport, used for road data fetching."""
        w = self.map_widget.winfo_width()
        h = self.map_widget.winfo_height()
        
        if w < 10 or h < 10:
            return None
        
        try:
            lat_nw, lon_nw = self.map_widget.convert_canvas_coords_to_decimal_coords(0, 0)
            lat_se, lon_se = self.map_widget.convert_canvas_coords_to_decimal_coords(w, h)
        except Exception as e:
            print("EXCEPTION from mapviewcontroller: ", e)
            return None
        
        return (min(lat_nw, lat_se), min(lon_nw, lon_se),
                max(lat_nw, lat_se), max(lon_nw, lon_se))
    
    @staticmethod
    def bbox_contains(outer, inner):
        """Check if outer bbox contains inner bbox."""
        return (outer[0] <= inner[0] and outer[1] <= inner[1] and
                outer[2] >= inner[2] and outer[3] >= inner[3])
    
    def go_to_coordinates(self, lat, lon, zoom=19):
        """Pan and zoom to specific coordinates."""
        self.map_widget.set_position(lat, lon)
        self.map_widget.set_zoom(zoom)
