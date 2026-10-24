"""Tests for Phase 8: What-If Simulation Engine & Interactive Cards."""

from datetime import datetime, timedelta, timezone
import pytest

from orca.agents.commander.agent import CommanderAgent
from orca.decision.engine import DecisionEngine
from orca.models.candidate import CandidateZone, DecisionOutput, SafetyEvaluation
from orca.models.mission import Coordinate, StructuredMission, TimeWindow
from orca.orchestration.what_if import WhatIfComparison, WhatIfEngine, WhatIfModification


@pytest.fixture
def baseline_mission() -> StructuredMission:
    now = datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc)
    return StructuredMission(
        request_id="req-base-001",
        activity="fishing",
        origin=Coordinate(lat=13.0827, lon=80.2707),
        time_window=TimeWindow(start=now, end=now + timedelta(hours=6)),
        max_distance_km=30.0,
        objective="high_fishing_potential",
        constraints=["low_weather_risk", "avoid_restricted_zones"],
    )


def test_parse_distance_increase(baseline_mission: StructuredMission):
    mod_mission, mods = WhatIfEngine.parse_modification(
        baseline_mission, "What if I go 15 km farther?"
    )
    assert mod_mission.max_distance_km == 45.0
    assert len(mods) == 1
    assert mods[0].field_modified == "max_distance_km"
    assert mods[0].old_value == 30.0
    assert mods[0].new_value == 45.0


def test_parse_distance_decrease(baseline_mission: StructuredMission):
    mod_mission, mods = WhatIfEngine.parse_modification(
        baseline_mission, "What if I stay 10 km closer to shore?"
    )
    assert mod_mission.max_distance_km == 20.0
    assert len(mods) == 1
    assert mods[0].field_modified == "max_distance_km"
    assert mods[0].new_value == 20.0


def test_parse_distance_absolute(baseline_mission: StructuredMission):
    mod_mission, mods = WhatIfEngine.parse_modification(
        baseline_mission, "What if I extend my radius to 50 km?"
    )
    assert mod_mission.max_distance_km == 50.0
    assert len(mods) == 1
    assert mods[0].field_modified == "max_distance_km"


def test_parse_objective_safest(baseline_mission: StructuredMission):
    mod_mission, mods = WhatIfEngine.parse_modification(
        baseline_mission, "What if I prioritize maximum safety over catch volume?"
    )
    assert mod_mission.objective == "safest"
    assert any(m.field_modified == "objective" for m in mods)


def test_parse_departure_time(baseline_mission: StructuredMission):
    mod_mission, mods = WhatIfEngine.parse_modification(
        baseline_mission, "What if I leave at 5:00 AM instead?"
    )
    assert mod_mission.time_window.start.hour == 5
    assert any(m.field_modified == "time_window" for m in mods)


def test_parse_wave_constraint(baseline_mission: StructuredMission):
    mod_mission, mods = WhatIfEngine.parse_modification(
        baseline_mission, "What if I need lower wave risk and calmer sea?"
    )
    assert "strict_low_wave_height" in mod_mission.constraints
    assert any(m.field_modified == "constraints" for m in mods)


def test_what_if_comparison_delta_calculation(baseline_mission: StructuredMission):
    mod_mission = baseline_mission.model_copy(update={"max_distance_km": 45.0})
    mods = [
        WhatIfModification(
            field_modified="max_distance_km",
            old_value=30.0,
            new_value=45.0,
            explanation="Extended radius +15 km",
        )
    ]

    base_zone = CandidateZone(
        id="ORCA-Z1",
        location=Coordinate(lat=13.15, lon=80.35),
        distance_km=25.0,
        fishing_score=80.0,
        safety_score=90.0,
        accessibility_score=62.5,
        composite_score=75.0,
        safety_status=SafetyEvaluation.SAFE,
    )
    base_dec = DecisionOutput(
        request_id="req-1",
        selected_zone=base_zone,
        recommendation_text="Rec 1",
        trade_off_analysis="Trade 1",
        safety_advisory="Safety 1",
    )

    new_zone = CandidateZone(
        id="ORCA-Z4",
        location=Coordinate(lat=13.25, lon=80.50),
        distance_km=42.0,
        fishing_score=95.0,
        safety_score=88.0,
        accessibility_score=37.0,
        composite_score=84.5,
        safety_status=SafetyEvaluation.SAFE,
    )
    new_dec = DecisionOutput(
        request_id="req-2",
        selected_zone=new_zone,
        recommendation_text="Rec 2",
        trade_off_analysis="Trade 2",
        safety_advisory="Safety 2",
    )

    comparison = WhatIfEngine.compare(
        baseline_mission=baseline_mission,
        modified_mission=mod_mission,
        baseline_decision=base_dec,
        new_decision=new_dec,
        modifications=mods,
    )

    assert comparison.selected_zone_changed is True
    assert comparison.composite_score_delta == 9.5  # 84.5 - 75.0
    assert comparison.fishing_score_delta == 15.0  # 95.0 - 80.0
    assert comparison.safety_score_delta == -2.0  # 88.0 - 90.0
    assert comparison.distance_delta_km == 17.0  # 42.0 - 25.0
    assert "### 🔄 ORCA What-If Recomputation & Trade-Off Analysis" in comparison.summary_markdown
    assert len(comparison.interactive_actions) > 0


def test_interactive_action_cards(baseline_mission: StructuredMission):
    actions = WhatIfEngine._generate_interactive_actions(baseline_mission)
    assert len(actions) >= 3
    prompts = [a["prompt"] for a in actions]
    assert any("45 km" in p for p in prompts)
    assert any("safety" in p.lower() for p in prompts)
    assert any("5:00 AM" in p for p in prompts)


@pytest.mark.asyncio
async def test_commander_simulate_what_if_e2e():
    """End-to-end integration test of What-If recomputation via CommanderAgent."""
    now = datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc)
    base_mission = StructuredMission(
        request_id="req-e2e-base",
        activity="fishing",
        origin=Coordinate(lat=13.0827, lon=80.2707),
        time_window=TimeWindow(start=now, end=now + timedelta(hours=6)),
        max_distance_km=25.0,  # restricted radius initially
        objective="high_fishing_potential",
        constraints=["low_weather_risk", "avoid_restricted_zones"],
    )

    commander = CommanderAgent()
    comparison = await commander.simulate_what_if(
        baseline_mission=base_mission,
        what_if_query="What if I travel 20 km farther offshore?",
    )

    assert isinstance(comparison, WhatIfComparison)
    assert comparison.modified_mission.max_distance_km == 45.0
    assert len(comparison.modifications) == 1
    assert comparison.new_decision is not None
    assert comparison.summary_markdown != ""
    assert "Comparative Decision Delta" in comparison.summary_markdown
