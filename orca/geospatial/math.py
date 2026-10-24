"""Deterministic geodesic and coordinate mathematical operations."""

import math
from orca.models.mission import Coordinate

EARTH_RADIUS_KM = 6371.0088
KM_PER_NAUTICAL_MILE = 1.852


def haversine_distance(coord1: Coordinate, coord2: Coordinate) -> float:
    """Calculate the great-circle distance between two coordinates in kilometers.

    Uses the haversine formula on a spherical Earth model (R = 6371.0088 km).
    """
    lat1 = math.radians(coord1.lat)
    lon1 = math.radians(coord1.lon)
    lat2 = math.radians(coord2.lat)
    lon2 = math.radians(coord2.lon)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(EARTH_RADIUS_KM * c, 3)


def haversine_distance_nm(coord1: Coordinate, coord2: Coordinate) -> float:
    """Calculate distance between two coordinates in nautical miles (NM)."""
    return round(haversine_distance(coord1, coord2) / KM_PER_NAUTICAL_MILE, 3)


def calculate_bearing(origin: Coordinate, target: Coordinate) -> float:
    """Calculate initial compass bearing from origin to target in degrees [0, 360).

    0° = North, 90° = East, 180° = South, 270° = West.
    """
    lat1 = math.radians(origin.lat)
    lat2 = math.radians(target.lat)
    dlon = math.radians(target.lon - origin.lon)

    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

    initial_bearing = math.atan2(y, x)
    degrees = math.degrees(initial_bearing)
    compass_bearing = (degrees + 360.0) % 360.0

    return round(compass_bearing, 2)


def destination_point(origin: Coordinate, bearing_degrees: float, distance_km: float) -> Coordinate:
    """Calculate destination coordinate given start point, bearing, and distance."""
    theta = math.radians(bearing_degrees)
    delta = distance_km / EARTH_RADIUS_KM

    lat1 = math.radians(origin.lat)
    lon1 = math.radians(origin.lon)

    lat2 = math.asin(math.sin(lat1) * math.cos(delta) + math.cos(lat1) * math.sin(delta) * math.cos(theta))
    lon2 = lon1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(lat1),
        math.cos(delta) - math.sin(lat1) * math.sin(lat2),
    )

    dest_lat = math.degrees(lat2)
    dest_lon = (math.degrees(lon2) + 540.0) % 360.0 - 180.0

    return Coordinate(lat=round(dest_lat, 6), lon=round(dest_lon, 6))


def bounding_box(center: Coordinate, radius_km: float) -> tuple[Coordinate, Coordinate]:
    """Calculate axis-aligned bounding box (southwest, northeast) for a radial search area."""
    lat_delta = math.degrees(radius_km / EARTH_RADIUS_KM)
    cos_lat = math.cos(math.radians(center.lat))

    # Protect against division by zero at poles
    lon_delta = math.degrees(radius_km / EARTH_RADIUS_KM / max(cos_lat, 1e-6))

    southwest = Coordinate(
        lat=max(-90.0, round(center.lat - lat_delta, 6)),
        lon=max(-180.0, round(center.lon - lon_delta, 6)),
    )
    northeast = Coordinate(
        lat=min(90.0, round(center.lat + lat_delta, 6)),
        lon=min(180.0, round(center.lon + lon_delta, 6)),
    )
    return (southwest, northeast)
