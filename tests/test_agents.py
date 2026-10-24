"""Unit and integration tests for Phase 3 Specialist Agents."""

import pytest
from datetime import datetime, timezone

from orca.agents.maritime import MaritimeSafetyAgent
from orca.agents.ocean import OceanAgent
from orca.agents.weather import WeatherAgent
from orca.models.agent_contract import AgentRequest, AgentResponse, AgentStatus
from orca.models.candidate import CandidateZone, SafetyEvaluation
from orca.models.mission import Coordinate, StructuredMission, TimeWindow


@pytest.fixture
def sample_mission() -> StructuredMission:
    """Fixture providing a standard coastal fishing mission off Chennai."""
    return StructuredMission(
        request_id="trace-agent-001",
        activity="fishing",
        origin=Coordinate(lat=13.0827, lon=80.2707),  # Chennai Port
        time_window=TimeWindow(
            start=datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc),
            end=datetime(2026, 10, 24, 18, 0, tzinfo=timezone.utc),
        ),
        max_distance_km=35.0,
        objective="high_fishing_potential",
        constraints=["low_weather_risk", "avoid_restricted_zones"],
    )


# ---------------------------------------------------------------------------
# Ocean Agent Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ocean_agent_success(sample_mission: StructuredMission):
    agent = OceanAgent()
    request = AgentRequest(
        request_id=sample_mission.request_id,
        target_agent="ocean",
        mission=sample_mission,
    )

    response = await agent.process(request)
    assert isinstance(response, AgentResponse)
    assert response.agent == "ocean"
    assert response.status == AgentStatus.SUCCESS
    assert response.request_id == sample_mission.request_id

    # Check data content
    candidates = response.data.get("candidate_zones", [])
    assert len(candidates) > 0
    first_candidate = candidates[0]
    assert "fishing_score" in first_candidate
    assert first_candidate["fishing_score"] > 0.0
    assert "ocean_data" in first_candidate

    # Verify evidence items
    assert len(response.evidence) > 0
    assert any("INCOIS" in e.source for e in response.evidence)


# ---------------------------------------------------------------------------
# Weather Agent Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_weather_agent_success(sample_mission: StructuredMission):
    agent = WeatherAgent()
    request = AgentRequest(
        request_id=sample_mission.request_id,
        target_agent="weather",
        mission=sample_mission,
        parameters={
            "candidate_zones": [
                {
                    "id": "ORCA-TEST-Z1",
                    "location": {"lat": 13.10, "lon": 80.35},
                }
            ]
        },
    )

    response = await agent.process(request)
    assert isinstance(response, AgentResponse)
    assert response.agent == "weather"
    assert response.status == AgentStatus.SUCCESS
    assert response.request_id == sample_mission.request_id

    evals = response.data.get("weather_evaluations", [])
    assert len(evals) == 1
    eval_result = evals[0]
    assert "weather_safety_score" in eval_result
    assert 0.0 <= eval_result["weather_safety_score"] <= 100.0
    assert "significant_wave_height_m" in eval_result

    # Evidence from Open-Meteo & IMD
    assert len(response.evidence) >= 2


@pytest.mark.asyncio
async def test_weather_agent_evaluates_origin_when_no_candidates(sample_mission: StructuredMission):
    agent = WeatherAgent()
    request = AgentRequest(
        request_id=sample_mission.request_id,
        target_agent="weather",
        mission=sample_mission,
    )

    response = await agent.process(request)
    assert response.status == AgentStatus.SUCCESS
    evals = response.data.get("weather_evaluations", [])
    assert len(evals) == 1
    assert evals[0]["zone_id"] == "ORIGIN"


# ---------------------------------------------------------------------------
# Maritime Safety Agent Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_maritime_agent_safe_and_restricted_zones(sample_mission: StructuredMission):
    agent = MaritimeSafetyAgent()

    # Pass 2 candidates: one safe offshore Chennai, one inside Gulf of Mannar MPA
    safe_candidate = CandidateZone(
        id="ORCA-SAFE-Z1",
        location=Coordinate(lat=13.05, lon=80.32),  # ~6 km offshore
        distance_km=0.0,
        fishing_score=80.0,
        safety_score=100.0,
    )
    restricted_candidate = CandidateZone(
        id="ORCA-MPA-Z2",
        location=Coordinate(lat=9.05, lon=78.60),  # Inside Gulf of Mannar MPA core & 400+ km away
        distance_km=0.0,
        fishing_score=95.0,
        safety_score=100.0,
    )

    request = AgentRequest(
        request_id=sample_mission.request_id,
        target_agent="maritime",
        mission=sample_mission,
        parameters={
            "candidate_zones": [safe_candidate.model_dump(), restricted_candidate.model_dump()]
        },
    )

    response = await agent.process(request)
    assert response.agent == "maritime"
    assert response.status == AgentStatus.SUCCESS

    evaluated = response.data.get("evaluated_candidates", [])
    assert len(evaluated) == 2

    # Check restricted candidate was penalized to 0 safety_score
    mpa_zone = next(z for z in evaluated if z["id"] == "ORCA-MPA-Z2")
    assert mpa_zone["safety_status"] == SafetyEvaluation.UNSAFE
    assert mpa_zone["safety_score"] == 0.0

    # Ensure violations were registered in response warnings
    assert response.data["violations_detected"] >= 1
    assert any(w.code == "RESTRICTED_ZONE_VIOLATION" for w in response.warnings)

    # Check evidence item
    assert any(e.source == "MARITIME_BOUNDARIES_GIS" for e in response.evidence)


# ---------------------------------------------------------------------------
# Agent Contract Compliance Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_all_specialists_satisfy_contract_types(sample_mission: StructuredMission):
    agents = [
        OceanAgent(),
        WeatherAgent(),
        MaritimeSafetyAgent(),
    ]

    for agent in agents:
        req = AgentRequest(
            request_id=sample_mission.request_id,
            target_agent="specialist",
            mission=sample_mission,
        )
        resp = await agent.process(req)
        assert isinstance(resp, AgentResponse)
        assert resp.request_id == sample_mission.request_id
        assert 0.0 <= resp.confidence <= 1.0
        assert isinstance(resp.evidence, list)
        assert isinstance(resp.warnings, list)
