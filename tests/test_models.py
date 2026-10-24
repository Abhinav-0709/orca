"""Unit tests for ORCA core data models and edge case validation."""

from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError

from orca.models import (
    AgentError,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    AgentWarning,
    CandidateZone,
    Coordinate,
    DataFreshness,
    DecisionOutput,
    EvidenceItem,
    SafetyEvaluation,
    StructuredMission,
    TimeWindow,
)


def test_coordinate_valid():
    """Verify valid coordinates instantiate and convert to tuple."""
    coord = Coordinate(lat=13.0827, lon=80.2707)
    assert coord.lat == 13.0827
    assert coord.lon == 80.2707
    assert coord.to_tuple() == (13.0827, 80.2707)


def test_coordinate_invalid_bounds():
    """Verify out-of-bounds coordinates raise ValidationError."""
    with pytest.raises(ValidationError):
        Coordinate(lat=91.0, lon=80.0)

    with pytest.raises(ValidationError):
        Coordinate(lat=-91.0, lon=80.0)

    with pytest.raises(ValidationError):
        Coordinate(lat=13.0, lon=181.0)

    with pytest.raises(ValidationError):
        Coordinate(lat=13.0, lon=-181.0)


def test_time_window_valid():
    """Verify valid operational window validation."""
    now = datetime.now(timezone.utc)
    tw = TimeWindow(start=now, end=now + timedelta(hours=6))
    assert tw.end > tw.start


def test_time_window_invalid_reversed():
    """Verify end preceding start raises ValueError."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="cannot precede start"):
        TimeWindow(start=now + timedelta(hours=2), end=now)


def test_structured_mission_serialization():
    """Verify StructuredMission model serialization and defaults."""
    now = datetime.now(timezone.utc)
    tw = TimeWindow(start=now, end=now + timedelta(hours=5))
    origin = Coordinate(lat=13.08, lon=80.27)

    mission = StructuredMission(
        request_id="req-mission-001",
        origin=origin,
        time_window=tw,
        max_distance_km=35.0,
    )

    data = mission.model_dump()
    assert data["request_id"] == "req-mission-001"
    assert data["origin"]["lat"] == 13.08
    assert data["max_distance_km"] == 35.0
    assert "low_weather_risk" in data["constraints"]


def test_structured_mission_invalid_distance():
    """Verify non-positive or excessive distances fail validation."""
    now = datetime.now(timezone.utc)
    tw = TimeWindow(start=now, end=now + timedelta(hours=2))
    origin = Coordinate(lat=13.08, lon=80.27)

    with pytest.raises(ValidationError):
        StructuredMission(
            request_id="req-bad",
            origin=origin,
            time_window=tw,
            max_distance_km=-5.0,
        )

    with pytest.raises(ValidationError):
        StructuredMission(
            request_id="req-bad",
            origin=origin,
            time_window=tw,
            max_distance_km=500.0,
        )


def test_agent_contract_success_and_failure():
    """Verify AgentResponse creation for both success and failure envelopes."""
    now = datetime.now(timezone.utc)
    tw = TimeWindow(start=now, end=now + timedelta(hours=4))
    mission = StructuredMission(
        request_id="req-test-99",
        origin=Coordinate(lat=13.0, lon=80.0),
        time_window=tw,
    )

    req = AgentRequest(
        request_id="req-test-99",
        target_agent="weather",
        mission=mission,
    )
    assert req.target_agent == "weather"

    # Successful response
    success_resp = AgentResponse(
        agent="weather",
        status=AgentStatus.SUCCESS,
        request_id="req-test-99",
        confidence=0.92,
        data={"wave_height_m": 1.2, "wind_kmh": 18.0},
        warnings=[AgentWarning(code="SWELL_MODERATE", message="Swell up to 1.5m expected", severity="low")],
    )
    assert success_resp.status == AgentStatus.SUCCESS
    assert success_resp.confidence == 0.92
    assert len(success_resp.warnings) == 1

    # Failed response
    fail_resp = AgentResponse(
        agent="weather",
        status=AgentStatus.FAILED,
        request_id="req-test-99",
        confidence=0.0,
        error=AgentError(
            type="TIMEOUT",
            message="Marine forecast service unavailable",
            retryable=True,
        ),
    )
    assert fail_resp.status == AgentStatus.FAILED
    assert fail_resp.error is not None
    assert fail_resp.error.type == "TIMEOUT"
    assert fail_resp.error.retryable is True


def test_candidate_zone_and_decision_output():
    """Verify CandidateZone and DecisionOutput integration."""
    zone = CandidateZone(
        id="ORCA-Z1",
        location=Coordinate(lat=13.15, lon=80.45),
        distance_km=22.4,
        fishing_score=85.0,
        safety_score=90.0,
        accessibility_score=88.0,
        composite_score=87.2,
        safety_status=SafetyEvaluation.SAFE,
    )
    assert zone.id == "ORCA-Z1"
    assert zone.safety_status == SafetyEvaluation.SAFE

    evidence = EvidenceItem(
        source="INCOIS",
        freshness=DataFreshness.LIVE,
        confidence=0.95,
        geographic_coverage="Chennai Coastal Grid",
    )

    decision = DecisionOutput(
        request_id="req-decision-01",
        selected_zone=zone,
        overall_confidence=0.93,
        recommendation_text="Zone ORCA-Z1 is recommended 22.4 km east of Chennai.",
        trade_off_analysis="Alternative zone Z2 has 5% higher fishing potential but unsafe wave risk.",
        safety_advisory="Check official IMD and Coast Guard bulletins prior to cast-off.",
        data_provenance=[evidence],
        what_if_suggestions=["What if I travel 15 km further south?"],
    )

    assert decision.selected_zone.id == "ORCA-Z1"
    assert len(decision.data_provenance) == 1
    assert decision.overall_confidence == 0.93
