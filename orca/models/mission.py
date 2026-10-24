"""Geographic coordinate and structured mission parameters."""

from datetime import datetime, timezone
from typing import Annotated
from pydantic import BaseModel, Field, model_validator


class Coordinate(BaseModel):
    """Geographic coordinate representing a point on Earth."""

    lat: Annotated[float, Field(ge=-90.0, le=90.0, description="Latitude in degrees [-90, 90]")]
    lon: Annotated[float, Field(ge=-180.0, le=180.0, description="Longitude in degrees [-180, 180]")]

    def to_tuple(self) -> tuple[float, float]:
        """Return (lat, lon) tuple."""
        return (self.lat, self.lon)


class TimeWindow(BaseModel):
    """Operational mission time window."""

    start: datetime = Field(description="Operational start time (UTC or timezone-aware)")
    end: datetime = Field(description="Operational end time (UTC or timezone-aware)")

    @model_validator(mode="after")
    def validate_window(self) -> "TimeWindow":
        if self.end < self.start:
            raise ValueError(f"TimeWindow end ({self.end}) cannot precede start ({self.start})")
        return self

    @property
    def duration_hours(self) -> float:
        """Operational duration in hours."""
        return (self.end - self.start).total_seconds() / 3600.0


class StructuredMission(BaseModel):
    """Contract between user intent and specialist agents."""

    request_id: str = Field(description="Unique trace identifier for the mission")
    activity: str = Field(default="fishing", description="Target marine activity")
    origin: Coordinate = Field(description="Departure coordinate or port location")
    time_window: TimeWindow = Field(description="Planned operational window")
    max_distance_km: float = Field(
        default=30.0,
        gt=0.0,
        le=300.0,
        description="Maximum permissible operational distance from origin in kilometers",
    )
    objective: str = Field(
        default="high_fishing_potential",
        description="Mission optimization objective (e.g. high_fishing_potential, safest, balanced)",
    )
    constraints: list[str] = Field(
        default_factory=lambda: ["low_weather_risk", "avoid_restricted_zones"],
        description="Hard and soft operational constraints",
    )
    vessel_type: str | None = Field(
        default=None,
        description="Vessel category (e.g. motorized_canoe, mechanized_boat, trawler)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Mission creation timestamp",
    )
