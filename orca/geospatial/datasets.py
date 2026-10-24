"""Curated maritime boundaries, MPAs, shipping lanes, and spatial boundary store."""

from typing import Iterable
from shapely.geometry import Point, Polygon

from orca.geospatial.math import haversine_distance
from orca.geospatial.models import MaritimeZone, RestrictionLevel, ZoneType
from orca.models.mission import Coordinate

# -------------------------------------------------------------------------
# Default Curated Indian Coastal Maritime Datasets
# Focused on Southeast Coast (Tamil Nadu, Palk Bay, Gulf of Mannar, Bay of Bengal)
# -------------------------------------------------------------------------

DEFAULT_MARITIME_ZONES: list[MaritimeZone] = [
    # 1. Gulf of Mannar Marine National Park (Core MPA)
    MaritimeZone(
        zone_id="IN-MPA-GULF-MANNAR",
        name="Gulf of Mannar Marine National Park",
        zone_type=ZoneType.MARINE_PROTECTED_AREA,
        restriction_level=RestrictionLevel.STRICT_NO_ENTRY,
        description=(
            "Gulf of Mannar Biosphere Reserve core zone. Commercial mechanized fishing, "
            "trawling, and anchoring are strictly prohibited under the Wildlife Protection Act."
        ),
        coordinates=[
            (9.28, 78.75),
            (9.28, 79.25),
            (8.85, 78.95),
            (8.85, 78.20),
            (9.10, 78.40),
            (9.28, 78.75),
        ],
        buffer_km=3.0,
        metadata={"jurisdiction": "Tamil Nadu Forest Dept / MoEFCC", "gazetted_year": 1986},
    ),
    # 2. Pulicat Marine & Estuarine Protected Sanctuary
    MaritimeZone(
        zone_id="IN-MPA-PULICAT",
        name="Pulicat Marine & Lagoon Sanctuary",
        zone_type=ZoneType.MARINE_PROTECTED_AREA,
        restriction_level=RestrictionLevel.RESTRICTED_FISHING,
        description=(
            "Pulicat Lake & Marine Buffer Sanctuary. Commercial bottom trawling and motorized "
            "seine fishing prohibited to preserve juvenile fish and brackish marine nurseries."
        ),
        coordinates=[
            (13.40, 80.25),
            (13.65, 80.35),
            (13.65, 80.20),
            (13.40, 80.18),
            (13.40, 80.25),
        ],
        buffer_km=2.0,
        metadata={"jurisdiction": "Andhra Pradesh & Tamil Nadu Wildlife", "protection": "Ramsar Site Candidate"},
    ),
    # 3. Chennai & Kamarajar Port Shipping Fairway / TSS
    MaritimeZone(
        zone_id="IN-TSS-CHENNAI",
        name="Chennai & Kamarajar Port Traffic Separation Scheme",
        zone_type=ZoneType.SHIPPING_LANE,
        restriction_level=RestrictionLevel.CAUTION_TRAFFIC,
        description=(
            "High-density commercial shipping channel and tanker approach fairway for Chennai "
            "and Ennore ports. Extreme collision hazard for small artisanal craft; do not cast static nets."
        ),
        coordinates=[
            (13.05, 80.34),
            (13.35, 80.38),
            (13.35, 80.48),
            (13.05, 80.44),
            (13.05, 80.34),
        ],
        buffer_km=1.5,
        metadata={"authority": "Chennai Port Trust & DG Shipping", "fairway_type": "Deep Water Route"},
    ),
    # 4. Indo-Sri Lanka International Maritime Boundary Line (IMBL) Exclusion Zone
    MaritimeZone(
        zone_id="IN-BORDER-IMBL",
        name="Indo-Sri Lanka IMBL Sensitive Border Corridor",
        zone_type=ZoneType.INTERNATIONAL_BOUNDARY,
        restriction_level=RestrictionLevel.STRICT_NO_ENTRY,
        description=(
            "International Maritime Boundary Line (IMBL) exclusion strip in Palk Bay / Gulf of Mannar. "
            "High security perimeter; navigating inside or crossing this border line risks foreign naval interdiction."
        ),
        coordinates=[
            (9.00, 79.40),
            (9.50, 79.55),
            (10.15, 79.85),
            (10.15, 80.05),
            (9.50, 79.75),
            (9.00, 79.60),
            (9.00, 79.40),
        ],
        buffer_km=5.0,
        metadata={"significance": "International Border / Security Risk", "patrolled_by": "Indian Coast Guard"},
    ),
    # 5. Offshore Naval Training & Firing Range
    MaritimeZone(
        zone_id="IN-MIL-EXCLUSION-01",
        name="Naval Offshore Firing & Defense Exercise Zone",
        zone_type=ZoneType.MILITARY_EXCLUSION_ZONE,
        restriction_level=RestrictionLevel.STRICT_NO_ENTRY,
        description=(
            "Indian Navy offshore gunnery and tactical training range. Strict temporary or permanent "
            "no-navigation exclusion zone when military operations are active."
        ),
        coordinates=[
            (12.50, 80.30),
            (12.85, 80.35),
            (12.85, 80.60),
            (12.50, 80.55),
            (12.50, 80.30),
        ],
        buffer_km=2.5,
        metadata={"authority": "Eastern Naval Command", "status": "Periodic / Active Range"},
    ),
]


