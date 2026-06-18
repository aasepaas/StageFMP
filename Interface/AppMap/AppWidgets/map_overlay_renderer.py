from typing import Dict, List, Optional, Set, Tuple
from AppMap.AppWidgets.AppConstants import calcMarker, posMarker
from AppMap.AppWidgets.AppConstants import ROAD_DRAW_ZOOM, NWBLineSettings, NWBLine

# Canvas tags and markers
NWBLine = "NWBLine"
helpLine = "helpLine"
posMarker = "posMarker"
calcMarker = "calcMarker"

class MapOverlayRenderer:
    """Renders all overlay elements on the map.
    
    Handles:
    - Marker drawing and styling
    - Road polyline drawing (cached and offset)
    - Scale bar drawing
    - Legend drawing
    - Marker direction arrows
    """
    
    def __init__(self, map_widget, canvas_renderer, marker_manager,
                 road_data_manager, offset_polyline_manager):
        """Initialize overlay renderer.
        
        Args:
            map_widget: The map widget instance
            canvas_renderer: CanvasRenderer for drawing operations
            marker_manager: MarkerManager for marker operations
            road_data_manager: RoadDataManager for road data
            offset_polyline_manager: OffsetPolylineManager for offset polylines
        """
        self.map_widget = map_widget
        self.canvas_renderer = canvas_renderer
        self.marker_manager = marker_manager
        self.road_data_manager = road_data_manager
        self.offset_polyline_manager = offset_polyline_manager
        
        # State
        self.legend_to_draw: Set[str] = set()
        self.adding_marker = False
        
        # Tags for canvas elements
        self._ROAD_TAG = "nwb_roads"
        self._OFFSET_TAG = "vlucht_strook_roads"
    
    # ────────────────────────────────────────────────────────────────
    # Marker operations
    # ────────────────────────────────────────────────────────────────
    
    def add_marker_with_styling(
        self,
        coords: Tuple[float, float],
        direction: Optional[float] = None,
        marker_text: str = "new mark",
        **styling_kwargs
    ) -> None:
        """Add marker with appropriate styling."""    
        self.adding_marker = True
        self._delete_position(marker_text)
        
        # Determine if this is a calculated marker and apply styling
        kwargs = {}
        if "calculated" in marker_text:
            # Import colors here to avoid circular imports
            from AppMap.AppWidgets.AppConstants import (
                marker_color_outside, marker_color_circle, marker_color_text
            )
            kwargs["marker_color_outside"] = marker_color_outside
            kwargs["marker_color_circle"] = marker_color_circle
            kwargs["text_color"] = marker_color_text
            self.legend_to_draw.add(calcMarker)
        
        # Add marker to manager
        self.marker_manager.add_marker(coords, direction, marker_text, **kwargs)
        
        # Update display
        self.map_widget.update_idletasks()
        self.adding_marker = False
        self.draw_marker_arrows()
        self.legend_to_draw.add(posMarker)
    
    def draw_marker_arrows(self) -> None:
        """Draw direction arrows for all markers.
        
        Indicates the direction each marker is facing.
        Only draws if not currently adding a new marker.
        """
        if self.adding_marker:
            return
        
        for marker, (line_tag, direction) in list(
            self.marker_manager.marker_lines.items()
        ):
            if not marker.deleted and direction is not None:
                self.canvas_renderer.draw_marker_arrows(
                    marker, direction, line_tag
                )
    
    # ────────────────────────────────────────────────────────────────
    # Road drawing
    # ────────────────────────────────────────────────────────────────
    
    def draw_roads(self, zoom_level: int) -> None:
        """Draw cached road polylines based on zoom level.
        
        Only draws roads when zoomed in enough to prevent clutter.
        Line width scales with zoom level.
        
        Args:
            zoom_level: Current map zoom level (integer)
        """
        
        if zoom_level >= ROAD_DRAW_ZOOM:
            line_width = max(1, zoom_level - 16)
            self.canvas_renderer.draw_roads(
                self.road_data_manager.road_polylines,
                self._ROAD_TAG,
                NWBLineSettings[1],
                line_width
            )
            self.legend_to_draw.add(NWBLine)
    
    def draw_offset_roads(self, zoom_level: int) -> None:
        """Draw offset vluchtstrook polyline.
        
        The offset line is used for robot position calculations.
        Only draws when zoomed in enough to prevent clutter.
        
        Args:
            zoom_level: Current map zoom level (integer)
        """
        from AppMap.AppWidgets.AppConstants import ROAD_DRAW_ZOOM, helpLineSettings, helpLine
        
        if zoom_level >= ROAD_DRAW_ZOOM:
            line_width = max(1, zoom_level - 16)
            offset_polyline = self.offset_polyline_manager.get_offset_polyline()
            
            if offset_polyline:
                self.canvas_renderer.draw_roads(
                    [offset_polyline],
                    self._OFFSET_TAG,
                    helpLineSettings[1],
                    line_width
                )
                self.legend_to_draw.add(helpLine)
    
    # ────────────────────────────────────────────────────────────────
    # Scale and legend
    # ────────────────────────────────────────────────────────────────
    
    def draw_scale(self) -> bool:
        """Draw scale bar on the map.
        
        Returns:
            True if scale was drawn, False otherwise
        """
        return self.canvas_renderer.draw_scale()
    
    def draw_legend(self, legend_config: Dict) -> bool:
        """Draw legend with current items.
        
        Args:
            legend_config: Dictionary with legend configuration
        
        Returns:
            True if legend was drawn, False otherwise
        """
        return self.canvas_renderer.draw_legend(
            self.legend_to_draw, legend_config
        )
    
    # ────────────────────────────────────────────────────────────────
    # Batch operations
    # ────────────────────────────────────────────────────────────────
    
    def redraw_all(self, zoom_level: Optional[int] = None) -> None:
        """Redraw all overlays.
        
        Called after pan or zoom events to refresh display.
        
        Args:
            zoom_level: Optional zoom level. If not provided, uses current
        """
        if zoom_level is None:
            zoom_level = int(self.map_widget.zoom)
        
        self.draw_marker_arrows()
        self.draw_roads(zoom_level)
        self.draw_offset_roads(zoom_level)
    
    # ────────────────────────────────────────────────────────────────
    # Cleanup operations
    # ────────────────────────────────────────────────────────────────
    
    def clear_offset_roads(self) -> None:
        """Clear offset roads from canvas and data."""
        self.offset_polyline_manager.clear()
    
    def clear_all_roads(self) -> None:
        """Clear all road overlays from canvas."""
        try:
            self.canvas_renderer.clear_canvas_tag(self._ROAD_TAG)
            self.canvas_renderer.clear_canvas_tag(self._OFFSET_TAG)
        except Exception as e:
            print("EXCEPTION while clearing roads: ", e)
    
    def clear_markers(self) -> None:
        """Clear all markers from map."""
        try:
            self.marker_manager.delete_all_markers()
        except Exception as e:
            print("EXCEPTION while clearing markers: ", e)

    def reset_legend(self) -> None:
        """Reset legend items."""
        try:
            #self.legend_to_draw.clear()
            self.legend_to_draw.discard(NWBLine)
            self.legend_to_draw.discard(helpLine)
            self.legend_to_draw.discard(posMarker)
            self.legend_to_draw.discard(calcMarker)
        except Exception as e:
            print("EXCEPTION while resetting legend: ", e)
    
    # ────────────────────────────────────────────────────────────────
    # Internal helper methods
    # ────────────────────────────────────────────────────────────────
    
    def _delete_position(self, name_to_delete: str = "calculated") -> None:
        """Delete positions by name pattern.
        
        Args:
            name_to_delete: Pattern to match in marker names (default: "calculated")
        """
        from AppMap.AppWidgets.AppConstants import calcMarker
        
        self.marker_manager.delete_markers_by_name(name_to_delete)
        
        # Clear associated canvas tags
        for marker, (line_tag, _) in list(self.marker_manager.marker_lines.items()):
            if name_to_delete in line_tag:
                self.canvas_renderer.clear_canvas_tag(line_tag)
        
        # Update legend
        if name_to_delete == "calculated":
            self.legend_to_draw.discard(calcMarker)
    
    def get_legend_items(self) -> Set[str]:
        """Get current legend items to draw.
        
        Returns:
            Set of legend item identifiers
        """
        return self.legend_to_draw.copy()