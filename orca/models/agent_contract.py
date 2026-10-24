"""Communication contracts and standard response envelopes between agents."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from orca.models.evidence import EvidenceItem
from orca.models.mission import StructuredMission


class AgentStatus(str, Enum):
    """Standard execution statuses for an agent."""

    SUCCESS = "success"
    PARTIAL = "partial"
    STALE = "stale"
    TIMEOUT = "timeout"
    FAILED = "failed"
    CONFLICTING = "conflicting"
    UNAVAILABLE = "unavailable"


class AgentError(BaseModel):
    """Structured error contract when an agent fails."""

    type: str = Field(description="Error classification (e.g. TIMEOUT, API_UNAVAILABLE, VALIDATION_ERROR)")
    message: str = Field(description="Human-readable description of what failed")
    retryable: bool = Field(default=False, description="Whether repeating the request might succeed")
    details: dict[str, Any] = Field(default_factory=dict, description="Supplementary error diagnostic context")


class AgentWarning(BaseModel):
    """Advisory or non-fatal warning raised by a specialist agent."""

    code: str = Field(description="Warning code identifier (e.g. HIGH_SWELL_ALERT, APPROACHING_EEZ)")
    message: str = Field(description="Explanatory warning message")
    severity: str = Field(default="moderate", description="Severity level: low, moderate, critical")


class AgentRequest(BaseModel):
    """Standardized input envelope sent from Commander to Specialists."""

    request_id: str = Field(description="Trace identifier matching the mission request_id")
    target_agent: str = Field(description="Target specialist agent name (ocean, weather, maritime, evidence)")
    mission: StructuredMission = Field(description="Complete structured mission contract")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional agent-specific execution parameters",
    )


class AgentResponse(BaseModel):
    """Standardized output envelope returned by all specialist agents."""

    agent: str = Field(description="Specialist agent identifier (ocean, weather, maritime, evidence, commander)")
    status: AgentStatus = Field(description="Execution outcome status")
    request_id: str = Field(description="Trace ID matching the initiating request")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Domain-specific structured observations or candidate evaluation data",
    )
    evidence: list[EvidenceItem] = Field(
        default_factory=list,
        description="Collection of traceable evidence sources backing this response",
    )
    warnings: list[AgentWarning] = Field(
        default_factory=list,
        description="Domain warnings or safety alerts flagged during evaluation",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Quantifiable confidence score [0.0 - 1.0]",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response completion timestamp",
    )
    error: AgentError | None = Field(
        default=None,
        description="Populated only when status is FAILED, TIMEOUT, or UNAVAILABLE",
    )
