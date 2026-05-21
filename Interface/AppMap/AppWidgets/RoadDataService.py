import threading
import requests

PDOK_WFS_URL   = "https://service.pdok.nl/rws/nationaal-wegenbestand-wegen/wfs/v1_0"

class RoadDataService:
    def __init__(self, master):
        self.master = master
        pass 
    

    def _get_viewport_bbox(self):
        w = self.master.map_widget.winfo_width()
        h = self.master.map_widget.winfo_height()
        if w < 10 or h < 10:
            return None
        try:
            lat_nw, lon_nw = self.master.convert_canvas_coords_to_decimal_coords(0, 0)
            lat_se, lon_se = self.master.map_widget.convert_canvas_coords_to_decimal_coords(w, h)
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
        