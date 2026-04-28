import customtkinter
from tkintermapview import TkinterMapView
import math
import threading
import requests

ARROWLENGTH    = 50
PDOK_WFS_URL   = "https://service.pdok.nl/rws/nationaal-wegenbestand-wegen/wfs/v1_0"
ROAD_DRAW_ZOOM = 18


class AppFrameMap(customtkinter.CTkFrame):
    def __init__(self, master, sendCallback):
        super().__init__(master)

        self.sendMessageCallback = sendCallback

        #self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=14)
        self.grid_rowconfigure(2, weight=1)

        # ── Map widget ────────────────────────────────────────────────────
        self.map_widget = TkinterMapView(self, corner_radius=5, database_path="map_tiles.db")
        self.map_widget.grid(row=1, column=0, columnspan=3, sticky="nswe",
                             padx=(10, 10), pady=(0, 0))

        self.label = customtkinter.CTkLabel(
            self, text="Map", fg_color='#01a6f8',
            width=100, height=20, font=('Bold', 28), corner_radius=5
        )
        self.label.grid(row=0, column=0, sticky="nw", padx=(8, 8), pady=(5, 5))

        self.map_widget.bind("<MouseWheel>", self._on_scroll)
        self.map_widget.canvas.bind("<MouseWheel>", self._on_scroll, add="+")

        # ── Tile server control ───────────────────────────────────────────
        self.control_frame = customtkinter.CTkFrame(self)
        self.control_frame.grid(row=2, column=0, sticky="nw", padx=10, pady=10)

        customtkinter.CTkLabel(self.control_frame, text="Tile Server:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(5, 0), sticky="nw")

        self.map_option_menu = customtkinter.CTkOptionMenu(
            self.control_frame,
            values=["Maps normal", "Maps satellite"],
            command=self.change_map
        )
        self.map_option_menu.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nw")

        self.map_widget.set_tile_server(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            max_zoom=21
        )
        self.map_widget.set_position(52.0172355, 4.3712940)
        self.map_option_menu.set("Maps satellite")
        self.MAX_ZOOM = 21

        self.after(500, self._draw_scale)

        self.map_widget.add_right_click_menu_command(
            label="Add Marker", command=self.AddMarker, pass_coords=True)

        # ── Positie-knoppen ────────────────────────────────────────────────
        self.controlFramePositionButtons = customtkinter.CTkFrame(self)
        self.controlFramePositionButtons.grid(row=2, column=1, columnspan=2, sticky="nwse", padx=10, pady=10)

        customtkinter.CTkButton(
            self.controlFramePositionButtons, text="Bereken overige posities",
            command=self.CalculatePositions, border_color="black", border_width=2
        ).grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        self.testPositionModeVar = customtkinter.StringVar(value=False)
        customtkinter.CTkSwitch(
            self.controlFramePositionButtons, text="Test mode", variable=self.testPositionModeVar,
           onvalue=True, offvalue=False,
           border_color="black", border_width=2, command=self.switchTest
        ).grid(row=0, column=3, padx=10, pady=10, sticky="ne")
        print("varrrrrrrrrrrrrrrrrr= ", self.testPositionModeVar.get())

        customtkinter.CTkButton(
            self.controlFramePositionButtons, text="Verwijder berekende coordinaten",
            command=self.DeletePositions, border_color="black", border_width=2, fg_color="red"
        ).grid(row=0, column=1, padx=10, pady=10, sticky="nw")

        customtkinter.CTkButton(
            self.controlFramePositionButtons, text="Stuur posities naar robots",
            command=self.SendMessagesToRobots, border_color="black", border_width=2, fg_color="green"
        ).grid(row=0, column=2, padx=10, pady=10, sticky="nw")

        # ── Marker state ───────────────────────────────────────────────────
        self.markersDict  = {}
        self.marker_lines = {}
        self.addingMarker = False

        self.map_widget.canvas.bind("<ButtonRelease-1>", self._on_pan_end, add="+")
        self.map_widget.canvas.bind("<B1-Motion>",       self._on_pan_end, add="+")
        self.map_widget.canvas.bind("<Button-1>",        self._on_pan_end, add="+")

        # ── Road overlay state ─────────────────────────────────────────────
        self._ROAD_TAG           = "nwb_roads"
        self._road_polylines     = []    # list of list of (lat, lon)
        self._road_fetch_bbox    = None  # bbox waarvoor data gecached is
        self._road_refresh_job   = None
        self._road_fetch_running = False

    # ══════════════════════════════════════════════════════════════════════
    # Map controls
    # ══════════════════════════════════════════════════════════════════════

    def switchTest(self):
        print(self.testPositionModeVar.get())

    def change_map(self, new_map: str):
        if new_map == "Maps normal":
            self.MAX_ZOOM = 20
            self.map_widget.set_tile_server(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
                max_zoom=20)
        elif new_map == "Maps satellite":
            self.MAX_ZOOM = 21
            self.map_widget.set_tile_server(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                max_zoom=21)

    def _on_scroll(self, event):
        self.after(50, self._enforce_zoom)
        self.after(70, self._redraw_all)
        self._schedule_road_refresh()

    def _on_pan_end(self, event):
        self.after(70, self._redraw_all)
        self._schedule_road_refresh()
        #self.map_widget.set_zoom(19)


    def _enforce_zoom(self):
        if self.map_widget.zoom > self.MAX_ZOOM:
            self.map_widget.set_zoom(self.MAX_ZOOM)

    def _redraw_all(self):
        """Herteken zowel de pijlen als de weglijnen na pan/zoom."""
        self.DrawMarkerLines()
        self._draw_cached_roads()

    # ══════════════════════════════════════════════════════════════════════
    # Scale bar
    # ══════════════════════════════════════════════════════════════════════

    def _draw_scale(self):
        canvas = self.map_widget.canvas
        canvas.delete("scale")
        w, h = self.map_widget.winfo_width(), self.map_widget.winfo_height()
        if w < 10 or h < 10:
            self.after(200, self._draw_scale)
            return
        x1, y1, x2, y2 = 20, h - 30, 120, h - 30
        meters = self._pixels_to_meters(100)
        canvas.create_line(x1, y1, x2, y2, fill="white", width=3, tags="scale")
        canvas.create_line(x1, y1-5, x1, y1+5, fill="white", width=3, tags="scale")
        canvas.create_line(x2, y2-5, x2, y2+5, fill="white", width=3, tags="scale")
        canvas.create_text((x1+x2)//2, y1-10, text=f"{meters:.0f} m",
                           fill="white", font=("Arial", 10, "bold"), tags="scale")
        self.after(500, self._draw_scale)

    def _pixels_to_meters(self, pixels):
        zoom = self.map_widget.zoom
        lat  = self.map_widget.get_position()[0]
        return pixels * (156543.03 * math.cos(math.radians(lat))) / (2 ** zoom)

    # ══════════════════════════════════════════════════════════════════════
    # Marker arrows
    # ══════════════════════════════════════════════════════════════════════

    def DrawMarkerLines(self, event=None):
        if self.addingMarker:
            return
        for marker, (line_tag, direction) in list(self.marker_lines.items()):
            if not marker.deleted:
                cx, cy = marker.get_canvas_pos(marker.position)
                self.map_widget.canvas.delete(line_tag)
                angle_rad = math.radians(direction)
                self.map_widget.canvas.create_line(
                    cx, cy,
                    cx + ARROWLENGTH * math.cos(angle_rad),
                    cy + ARROWLENGTH * math.sin(angle_rad),
                    fill="green", width=5, tags=line_tag,
                    arrow=customtkinter.LAST
                )

    # ══════════════════════════════════════════════════════════════════════
    # NWB road overlay
    # ══════════════════════════════════════════════════════════════════════

    def _schedule_road_refresh(self):
        """Debounce: wacht 400 ms na het laatste event, dan pas ophalen."""
        if self._road_refresh_job is not None:
            self.after_cancel(self._road_refresh_job)
        self._road_refresh_job = self.after(400, self._refresh_roads)

    def _refresh_roads(self):
        self._road_refresh_job = None
        zoom = self.map_widget.zoom
        zoomInteger = int(zoom)
        self.map_widget.set_zoom(zoomInteger)
        if zoomInteger < ROAD_DRAW_ZOOM:
            self.map_widget.canvas.delete(self._ROAD_TAG)
            return
        bbox = self._get_viewport_bbox()
        if bbox is None:
            return

        # Gecachte data dekt de view al → alleen hertekenen, geen nieuw verzoek
        if (self._road_fetch_bbox is not None
                and self._bbox_contains(self._road_fetch_bbox, bbox)
                and self._road_polylines):
            self._draw_cached_roads()
            return

        # Nieuw WFS-verzoek starten
        if not self._road_fetch_running:
            self._road_fetch_running = True
            lat_min, lon_min, lat_max, lon_max = bbox
            dlat = (lat_max - lat_min) * 0.30
            dlon = (lon_max - lon_min) * 0.30
            fetch_bbox = (lat_min - dlat, lon_min - dlon,
                          lat_max + dlat, lon_max + dlon)
            threading.Thread(
                target=self._fetch_roads_thread,
                args=(fetch_bbox,),
                daemon=True
            ).start()

    def _get_viewport_bbox(self):
        w = self.map_widget.winfo_width()
        h = self.map_widget.winfo_height()
        if w < 10 or h < 10:
            return None
        try:
            lat_nw, lon_nw = self.map_widget.convert_canvas_coords_to_decimal_coords(0, 0)
            lat_se, lon_se = self.map_widget.convert_canvas_coords_to_decimal_coords(w, h)
        except Exception:
            return None
        return (min(lat_nw, lat_se), min(lon_nw, lon_se),
                max(lat_nw, lat_se), max(lon_nw, lon_se))

    @staticmethod
    def _bbox_contains(outer, inner):
        return (outer[0] <= inner[0] and outer[1] <= inner[1] and
                outer[2] >= inner[2] and outer[3] >= inner[3])

    def _fetch_roads_thread(self, bbox):
        lat_min, lon_min, lat_max, lon_max = bbox
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NWB-overlay/1.0)"}

        # WFS 2.0 + EPSG:4326: bbox-volgorde = lat_min,lon_min,lat_max,lon_max
        params = {
            "service":      "WFS",
            "version":      "2.0.0",
            "request":      "GetFeature",
            "typeNames":    "nwbwegen:wegvakken",
            "outputFormat": "application/json; subtype=geojson",
            "srsName":      "EPSG:4326",
            "bbox":         f"{lat_min},{lon_min},{lat_max},{lon_max},EPSG:4326",
            "count":        "2000",
        }

        try:
            resp = requests.get(PDOK_WFS_URL, params=params,
                                headers=headers, timeout=15)
            resp.raise_for_status()
            data     = resp.json()
            features = data.get("features", [])
            print(f"[NWB WFS] {len(features)} wegvakken ontvangen.")

            polylines = []
            for feature in features:
                geom = feature.get("geometry")
                if geom is None:
                    continue
                gtype  = geom.get("type", "")
                coords = geom.get("coordinates", [])
                if gtype == "LineString":
                    segments = [coords]
                elif gtype == "MultiLineString":
                    segments = coords
                else:
                    continue
                for seg in segments:
                    # GeoJSON in EPSG:4326 levert [lon, lat] per punt
                    latlon = [(pt[1], pt[0]) for pt in seg if len(pt) >= 2]
                    if len(latlon) >= 2:
                        polylines.append(latlon)

            # Sla op en plan hertekening op de main thread
            self._road_polylines  = polylines
            self._road_fetch_bbox = bbox

        except Exception as exc:
            print(f"[NWB WFS] fout: {exc}")

        # Altijd vrijgeven en hertekenen aanvragen, ook bij fout
        self._road_fetch_running = False
        self.after(0, self._draw_cached_roads)

    def _draw_cached_roads(self):
        """
        Tekent alle gecachte wegvakken op het canvas.
        Wordt aangeroepen vanuit de main thread:
          - direct na een WFS-fetch (via self.after(0, ...))
          - bij elke pan/zoom via _redraw_all()
        """
        canvas = self.map_widget.canvas
        canvas.delete(self._ROAD_TAG)

        if self.map_widget.zoom < ROAD_DRAW_ZOOM:
            return

        if not self._road_polylines:
            return

        line_width = max(1, self.map_widget.zoom - 16)  # 1px @ z17, 2px @ z18 …

        for polyline in self._road_polylines:
            pts = []
            for lat, lon in polyline:
                try:
                    cx, cy = self._latlon_to_canvas(lat, lon)
                    pts.append(cx)
                    pts.append(cy)
                except Exception:
                    pass
            if len(pts) >= 4:
                canvas.create_line(
                    *pts,
                    fill="#FFD700",       # goud-geel — goed zichtbaar op satelliet
                    width=line_width,
                    tags=self._ROAD_TAG,
                    capstyle="round",
                    joinstyle="round",
                )

        # Weglijnen achter markers/pijlen houden
        canvas.tag_raise(self._ROAD_TAG)

    # ══════════════════════════════════════════════════════════════════════
    # Markers
    # ══════════════════════════════════════════════════════════════════════

    def AddMarker(self, coords, direction=None, markerText="new mark"):
        self.addingMarker = True
        print("adding new marker:", coords)
        self.DeletePositions(markerText)
        newMarker = self.map_widget.set_marker(coords[0], coords[1], text=markerText)
        self.markersDict[newMarker] = markerText
        self.map_widget.update_idletasks()
        self.marker_lines[newMarker] = [markerText, direction]
        self.addingMarker = False
        self.DrawMarkerLines()

    def CalculatePositions(self, distance = 5):
        print("calculateButtonPressed")
        testModeVar = self.testPositionModeVar.get()
        print(self.markersDict)
        print(testModeVar)
        print(testModeVar == "0")
        if not self.markersDict or testModeVar == "0":
            print("geen markers om op te berekenen of het is geen testmodus dus ook geen berekening")
            return

        first_marker        = list(self.markersDict.keys())[0]
        lat, lon            = first_marker.position
        direction           = self.marker_lines[first_marker][1]
        if direction is None:
            print("Geen richting ingesteld")
            return
        normalizedDirection = self.NormalisePositionDegreeValues(direction, 1)
        new_lat, new_lon    = self.calculate_destination(lat, lon, normalizedDirection, distance)
        self.AddMarker((new_lat, new_lon), direction, markerText="calculated")

    def calculate_destination(self, lat, lon, bearing, distance):
        R     = 6371000
        lat1  = math.radians(lat)
        lon1  = math.radians(lon)
        theta = math.radians(bearing)
        delta = distance / R
        lat2  = math.asin(
            math.sin(lat1) * math.cos(delta) +
            math.cos(lat1) * math.sin(delta) * math.cos(theta)
        )
        lon2 = lon1 + math.atan2(
            math.sin(theta) * math.sin(delta) * math.cos(lat1),
            math.cos(delta) - math.sin(lat1) * math.sin(lat2)
        )
        return math.degrees(lat2), math.degrees(lon2)

    def NormalisePositionDegreeValues(self, degrees, situation):
        if situation == 1 and degrees is not None:
            return degrees + 90

    def DeletePositions(self, nameToDelete="calculated"):
        for key in [k for k, v in self.markersDict.items() if nameToDelete in v]:
            del self.markersDict[key]
            key.delete()
        for key in [k for k, v in self.marker_lines.items() if nameToDelete in v[0]]:
            del self.marker_lines[key]

    def SendMessagesToRobots(self, robotName=None, msgField=None, msg=None):
        coordsDict = {}
        nameFromFirstRobot = None
        for marker, name in self.markersDict.items():
            if "calc" in name:
                coords = marker.position
                print("print coords dit zijn: ", coords)
                coordsDict[name] = coords
            else:
                coordsDict[name] = None
        print("coordsdict = ", coordsDict)
        self.sendMessageCallback(coordsDict)


    def _latlon_to_canvas(self, lat, lon):
        """Converteert lat/lon naar canvas-pixelcoördinaten via TkinterMapView internals."""
        # TkinterMapView slaat de huidige tile-offset op in deze attributen
        widget = self.map_widget
        zoom = widget.zoom
    
        # Tile coördinaten (float)
        tile_x = (lon + 180) / 360 * (2 ** zoom)
        sin_lat = math.sin(math.radians(lat))
        tile_y = (1 - math.log((1 + sin_lat) / (1 - sin_lat)) / (2 * math.pi)) / 2 * (2 ** zoom)
    
        # Canvas pixels — widget.upper_left_tile_pos is de tile-offset van de linkerbovenhoek
        upper_left_x, upper_left_y = widget.upper_left_tile_pos
        cx = (tile_x - upper_left_x) * widget.tile_size
        cy = (tile_y - upper_left_y) * widget.tile_size
        return cx, cy