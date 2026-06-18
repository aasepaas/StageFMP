class MarkerManager:
    """Manages marker creation, storage, and deletion."""
    
    def __init__(self, map_widget):
        self.map_widget = map_widget
        self.markers_dict = {}
        self.marker_lines = {}
    
    def add_marker(self, coords, direction=None, marker_text="new mark", **kwargs):
        """Add a marker to the map."""
        new_marker = self.map_widget.set_marker(coords[0], coords[1], text=marker_text, **kwargs)
        self.markers_dict[new_marker] = marker_text
        self.marker_lines[new_marker] = [marker_text, direction]
        return new_marker
    
    def delete_markers_by_name(self, name_pattern):
        """Delete markers matching name pattern."""
        for marker in [m for m, t in self.markers_dict.items() if name_pattern in t]:
            self.markers_dict.pop(marker, None)
            marker.delete()
        
        for marker in [m for m, (t, _) in self.marker_lines.items() if name_pattern in t]:
            self.marker_lines.pop(marker, None)
    
    def delete_all_markers(self):
        """Delete all markers."""
        for marker in list(self.markers_dict.keys()):
            marker.delete()
        self.markers_dict.clear()
        self.marker_lines.clear()
    
    def get_calculated_positions(self):
        """Get all calculated position markers as dict."""
        coords_dict = {}
        for marker, name in self.markers_dict.items():
            if "calc" in name:
                coords_dict[name] = marker.position
            else:
                coords_dict[name] = None
        return coords_dict
    
    def get_first_marker(self):
        """Get the first marker."""
        if self.markers_dict:
            return list(self.markers_dict.keys())[0]
        return None
    
    def has_markers(self):
        """Check if any markers exist."""
        return len(self.markers_dict) > 0
