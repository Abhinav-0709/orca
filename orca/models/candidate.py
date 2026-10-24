"""Candidate marine zones and final decision output models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from orca.models.evidence import EvidenceItem
from orca.models.mission import Coordinate


class SafetyEvaluation(str, Enum):
    """Safety status category for a candidate zone."""

    SAFE = "SAFE"
    CAUTION = "CAUTION"
    RESTRICTED = "RESTRICTED"
    UNSAFE = "UNSAFE"


class CandidateZone(BaseModel):
    """An evaluated geographic offshore candidate zone."""

    id: str = Field(description="Unique candidate identifier (e.g. ORCA-Z1)")
    location: Coordinate = Field(description="Center coordinate of the candidate zone")
    distance_km: float = Field(ge=0.0, description="Calculated geodesic distance from departure origin")
    bearing_degrees: float | None = Field(
        default=None,
        ge=0.0,
        le=360.0,
        description="Compass bearing from origin to zone in degrees",
    )

    # Dimensional Scores (0 - 100)
    fishing_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Oceanographic opportunity score (SST, chlorophyll, PFZ match)",
    )
    safety_score: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Environmental safety score (wave height, wind, swell)",
    )
    accessibility_score: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Spatial accessibility score based on distance and fuel/effort",
    )
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Evidence reliability factor [0.0 - 1.0]",
    )

    # Risk-Adjusted Composite Score
    composite_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Final risk-adjusted weighted score computed by Decision Engine",
    )

    safety_status: SafetyEvaluation = Field(
        default=SafetyEvaluation.SAFE,
        description="Categorical safety status",
    )
    ocean_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Ocean observations: SST (°C), Chlorophyll (mg/m³), PFZ status",
    )
    weather_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Weather observations: Wave height (m), Swell (m), Wind speed (km/h)",
    )
    geospatial_notes: list[str] = Field(
        default_factory=list,
        description="Boundary proximity, distance to EEZ, restricted area checks",
    )
    reasoning: str | None = Field(
        default=None,
        description="Human-readable explanation of why this zone scored as it did",
    )


class DecisionOutput(BaseModel):
    """Final risk-adjusted decision package delivered to ASI:One / user."""

    request_id: str = Field(description="Originating request trace ID")
    selected_zone: CandidateZone | None = Field(
        default=None,
        description="Top recommended zone satisfying all safety & objective constraints",
    )
    alternative_zones: list[CandidateZone] = Field(
        default_factory=list,
        description="Lower-ranking alternative zones for comparative analysis",
    )
    overall_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Global decision confidence derived from evidence layer",
    )
    recommendation_text: str = Field(
        description="Human-readable synthesis explaining the recommended action",
    )
    trade_off_analysis: str = Field(
        description="Explicit explanation of why alternatives were rejected or ranked lower",
    )
    safety_advisory: str = Field(
        description="Operational safety caution and legal disclaimer",
    )
    data_provenance: list[EvidenceItem] = Field(
        default_factory=list,
        description="Traceable data sources and timestamps used in decision",
    )
    what_if_suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested constraint adjustments for the user (e.g. 'What if I go 10 km further?')",
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Decision timestamp",
    )
