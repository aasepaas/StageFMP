import math
from AppMap.AppWidgets.FormationCalculator import (
    latlon_to_local_xy, offset_polyline, _project_onto_polyline
)


class OffsetPolylineManager:
    """Manages offset polyline calculations for vluchtstrook."""
    
    def __init__(self):
        self.offset_polyline_single = None
    
    def find_nearest_polyline(self, lat, lon, polylines):
        """Find nearest polyline to given coordinates."""
        if not polylines:
            return None
        
        best_polyline = None
        best_dist = float("inf")
        
        for polyline in polylines:
            ref_lat, ref_lon = polyline[0]
            px, py = latlon_to_local_xy(lat, lon, ref_lat, ref_lon)
            
            for i in range(len(polyline) - 1):
                x1, y1 = latlon_to_local_xy(*polyline[i], ref_lat, ref_lon)
                x2, y2 = latlon_to_local_xy(*polyline[i + 1], ref_lat, ref_lon)
                dx, dy = x2 - x1, y2 - y1
                len_sq = dx * dx + dy * dy
                
                if len_sq < 1e-9:
                    continue
                
                t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
                cx_f = x1 + t * dx
                cy_f = y1 + t * dy
                d = math.hypot(px - cx_f, py - cy_f)
                
                if d < best_dist:
                    best_dist = d
                    best_polyline = polyline
        
        return best_polyline
    
    def compute_offset_vector(self, marker_lat, marker_lon, polyline):
        """Compute offset vector from polyline to marker."""
        ref_lat, ref_lon = polyline[0]
        px, py = latlon_to_local_xy(marker_lat, marker_lon, ref_lat, ref_lon)
        
        best_dist = float("inf")
        best_foot = (px, py)
        
        for i in range(len(polyline) - 1):
            x1, y1 = latlon_to_local_xy(*polyline[i], ref_lat, ref_lon)
            x2, y2 = latlon_to_local_xy(*polyline[i + 1], ref_lat, ref_lon)
            dx, dy = x2 - x1, y2 - y1
            len_sq = dx * dx + dy * dy
            
            if len_sq < 1e-9:
                continue
            
            t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
            fx = x1 + t * dx
            fy = y1 + t * dy
            d = math.hypot(px - fx, py - fy)
            
            if d < best_dist:
                best_dist = d
                best_foot = (fx, fy)
        
        offset_x = px - best_foot[0]
        offset_y = py - best_foot[1]
        print(f"[Offset] vector ({offset_x:.1f}, {offset_y:.1f}) m, afstand {best_dist:.1f} m")
        return offset_x, offset_y
    
    def build_offset_polylines(self, marker_lat, marker_lon, polylines):
        """Build offset polyline based on marker position."""
        nearest = self.find_nearest_polyline(marker_lat, marker_lon, polylines)
        
        if nearest is None:
            print("[Offset] Geen NWB-data beschikbaar.")
            self.offset_polyline_single = None
            return
        
        offset_x, offset_y = self.compute_offset_vector(marker_lat, marker_lon, nearest)
        offset_dist = math.hypot(offset_x, offset_y)
        
        if offset_dist < 0.5:
            print("[Offset] Marker staat al op de weg; geen offset toegepast.")
            self.offset_polyline_single = nearest
            return
        
        self.offset_polyline_single = offset_polyline(nearest, offset_x, offset_y)
        print(f"[Offset] 1 polyline verschoven met {offset_dist:.1f} m.")
    
    def snap_to_offset_polyline(self, lat, lon):
        """Project point onto offset polyline."""
        if self.offset_polyline_single is None:
            return lat, lon
        
        foot_lat, foot_lon, _, _, _ = _project_onto_polyline(
            lat, lon, self.offset_polyline_single)
        return foot_lat, foot_lon
    
    def get_offset_polyline(self):
        """Get current offset polyline."""
        return self.offset_polyline_single
    
    def clear(self):
        """Clear offset polyline."""
        self.offset_polyline_single = None
