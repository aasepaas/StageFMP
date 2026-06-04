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
        
        self.send_message_callback = sendCallback
        self.reset_interface_callback = resetCallback
        self.get_robot_names_callback = getRobotNames
        print(" nieuwe naam van sendcallback in appframemap = self.send_message_callback", self.send_message_callback)
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
        self.popup_window = PopupWindow(self, self._after_popop_to_calculate)
    
    def _setup_ui(self):
        """Init and setup up UI components internally."""
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
            command=self._reset_button_pressed, border_color="black", 
            border_width=2, fg_color="red"
        ).grid(row=5, column=0, padx=10, pady=(0, 5), sticky="nw")
        
        # Position buttons frame
        self.controlFramePositionButtons, self.testPositionModeVar = \
            UIBuilder.create_position_buttons_frame(
                self,
                calculate_callback=self._calculate_button_pressed,
                delete_callback=self._delete_position_button_pressed,
                send_callback=self._send_message_to_robots,
                switch_test_callback=self._switch_test
            )
        self.controlFramePositionButtons.grid(row=2, column=1, columnspan=2, 
                                             sticky="nwse", padx=10, pady=10)
    
    def _setup_map(self):
        """Init and set up initial map settings internally."""
        self.map_view_controller.set_tile_server("Map satelliet")
        self.map_widget.set_position(52.0172355, 4.3712940)
        self.map_option_menu.set("Map satelliet")
        
        self.after(500, self._draw_scale)
        self.after(500, self.DrawLegend)
    
    def _bind_events(self):
        """Bind mouse event handlers."""

        self.map_widget.add_right_click_menu_command(
            label="Add Marker", command=self.add_marker, pass_coords=True
        )
        #Mouse event: scroll for zooming, pan end for refreshing roads and markers
        self.map_widget.bind("<MouseWheel>", self._on_scroll)
        self.map_widget.canvas.bind("<MouseWheel>", self._on_scroll, add="+")
        
        self.map_widget.canvas.bind("<ButtonRelease-1>", self._on_pan_end, add="+")
        self.map_widget.canvas.bind("<B1-Motion>", self._on_pan_end, add="+")
        self.map_widget.canvas.bind("<Button-1>", self._on_pan_end, add="+")
    
    # ── Map control events ────────────────────────────────────────────────
    
    def change_map(self, new_map: str):
        """Change map tile type(satellite or normal view)."""
        self.map_view_controller.set_tile_server(new_map)
    
    def _on_scroll(self, event=None):
        """Handle scroll (zoom) events, necessary to not zoom in too far and the drawings of road markings etc are up to date."""
        self.after(50, self._enforce_zoom)
        self.after(70, self._redraw_all)
        self._schedule_road_refresh()
    
    def _on_pan_end(self, event=None):
        """Handle pan events, necessary to refresh the map display after scroll is done."""
        self.after(70, self._redraw_all)
        self._schedule_road_refresh()
    
    def _enforce_zoom(self):
        """Enforce maximum zoom level, to prevent zooming in too much."""
        self.map_view_controller.enforce_zoom()
    
    def _redraw_all(self):
        """Redraw all overlays, such as roadmarkings."""
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
        """Draw direction arrows for markers, to indicate which way the robot is facing."""
        if self.adding_marker:
            return
        
        for marker, (line_tag, direction) in list(self.marker_manager.marker_lines.items()):
            if not marker.deleted and direction is not None:
                self.canvas_renderer.draw_marker_arrows(marker, direction, line_tag)
    
    def add_marker(self, coords, direction=None, markerText="new mark"):
        """Add a marker at incoming coordinates."""
        self.adding_marker = True
        print("adding new marker:", coords)
        self._delete_position(markerText)
        
        #calculated markers look different and are added to the legend, so we need to pass different kwargs to the marker manager when adding them
        kwargs = {}
        if "calculated" in markerText:
            kwargs["marker_color_outside"] = marker_color_outside
            kwargs["marker_color_circle"] = marker_color_circle
            kwargs["text_color"] = marker_color_text
            self.legend_to_draw.add(calcMarker)
        
        new_marker = self.marker_manager.add_marker(coords, direction, markerText, **kwargs)
        #add incident location, with threading to make sure it doesnt block the UI,
        self.after(15, lambda: self._add_incident_location(coords))
        
        self.map_widget.update_idletasks()
        self.adding_marker = False
        self._draw_marker_arrows()
        self.legend_to_draw.add(posMarker)
    
    def _add_incident_location(self, coords):
        """Add incident location on UI, based on the first marker that was added."""
        location_dict = self.location_manager.reverse_geocode(coords[0], coords[1])
        if location_dict:
            frame = self.location_manager.create_incident_frame(
                self.controlFramePositionButtons,
                location_dict,
                self._go_to_coords
            )
            frame.grid(row=0, column=3, rowspan=2, sticky="ne", padx=10, pady=10)
    
    def _delete_position(self, nameToDelete="calculated"):
        """Delete markers by name, default are the calculated markers."""
        self.marker_manager.delete_markers_by_name(nameToDelete)
        for marker in [m for m, (t, _) in self.marker_manager.marker_lines.items() 
                      if nameToDelete in t]:
            self.canvas_renderer.clear_canvas_tag(t)
        
        try:
            self.legend_to_draw.discard(calcMarker)
        except Exception as e:
            print("EXCEPTION: ", e)
    
    def _delete_position_button_pressed(self):
        """Handle delete positions button press."""
        self.canvas_renderer.clear_canvas_tag(self._OFFSET_TAG)
        self.offset_polyline_manager.clear()
        self._delete_position()
    
    # ── Road management ──────────────────────────────────────────────────
    
    def _schedule_road_refresh(self):
        """Schedule road data refresh."""
        if self.road_refresh_job is not None:
            self.after_cancel(self.road_refresh_job)
        self.road_refresh_job = self.after(400, self._refresh_roads)
    
    def _refresh_roads(self):
        """Refresh road data based on viewport(zoom, lat, lon)."""
        self.road_refresh_job = None
        zoom = self.map_widget.zoom
        zoom_int = int(zoom)
        self.map_widget.set_zoom(zoom_int)
        #only fetch and draw roads when zoomed in enough, to prevent clutter and performance issues
        if zoom_int < self.ROAD_DRAW_ZOOM:
            self.canvas_renderer.clear_canvas_tag(self._ROAD_TAG)
            self.canvas_renderer.clear_canvas_tag(self._OFFSET_TAG)
            self.legend_to_draw.discard(NWBLine)
            self.legend_to_draw.discard(helpLine)
            return
        #get the current viewport bbox(lat,lon of the corners) to know which roads to fetch
        bbox = self.map_view_controller.get_viewport_bbox()
        if bbox is None:
            return
        
        if (self.road_data_manager.road_fetch_bbox is not None
                and MapViewController.bbox_contains(self.road_data_manager.road_fetch_bbox, bbox)
                and self.road_data_manager.has_data()):
            self._draw_cached_roads()
            self._draw_offset_roads()
            return
        
        #only fetch new roads when there isnt already a fetch running, to prevent multiple fetches at the same time which can cause performance issues and bugs
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
        """Draw cached road polylines on the canvas/map."""
        #only draw roads when zoomed in enough, to prevent clutter and performance issues, line width also scales with zoom level
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
        """Draw offset vluchtstrook polyline, the second line that is used for calculations of robot positions."""
        #only draw offset roads when zoomed in enough, to prevent clutter and performance issues, line width also scales with zoom level
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
    
    def _switch_test(self):
        """Handle test mode switch, only used for test cases where the calculation is needed without pop up window."""
        print(self.testPositionModeVar.get())
    
    def _calculate_button_pressed(self):
        """Handle calculate button press."""
        #only calculate when there are markers
        if not self.marker_manager.has_markers():
            print("geen markers om op te berekenen")
            return
        
        test_mode = self.testPositionModeVar.get()
        robot_names = self.get_robot_names_callback()
        # in test mode, we skip the popup and use default values for the calculation, else open popup window 
        if test_mode == "1":
            self._calculate_positions(distance=5, amount=1, motherBotPos=1)
        else:
            self.popup_window.pop_up(listOfRobotNames=robot_names)
    
    def _calculate_positions(self, distance=10, amount=1, motherBotPos=1, formation="Standaard 10m afstand",):
        """Calculate robot positions along offset polyline(vluchstrook line)."""

        first_marker = self.marker_manager.get_first_marker()
        if first_marker is None:
            return
        
        lat, lon = first_marker.position
        direction = self.marker_manager.marker_lines[first_marker][1]
        
        # Build offset polyline, draws the NWB line through the first marker 
        self.offset_polyline_manager.build_offset_polylines(
            lat, lon, self.road_data_manager.road_polylines
        )
        
        offset_polyline = self.offset_polyline_manager.get_offset_polyline()
        if offset_polyline is None:
            return
        
        # #Calculate position2s on the poly line based on the chosen settings from pop up window or test situation
        # positions = PositionCalculator.calculate_positions(
        #     lat, lon, direction, offset_polyline, distance, amount
        # )

        if "CROW" in formation:
            positions = PositionCalculator.calculate_crow_positions(
                lat, lon, direction, offset_polyline, amount
            )
        else:
            positions = PositionCalculator.calculate_positions(
                lat, lon, direction, offset_polyline, distance, amount
            )

        #Add the calculated positions as markers on the map, with different styling than the original position marker, and add them to the legend
        for i, (pos_lat, pos_lon, pos_direction) in enumerate(positions, 1):
            self.add_marker((pos_lat, pos_lon), pos_direction, f"calculated{i}")
        
        self._draw_offset_roads()
    
    def _send_message_to_robots(self, robotName=None, msgField=None, msg=None):
        """Send calculated positions to robots."""
        coords_dict = self.marker_manager.get_calculated_positions()
        print("coordsdict = ", coords_dict)
        self.send_message_callback(coords_dict)
    
    def _go_to_coords(self):
        """Pan to first marker."""
        #get the first marker position and force move the map to that position
        first_marker = self.marker_manager.get_first_marker()
        if first_marker:
            lat, lon = first_marker.position
            self.map_view_controller.go_to_coordinates(lat, lon)
            self._on_scroll()
    
    def _after_popop_to_calculate(self, chosenSettings):
        """
        Callback vanuit het popup-venster.
        Routeert naar de juiste berekeningsmethod op basis van de gekozen formatie.
        """
        amount = 1
        try:
            amount = int(chosenSettings["Aantal"])
        except Exception:
            pass
 
        formation  = chosenSettings.get("Formatie", "Standaard 10m afstand") or \
                     "Standaard 10m afstand"
        start_robot = chosenSettings["RobotStart"]
        print(f"Gekozen instellingen: aantal={amount}, "
              f"formatie={formation}, start={start_robot}")

        self._calculate_positions(amount=amount, formation=formation)
    
    def _reset_button_pressed(self):
        """Handle reset button press."""
        self.reset_interface_callback()
    
    def reset_frame(self):
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
            print("EXCEPTION: ", e)
