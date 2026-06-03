import customtkinter
import threading
from AppMap.AppWidgets.CanvasRenderer import CanvasRenderer
from AppMap.AppWidgets.MarkerManager import MarkerManager
from AppMap.AppWidgets.RoadDataManager import RoadDataManager
from AppMap.AppWidgets.OffsetPolylineManager import OffsetPolylineManager
from AppMap.AppWidgets.PositionCalculator import PositionCalculator
from AppMap.AppWidgets.MapViewController import MapViewController
from AppMap.AppWidgets.UIBuilder import UIBuilder
from AppMap.AppWidgets.LocationManager import LocationManager
from AppMap.AppWidgets.PopupWindow import PopupWindow
from AppMap.AppWidgets.AppConstants import (
    marker_color_outside, marker_color_circle, marker_color_text,
    NWBLineSettings, helpLineSettings, NWBLine, helpLine,
    posMarker, calcMarker, ROAD_DRAW_ZOOM
)


class AppFrameMap(customtkinter.CTkFrame):
    """Main frame coordinating map, markers, roads, and UI."""
    
    def __init__(self, master, sendCallback, resetCallback, getRobotNames):
        super().__init__(master)
        
        self.sendMessageCallback = sendCallback
        self.resetInterface = resetCallback
        self.getRobotNames = getRobotNames
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=14)
        self.grid_rowconfigure(2, weight=0)
        
        # Initialize managers and controllers
        self.map_widget = UIBuilder.create_map_widget(self)
        self.map_view_controller = MapViewController(self.map_widget)
        self.canvas_renderer = CanvasRenderer(self.map_widget)
        self.marker_manager = MarkerManager(self.map_widget)
        self.road_data_manager = RoadDataManager()
        self.offset_polyline_manager = OffsetPolylineManager()
        self.location_manager = LocationManager()
        
        # UI State
        self.adding_marker = False
        self.legend_to_draw = set()
        self.road_refresh_job = None
        
        # Constants
        self._ROAD_TAG = "nwb_roads"
        self._OFFSET_TAG = "vlucht_strook_roads"
        self.ROAD_DRAW_ZOOM = ROAD_DRAW_ZOOM
        
        # Legend configuration
        self.legend_config = {
            "NWBLine": NWBLine,
            "helpLine": helpLine,
            "calcMarker": calcMarker,
            "posMarker": posMarker,
            "NWBLineSettings": NWBLineSettings,
            "helpLineSettings": helpLineSettings
        }
        
        self._setup_ui()
        self._setup_map()
        self._bind_events()
        
        # Popup window
        self.popupWindow = PopupWindow(self, self.AfterPopUpToCalculate)
    
    def _setup_ui(self):
        """Set up UI components."""
        # Title label
        self.label = customtkinter.CTkLabel(
            self, text="Map:", fg_color='#01a6f8',
            width=100, height=20, font=('Bold', 28), corner_radius=5
        )
        self.label.grid(row=0, column=0, sticky="nw", padx=(8, 8), pady=(5, 5))
        
        # Map widget
        self.map_widget.grid(row=1, column=0, columnspan=3, sticky="nswe",
                            padx=(10, 10), pady=(0, 0))
        
        # Control frame
        self.control_frame, self.map_option_menu = UIBuilder.create_control_frame(
            self, self.change_map
        )
        self.control_frame.grid(row=2, column=0, sticky="nw", padx=10, pady=10)
        
        customtkinter.CTkButton(
            self.control_frame, text="Reset",
            command=self.ResetButtonPressed, border_color="black", 
            border_width=2, fg_color="red"
        ).grid(row=5, column=0, padx=10, pady=(0, 5), sticky="nw")
        
        # Position buttons frame
        self.controlFramePositionButtons, self.testPositionModeVar = \
            UIBuilder.create_position_buttons_frame(
                self,
                calculate_callback=self.CalculateButtonPressed,
                delete_callback=self.DeletePositionsButtonPressed,
                send_callback=self.SendMessagesToRobots,
                switch_test_callback=self.switchTest
            )
        self.controlFramePositionButtons.grid(row=2, column=1, columnspan=2, 
                                             sticky="nwse", padx=10, pady=10)
    
    def _setup_map(self):
        """Set up initial map settings."""
        self.map_view_controller.set_tile_server("Map satelliet")
        self.map_widget.set_position(52.0172355, 4.3712940)
        self.map_option_menu.set("Map satelliet")
        
        self.after(500, self._draw_scale)
        self.after(500, self.DrawLegend)
    
    def _bind_events(self):
        """Bind event handlers."""
        self.map_widget.add_right_click_menu_command(
            label="Add Marker", command=self.AddMarker, pass_coords=True
        )
        
        self.map_widget.bind("<MouseWheel>", self._on_scroll)
        self.map_widget.canvas.bind("<MouseWheel>", self._on_scroll, add="+")
        
        self.map_widget.canvas.bind("<ButtonRelease-1>", self._on_pan_end, add="+")
        self.map_widget.canvas.bind("<B1-Motion>", self._on_pan_end, add="+")
        self.map_widget.canvas.bind("<Button-1>", self._on_pan_end, add="+")
    
    # ── Map control events ────────────────────────────────────────────────
    
    def change_map(self, new_map: str):
        """Change map tile type."""
        self.map_view_controller.set_tile_server(new_map)
    
    def _on_scroll(self, event=None):
        """Handle scroll (zoom) events."""
        self.after(50, self._enforce_zoom)
        self.after(70, self._redraw_all)
        self._schedule_road_refresh()
    
    def _on_pan_end(self, event=None):
        """Handle pan events."""
        self.after(70, self._redraw_all)
        self._schedule_road_refresh()
    
    def _enforce_zoom(self):
        """Enforce maximum zoom level."""
        self.map_view_controller.enforce_zoom()
    
    def _redraw_all(self):
        """Redraw all overlays."""
        self._draw_marker_arrows()
        self._draw_cached_roads()
        self._draw_offset_roads()
    
    # ── Scale and legend ──────────────────────────────────────────────────
    
    def _draw_scale(self):
        """Draw scale bar."""
        if self.canvas_renderer.draw_scale():
            self.after(500, self._draw_scale)
        else:
            self.after(200, self._draw_scale)
    
    def DrawLegend(self):
        """Draw legend."""
        if self.canvas_renderer.draw_legend(self.legend_to_draw, self.legend_config):
            self.after(500, self.DrawLegend)
        elif not self.legend_to_draw:
            self.after(500, self.DrawLegend)
        else:
            self.after(200, self.DrawLegend)
    
    # ── Marker management ─────────────────────────────────────────────────
    
    def _draw_marker_arrows(self):
        """Draw direction arrows for markers."""
        if self.adding_marker:
            return
        
        for marker, (line_tag, direction) in list(self.marker_manager.marker_lines.items()):
            if not marker.deleted and direction is not None:
                self.canvas_renderer.draw_marker_arrows(marker, direction, line_tag)
    
    def AddMarker(self, coords, direction=None, markerText="new mark"):
        """Add a marker at coordinates."""
        self.adding_marker = True
        print("adding new marker:", coords)
        self.DeletePositions(markerText)
        
        kwargs = {}
        if "calculated" in markerText:
            kwargs["marker_color_outside"] = marker_color_outside
            kwargs["marker_color_circle"] = marker_color_circle
            kwargs["text_color"] = marker_color_text
            self.legend_to_draw.add(calcMarker)
        
        new_marker = self.marker_manager.add_marker(coords, direction, markerText, **kwargs)
        
        self.after(15, lambda: self._add_incident_location(coords))
        
        self.map_widget.update_idletasks()
        self.adding_marker = False
        self._draw_marker_arrows()
        self.legend_to_draw.add(posMarker)
    
    def _add_incident_location(self, coords):
        """Add incident location display."""
        location_dict = self.location_manager.reverse_geocode(coords[0], coords[1])
        if location_dict:
            frame = self.location_manager.create_incident_frame(
                self.controlFramePositionButtons,
                location_dict,
                self.GoToCoords
            )
            frame.grid(row=0, column=3, rowspan=2, sticky="ne", padx=10, pady=10)
    
    def DeletePositions(self, nameToDelete="calculated"):
        """Delete markers matching pattern."""
        self.marker_manager.delete_markers_by_name(nameToDelete)
        for marker in [m for m, (t, _) in self.marker_manager.marker_lines.items() 
                      if nameToDelete in t]:
            self.canvas_renderer.clear_canvas_tag(t)
        
        try:
            self.legend_to_draw.discard(calcMarker)
        except:
            pass
    
    def DeletePositionsButtonPressed(self):
        """Handle delete positions button press."""
        self.canvas_renderer.clear_canvas_tag(self._OFFSET_TAG)
        self.offset_polyline_manager.clear()
        self.DeletePositions()
    
    # ── Road management ──────────────────────────────────────────────────
    
    def _schedule_road_refresh(self):
        """Schedule road data refresh."""
        if self.road_refresh_job is not None:
            self.after_cancel(self.road_refresh_job)
        self.road_refresh_job = self.after(400, self._refresh_roads)
    
    def _refresh_roads(self):
        """Refresh road data based on viewport."""
        self.road_refresh_job = None
        zoom = self.map_widget.zoom
        zoom_int = int(zoom)
        self.map_widget.set_zoom(zoom_int)
        
        if zoom_int < self.ROAD_DRAW_ZOOM:
            self.canvas_renderer.clear_canvas_tag(self._ROAD_TAG)
            self.canvas_renderer.clear_canvas_tag(self._OFFSET_TAG)
            self.legend_to_draw.discard(NWBLine)
            self.legend_to_draw.discard(helpLine)
            return
        
        bbox = self.map_view_controller.get_viewport_bbox()
        if bbox is None:
            return
        
        if (self.road_data_manager.road_fetch_bbox is not None
                and MapViewController.bbox_contains(self.road_data_manager.road_fetch_bbox, bbox)
                and self.road_data_manager.has_data()):
            self._draw_cached_roads()
            self._draw_offset_roads()
            return
        
        if not self.road_data_manager.road_fetch_running:
            self.road_data_manager.road_fetch_running = True
            lat_min, lon_min, lat_max, lon_max = bbox
            dlat = (lat_max - lat_min) * 0.30
            dlon = (lon_max - lon_min) * 0.30
            fetch_bbox = (lat_min - dlat, lon_min - dlon,
                         lat_max + dlat, lon_max + dlon)
            
            threading.Thread(
                target=self.road_data_manager.fetch_roads_thread,
                args=(fetch_bbox,),
                daemon=True
            ).start()
    
    def _draw_cached_roads(self):
        """Draw cached road polylines."""
        if self.map_widget.zoom >= self.ROAD_DRAW_ZOOM:
            line_width = max(1, int(self.map_widget.zoom) - 16)
            self.canvas_renderer.draw_roads(
                self.road_data_manager.road_polylines,
                self._ROAD_TAG,
                NWBLineSettings[1],
                line_width
            )
            self.legend_to_draw.add(NWBLine)
    
    def _draw_offset_roads(self):
        """Draw offset vluchtstrook polyline."""
        if self.map_widget.zoom >= self.ROAD_DRAW_ZOOM:
            line_width = max(1, int(self.map_widget.zoom) - 16)
            offset_polyline = self.offset_polyline_manager.get_offset_polyline()
            if offset_polyline:
                self.canvas_renderer.draw_roads(
                    [offset_polyline],
                    self._OFFSET_TAG,
                    helpLineSettings[1],
                    line_width
                )
                self.legend_to_draw.add(helpLine)
    
    # ── Position calculation ──────────────────────────────────────────────
    
    def switchTest(self):
        """Handle test mode switch."""
        print(self.testPositionModeVar.get())
    
    def CalculateButtonPressed(self):
        """Handle calculate button press."""
        if not self.marker_manager.has_markers():
            print("geen markers om op te berekenen")
            return
        
        test_mode = self.testPositionModeVar.get()
        robot_names = self.getRobotNames()
        
        if test_mode == "1":
            self.CalculatePositions(distance=5, amount=1, motherBotPos=1)
        else:
            self.popupWindow.pop_up(listOfRobotNames=robot_names)
    
    def CalculatePositions(self, distance=10, amount=1, motherBotPos=1):
        """Calculate robot positions along offset polyline."""
        first_marker = self.marker_manager.get_first_marker()
        if first_marker is None:
            return
        
        lat, lon = first_marker.position
        direction = self.marker_manager.marker_lines[first_marker][1]
        
        # Build offset polyline
        self.offset_polyline_manager.build_offset_polylines(
            lat, lon, self.road_data_manager.road_polylines
        )
        
        offset_polyline = self.offset_polyline_manager.get_offset_polyline()
        if offset_polyline is None:
            return
        
        # Calculate positions
        positions = PositionCalculator.calculate_positions(
            lat, lon, direction, offset_polyline, distance, amount
        )
        
        for i, (pos_lat, pos_lon, pos_direction) in enumerate(positions, 1):
            self.AddMarker((pos_lat, pos_lon), pos_direction, f"calculated{i}")
        
        self._draw_offset_roads()
    
    def SendMessagesToRobots(self, robotName=None, msgField=None, msg=None):
        """Send calculated positions to robots."""
        coords_dict = self.marker_manager.get_calculated_positions()
        print("coordsdict = ", coords_dict)
        self.sendMessageCallback(coords_dict)
    
    def GoToCoords(self):
        """Pan to first marker."""
        first_marker = self.marker_manager.get_first_marker()
        if first_marker:
            lat, lon = first_marker.position
            self.map_view_controller.go_to_coordinates(lat, lon)
            self._on_scroll()
    
    def AfterPopUpToCalculate(self, chosenSettings):
        """Handle popup window callback."""
        amount = 1
        try:
            amount = int(chosenSettings["Aantal"])
        except Exception:
            pass
        
        formation = chosenSettings["Formatie"]
        start_robot = chosenSettings["RobotStart"]
        print(f"volgende waardes zijn ingetikt: {amount}, {formation}, {start_robot}")
        self.CalculatePositions(amount=amount)
    
    def ResetButtonPressed(self):
        """Handle reset button press."""
        self.resetInterface()
    
    def Reset(self):
        """Reset all UI and data."""
        print("map reset")
        try:
            self.location_manager.destroy_incident_frame()
            self.marker_manager.delete_all_markers()
            self.canvas_renderer.clear_canvas_tag(self._OFFSET_TAG)
            self.offset_polyline_manager.clear()
            self.legend_to_draw.discard(posMarker)
            self.legend_to_draw.discard(calcMarker)
            self.legend_to_draw.discard(helpLine)
        except Exception as e:
            print(f"error hier is = {e}")
