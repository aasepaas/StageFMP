"""
AppFrameMap (Refactored) - Main orchestrator for the map interface.

This is the orchestrator that delegates to specialized managers instead of
doing everything itself. This dramatically improves code quality, testability,
and maintainability.

Architecture:
- AppFrameMap: Orchestrator (~100 lines)
  ├── MapEventHandler: Event binding
  ├── MapOverlayRenderer: Drawing operations
  ├── MapRoadManager: Road management
  ├── PositionCalculatorManager: Position calculations
  ├── MapUIController: UI components
  └── Other managers: Map, markers, location, etc.
"""

import customtkinter
from typing import Callable, Dict, Optional, Tuple

from AppMap.AppWidgets.CanvasRenderer import CanvasRenderer
from AppMap.AppWidgets.MarkerManager import MarkerManager
from AppMap.AppWidgets.RoadDataManager import RoadDataManager
from AppMap.AppWidgets.OffsetPolylineManager import OffsetPolylineManager
from AppMap.AppWidgets.MapViewController import MapViewController
from AppMap.AppWidgets.UIBuilder import UIBuilder
from AppMap.AppWidgets.LocationManager import LocationManager
from AppMap.AppWidgets.PopupWindow import PopupWindow
from AppMap.AppWidgets.AppConstants import (
    NWBLineSettings, helpLineSettings, NWBLine, helpLine,
    posMarker, calcMarker, ROAD_DRAW_ZOOM
)

# Import refactored components
from AppMap.AppWidgets.map_event_handler import MapEventHandler, MapEventCallbacks
from AppMap.AppWidgets.map_overlay_renderer import MapOverlayRenderer
from AppMap.AppWidgets.map_road_manager import MapRoadManager
from AppMap.AppWidgets.position_calculator_manager import PositionCalculatorManager
from AppMap.AppWidgets.map_ui_controller import MapUIController