class MaritimeBoundaryStore:
    """In-memory store providing spatial indexing and query methods for maritime boundaries."""

    def __init__(self, initial_zones: Iterable[MaritimeZone] | None = None) -> None:
        self._zones: dict[str, MaritimeZone] = {}
        self._polygons: dict[str, Polygon] = {}

        zones_to_load = initial_zones if initial_zones is not None else DEFAULT_MARITIME_ZONES
        for zone in zones_to_load:
            self.add_zone(zone)

    def add_zone(self, zone: MaritimeZone) -> None:
        """Register a new maritime zone and pre-compute its Shapely polygon."""
        self._zones[zone.zone_id] = zone
        self._polygons[zone.zone_id] = zone.to_polygon()

    def get_zone(self, zone_id: str) -> MaritimeZone | None:
        """Retrieve a zone by its identifier."""
        return self._zones.get(zone_id)

    def get_all_zones(self) -> list[MaritimeZone]:
        """Return all registered maritime zones."""
        return list(self._zones.values())

    def find_zones_containing(self, coord: Coordinate) -> list[MaritimeZone]:
        """Find all zones whose polygon strictly contains the given offshore coordinate."""
        pt = Point(coord.lon, coord.lat)
        matched: list[MaritimeZone] = []
        for zone_id, poly in self._polygons.items():
            if poly.contains(pt) or poly.touches(pt):
                matched.append(self._zones[zone_id])
        return matched

    def find_zones_within_buffer(
        self,
        coord: Coordinate,
        extra_margin_km: float = 0.0,
    ) -> list[tuple[MaritimeZone, float]]:
        """Find zones where coordinate is within boundary buffer distance.

        Returns list of (MaritimeZone, distance_to_zone_km).
        """
        results: list[tuple[MaritimeZone, float]] = []

        for zone_id, zone in self._zones.items():
            dist_km = self.distance_to_zone_km(coord, zone_id)
            effective_buffer = zone.buffer_km + extra_margin_km
            if dist_km <= effective_buffer:
                results.append((zone, dist_km))

        return sorted(results, key=lambda x: x[1])

    def distance_to_zone_km(self, coord: Coordinate, zone_id: str) -> float:
        """Calculate minimum geodesic distance from coordinate to zone boundary vertices in km.

        If point is inside polygon, returns 0.0 km.
        """
        poly = self._polygons.get(zone_id)
        if poly is None:
            raise KeyError(f"Zone {zone_id} not registered.")

        pt = Point(coord.lon, coord.lat)
        if poly.contains(pt) or poly.touches(pt):
            return 0.0

        zone = self._zones[zone_id]
        min_dist = float("inf")
        # Check distance to all polygon perimeter sample points/vertices
        for v_lat, v_lon in zone.coordinates:
            d = haversine_distance(coord, Coordinate(lat=v_lat, lon=v_lon))
            if d < min_dist:
                min_dist = d

        return round(min_dist, 3)

    def get_nearest_boundary_distance(self, coord: Coordinate) -> tuple[MaritimeZone | None, float | None]:
        """Find the nearest maritime zone boundary and its distance in km."""
        if not self._zones:
            return (None, None)

        nearest_zone: MaritimeZone | None = None
        min_dist = float("inf")

        for zone_id, zone in self._zones.items():
            d = self.distance_to_zone_km(coord, zone_id)
            if d < min_dist:
                min_dist = d
                nearest_zone = zone

        return (nearest_zone, round(min_dist, 3) if nearest_zone else None)
