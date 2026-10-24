"""Normalized data models for operational marine and weather sources."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from orca.models.evidence import EvidenceItem
from orca.models.mission import Coordinate


class WarningSeverity(str, Enum):
    """Warning urgency levels conforming to IMD colour-coded alerts."""

    GREEN = "GREEN"      # No warning (Safe)
    YELLOW = "YELLOW"    # Watch / Be updated
    ORANGE = "ORANGE"    # Alert / Be prepared
    RED = "RED"          # Warning / Take action


class WarningType(str, Enum):
    """Classification of marine meteorological warning."""

    FISHERMEN_WARNING = "FISHERMEN_WARNING"
    COASTAL_BULLETIN = "COASTAL_BULLETIN"
    SEA_AREA_BULLETIN = "SEA_AREA_BULLETIN"
    CYCLONE_ALERT = "CYCLONE_ALERT"
    PORT_WARNING = "PORT_WARNING"
    HIGH_WAVE_ALERT = "HIGH_WAVE_ALERT"


class PFZAdvisory(BaseModel):
    """Normalized INCOIS Potential Fishing Zone (PFZ) advisory item."""

    sector_id: str = Field(description="Advisory sector (e.g. TAMIL_NADU_SOUTH, CHENNAI_COAST)")
    location: Coordinate = Field(description="Center coordinate of the potential fishing zone")
    depth_m: float = Field(ge=0.0, description="Ocean depth at fishing zone in meters")
    distance_km: float = Field(ge=0.0, description="Distance from reference coastal point in km")
    direction: str = Field(description="Compass bearing/direction from coastal landing center (e.g. ENE, SE)")
    reference_landing_center: str = Field(description="Coastal reference point (e.g. Kasimedu / Chennai Fishing Harbour)")
    sst_c: float | None = Field(default=None, description="Sea Surface Temperature in degrees Celsius")
    chlorophyll_mg_m3: float | None = Field(default=None, description="Chlorophyll concentration in mg/m³")
    potential_score: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Normalized fishing potential indicator [0.0 - 1.0]",
    )
    observed_at: datetime = Field(description="Timestamp of satellite ocean pass")
    valid_until: datetime = Field(description="Expiration timestamp of the advisory")
    evidence: EvidenceItem = Field(description="Data provenance and freshness audit trail")


class OceanStateForecast(BaseModel):
    """Normalized INCOIS Ocean State Forecast (OSF)."""

    location: Coordinate = Field(description="Location of forecast point or grid cell")
    significant_wave_height_m: float = Field(ge=0.0, description="Significant Wave Height (SWH) in meters")
    swell_height_m: float = Field(ge=0.0, description="Swell height in meters")
    swell_period_s: float = Field(ge=0.0, description="Swell period in seconds")
    swell_direction_deg: float = Field(ge=0.0, le=360.0, description="Swell direction in degrees")
    wind_speed_kmh: float = Field(ge=0.0, description="Surface wind speed in km/h")
    wind_direction_deg: float = Field(ge=0.0, le=360.0, description="Wind direction in degrees")
    surface_current_ms: float = Field(ge=0.0, description="Surface ocean current speed in m/s")
    water_temperature_c: float | None = Field(default=None, description="Water temperature in degrees Celsius")
    forecast_valid_from: datetime = Field(description="Forecast window start")
    forecast_valid_to: datetime = Field(description="Forecast window end")
    issued_at: datetime = Field(description="Timestamp when forecast model was run/issued")
    evidence: EvidenceItem = Field(description="Provenance and freshness trace")


class MarineWarning(BaseModel):
    """Normalized IMD weather, sea-area, or fishermen warning bulletin."""

    warning_type: WarningType = Field(description="Type of warning bulletin")
    severity: WarningSeverity = Field(description="Colour-coded severity level")
    affected_coast: str = Field(description="Affected coastal strip (e.g. Tamil Nadu Coast, South Andhra Coast)")
    description: str = Field(description="Detailed bulletin advisory text")
    issued_at: datetime = Field(description="Timestamp when bulletin was officially issued")
    valid_until: datetime = Field(description="Expiration timestamp of the advisory")
    advice_for_fishermen: str = Field(description="Specific advice (e.g. 'Advised not to venture into southwest Bay of Bengal')")
    cyclone_info: dict[str, Any] | None = Field(
        default=None,
        description="Optional cyclone tracking details (wind speed, cone of uncertainty, distance to coast)",
    )
    evidence: EvidenceItem = Field(description="Source metadata and provenance")


class MarineDataPackage(BaseModel):
    """Aggregated marine intelligence package for a given location and time window."""

    query_location: Coordinate = Field(description="Center coordinate of the search area")
    query_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pfz_advisories: list[PFZAdvisory] = Field(default_factory=list)
    ocean_forecasts: list[OceanStateForecast] = Field(default_factory=list)
    marine_warnings: list[MarineWarning] = Field(default_factory=list)
    overall_freshness: str = Field(default="live")
    is_complete: bool = Field(default=True, description="Whether all primary operational feeds returned data")
