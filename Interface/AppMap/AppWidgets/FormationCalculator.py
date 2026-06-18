import math



def latlon_to_local_xy(lat, lon, ref_lat, ref_lon):
    """Converteert lat/lon naar lokale Cartesische meters t.o.v. referentiepunt."""
    R = 6371000
    x = math.radians(lon - ref_lon) * R * math.cos(math.radians(ref_lat))
    y = math.radians(lat - ref_lat) * R
    return x, y


def local_xy_to_latlon(x, y, ref_lat, ref_lon):
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
    xy = [latlon_to_local_xy(lat, lon, ref_lat, ref_lon)
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
        result.append(local_xy_to_latlon(new_x, new_y, ref_lat, ref_lon))

    return result


def _polyline_length_along(polyline_latlon):
    """
    Geeft een lijst van cumulatieve afstanden (in meters) langs de polyline.
    Lengte van de lijst = len(polyline_latlon).
    """
    ref_lat, ref_lon = polyline_latlon[0]
    xy = [latlon_to_local_xy(lat, lon, ref_lat, ref_lon)
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
    px, py = latlon_to_local_xy(lat, lon, ref_lat, ref_lon)
    xy = [latlon_to_local_xy(la, lo, ref_lat, ref_lon) for la, lo in polyline_latlon]

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

    foot_lat, foot_lon = local_xy_to_latlon(best_foot[0], best_foot[1], ref_lat, ref_lon)
    return foot_lat, foot_lon, best_along, best_seg, best_t


def _point_along_polyline(polyline_latlon, along_dist):
    """
    Geeft het punt op de polyline op afstand `along_dist` meters vanaf het begin.
    Knipt af aan begin of einde als along_dist buiten bereik valt.
    """
    ref_lat, ref_lon = polyline_latlon[0]
    xy = [latlon_to_local_xy(la, lo, ref_lat, ref_lon) for la, lo in polyline_latlon]

    cum = 0.0
    for i in range(len(xy) - 1):
        seg_len = math.hypot(xy[i+1][0]-xy[i][0], xy[i+1][1]-xy[i][1])
        if cum + seg_len >= along_dist:
            t  = (along_dist - cum) / seg_len if seg_len > 1e-9 else 0.0
            lx = xy[i][0] + t * (xy[i+1][0] - xy[i][0])
            ly = xy[i][1] + t * (xy[i+1][1] - xy[i][1])
            return local_xy_to_latlon(lx, ly, ref_lat, ref_lon)
        cum += seg_len

    # Voorbij het einde → laatste punt teruggeven
    return polyline_latlon[-1]