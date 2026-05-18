from os import close
from tracemalloc import start
import customtkinter
from tkintermapview import TkinterMapView
import math
import threading
import requests
from geopy.geocoders import Nominatim
from AppMap.AppWidgets.FormationParser import parse_input
from AppMap.AppWidgets.PopupWindow import PopupWindow

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
    """
    if len(polyline_latlon) < 2:
        return list(polyline_latlon)

    ref_lat, ref_lon = polyline_latlon[0]
    xy = [_latlon_to_local_xy(lat, lon, ref_lat, ref_lon)
          for lat, lon in polyline_latlon]

    normals = []
    for i in range(len(xy) - 1):
        dx = xy[i + 1][0] - xy[i][0]
        dy = xy[i + 1][1] - xy[i][1]
        seg_len = math.hypot(dx, dy)
        if seg_len < 1e-9:
            normals.append((0.0, 0.0))
        else:
            normals.append((dy / seg_len, -dx / seg_len))

    result = []
    for i in range(len(xy)):
        if i == 0:
            nx, ny = normals[0]
        elif i == len(xy) - 1:
            nx, ny = normals[-1]
        else:
            nx = (normals[i - 1][0] + normals[i][0]) / 2
            ny = (normals[i - 1][1] + normals[i][1]) / 2
            n_len = math.hypot(nx, ny)
            if n_len > 1e-9:
                nx /= n_len
                ny /= n_len

        projection = offset_x * nx + offset_y * ny
        new_x = xy[i][0] + projection * nx
        new_y = xy[i][1] + projection * ny
        result.append(_local_xy_to_latlon(new_x, new_y, ref_lat, ref_lon))

    return result


def _polyline_length_along(polyline_latlon):
    """
    Geeft een lijst van cumulatieve afstanden (in meters) langs de polyline.
    Lengte van de lijst = len(polyline_latlon).
    """
    ref_lat, ref_lon = polyline_latlon[0]
    xy = [_latlon_to_local_xy(lat, lon, ref_lat, ref_lon)
          for lat, lon in polyline_latlon]
    dists = [0.0]
    for i in range(1, len(xy)):
        seg = math.hypot(xy[i][0] - xy[i-1][0], xy[i][1] - xy[i-1][1])
        dists.append(dists[-1] + seg)
    return dists


def _project_onto_polyline(lat, lon, polyline_latlon):
    """
    Projecteert (lat, lon) op de polyline.

    Returns:
        (foot_lat, foot_lon, along_dist, segment_idx, t)
        along_dist  : afstand langs de polyline tot het voetloodpunt (meters)
        segment_idx : index van het segment waarop geprojecteerd is
        t           : parameter [0,1] binnen dat segment
    """
    ref_lat, ref_lon = polyline_latlon[0]
    px, py = _latlon_to_local_xy(lat, lon, ref_lat, ref_lon)
    xy = [_latlon_to_local_xy(la, lo, ref_lat, ref_lon) for la, lo in polyline_latlon]

    cum_dists = [0.0]
    for i in range(1, len(xy)):
        cum_dists.append(cum_dists[-1] + math.hypot(xy[i][0]-xy[i-1][0], xy[i][1]-xy[i-1][1]))

    best_dist   = float("inf")
    best_foot   = (px, py)
    best_along  = 0.0
    best_seg    = 0
    best_t      = 0.0

    for i in range(len(xy) - 1):
        x1, y1 = xy[i]
        x2, y2 = xy[i + 1]
        dx, dy  = x2 - x1, y2 - y1
        len_sq  = dx * dx + dy * dy
        if len_sq < 1e-9:
            continue
        t  = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
        fx = x1 + t * dx
        fy = y1 + t * dy
        d  = math.hypot(px - fx, py - fy)
        if d < best_dist:
            best_dist  = d
            best_foot  = (fx, fy)
            best_along = cum_dists[i] + t * math.hypot(dx, dy)
            best_seg   = i
            best_t     = t

    foot_lat, foot_lon = _local_xy_to_latlon(best_foot[0], best_foot[1], ref_lat, ref_lon)
    return foot_lat, foot_lon, best_along, best_seg, best_t


def _point_along_polyline(polyline_latlon, along_dist):
    """
    Geeft het punt op de polyline op afstand `along_dist` meters vanaf het begin.
    Knipt af aan begin of einde als along_dist buiten bereik valt.
    """
    ref_lat, ref_lon = polyline_latlon[0]
    xy = [_latlon_to_local_xy(la, lo, ref_lat, ref_lon) for la, lo in polyline_latlon]

    cum = 0.0
    for i in range(len(xy) - 1):
        seg_len = math.hypot(xy[i+1][0]-xy[i][0], xy[i+1][1]-xy[i][1])
        if cum + seg_len >= along_dist:
            t  = (along_dist - cum) / seg_len if seg_len > 1e-9 else 0.0
            lx = xy[i][0] + t * (xy[i+1][0] - xy[i][0])
            ly = xy[i][1] + t * (xy[i+1][1] - xy[i][1])
            return _local_xy_to_latlon(lx, ly, ref_lat, ref_lon)
        cum += seg_len

    # Voorbij het einde → laatste punt teruggeven
    return polyline_latlon[-1]


class AppFrameMap(customtkinter.CTkFrame):
    def __init__(self, master, sendCallback, resetCallback):
        super().__init__(master)

        self.sendMessageCallback = sendCallback
        self.resetInterface = resetCallback

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=14)
        self.grid_rowconfigure(2, weight=0)

        # ── Map widget ────────────────────────────────────────────────────
        self.map_widget = TkinterMapView(self, corner_radius=5, database_path="map_tiles.db")
        self.map_widget.grid(row=1, column=0, columnspan=3, sticky="nswe",
                             padx=(10, 10), pady=(0, 0))

        self.label = customtkinter.CTkLabel(
            self, text="Map:", fg_color='#01a6f8',
            width=100, height=20, font=('Bold', 28), corner_radius=5
        )
        self.label.grid(row=0, column=0, sticky="nw", padx=(8, 8), pady=(5, 5))

        self.map_widget.bind("<MouseWheel>", self._on_scroll)
        self.map_widget.canvas.bind("<MouseWheel>", self._on_scroll, add="+")

        # ── Tile server control ───────────────────────────────────────────
        self.control_frame = customtkinter.CTkFrame(self)
        self.control_frame.grid(row=2, column=0, sticky="nw", padx=10, pady=10)

        customtkinter.CTkLabel(self.control_frame, text="Soort map:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(5, 0), sticky="nw")

        self.map_option_menu = customtkinter.CTkOptionMenu(
            self.control_frame,
            values=["Map normaal", "Map satelliet"],
            command=self.change_map
        )
        self.map_option_menu.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="nw")

        customtkinter.CTkLabel(self.control_frame, text="Reset scherm:", anchor="w").grid(
            row=4, column=0, padx=10, pady=(5, 0), sticky="nw")

        customtkinter.CTkButton(
            self.control_frame, text="Reset",
            command=self.ResetButtonPressed, border_color="black", border_width=2, fg_color="red"
        ).grid(row=5, column=0, padx=10, pady=(0,5), sticky="nw")

        #---Initial map settings------------
        self.map_widget.set_tile_server(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            max_zoom=21
        )
        self.map_widget.set_position(52.0172355, 4.3712940)
        self.map_option_menu.set("Map satelliet")
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
            command=self.DeletePositionsButtonPressed, border_color="black", border_width=2, fg_color="red"
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
        self._road_polylines     = []
        self._road_fetch_bbox    = None
        self._road_refresh_job   = None
        self._road_fetch_running = False
        self.geolocator          = Nominatim(user_agent="my_app")
        self.helpLineMarker      = {}

        # ── Vluchtstrook state ─────────────────────────────────────────────
        # Slechts ÉÉN verschoven polyline — de dichtstbijzijnde NWB-lijn
        # verschoven zodat hij door de marker gaat.
        self._offset_polyline_single = None   # list of (lat, lon)  ← nieuw
        self._offset_polylines       = []     # behouden voor compatibiliteit (leeg houden)
        self.incidentFrame = None

        self.popupWindow = PopupWindow(self, self.AfterPopUpToCalculate)

    # ══════════════════════════════════════════════════════════════════════
    # Map controls
    # ══════════════════════════════════════════════════════════════════════

    def switchTest(self):
        print(self.testPositionModeVar.get())

    def change_map(self, new_map: str):
        if new_map == "Map normaal":
            self.MAX_ZOOM = 20
            self.map_widget.set_tile_server(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
                max_zoom=20)
        elif new_map == "Map satelliet":
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

    # ══════════════════════════════════════════════════════════════════════
    # NWB road overlay
    # ══════════════════════════════════════════════════════════════════════

    def _schedule_road_refresh(self):
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

        if (self._road_fetch_bbox is not None
                and self._bbox_contains(self._road_fetch_bbox, bbox)
                and self._road_polylines):
            self._draw_cached_roads()
            self._draw_offset_roads()
            return

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
    # GEWIJZIGD: alleen de dichtstbijzijnde NWB-polyline wordt verschoven
    # en getoond — geen massa aan oranje lijnen meer.
    # ══════════════════════════════════════════════════════════════════════

    def _find_nearest_polyline(self, lat, lon):
        """Geeft de NWB-polyline die het dichtst bij (lat, lon) ligt."""
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
                cx_f = x1 + t * dx
                cy_f = y1 + t * dy
                d  = math.hypot(px - cx_f, py - cy_f)
                if d < best_dist:
                    best_dist     = d
                    best_polyline = polyline

        return best_polyline

    def _compute_offset_vector(self, marker_lat, marker_lon, polyline):
        """
        Berekent de offset-vector (meters, lokaal Cartesisch) van de
        dichtstbijzijnde punt op de polyline naar de marker.
        """
        ref_lat, ref_lon = polyline[0]
        px, py = _latlon_to_local_xy(marker_lat, marker_lon, ref_lat, ref_lon)

        best_dist = float("inf")
        best_foot = (px, py)

        for i in range(len(polyline) - 1):
            x1, y1 = _latlon_to_local_xy(*polyline[i],     ref_lat, ref_lon)
            x2, y2 = _latlon_to_local_xy(*polyline[i + 1], ref_lat, ref_lon)
            dx, dy  = x2 - x1, y2 - y1
            len_sq  = dx * dx + dy * dy
            if len_sq < 1e-9:
                continue
            t  = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
            fx = x1 + t * dx
            fy = y1 + t * dy
            d  = math.hypot(px - fx, py - fy)
            if d < best_dist:
                best_dist = d
                best_foot = (fx, fy)

        offset_x = px - best_foot[0]
        offset_y = py - best_foot[1]
        print(f"[Offset] vector ({offset_x:.1f}, {offset_y:.1f}) m, "
              f"afstand {best_dist:.1f} m")
        return offset_x, offset_y

    def _build_offset_polylines(self, marker_lat, marker_lon):
        """
        FIX: verschuift alleen de dichtstbijzijnde NWB-polyline — niet alle.
        Slaat het resultaat op in self._offset_polyline_single.
        """
        nearest = self._find_nearest_polyline(marker_lat, marker_lon)
        if nearest is None:
            print("[Offset] Geen NWB-data beschikbaar.")
            self._offset_polyline_single = None
            return

        offset_x, offset_y = self._compute_offset_vector(marker_lat, marker_lon, nearest)

        offset_dist = math.hypot(offset_x, offset_y)
        if offset_dist < 0.5:
            print("[Offset] Marker staat al op de weg; geen offset toegepast.")
            # Gebruik de originele lijn als vluchtstrook-referentie
            self._offset_polyline_single = nearest
            return

        self._offset_polyline_single = offset_polyline(nearest, offset_x, offset_y)
        print(f"[Offset] 1 polyline verschoven met {offset_dist:.1f} m.")

    def _draw_offset_roads(self):
        """
        FIX: tekent alleen de enkele verschoven vluchtstrook-polyline (oranje).
        """
        canvas = self.map_widget.canvas
        canvas.delete(self._OFFSET_TAG)

        if self.map_widget.zoom < ROAD_DRAW_ZOOM or self._offset_polyline_single is None:
            return

        line_width = max(1, self.map_widget.zoom - 16)
        pts = []
        for lat, lon in self._offset_polyline_single:
            try:
                cx, cy = self._latlon_to_canvas(lat, lon)
                pts.extend([cx, cy])
            except Exception:
                pass

        if len(pts) >= 4:
            canvas.create_line(
                *pts,
                fill="#FF6600",
                width=line_width,
                tags=self._OFFSET_TAG,
                capstyle="round",
                joinstyle="round",
            )

        canvas.tag_raise(self._OFFSET_TAG)

    def _snap_to_offset_polyline(self, lat, lon):
        """
        Projecteert (lat, lon) op de enkele verschoven vluchtstrook-polyline.
        """
        if self._offset_polyline_single is None:
            return lat, lon

        foot_lat, foot_lon, _, _, _ = _project_onto_polyline(
            lat, lon, self._offset_polyline_single)
        return foot_lat, foot_lon

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
            self.popupWindow.pop_up()
            #self.pop_up(["robot1", "robot2"], self.AfterPopUpToCalculate)

    def CalculatePositions(self, distance=10, amount=1, motherBotPos=1):
        """
        FIX: posities worden langs de vluchtstrook-polyline berekend,
        niet via een losse geodetische berekening in de lucht.

        Werkwijze:
        1. Bouw de parallel-offset polyline op basis van de eerste marker.
        2. Projecteer de marker op die polyline → startpunt + startafstand.
        3. Bereken elke volgende positie door startafstand + i*distance op
           te zoeken langs de polyline → punt ligt gegarandeerd OP de lijn.
        """
        first_marker = list(self.markersDict.keys())[0]
        lat, lon     = first_marker.position
        direction    = self.marker_lines[first_marker][1]

        # Stap 1: bouw de (enkele) vluchtstrook-polyline
        self._build_offset_polylines(lat, lon)

        if self._offset_polyline_single is None:
            print("[Calc] Geen vluchtstrook-polyline beschikbaar.")
            return

        # Stap 2: projecteer de marker op de vluchtstrook → startafstand
        _, _, start_along, _, _ = _project_onto_polyline(
            lat, lon, self._offset_polyline_single)
        print(f"[Calc] Startafstand langs vluchtstrook: {start_along:.1f} m")

        # Stap 3: bereken posities op vaste afstanden langs de polyline
        for i in range(1, amount + 1):
            target_along = start_along + distance * i
            pos_lat, pos_lon = _point_along_polyline(
                self._offset_polyline_single, target_along)
            print(f"[Calc] Kegel {i}: {pos_lat:.6f}, {pos_lon:.6f} "
                  f"(+{distance * i:.0f} m langs lijn)")
            self.AddMarker((pos_lat, pos_lon), direction,
                           markerText=f"calculated{i}")

        # Herteken de vluchtstrook overlay
        self._draw_offset_roads()

    def calculate_destination(self, lat, lon, bearing, distanceFirst, posList):
        """Behouden voor eventueel ander gebruik; wordt niet meer aangeroepen vanuit CalculatePositions."""
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

    def NormalisePositionDegreeValues(self, degrees, situation):
        if situation == 1 and degrees is not None:
            return degrees + 90

    def DeletePositions(self, nameToDelete="calculated"):
        for key in [k for k, v in self.markersDict.items() if nameToDelete in v]:
            del self.markersDict[key]
            key.delete()
        for key in [k for k, v in self.marker_lines.items() if nameToDelete in v[0]]:
            self.map_widget.canvas.delete(self.marker_lines[key][0])
            del self.marker_lines[key]

    def DeletePositionsButtonPressed(self):
        canvas = self.map_widget.canvas
        canvas.delete(self._OFFSET_TAG)
        self._offset_polyline_single = None   # ← reset de enkele offset-lijn
        self._offset_polylines       = []
        self.DeletePositions()

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
        print("adding location")
        if self.incidentFrame is not None:
            print("there already is a frame")
            return
        location = location.raw["address"]
        print(location)
        road  = location.get("road")
        city  = location.get("city")
        state = location.get("state")
        self.incidentFrame = customtkinter.CTkFrame(self.controlFramePositionButtons)
        self.incidentFrame.grid(row=0, column=3, rowspan=2, sticky="ne", padx=10, pady=10)

        customtkinter.CTkLabel(
            self.incidentFrame,
            text="Incidentlocatie:",
            font=("Arial", 14, "bold"),
            fg_color='#01a6f8',
            corner_radius=5,
            text_color="black"
        ).grid(row=0, column=0, padx=10, pady=(5,0), sticky="w")

        customtkinter.CTkLabel(
            self.incidentFrame,
            text=f"{road}, {city}, {state}",
            fg_color='#01a6f8',
            corner_radius=5,
            text_color="black"
        ).grid(row=1, column=0, padx=10, pady=(0,5), sticky="w")

        customtkinter.CTkButton(
            self.incidentFrame, text="Ga naar positie",
            command=self.GoToCoords, border_color="black", border_width=2, fg_color="green"
        ).grid(row=2, column=0, padx=10, pady=10, sticky="nw")

    def GoToCoords(self):
        coords = next(iter(self.markersDict))
        lat, lon = coords.position
        self.map_widget.set_position(lat, lon)
        self.map_widget.set_zoom(19)
        self._on_scroll()

    def _latlon_to_canvas(self, lat, lon):
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

    def ResetButtonPressed(self):
        self.resetInterface()

    def Reset(self):
        print("map reset")
        try:
            self.incidentFrame.grid_forget()
            self.incidentFrame.destroy()
            self.incidentFrame = None
            markerslist = [k for k, v in self.markersDict.items()]
            for key in markerslist:
                del self.markersDict[key]
                key.delete()
            markerslist2 = [k for k, v in self.marker_lines.items()]
            for key in markerslist2:
                self.map_widget.canvas.delete(self.marker_lines[key][0])
                del self.marker_lines[key]
            canvas = self.map_widget.canvas
            canvas.delete(self._OFFSET_TAG)
            self._offset_polyline_single = None
            self._offset_polylines       = []
        except Exception as e:
            print("error hier is = ", e)