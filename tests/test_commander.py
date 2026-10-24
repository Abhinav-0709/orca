"""Unit and integration tests for Phase 5 Commander Agent and orchestration."""

from datetime import datetime, timezone
import pytest

from orca.agents.commander.agent import CommanderAgent, CommanderWorkflowResult
from orca.models.candidate import CandidateZone
from orca.models.mission import Coordinate, StructuredMission, TimeWindow


@pytest.fixture
def commander() -> CommanderAgent:
    """Fixture providing an initialized CommanderAgent with all registered specialists."""
    return CommanderAgent()


@pytest.mark.asyncio
async def test_commander_execute_query_chennai(commander: CommanderAgent):
    """Verify natural-language query triggers full multi-agent orchestration."""
    query = (
        "I want to go fishing tomorrow morning from Chennai. "
        "Find the best fishing zone within 30 km, keep the sea risk low, and avoid restricted areas."
    )
    now = datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc)

    result: CommanderWorkflowResult = await commander.execute_query(
        query=query,
        now=now,
        request_id="test-commander-001",
    )

    assert result.request_id == "test-commander-001"
    assert result.workflow_status == "completed"
    assert result.mission.origin.lat == 13.0827
    assert result.mission.max_distance_km == 30.0

    # Verify all specialist responses were collected
    assert result.ocean_response is not None
    assert result.ocean_response.agent == "ocean"
    assert result.weather_response is not None
    assert result.weather_response.agent == "weather"
    assert result.maritime_response is not None
    assert result.maritime_response.agent == "maritime"

    # Verify candidate zones were populated and enriched
    assert len(result.candidate_zones) > 0
    for cand in result.candidate_zones:
        assert isinstance(cand, CandidateZone)
        assert cand.distance_km <= 30.0
        assert cand.fishing_score > 0.0
        assert 0.0 <= cand.safety_score <= 100.0
        assert 0.0 <= cand.accessibility_score <= 100.0
        assert 0.0 <= cand.confidence_score <= 1.0

    # Verify evidence and reliability assessment
    assert result.evidence_assessment is not None
    assert result.overall_confidence > 0.0
    assert len(result.all_evidence) > 0


@pytest.mark.asyncio
async def test_commander_execute_mission_direct(commander: CommanderAgent):
    """Verify executing a pre-constructed StructuredMission directly."""
    now = datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc)
    mission = StructuredMission(
        request_id="direct-mission-002",
        origin=Coordinate(lat=13.1264, lon=80.2982),  # Kasimedu
        time_window=TimeWindow(start=now, end=now),
        max_distance_km=25.0,
        objective="high_fishing_potential",
    )

    result = await commander.execute_mission(mission)

    assert result.request_id == "direct-mission-002"
    assert result.workflow_status == "completed"
    assert len(result.candidate_zones) > 0


@pytest.mark.asyncio
async def test_commander_clarification_on_vague_query(commander: CommanderAgent):
    """Verify vague query without origin cleanly returns a clarification prompt."""
    vague_query = "Find good fishing spots tomorrow."
    result = await commander.execute_query(query=vague_query)

    assert result.workflow_status == "clarification_needed"
    assert result.clarification_prompt is not None
    assert "departure port or coastal origin" in result.clarification_prompt
    assert len(result.candidate_zones) == 0
