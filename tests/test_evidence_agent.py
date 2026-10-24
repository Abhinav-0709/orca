"""Tests for Phase 4 evidence and reliability assessment."""

from datetime import datetime, timedelta, timezone

import pytest

from orca.agents.evidence import EvidenceAgent
from orca.models.agent_contract import AgentError, AgentRequest, AgentResponse, AgentStatus
from orca.models.evidence import DataFreshness, EvidenceItem
from orca.models.mission import Coordinate, StructuredMission, TimeWindow


FIXED_NOW = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_request() -> AgentRequest:
    mission = StructuredMission(
        request_id="trace-evidence-001",
        activity="fishing",
        origin=Coordinate(lat=13.0827, lon=80.2707),
        time_window=TimeWindow(start=FIXED_NOW, end=FIXED_NOW + timedelta(hours=6)),
    )
    return AgentRequest(
        request_id=mission.request_id,
        target_agent="evidence",
        mission=mission,
    )


def evidence_item(
    source: str,
    *,
    observed_at: datetime = FIXED_NOW - timedelta(hours=1),
    confidence: float = 0.9,
    details: dict | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        source=source,
        retrieved_at=FIXED_NOW,
        observed_at=observed_at,
        valid_to=FIXED_NOW + timedelta(hours=6),
        geographic_coverage="Tamil Nadu coastal waters",
        confidence=confidence,
        details=details or {},
    )


@pytest.mark.asyncio
async def test_evidence_agent_reports_complete_current_evidence(sample_request: AgentRequest):
    agent = EvidenceAgent(
        required_sources=("INCOIS", "OPEN_METEO_MARINE", "IMD", "MARITIME_BOUNDARIES_GIS"),
        now_provider=lambda: FIXED_NOW,
    )
    sample_request.parameters = {
        "evidence": [
            evidence_item("INCOIS_OPERATIONAL_FALLBACK"),
            evidence_item("OPEN_METEO_MARINE"),
            evidence_item("IMD_OPERATIONAL_FALLBACK"),
            evidence_item("MARITIME_BOUNDARIES_GIS"),
        ]
    }

    response = await agent.process(sample_request)

    assert response.status == AgentStatus.SUCCESS
    assert response.error is None
    assert response.data["assessment"]["complete"] is True
    assert response.data["assessment"]["missing_sources"] == []
    assert response.data["assessment"]["freshness_score"] == 1.0
    assert response.confidence > 0.8
    assert all(item.freshness == DataFreshness.LIVE for item in response.evidence)


@pytest.mark.asyncio
async def test_evidence_agent_flags_stale_and_missing_sources(sample_request: AgentRequest):
    agent = EvidenceAgent(
        required_sources=("INCOIS", "OPEN_METEO_MARINE", "IMD"),
        now_provider=lambda: FIXED_NOW,
    )
    sample_request.parameters = {
        "evidence": [
            evidence_item(
                "OPEN_METEO_MARINE",
                observed_at=FIXED_NOW - timedelta(hours=30),
            )
        ]
    }

    response = await agent.process(sample_request)
    assessment = response.data["assessment"]

    assert response.status == AgentStatus.PARTIAL
    assert assessment["missing_sources"] == ["IMD", "INCOIS"]
    assert assessment["stale_sources"] == ["OPEN_METEO_MARINE"]
    assert assessment["freshness_score"] < 1.0
    assert {warning.code for warning in response.warnings} >= {"EVIDENCE_MISSING", "EVIDENCE_STALE"}


@pytest.mark.asyncio
async def test_evidence_agent_detects_conflicting_observations(sample_request: AgentRequest):
    agent = EvidenceAgent(now_provider=lambda: FIXED_NOW)
    sample_request.parameters = {
        "evidence": [
            evidence_item(
                "INCOIS",
                details={"observations": {"wave_height_m": 1.0}},
            ),
            evidence_item(
                "OPEN_METEO_MARINE",
                details={"observations": {"wave_height_m": 2.5}},
            ),
        ]
    }

    response = await agent.process(sample_request)
    assessment = response.data["assessment"]

    assert response.status == AgentStatus.PARTIAL
    assert assessment["agreement_score"] == 0.75
    assert assessment["conflicts"][0]["observation"] == "wave_height_m"
    assert any(warning.code == "EVIDENCE_CONFLICT" for warning in response.warnings)


@pytest.mark.asyncio
async def test_evidence_agent_degrades_when_specialist_failed(sample_request: AgentRequest):
    agent = EvidenceAgent(now_provider=lambda: FIXED_NOW)
    failed_weather = AgentResponse(
        agent="weather",
        status=AgentStatus.FAILED,
        request_id=sample_request.request_id,
        error=AgentError(
            type="API_UNAVAILABLE",
            message="Marine forecast unavailable",
            retryable=True,
        ),
    )
    sample_request.parameters = {"agent_responses": [failed_weather.model_dump()]}

    response = await agent.process(sample_request)

    assert response.status == AgentStatus.UNAVAILABLE
    assert response.error is not None
    assert response.error.type == "NO_EVIDENCE"
    assert response.error.retryable is True
    assert response.data["assessment"]["failed_agents"] == ["weather"]
    assert any(warning.code == "SPECIALIST_DEGRADED" for warning in response.warnings)


@pytest.mark.asyncio
async def test_evidence_agent_persists_reviewed_evidence(sample_request: AgentRequest, tmp_path):
    agent = EvidenceAgent(
        now_provider=lambda: FIXED_NOW,
        store_path=str(tmp_path / "evidence.sqlite3"),
    )
    sample_request.parameters = {"evidence": [evidence_item("OPEN_METEO_MARINE")]}

    response = await agent.process(sample_request)
    persisted = agent.store.get_evidence(sample_request.request_id) if agent.store else []
    assessment = agent.store.get_assessment(sample_request.request_id) if agent.store else None

    assert response.data["persistence"]["enabled"] is True
    assert response.data["persistence"]["evidence_saved"] == 1
    assert response.data["persistence"]["assessment_saved"] is True
    assert len(persisted) == 1
    assert assessment is not None
    assert assessment.overall_confidence == response.confidence

    if agent.store:
        agent.store.close()