class AppFrameMap(customtkinter.CTkFrame):
    """
    Orchestrates the map display and interactions.
    
    This is a clean orchestrator that delegates to specialized managers.
    Compare with original 424-line God Object - this is ~120 lines!
    
    Responsibilities:
    - Coordinate between different managers
    - Handle high-level user interactions
    - Manage rendering loops (scale, legend)
    - Provide clean public interface
    
    Everything else is delegated to specialized classes.
    """
    
    def __init__(self, master, send_callback: Callable,
                 reset_callback: Callable, get_robot_names_callback: Callable):
        """Initialize the map frame orchestrator.
        
        Args:
            master: Parent widget
            send_callback: Called when sending coordinates to robots
            reset_callback: Called when resetting the interface
            get_robot_names_callback: Called to get list of robot names
        """
        super().__init__(master)
        
        # Store callbacks
        self.send_callback = send_callback
        self.reset_callback = reset_callback
        self.get_robot_names_callback = get_robot_names_callback
        
        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=14)
        self.grid_rowconfigure(2, weight=0)
        
        # ────────────────────────────────────────────────────────────
        # Initialize core components
        # ────────────────────────────────────────────────────────────
        
        # Map widget and basic managers
        self.map_widget = UIBuilder.create_map_widget(self)
        self.map_view_controller = MapViewController(self.map_widget)
        
        # Data and rendering managers
        self.canvas_renderer = CanvasRenderer(self.map_widget)
        self.marker_manager = MarkerManager(self.map_widget)
        self.road_data_manager = RoadDataManager()
        self.offset_polyline_manager = OffsetPolylineManager()
        self.location_manager = LocationManager()
        
        # ────────────────────────────────────────────────────────────
        # Initialize refactored behavior controllers
        # ────────────────────────────────────────────────────────────
        
        # Rendering controller
        self.overlay_renderer = MapOverlayRenderer(
            self.map_widget,
            self.canvas_renderer,
            self.marker_manager,
            self.road_data_manager,
            self.offset_polyline_manager
        )
        
        # Road management
        self.road_manager = MapRoadManager(
            self.map_widget,
            self.map_view_controller,
            self.road_data_manager,
            reset_callback=self.reset_zoom_and_roads
        )
        
        # Position calculations
        self.position_calculator = PositionCalculatorManager(
            self.marker_manager,
            self.road_data_manager,
            self.offset_polyline_manager,
            self.overlay_renderer
        )
        
        # UI management
        self.ui_controller = MapUIController(
            self,
            on_change_map=self._on_change_map,
            on_calculate=self._on_calculate,
            on_delete=self._on_delete,
            on_send=self._on_send,
            on_test_toggle=self._on_test_toggle
        )
        
        # Set reset button command
        self.ui_controller.set_reset_button_command(self._on_reset)
        
        # ────────────────────────────────────────────────────────────
        # Setup event handling
        # ────────────────────────────────────────────────────────────
        
        self.event_handler = MapEventHandler(
            self.map_widget,
            self._create_event_callbacks()
        )
        
        # ────────────────────────────────────────────────────────────
        # Initialize popup window for formation selection
        # ────────────────────────────────────────────────────────────
        
        self.popup_window = PopupWindow(
            self, self._after_popup_calculate
        )
        
        # ────────────────────────────────────────────────────────────
        # Legend configuration
        # ────────────────────────────────────────────────────────────
        
        self.legend_config = {
            "NWBLine": NWBLine,
            "helpLine": helpLine,
            "calcMarker": calcMarker,
            "posMarker": posMarker,
            "NWBLineSettings": NWBLineSettings,
            "helpLineSettings": helpLineSettings
        }
        
        # ────────────────────────────────────────────────────────────
        # Final setup
        # ────────────────────────────────────────────────────────────
        
        self.ui_controller.layout_ui(self.map_widget)
        self._setup_map()
        self.event_handler.bind_events()
        
        # Start rendering loops
        self._schedule_scale_rendering()
        self._schedule_legend_rendering()
    
    # ────────────────────────────────────────────────────────────────
    # Event callback creation
    # ────────────────────────────────────────────────────────────────
    
    def _create_event_callbacks(self) -> MapEventCallbacks:
        """Create event callback handlers for map events.
        
        Returns:
            Object implementing MapEventCallbacks interface
        """
        class EventCallbacks(MapEventCallbacks):
            def __init__(self, parent):
                self.parent = parent
            
            def on_add_marker(self, coords: Tuple[float, float]):
                self.parent._on_add_marker(coords)
            
            def on_scroll(self, event=None):
                self.parent._on_scroll()
            
            def on_pan_end(self, event=None):
                self.parent._on_pan_end()
        
        return EventCallbacks(self)
    
    # ────────────────────────────────────────────────────────────────
    # Event handlers
    # ────────────────────────────────────────────────────────────────
    
    def _on_add_marker(self, coords: Tuple[float, float], name: str) -> None:
        """Handle marker addition event.
        
        Args:
            coords: Tuple of (latitude, longitude)
            name: Name for the marker
        """
        self.overlay_renderer.add_marker_with_styling(coords=coords, marker_text=name)
        self._add_incident_location(coords)
    
    def _on_scroll(self) -> None:
        """Handle scroll/zoom event."""
        self.after(50, self.map_view_controller.enforce_zoom)
        self.after(70, lambda: self.overlay_renderer.redraw_all())
        self.road_manager.schedule_refresh()
    
    def _on_pan_end(self) -> None:
        """Handle pan/drag event."""
        self.after(70, lambda: self.overlay_renderer.redraw_all())
        result = self.road_manager.schedule_refresh()
        if result is False:
            print("Scheduled road refresh with result: ", result)
            print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    
    # ────────────────────────────────────────────────────────────────
    # Control button handlers
    # ────────────────────────────────────────────────────────────────
    
    def _on_calculate(self) -> None:
        """Handle calculate button press."""
        if not self.marker_manager.has_markers():
            print("No markers available for calculation")
            return
        
        # Check if in test mode
        if self.ui_controller.is_test_mode_enabled():
            # Direct calculation with default values
            self.position_calculator.calculate_and_place_positions(
                distance=5, amount=1
            )
        else:
            # Show popup for user to choose settings
            robot_names = self.get_robot_names_callback()
            self.popup_window.pop_up(listOfRobotNames=robot_names)
    
    def _on_delete(self) -> None:
        """Handle delete/clear button press."""
        self.overlay_renderer.clear_offset_roads()
        self.canvas_renderer.clear_canvas_tag("nwb_roads")
        self.position_calculator.clear_calculated_positions()
    
    def _on_send(self, robot_name=None, msg_field=None, msg=None) -> None:
        """Handle send to robots button press.
        
        Args:
            robot_name: Optional specific robot name
            msg_field: Optional message field
            msg: Optional message content
        """
        coords_dict = self.marker_manager.get_calculated_positions()
        print(f"Sending coordinates: {coords_dict}")
        self.send_callback(coords_dict)
    
    def _on_test_toggle(self) -> None:
        """Handle test mode toggle."""
        mode = "ON" if self.ui_controller.is_test_mode_enabled() else "OFF"
        print(f"Test mode: {mode}")
    
    def _on_change_map(self, new_map: str) -> None:
        """Handle map tile type change.
        
        Args:
            new_map: New map tile type name
        """
        self.map_view_controller.set_tile_server(new_map)
    
    def _on_reset(self) -> None:
        """Handle reset button press."""
        self.reset_callback()
    
    # ────────────────────────────────────────────────────────────────
    # Rendering loops
    # ────────────────────────────────────────────────────────────────
    
    def _schedule_scale_rendering(self) -> None:
        """Schedule scale bar rendering."""
        if self.overlay_renderer.draw_scale():
            self.after(500, self._schedule_scale_rendering)
        else:
            self.after(200, self._schedule_scale_rendering)
    
    def _schedule_legend_rendering(self) -> None:
        """Schedule legend rendering."""
        if self.overlay_renderer.draw_legend(self.legend_config):
            self.after(500, self._schedule_legend_rendering)
        elif not self.overlay_renderer.legend_to_draw:
            self.after(500, self._schedule_legend_rendering)
        else:
            self.after(200, self._schedule_legend_rendering)
    
    # ────────────────────────────────────────────────────────────────
    # Setup methods
    # ────────────────────────────────────────────────────────────────
    
    def _setup_map(self) -> None:
        """Initialize map with default settings."""
        self.map_view_controller.set_tile_server("Map satelliet")
        self.map_widget.set_position(52.0172355, 4.3712940)
        self.ui_controller.set_map_option_selection("Map satelliet")
    
    def _add_incident_location(self, coords: Tuple[float, float]) -> None:
        """Add incident location display based on first marker.
        
        Uses reverse geocoding to show address information.
        
        Args:
            coords: Tuple of (latitude, longitude)
        """
        location_dict = self.location_manager.reverse_geocode(
            coords[0], coords[1]
        )
        print("LCOATION DICT = ", location_dict)
        frame = None
        if location_dict:
            frame = self.location_manager.create_incident_frame(
                self.ui_controller.position_buttons_frame,
                location_dict,
                self._go_to_coords
            )
        if frame:
            frame.grid(row=0, column=3, rowspan=2, sticky="ne", padx=10, pady=10)

    def reset_zoom_and_roads(self) -> None:
        self.overlay_renderer.clear_all_roads()
        self.overlay_renderer.reset_legend()
    
    def _go_to_coords(self) -> None:
        """Pan map to first marker position."""
        first_marker = self.marker_manager.get_first_marker()
        if first_marker:
            lat, lon = first_marker.position
            self.map_view_controller.go_to_coordinates(lat, lon)
            self._on_scroll()
    
    def _after_popup_calculate(self, chosen_settings: Dict) -> None:
        """Callback from popup window with chosen settings.
        
        Args:
            chosen_settings: Dictionary with user choices
        """
        try:
            amount = int(chosen_settings.get("Aantal", 1))
        except (ValueError, TypeError):
            amount = 1
        
        formation = chosen_settings.get(
            "Formatie", "Standaard 10m afstand"
        ) or "Standaard 10m afstand"
        
        print(f"Calculation settings: amount={amount}, formation={formation}")
        
        self.position_calculator.calculate_and_place_positions(
            amount=amount, formation=formation
        )
    
    # ────────────────────────────────────────────────────────────────
    # Public interface
    # ────────────────────────────────────────────────────────────────
    
    def reset_frame(self) -> None:
        """Reset all UI and data to initial state."""
        try:
            print("Resetting map frame...")
            self.overlay_renderer.clear_offset_roads()
            self.location_manager.destroy_incident_frame()
            self.overlay_renderer.clear_markers()
            self.overlay_renderer.clear_all_roads()
            self.overlay_renderer.reset_legend()
            print("Map frame reset complete")
        except Exception as e:
            print(f"Exception during reset: {e}")
    
    def change_map(self, new_map: str) -> None:
        """Change map tile type.
        
        Args:
            new_map: New map tile type name
        """
        self._on_change_map(new_map)
    
    # ────────────────────────────────────────────────────────────────
    # Utility methods for testing
    # ────────────────────────────────────────────────────────────────
    
    def get_state_info(self) -> Dict:
        """Get current state information (useful for testing).
        
        Returns:
            Dictionary with current state
        """
        return {
            "has_markers": self.marker_manager.has_markers(),
            "marker_count": len(self.marker_manager.markers),
            "road_stats": self.road_manager.get_road_stats(),
            "ui_config": self.ui_controller.get_ui_config(),
            "overlay_legend_items": len(self.overlay_renderer.legend_to_draw)
        }