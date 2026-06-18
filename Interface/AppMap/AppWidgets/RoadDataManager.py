import requests


class RoadDataManager:
    """Manages NWB road data fetching and caching."""
    
    PDOK_WFS_URL = "https://service.pdok.nl/rws/nationaal-wegenbestand-wegen/wfs/v1_0"
    
    def __init__(self):
        self.road_polylines = []
        self.road_fetch_bbox = None
        self.road_fetch_running = False
    
    def fetch_roads_thread(self, bbox):
        """Fetch road data from PDOK WFS in separate thread."""
        print("BBOX is, ", bbox)
        lat_min, lon_min, lat_max, lon_max = bbox
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NWB-overlay/1.0)"}
        
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": "nwbwegen:wegvakken",
            "outputFormat": "application/json; subtype=geojson",
            "srsName": "EPSG:4326",
            "bbox": f"{lat_min},{lon_min},{lat_max},{lon_max},EPSG:4326",
            "count": "2000",
            "CQL_FILTER": "dienstnaam LIKE 'RWS%'"
        }
        
        try:
            resp = requests.get(self.PDOK_WFS_URL, params=params, 
                               headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            print(f"[NWB WFS] {len(features)} wegvakken ontvangen.")
            
            polylines = self._parse_features(features)
            self.road_polylines = polylines
            self.road_fetch_bbox = bbox
        
        except Exception as e:
            print(f"EXCEPTION: [NWB WFS] fout: {e}")
        
        finally:
            self.road_fetch_running = False
    
    def _parse_features(self, features):
        """Parse GeoJSON features into polylines."""
        polylines = []
        for feature in features:
            props = feature.get("properties", {})
            if not props.get("dienstnaam", "").startswith("RWS"):
                continue
            
            geom = feature.get("geometry")
            if geom is None:
                continue
            
            gtype = geom.get("type", "")
            coords = geom.get("coordinates", [])
            
            segments = [coords] if gtype == "LineString" else coords if gtype == "MultiLineString" else []
            
            for seg in segments:
                latlon = [(pt[1], pt[0]) for pt in seg if len(pt) >= 2]
                if len(latlon) >= 2:
                    polylines.append(latlon)
        
        return polylines
    
    def has_data(self):
        """Check if road data is cached."""
        return bool(self.road_polylines)
    
    def clear_cache(self):
        """Clear cached road data."""
        self.road_polylines = []
        self.road_fetch_bbox = None
