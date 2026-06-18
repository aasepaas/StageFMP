import math
from AppMap.AppWidgets.FormationCalculator import (
    _project_onto_polyline, _point_along_polyline,
    latlon_to_local_xy, local_xy_to_latlon
)

 

 


class PositionCalculator:
    """Calculates robot positions along polylines."""
    
    @staticmethod
    def calculate_positions(marker_lat, marker_lon, direction, offset_polyline, 
                           distance=10, amount=1):
        """
        Calculate robot positions along offset polyline.
        Returns list of (lat, lon, direction) tuples.
        """
        if offset_polyline is None:
            print("[Calc] Geen vluchtstrook-polyline beschikbaar.")
            return []
        
        _, _, start_along, _, _ = _project_onto_polyline(
            marker_lat, marker_lon, offset_polyline)
        print(f"[Calc] Startafstand langs vluchtstrook: {start_along:.1f} m")
        
        positions = []
        for i in range(1, amount + 1):
            target_along = start_along + distance * i
            pos_lat, pos_lon = _point_along_polyline(offset_polyline, target_along)
            print(f"[Calc] Kegel {i}: {pos_lat:.6f}, {pos_lon:.6f} (+{distance * i:.0f} m langs lijn)")
            positions.append((pos_lat, pos_lon, direction))
        
        return positions


    
