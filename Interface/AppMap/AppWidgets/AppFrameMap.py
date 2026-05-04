from os import close
from tracemalloc import start
import customtkinter
from tkintermapview import TkinterMapView
import math
import threading
import requests
from geopy.geocoders import Nominatim

ARROWLENGTH    = 50
PDOK_WFS_URL   = "https://service.pdok.nl/rws/nationaal-wegenbestand-wegen/wfs/v1_0"
ROAD_DRAW_ZOOM = 18


# ══════════════════════════════════════════════════════════════════════
# Hulpfuncties voor parallel offset (buiten de klasse, puur wiskundig)
# ══════════════════════════════════════════════════════════════════════

def _latlon_to_local_xy(lat, lon, ref_lat, ref_lon):
    """Converteert lat/lon naar lokale Cartesische meters t.o.v. referentiepunt."""
    R = 6371000
    x = math.radians(lon - ref_lon) * R * math.cos(math.radians(ref_lat))
    y = math.radians(lat - ref_lat) * R
    return x, y


def _local_xy_to_latlon(x, y, ref_lat, ref_lon):
    """Converteert lokale Cartesische meters terug naar lat/lon."""
    R = 6371000
    lat = ref_lat + math.degrees(y / R)
    lon = ref_lon + math.degrees(x / (R * math.cos(math.radians(ref_lat))))
    return lat, lon


def offset_polyline(polyline_latlon, offset_x, offset_y):
    """
    Verschuift een polyline parallel zodat de lijn door een specifiek punt gaat.

    De verschuiving wordt uitgedrukt als een vector (offset_x, offset_y) in meters
    in het lokale Cartesische stelsel van het eerste punt van de polyline.
    Die vector wordt loodrecht op elk segment geprojecteerd, zodat bochten
    correct mee worden getransformeerd.

    Args:
        polyline_latlon : lijst van (lat, lon) tuples
        offset_x        : verschuiving in oost-richting (meters, kan negatief zijn)
        offset_y        : verschuiving in noord-richting (meters, kan negatief zijn)

    Returns:
        Nieuwe lijst van (lat, lon) tuples — de verschoven polyline.
    """
    if len(polyline_latlon) < 2:
        return list(polyline_latlon)

    ref_lat, ref_lon = polyline_latlon[0]

    # Converteer alle punten naar lokale XY (meters)
    xy = [_latlon_to_local_xy(lat, lon, ref_lat, ref_lon)
          for lat, lon in polyline_latlon]

    # Bereken eenheidsnormalen per segment (loodrecht naar rechts op rijrichting)
    normals = []
    for i in range(len(xy) - 1):
        dx = xy[i + 1][0] - xy[i][0]
        dy = xy[i + 1][1] - xy[i][1]
        seg_len = math.hypot(dx, dy)
        if seg_len < 1e-9:
            normals.append((0.0, 0.0))
        else:
            # Eenheidsnormaal naar rechts: (dy/L, -dx/L)
            normals.append((dy / seg_len, -dx / seg_len))

    # Projecteer de offset-vector op de normaal van elk punt:
    # De signed scalaire projectie geeft hoeveel van de gewenste verschuiving
    # loodrecht op het segment valt — dat is de correcte offset voor dat punt.
    # Door te vermenigvuldigen met de normaal krijgen we de echte verplaatsing.
    result = []
    for i in range(len(xy)):
        if i == 0:
            nx, ny = normals[0]
        elif i == len(xy) - 1:
            nx, ny = normals[-1]
        else:
            # Gemiddelde van aangrenzende normalen → soepele bocht
            nx = (normals[i - 1][0] + normals[i][0]) / 2
            ny = (normals[i - 1][1] + normals[i][1]) / 2
            n_len = math.hypot(nx, ny)
            if n_len > 1e-9:
                nx /= n_len
                ny /= n_len

        # Scalaire projectie van offset-vector op de normaal van dit punt
        projection = offset_x * nx + offset_y * ny

        # Verschuif het punt langs de normaal met de geprojecteerde afstand
        new_x = xy[i][0] + projection * nx
        new_y = xy[i][1] + projection * ny
        result.append(_local_xy_to_latlon(new_x, new_y, ref_lat, ref_lon))

    return result


