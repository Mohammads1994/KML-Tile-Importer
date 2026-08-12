import math

EARTH_RADIUS_M = 6378137.0


def enu_offset(lon, lat, alt, origin_lon, origin_lat, origin_alt):
    """Small-area WGS84 tangent-plane approximation: X=East, Y=North, Z=Up."""
    lat0 = math.radians(origin_lat)
    dlon = math.radians(lon - origin_lon)
    dlat = math.radians(lat - origin_lat)
    x = EARTH_RADIUS_M * math.cos(lat0) * dlon
    y = EARTH_RADIUS_M * dlat
    z = alt - origin_alt
    return x, y, z
