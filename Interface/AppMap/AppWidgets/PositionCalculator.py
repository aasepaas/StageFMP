import math
from AppMap.AppWidgets.FormationCalculator import (
    _project_onto_polyline, _point_along_polyline,
    latlon_to_local_xy, local_xy_to_latlon
)



# ─────────────────────────────────────────────────────────────────────────────
#  CROW-afstanden conform de richtlijn (zie afbeelding)
#
#  De overgangszone bestaat uit 2 schuine kegels:
#    kegel 1 en kegel 2 staan loodrecht op de rijrichting verschoven
#    (dwars op de vluchtstrook), samen goed voor 50 m overkruisafstand.
#
#  De afstand langs de vluchtstrook per kegel in de schuine sectie:
#    - conform CROW 96b is de "insteekastand" 50 m voor 2 kegels,
#      dus 25 m per stap langs de lijn.
#  De zijdelingse verschuiving per stap (naar de rijbaan toe):
#    - de helft van de totale laterale offset (halve rijstrookbreedte ~1.75 m).
#
#  Vanaf kegel 3 staan de kegels parallel aan de vluchtstrooklijn,
#  met 10 m tussenafstand.
# ─────────────────────────────────────────────────────────────────────────────
 
CROW_TAPER_STEPS      = 2        # aantal schuine kegels (1 en 2)
CROW_TAPER_ALONG_M    = 25.0     # afstand langs lijn per schuine kegel (m)
CROW_PARALLEL_DIST_M  = 10.0     # afstand langs lijn voor parallelle kegels (m)
CROW_LATERAL_TOTAL_M  = 3.5      # totale zijdelingse verschuiving in de taper (m)
#   (bij een rijstrookbreedte van ~3.5 m schuiven we over de halve rijstrook)
 
 
def _get_segment_direction(polyline_latlon, along_dist):
    """
    Geeft de rijrichting (dx_norm, dy_norm) in lokale meters op positie
    `along_dist` langs de polyline.
    """
    ref_lat, ref_lon = polyline_latlon[0]
    xy = [latlon_to_local_xy(la, lo, ref_lat, ref_lon)
          for la, lo in polyline_latlon]
 
    cum = 0.0
    for i in range(len(xy) - 1):
        seg_len = math.hypot(xy[i+1][0]-xy[i][0], xy[i+1][1]-xy[i][1])
        if cum + seg_len >= along_dist or i == len(xy) - 2:
            dx = xy[i+1][0] - xy[i][0]
            dy = xy[i+1][1] - xy[i][1]
            norm = math.hypot(dx, dy)
            if norm < 1e-9:
                return (1.0, 0.0), ref_lat, ref_lon
            return (dx/norm, dy/norm), ref_lat, ref_lon
        cum += seg_len
 
    # fallback: laatste segment
    dx = xy[-1][0] - xy[-2][0]
    dy = xy[-1][1] - xy[-2][1]
    norm = math.hypot(dx, dy)
    return (dx/norm, dy/norm) if norm > 1e-9 else (1.0, 0.0), ref_lat, ref_lon
 


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


    @staticmethod
    def calculate_crow_positions(marker_lat, marker_lon, direction,
                                 offset_polyline, amount):
        """
        Berekent `amount` kegels volgens de CROW-afzettingsrichtlijn:
 
          - Kegel 1 & 2  : schuine overgangszone (taper).
                           Elke stap = CROW_TAPER_ALONG_M meter langs de lijn
                           + een zijdelingse verschuiving richting de rijbaan.
                           Kegel 1 heeft de grootste laterale offset (dichtst
                           bij de rijbaan), kegel 2 een kleinere offset.
          - Kegel 3+     : parallel aan de vluchtstrooklijn,
                           CROW_PARALLEL_DIST_M meter tussenafstand.
 
        De laterale offset-richting (loodrechte kant van de polyline richting
        rijbaan) wordt automatisch bepaald uit de polyline-geometrie.
 
        Returns: lijst van (lat, lon, direction) tuples.
        """
        if offset_polyline is None:
            print("[CROW] Geen vluchtstrook-polyline beschikbaar.")
            return []
 
        _, _, start_along, _, _ = _project_onto_polyline(
            marker_lat, marker_lon, offset_polyline)
        print(f"[CROW] Startafstand langs vluchtstrook: {start_along:.1f} m")
 
        ref_lat, ref_lon = offset_polyline[0]
        positions = []
 
        for i in range(1, amount + 1):
            if i <= CROW_TAPER_STEPS:
                # ── Schuine zone (kegel 1 en 2) ───────────────────────────
                along = start_along + CROW_TAPER_ALONG_M * i
 
                # Basispositie op de vluchtstrooklijn
                base_lat, base_lon = _point_along_polyline(offset_polyline, along)
 
                # Rijrichting op dit punt (lokale meters)
                (tx, ty), r_lat, r_lon = _get_segment_direction(
                    offset_polyline, along)
 
                # Loodrechte richting (naar rijbaan = linkerzijde in NL)
                # Links van rijrichting: (-ty, tx)
                perp_x = -ty
                perp_y =  tx
 
                # De laterale offset neemt af: kegel 1 het verst, kegel 2 minder
                # fraction: i=1 → 2/2 = 1.0, i=2 → 1/2 = 0.5
                fraction = (CROW_TAPER_STEPS - i + 1) / CROW_TAPER_STEPS
                lateral_m = CROW_LATERAL_TOTAL_M * fraction
 
                # Zet offset om naar lat/lon
                bx, by = latlon_to_local_xy(base_lat, base_lon, ref_lat, ref_lon)
                nx = bx + perp_x * lateral_m
                ny = by + perp_y * lateral_m
                pos_lat, pos_lon = local_xy_to_latlon(nx, ny, ref_lat, ref_lon)
 
                print(f"[CROW] Kegel {i} (schuin): {pos_lat:.6f}, {pos_lon:.6f} "
                      f"(along={along:.1f} m, lateral={lateral_m:.2f} m)")
 
            else:
                # ── Parallelle zone (kegel 3 en verder) ──────────────────
                parallel_idx = i - CROW_TAPER_STEPS   # 1, 2, 3, …
                along = (start_along
                         + CROW_TAPER_ALONG_M * CROW_TAPER_STEPS
                         + CROW_PARALLEL_DIST_M * parallel_idx)
 
                pos_lat, pos_lon = _point_along_polyline(offset_polyline, along)
                print(f"[CROW] Kegel {i} (parallel): {pos_lat:.6f}, {pos_lon:.6f} "
                      f"(along={along:.1f} m)")
 
            positions.append((pos_lat, pos_lon, direction))
 
        return positions