class AppFrameMap(customtkinter.CTkFrame):
    def __init__(self, master, sendCallback):
        super().__init__(master)

        self.sendMessageCallback = sendCallback

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
            command=self.CalculateButtonPressed, border_color="black", border_width=2
        ).grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        self.testPositionModeVar = customtkinter.StringVar(value=False)
        customtkinter.CTkSwitch(
            self.controlFramePositionButtons, text="Test mode", variable=self.testPositionModeVar,
            onvalue=True, offvalue=False,
            border_color="black", border_width=2, command=self.switchTest
        ).grid(row=1, column=0, padx=10, pady=10, sticky="nw")

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
        self._OFFSET_TAG         = "vluchtstrook_roads"
        self.THROUGHMARKER       = "vluchtstrook"
        self._road_polylines     = []    # lijst van list van (lat, lon)
        self._road_fetch_bbox    = None  # bbox waarvoor data gecached is
        self._road_refresh_job   = None
        self._road_fetch_running = False
        self.geolocator          = Nominatim(user_agent="my_app")
        self.helpLineMarker      = {}

        # ── Vluchtstrook state ─────────────────────────────────────────────
        # Gecachte verschoven polylines (worden bewaard na berekening)
        self._offset_polylines   = []

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

    def _on_scroll(self, event=None):
        self.after(50, self._enforce_zoom)
        self.after(70, self._redraw_all)
        self._schedule_road_refresh()

    def _on_pan_end(self, event=None):
        self.after(70, self._redraw_all)
        self._schedule_road_refresh()

    def _enforce_zoom(self):
        if self.map_widget.zoom > self.MAX_ZOOM:
            self.map_widget.set_zoom(self.MAX_ZOOM)

    def _redraw_all(self):
        """Herteken pijlen, weglijnen en vluchtstrook-overlay na pan/zoom."""
        self.DrawMarkerLines()
        self._draw_cached_roads()
        self._draw_offset_roads()
        self.DrawHelpMarkers()

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
        canvas.create_line(x1, y1 - 5, x1, y1 + 5, fill="white", width=3, tags="scale")
        canvas.create_line(x2, y2 - 5, x2, y2 + 5, fill="white", width=3, tags="scale")
        canvas.create_text((x1 + x2) // 2, y1 - 10, text=f"{meters:.0f} m",
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
                try:
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
                except Exception:
                    pass

    def DrawHelpMarkers(self, event=None):
        if not self.helpLineMarker:
            return
        canvas = self.map_widget.canvas
        canvas.delete(self.THROUGHMARKER)
        for key, val in self.helpLineMarker.items():
            latCanvas, lonCanvas = self._latlon_to_canvas(val[0], val[1])
            cxCanvas, cyCanvas   = self._latlon_to_canvas(key[0], key[1])
            canvas.create_oval(cxCanvas - 3, cyCanvas - 3, cxCanvas + 3, cyCanvas + 3,
                               fill="blue", tags=self.THROUGHMARKER)
            canvas.create_line(latCanvas, lonCanvas, cxCanvas, cyCanvas,
                               fill="red", dash=(2, 2), tags=self.THROUGHMARKER)

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
        zoom        = self.map_widget.zoom
        zoomInteger = int(zoom)
        self.map_widget.set_zoom(zoomInteger)
        if zoomInteger < ROAD_DRAW_ZOOM:
            self.map_widget.canvas.delete(self._ROAD_TAG)
            self.map_widget.canvas.delete(self._OFFSET_TAG)
            return
        bbox = self._get_viewport_bbox()
        if bbox is None:
            return

        # Gecachte data dekt de view al → alleen hertekenen, geen nieuw verzoek
        if (self._road_fetch_bbox is not None
                and self._bbox_contains(self._road_fetch_bbox, bbox)
                and self._road_polylines):
            self._draw_cached_roads()
            self._draw_offset_roads()
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

        params = {
            "service":      "WFS",
            "version":      "2.0.0",
            "request":      "GetFeature",
            "typeNames":    "nwbwegen:wegvakken",
            "outputFormat": "application/json; subtype=geojson",
            "srsName":      "EPSG:4326",
            "bbox":         f"{lat_min},{lon_min},{lat_max},{lon_max},EPSG:4326",
            "count":        "2000",
            "CQL_FILTER":   "dienstnaam LIKE 'RWS%'"
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
                props = feature.get("properties", {})
                if not props.get("dienstnaam", "").startswith("RWS"):
                    continue
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
                    latlon = [(pt[1], pt[0]) for pt in seg if len(pt) >= 2]
                    if len(latlon) >= 2:
                        polylines.append(latlon)

            self._road_polylines  = polylines
            self._road_fetch_bbox = bbox

        except Exception as exc:
            print(f"[NWB WFS] fout: {exc}")

        self._road_fetch_running = False
        self.after(0, self._draw_cached_roads)
        self.after(0, self._draw_offset_roads)

    def _draw_cached_roads(self):
        """Tekent alle gecachte NWB-wegvakken (geel) op het canvas."""
        canvas = self.map_widget.canvas
        canvas.delete(self._ROAD_TAG)

        if self.map_widget.zoom < ROAD_DRAW_ZOOM or not self._road_polylines:
            return

        line_width = max(1, self.map_widget.zoom - 16)

        for polyline in self._road_polylines:
            pts = []
            for lat, lon in polyline:
                try:
                    cx, cy = self._latlon_to_canvas(lat, lon)
                    pts.extend([cx, cy])
                except Exception:
                    pass
            if len(pts) >= 4:
                canvas.create_line(
                    *pts,
                    fill="#FFD700",
                    width=line_width,
                    tags=self._ROAD_TAG,
                    capstyle="round",
                    joinstyle="round",
                )

        canvas.tag_raise(self._ROAD_TAG)

    # ══════════════════════════════════════════════════════════════════════
    # Vluchtstrook parallel-offset overlay
    # ══════════════════════════════════════════════════════════════════════

    def _find_nearest_polyline(self, lat, lon):
        """
        Geeft de NWB-polyline terug die het dichtst bij (lat, lon) ligt.
        Geeft None terug als er geen data is.
        """
        if not self._road_polylines:
            return None

        best_polyline = None
        best_dist     = float("inf")

        for polyline in self._road_polylines:
            ref_lat, ref_lon = polyline[0]
            px, py = _latlon_to_local_xy(lat, lon, ref_lat, ref_lon)

            for i in range(len(polyline) - 1):
                x1, y1 = _latlon_to_local_xy(*polyline[i],     ref_lat, ref_lon)
                x2, y2 = _latlon_to_local_xy(*polyline[i + 1], ref_lat, ref_lon)
                dx, dy  = x2 - x1, y2 - y1
                len_sq  = dx * dx + dy * dy
                if len_sq < 1e-9:
                    continue
                t  = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
                cx = x1 + t * dx
                cy = y1 + t * dy
                d  = math.hypot(px - cx, py - cy)
                if d < best_dist:
                    best_dist     = d
                    best_polyline = polyline

        return best_polyline

    def _compute_offset_vector(self, marker_lat, marker_lon, polyline):
        """
        Berekent de offset-vector (in meters, lokaal Cartesisch) van de
        dichtstbijzijnde punt op de polyline naar de marker.

        De lijn wordt met exact deze vector verschoven, zodat de verschoven
        lijn gegarandeerd door de marker gaat — ongeacht of hij links of
        rechts van de NWB-hartlijn staat.

        Returns: (offset_x, offset_y) in meters t.o.v. het eerste punt van
                 de polyline als referentie.
        """
        ref_lat, ref_lon = polyline[0]
        px, py = _latlon_to_local_xy(marker_lat, marker_lon, ref_lat, ref_lon)

        best_dist = float("inf")
        best_foot = (px, py)   # voetloodpunt op de lijn (fallback = marker zelf)

        for i in range(len(polyline) - 1):
            x1, y1 = _latlon_to_local_xy(*polyline[i],     ref_lat, ref_lon)
            x2, y2 = _latlon_to_local_xy(*polyline[i + 1], ref_lat, ref_lon)
            dx, dy  = x2 - x1, y2 - y1
            len_sq  = dx * dx + dy * dy
            if len_sq < 1e-9:
                continue
            t  = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
            fx = x1 + t * dx   # voetloodpunt x
            fy = y1 + t * dy   # voetloodpunt y
            d  = math.hypot(px - fx, py - fy)
            if d < best_dist:
                best_dist = d
                best_foot = (fx, fy)

        # Vector van voetloodpunt → marker = de gewenste verschuiving
        offset_x = px - best_foot[0]
        offset_y = py - best_foot[1]
        print(f"[Offset] vector ({offset_x:.1f}, {offset_y:.1f}) m, "
              f"afstand {best_dist:.1f} m")
        return offset_x, offset_y

    def _build_offset_polylines(self, marker_lat, marker_lon):
        """
        Zoekt de dichtstbijzijnde NWB-polyline, berekent de offset-vector van
        die lijn naar de marker, en verschuift alle NWB-polylines met diezelfde
        vector. De verschoven lijn gaat zo gegarandeerd door de marker.
        """
        nearest = self._find_nearest_polyline(marker_lat, marker_lon)
        if nearest is None:
            print("[Offset] Geen NWB-data beschikbaar.")
            return

        offset_x, offset_y = self._compute_offset_vector(marker_lat, marker_lon, nearest)

        offset_dist = math.hypot(offset_x, offset_y)
        if offset_dist < 0.5:
            print("[Offset] Marker staat al op de weg; geen offset toegepast.")
            self._offset_polylines = []
            return

        self._offset_polylines = [
            offset_polyline(pl, offset_x, offset_y)
            for pl in self._road_polylines
        ]
        print(f"[Offset] {len(self._offset_polylines)} polylines verschoven "
              f"met {offset_dist:.1f} m.")

    def _draw_offset_roads(self):
        """Tekent de verschoven vluchtstrook-polylines (oranje) op het canvas."""
        canvas = self.map_widget.canvas
        canvas.delete(self._OFFSET_TAG)

        if self.map_widget.zoom < ROAD_DRAW_ZOOM or not self._offset_polylines:
            return

        line_width = max(1, self.map_widget.zoom - 16)

        for polyline in self._offset_polylines:
            pts = []
            for lat, lon in polyline:
                try:
                    cx, cy = self._latlon_to_canvas(lat, lon)
                    pts.extend([cx, cy])
                except Exception:
                    pass
            if len(pts) >= 4:
                canvas.create_line(
                    *pts,
                    fill="#FF6600",   # oranje — onderscheidend van gele NWB-lijn
                    width=line_width,
                    tags=self._OFFSET_TAG,
                    capstyle="round",
                    joinstyle="round",
                )

        canvas.tag_raise(self._OFFSET_TAG)

    def _snap_to_offset_polyline(self, lat, lon):
        """
        Projecteert (lat, lon) op de dichtstbijzijnde verschoven polyline.
        Geeft de geprojecteerde (lat, lon) terug, of de originele waarde als
        er geen offset-data is.
        """
        if not self._offset_polylines:
            return lat, lon

        best_dist = float("inf")
        best_pt   = (lat, lon)

        for polyline in self._offset_polylines:
            ref_lat, ref_lon = polyline[0]
            px, py = _latlon_to_local_xy(lat, lon, ref_lat, ref_lon)

            for i in range(len(polyline) - 1):
                x1, y1 = _latlon_to_local_xy(*polyline[i],     ref_lat, ref_lon)
                x2, y2 = _latlon_to_local_xy(*polyline[i + 1], ref_lat, ref_lon)
                dx, dy  = x2 - x1, y2 - y1
                len_sq  = dx * dx + dy * dy
                if len_sq < 1e-9:
                    continue
                t  = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
                cx = x1 + t * dx
                cy = y1 + t * dy
                d  = math.hypot(px - cx, py - cy)
                if d < best_dist:
                    best_dist = d
                    best_pt   = _local_xy_to_latlon(cx, cy, ref_lat, ref_lon)

        return best_pt

    # ══════════════════════════════════════════════════════════════════════
    # Markers
    # ══════════════════════════════════════════════════════════════════════

    def AddMarker(self, coords, direction=None, markerText="new mark"):
        self.addingMarker = True
        print("adding new marker:", coords)
        self.DeletePositions(markerText)
        newMarker = self.map_widget.set_marker(coords[0], coords[1], text=markerText)

        self.after(150, lambda: self.AddIncidentLocation(
            self.geolocator.reverse(f"{coords[0]}, {coords[1]}")))

        self.markersDict[newMarker] = markerText
        self.map_widget.update_idletasks()
        self.marker_lines[newMarker] = [markerText, direction]
        self.addingMarker = False
        self.DrawMarkerLines()

    def CalculateButtonPressed(self):
        testModeVar = self.testPositionModeVar.get()
        if not self.markersDict:
            print("geen markers om op te berekenen")
            return
        if testModeVar == "1":
            self.CalculatePositions(distance=5, amount=1, motherBotPos=1)
        else:
            self.pop_up(["robot1", "robot2"], self.AfterPopUpToCalculate)

    def CalculatePositions(self, distance=5, amount=1, motherBotPos=1):
        """
        Berekent 'amount' posities op de vluchtstrook.

        Werkwijze:
        1. Bouw de parallel-offset polylines op basis van de eerste marker.
        2. Snap de eerste marker zelf naar de vluchtstrook → dit is het
           werkelijke startpunt (positie 0 op de vluchtstrook).
        3. Bereken de overige posities langs de rijrichting VANAF het
           gesnnapte startpunt, zodat alle posities op de vluchtstrook liggen.
        4. Snap ook de overige posities naar de vluchtstrook (corrigeert
           kleine afwijkingen bij bochten).
        """
        first_marker = list(self.markersDict.keys())[0]
        lat, lon     = first_marker.position
        direction    = self.marker_lines[first_marker][1]

        if direction is None:
            print("Geen richting ingesteld")
            return

        # Stap 1: bouw de vluchtstrook-polylines (parallel offset)
        self._build_offset_polylines(lat, lon)

        # Stap 2: snap de marker zelf naar de vluchtstrook
        # Dit geeft het werkelijke startpunt op de vluchtstrook.
        start_lat, start_lon = self._snap_to_offset_polyline(lat, lon)
        print(f"[Calc] Startpunt op vluchtstrook: {start_lat:.6f}, {start_lon:.6f}")

        # Stap 3: bereken tussenposities VANAF het gesnnapte startpunt
        normalizedDirection = self.NormalisePositionDegreeValues(direction, 1)
        newPosList = [[None, None] for _ in range(amount)]
        self.calculate_destination(start_lat, start_lon, normalizedDirection, distance, newPosList)

        # Stap 4: snap elke positie naar de vluchtstrook en plaats marker
        # (corrigeert bochten — langs rechte stukken verandert er niets)
        for i in range(amount):
            raw_lat, raw_lon   = newPosList[i]
            snap_lat, snap_lon = self._snap_to_offset_polyline(raw_lat, raw_lon)
            self.AddMarker((snap_lat, snap_lon), direction, markerText=f"calculated{i}")

        # Helplijnen tekenen (behoud bestaande functionaliteit)
        self.CheckNearestPointOfLine([lat, lon])

        # Herteken de vluchtstrook overlay
        self._draw_offset_roads()

    def calculate_destination(self, lat, lon, bearing, distanceFirst, posList):
        R     = 6371000
        lat1  = math.radians(lat)
        lon1  = math.radians(lon)
        theta = math.radians(bearing)
        for i in range(1, len(posList) + 1):
            distance = distanceFirst * i
            delta    = distance / R
            lat2     = math.asin(
                math.sin(lat1) * math.cos(delta) +
                math.cos(lat1) * math.sin(delta) * math.cos(theta)
            )
            lon2 = lon1 + math.atan2(
                math.sin(theta) * math.sin(delta) * math.cos(lat1),
                math.cos(delta) - math.sin(lat1) * math.sin(lat2)
            )
            posList[i - 1] = [math.degrees(lat2), math.degrees(lon2)]

    def CalculateDistance(self, lat1, lon1, lat2, lon2):
        R        = 6371000
        lat1Rad  = math.radians(lat1)
        lat2Rad  = math.radians(lat2)
        deltaLat = math.radians(lat2 - lat1)
        deltaLon = math.radians(lon2 - lon1)
        a = (math.sin(deltaLat / 2) ** 2
             + math.cos(lat1Rad) * math.cos(lat2Rad) * math.sin(deltaLon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def closest_point_on_segment(self, px, py, x1, y1, x2, y2):
        dxAB     = x2 - x1
        dyAB     = y2 - y1
        dxAP     = px - x1
        dyAP     = py - y1
        len_sqAB = dxAB ** 2 + dyAB ** 2
        t        = (dxAB * dxAP + dyAB * dyAP) / len_sqAB
        return x1 + t * dxAB, y1 + t * dyAB

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
        for marker, name in self.markersDict.items():
            if "calc" in name:
                coords = marker.position
                print("print coords dit zijn: ", coords)
                coordsDict[name] = coords
            else:
                coordsDict[name] = None
        print("coordsdict = ", coordsDict)
        self.sendMessageCallback(coordsDict)

    def AddIncidentLocation(self, location):
        location = location.raw["address"]
        print(location)
        road  = location.get("road")
        city  = location.get("city")
        state = location.get("state")
        self.incidentFrame = customtkinter.CTkFrame(self.controlFramePositionButtons)
        self.incidentFrame.grid(row=0, column=3, rowspan=2, sticky="ne", padx=10, pady=10)
        customtkinter.CTkLabel(
            self.incidentFrame,
            text=f"Incidentlocatie: {road}, {city}, {state}",
            fg_color='#01a6f8', corner_radius=5, text_color="black"
        ).grid(row=0, column=0, padx=10, pady=5, sticky="ne")
        customtkinter.CTkButton(
            self.incidentFrame, text="Ga naar positie",
            command=self.GoToCoords, border_color="black", border_width=2, fg_color="green"
        ).grid(row=1, column=0, padx=10, pady=10, sticky="nw")

    def GoToCoords(self):
        coords = next(iter(self.markersDict))
        lat, lon = coords.position
        self.map_widget.set_position(lat, lon)
        self.map_widget.set_zoom(19)
        self._on_scroll()

    def _latlon_to_canvas(self, lat, lon):
        """Converteert lat/lon naar canvas-pixelcoördinaten via TkinterMapView internals."""
        widget  = self.map_widget
        zoom    = widget.zoom
        tile_x  = (lon + 180) / 360 * (2 ** zoom)
        sin_lat = math.sin(math.radians(lat))
        tile_y  = (1 - math.log((1 + sin_lat) / (1 - sin_lat)) / (2 * math.pi)) / 2 * (2 ** zoom)
        upper_left_x, upper_left_y = widget.upper_left_tile_pos
        cx = (tile_x - upper_left_x) * widget.tile_size
        cy = (tile_y - upper_left_y) * widget.tile_size
        return cx, cy

    def AfterPopUpToCalculate(self, chosenSettings):
        amount = 1
        try:
            amount = int(chosenSettings["Aantal"])
        except Exception:
            pass
        formation  = chosenSettings["Formatie"]
        startRobot = chosenSettings["RobotStart"]
        print(f"volgende waardes zijn ingetikt: {amount}, {formation}, {startRobot}")
        self.CalculatePositions(amount=amount)

    def pop_up(self, listOfRobotNames, afterPopup):
        chosenSettings = {"Aantal": None, "Formatie": None, "RobotStart": None}

        def klaarKnopCommand():
            if any(val is None for val in chosenSettings.values()):
                print("selecteer alle waardes voor returneren")
                return
            popup.destroy()
            afterPopup(chosenSettings)

        def change_val(value):
            try:
                int(value)
                chosenSettings["Aantal"] = value
            except Exception:
                pass

        def changeFormation(formation):
            chosenSettings["Formatie"] = formation

        def changeStartRobot(robotName):
            chosenSettings["RobotStart"] = robotName

        popup = customtkinter.CTkToplevel(self)
        popup.title("Instellingen voor berekeningen")
        popup.wm_maxsize(500, 550)
        popup.wm_resizable(False, False)
        popup.wm_transient(self)
        popup.configure(fg_color="white")

        # Hoeveelheid robots
        frame_amount = customtkinter.CTkFrame(popup)
        frame_amount.grid(row=2, column=0, sticky="nw", padx=10, pady=10)
        customtkinter.CTkLabel(frame_amount, text="Hoeveelheid robots:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(5, 0), sticky="nw")
        customtkinter.CTkOptionMenu(frame_amount, values=[str(i) for i in range(1, 11)],
                                    command=change_val).grid(
            row=1, column=0, padx=10, pady=(0, 10), sticky="nw")

        # Formatie
        frame_formation = customtkinter.CTkFrame(popup)
        frame_formation.grid(row=3, column=0, sticky="nw", padx=10, pady=10)
        customtkinter.CTkLabel(frame_formation, text="Welke formatie:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(5, 0), sticky="nw")
        customtkinter.CTkOptionMenu(frame_formation,
                                    values=["CROW-standaard", "Bocht", "Test"],
                                    command=changeFormation).grid(
            row=1, column=0, padx=10, pady=(0, 10), sticky="nw")

        # Huidige robot
        frame_robot = customtkinter.CTkFrame(popup)
        frame_robot.grid(row=4, column=0, sticky="nw", padx=10, pady=10)
        customtkinter.CTkLabel(frame_robot, text="Welke robot:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(5, 0), sticky="nw")
        customtkinter.CTkOptionMenu(frame_robot,
                                    values=[str(i) for i in listOfRobotNames],
                                    command=changeStartRobot).grid(
            row=1, column=0, padx=10, pady=(0, 10), sticky="nw")

        customtkinter.CTkButton(popup, text="Configuratie klaar",
                                command=klaarKnopCommand,
                                border_color="black", border_width=2).grid(
            row=5, column=0, pady=10)

    # ══════════════════════════════════════════════════════════════════════
    # Helplijnen (dichtstbijzijnde punt op NWB-lijn vanuit marker)
    # ══════════════════════════════════════════════════════════════════════

    def CheckNearestPointOfLine(self, coords):
        closestPts = {}
        print("in checknearestpoint")
        try:
            for polyline in self._road_polylines:
                for lat, lon in polyline:
                    distance = self.CalculateDistance(coords[0], coords[1], lat, lon)
                    if distance < 100:
                        closestPts[distance] = [lat, lon]

            closestPtsSorted = dict(sorted(closestPts.items()))
            coordsList = list(closestPtsSorted.values())[:2]
            print("closest point to the marker is: ", coordsList)
            if len(coordsList) < 2:
                print("Niet genoeg punten gevonden voor helplijn")
                return
            self.AddMarker(coords=coordsList[0], markerText="calculated closeMark1")
            self.AddMarker(coords=coordsList[1], markerText="calculated closeMark2")
            self.DrawHelpLine(coords1=coordsList[0], coords2=coordsList[1])
        except Exception as e:
            print("exception in CheckNearestPointOfLine:", e)

    def DrawHelpLine(self, coords1, coords2):
        canvas       = self.map_widget.canvas
        first_marker = list(self.markersDict.keys())[0]
        lat, lon     = first_marker.position
        cx, cy       = self.closest_point_on_segment(
            px=lat, py=lon,
            x1=coords1[0], y1=coords1[1],
            x2=coords2[0], y2=coords2[1]
        )
        latCanvas, lonCanvas = self._latlon_to_canvas(lat, lon)
        cxCanvas,  cyCanvas  = self._latlon_to_canvas(cx, cy)
        canvas.create_oval(cxCanvas - 3, cyCanvas - 3, cxCanvas + 3, cyCanvas + 3,
                           fill="blue", tags=self.THROUGHMARKER)
        canvas.create_line(latCanvas, lonCanvas, cxCanvas, cyCanvas,
                           fill="red", dash=(2, 2), tags=self.THROUGHMARKER)
        print(f"dichtsbijzijnde coordinaat is: {cx}, {cy}")
        self.helpLineMarker[cx, cy] = [lat, lon]

    def draw_infinite_line(self, x1, y1, x2, y2, **kwargs):
        canvas = self.map_widget.canvas
        length = 10000
        dx = x2 - x1
        dy = y2 - y1
        ex1 = x1 - dx * length
        ey1 = y1 - dy * length
        ex2 = x1 + dx * length
        ey2 = y1 + dy * length
        return canvas.create_line(ex1, ey1, ex2, ey2, **kwargs)

    def DrawLineThroughMarker(self, coords):
        canvas = self.map_widget.canvas
        if self.map_widget.zoom < ROAD_DRAW_ZOOM or not self._road_polylines:
            return
        line_width = max(1, self.map_widget.zoom - 16)
        for polyline in self._road_polylines:
            pts = []
            for lat, lon in polyline:
                try:
                    cx, cy = self._latlon_to_canvas(lat, lon)
                    pts.extend([cx, cy])
                except Exception:
                    pass
            if len(pts) >= 4:
                canvas.create_line(
                    *pts,
                    fill="#FFD700",
                    width=line_width,
                    tags=self._ROAD_TAG,
                    capstyle="round",
                    joinstyle="round",
                )
        canvas.tag_raise(self._ROAD_TAG)