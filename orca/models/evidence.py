"""Evidence metadata, source tracking, and confidence tracking."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class DataFreshness(str, Enum):
    """Categorization of data age and validity."""

    LIVE = "live"          # Observed/updated within 3 hours
    RECENT = "recent"      # Within 12-24 hours
    STALE = "stale"        # Older than operational validity
    EXPIRED = "expired"    # Beyond valid-to timestamp
    UNKNOWN = "unknown"


class EvidenceItem(BaseModel):
    """Traceable evidence unit backing an observation or specialist decision."""

    source: str = Field(description="Originating authority or provider (e.g., INCOIS, IMD, GeoGIS)")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when ORCA retrieved the data",
    )
    observed_at: datetime | None = Field(
        default=None,
        description="Timestamp when original sensor/satellite measurement occurred",
    )
    issued_at: datetime | None = Field(
        default=None,
        description="Timestamp when official bulletin or model was published",
    )
    valid_to: datetime | None = Field(
        default=None,
        description="Forecast validity expiration timestamp",
    )
    freshness: DataFreshness = Field(
        default=DataFreshness.UNKNOWN,
        description="Evaluated freshness state",
    )
    geographic_coverage: str | None = Field(
        default=None,
        description="Geographic region, station, or polygon ID",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Reliability and quality score of this specific evidence item [0.0 - 1.0]",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw or normalized evidence payload",
    )


class EvidenceConflict(BaseModel):
    """Structured description of disagreeing observations from multiple sources."""

    observation: str = Field(description="Canonical observation name being compared")
    sources: list[str] = Field(description="Sources contributing the conflicting values")
    values: list[Any] = Field(description="Observed values in source order")
    tolerance: float = Field(default=0.0, ge=0.0, description="Allowed numeric disagreement")
    message: str = Field(description="Human-readable explanation of the disagreement")


class EvidenceAssessment(BaseModel):
    """Deterministic reliability summary produced by the Evidence Agent."""

    evidence_count: int = Field(default=0, ge=0)
    valid_evidence_count: int = Field(default=0, ge=0)
    complete: bool = Field(default=False)
    source_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    freshness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    agreement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    coverage_score: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    missing_sources: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    stale_sources: list[str] = Field(default_factory=list)
    invalid_sources: list[str] = Field(default_factory=list)
    failed_agents: list[str] = Field(default_factory=list)
    conflicts: list[EvidenceConflict] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
