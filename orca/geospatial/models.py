"""Geospatial domain models and maritime boundary definitions."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
from shapely.geometry import Polygon

from orca.models.candidate import SafetyEvaluation
from orca.models.mission import Coordinate


class ZoneType(str, Enum):
    """Categorical type of maritime zone."""

    MARINE_PROTECTED_AREA = "MARINE_PROTECTED_AREA"
    MILITARY_EXCLUSION_ZONE = "MILITARY_EXCLUSION_ZONE"
    SHIPPING_LANE = "SHIPPING_LANE"
    INTERNATIONAL_BOUNDARY = "INTERNATIONAL_BOUNDARY"
    TERRITORIAL_WATERS = "TERRITORIAL_WATERS"
    EEZ = "EEZ"
    PORT_APPROACH = "PORT_APPROACH"


class RestrictionLevel(str, Enum):
    """Enforcement severity of maritime zone."""

    STRICT_NO_ENTRY = "STRICT_NO_ENTRY"
    RESTRICTED_FISHING = "RESTRICTED_FISHING"
    CAUTION_TRAFFIC = "CAUTION_TRAFFIC"
    BUFFER_PROXIMITY = "BUFFER_PROXIMITY"
    ADVISORY = "ADVISORY"


class MaritimeZone(BaseModel):
    """A defined geographic polygon zone with maritime constraints."""

    zone_id: str = Field(description="Unique zone identifier (e.g. IN-MPA-01)")
    name: str = Field(description="Official name of the maritime region")
    zone_type: ZoneType = Field(description="Type of maritime zone")
    restriction_level: RestrictionLevel = Field(description="Severity of restriction")
    description: str = Field(description="Operational rationale for restriction")
    coordinates: list[tuple[float, float]] = Field(
        description="Boundary vertices as list of (lat, lon) pairs forming a closed polygon",
    )
    buffer_km: float = Field(
        default=2.0,
        ge=0.0,
        description="Safety buffer perimeter around boundary in kilometers",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional maritime attributes")

    def to_polygon(self) -> Polygon:
        """Convert coordinates to Shapely Polygon with (lon, lat) Cartesian orientation.

        Shapely uses (x, y) = (lon, lat).
        """
        if not self.coordinates or len(self.coordinates) < 3:
            raise ValueError(f"Zone {self.zone_id} has insufficient coordinates for a polygon.")

        # Convert (lat, lon) to (x=lon, y=lat)
        coords_xy = [(lon, lat) for lat, lon in self.coordinates]
        # Ensure polygon is closed
        if coords_xy[0] != coords_xy[-1]:
            coords_xy.append(coords_xy[0])
        return Polygon(coords_xy)


class GeospatialSafetyResult(BaseModel):
    """Result of deterministic geospatial constraint evaluation."""

    coordinate: Coordinate = Field(description="Evaluated offshore coordinate")
    is_safe: bool = Field(description="True if coordinate satisfies all hard safety criteria")
    safety_status: SafetyEvaluation = Field(
        default=SafetyEvaluation.SAFE,
        description="Categorical safety status: SAFE, CAUTION, RESTRICTED, UNSAFE",
    )
    distance_from_origin_km: float | None = Field(
        default=None,
        description="Distance from mission departure origin in km",
    )
    bearing_degrees: float | None = Field(
        default=None,
        description="Compass bearing from departure origin in degrees",
    )
    zone_violations: list[str] = Field(
        default_factory=list,
        description="Names of prohibited or restricted zones penetrated",
    )
    buffer_warnings: list[str] = Field(
        default_factory=list,
        description="Names of zones whose safety buffer is entered",
    )
    traffic_warnings: list[str] = Field(
        default_factory=list,
        description="Active commercial shipping lanes or traffic separation schemes intersecting",
    )
    nearest_boundary_distance_km: float | None = Field(
        default=None,
        description="Shortest distance to nearest restricted boundary or sensitive border in km",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Explainable human-readable findings for the decision log",
    )
