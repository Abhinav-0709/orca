"""Unit tests for Agent Chat Protocol (ACP) router and envelopes."""

import asyncio
from datetime import datetime, timezone
import pytest

from orca.models.agent_contract import AgentRequest, AgentResponse, AgentStatus
from orca.models.mission import Coordinate, StructuredMission, TimeWindow
from orca.orchestration.acp import ACPMessage, ACPMessageType, ACPRouter


@pytest.fixture
def dummy_mission() -> StructuredMission:
    return StructuredMission(
        request_id="acp-test-trace",
        origin=Coordinate(lat=13.08, lon=80.27),
        time_window=TimeWindow(
            start=datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc),
            end=datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc),
        ),
    )


@pytest.mark.asyncio
async def test_acp_successful_dispatch(dummy_mission: StructuredMission):
    """Verify ACP router successfully forwards request to registered handler."""
    router = ACPRouter()

    async def mock_ocean_handler(req: AgentRequest) -> AgentResponse:
        return AgentResponse(
            agent="ocean",
            status=AgentStatus.SUCCESS,
            request_id=req.request_id,
            data={"test_key": "test_val"},
            confidence=0.95,
        )

    router.register_agent("ocean", mock_ocean_handler)

    req = AgentRequest(
        request_id=dummy_mission.request_id,
        target_agent="ocean",
        mission=dummy_mission,
    )

    resp = await router.send_request("commander", "ocean", req)
    assert resp.agent == "ocean"
    assert resp.status == AgentStatus.SUCCESS
    assert resp.data["test_key"] == "test_val"


@pytest.mark.asyncio
async def test_acp_timeout_handling(dummy_mission: StructuredMission):
    """Verify ACP router safely intercepts timeouts and returns TIMEOUT status."""
    router = ACPRouter(default_timeout_seconds=0.1)

    async def hanging_handler(req: AgentRequest) -> AgentResponse:
        await asyncio.sleep(0.5)
        return AgentResponse(agent="weather", status=AgentStatus.SUCCESS, request_id=req.request_id)

    router.register_agent("weather", hanging_handler)

    req = AgentRequest(
        request_id=dummy_mission.request_id,
        target_agent="weather",
        mission=dummy_mission,
    )

    resp = await router.send_request("commander", "weather", req)
    assert resp.status == AgentStatus.TIMEOUT
    assert resp.error is not None
    assert resp.error.type == "TIMEOUT"
    assert resp.confidence == 0.0


@pytest.mark.asyncio
async def test_acp_unregistered_agent(dummy_mission: StructuredMission):
    """Verify ACP router handles requests to non-existent agents without crashing."""
    router = ACPRouter()

    req = AgentRequest(
        request_id=dummy_mission.request_id,
        target_agent="unknown_specialist",
        mission=dummy_mission,
    )

    resp = await router.send_request("commander", "unknown_specialist", req)
    assert resp.status == AgentStatus.UNAVAILABLE
    assert resp.error is not None
    assert resp.error.type == "AGENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_acp_exception_handling(dummy_mission: StructuredMission):
    """Verify ACP router catches unhandled agent exceptions and wraps in FAILED response."""
    router = ACPRouter()

    async def crashing_handler(req: AgentRequest) -> AgentResponse:
        raise ValueError("Simulated unexpected specialist crash")

    router.register_agent("failing_agent", crashing_handler)

    req = AgentRequest(
        request_id=dummy_mission.request_id,
        target_agent="failing_agent",
        mission=dummy_mission,
    )

    resp = await router.send_request("commander", "failing_agent", req)
    assert resp.status == AgentStatus.FAILED
    assert resp.error is not None
    assert resp.error.type == "AGENT_EXECUTION_ERROR"
    assert "Simulated unexpected specialist crash" in resp.error.message
