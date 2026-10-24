"""Unit and integration tests for Phase 6 Decision Engine and Explainer."""

from datetime import datetime, timezone
import pytest

from orca.agents.commander.agent import CommanderAgent
from orca.decision.engine import DecisionEngine
from orca.decision.explainer import DecisionExplainer
from orca.models.candidate import CandidateZone, DecisionOutput, SafetyEvaluation
from orca.models.evidence import DataFreshness, EvidenceItem
from orca.models.mission import Coordinate, StructuredMission, TimeWindow


@pytest.fixture
def baseline_mission() -> StructuredMission:
    return StructuredMission(
        request_id="decision-test-001",
        activity="fishing",
        origin=Coordinate(lat=13.0827, lon=80.2707),
        time_window=TimeWindow(
            start=datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc),
            end=datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc),
        ),
        max_distance_km=30.0,
        objective="high_fishing_potential",
    )


def test_safety_strictly_dominates_opportunity(baseline_mission: StructuredMission):
    """Golden Rule: High fishing + low safety MUST NOT beat moderate fishing + high safety."""
    cand_dangerous = CandidateZone(
        id="ZONE-RISKY",
        location=Coordinate(lat=13.20, lon=80.45),
        distance_km=25.0,
        fishing_score=96.0,  # Extremely high opportunity
        safety_score=35.0,   # Hazardous wave conditions
        accessibility_score=80.0,
        confidence_score=0.95,
        safety_status=SafetyEvaluation.CAUTION,
    )

    cand_safe = CandidateZone(
        id="ZONE-SAFE",
        location=Coordinate(lat=13.15, lon=80.35),
        distance_km=20.0,
        fishing_score=82.0,  # Good opportunity
        safety_score=92.0,   # Very calm, safe waters
        accessibility_score=85.0,
        confidence_score=0.95,
        safety_status=SafetyEvaluation.SAFE,
    )

    decision: DecisionOutput = DecisionEngine.evaluate(
        mission=baseline_mission,
        candidates=[cand_dangerous, cand_safe],
        overall_confidence=0.95,
    )

    assert decision.selected_zone is not None
    assert decision.selected_zone.id == "ZONE-SAFE"
    assert cand_safe.composite_score > cand_dangerous.composite_score


def test_disqualification_of_unsafe_and_restricted(baseline_mission: StructuredMission):
    """Verify UNSAFE or RESTRICTED candidates are disqualified from selection."""
    cand_restricted = CandidateZone(
        id="ZONE-RESTRICTED",
        location=Coordinate(lat=13.25, lon=80.50),
        distance_km=28.0,
        fishing_score=98.0,
        safety_score=100.0,
        safety_status=SafetyEvaluation.RESTRICTED,
    )

    cand_unsafe = CandidateZone(
        id="ZONE-UNSAFE",
        location=Coordinate(lat=13.10, lon=80.40),
        distance_km=15.0,
        fishing_score=90.0,
        safety_score=20.0,
        safety_status=SafetyEvaluation.UNSAFE,
    )

    cand_ok = CandidateZone(
        id="ZONE-OK",
        location=Coordinate(lat=13.05, lon=80.30),
        distance_km=10.0,
        fishing_score=75.0,
        safety_score=85.0,
        safety_status=SafetyEvaluation.SAFE,
    )

    decision = DecisionEngine.evaluate(
        mission=baseline_mission,
        candidates=[cand_restricted, cand_unsafe, cand_ok],
    )

    assert decision.selected_zone is not None
    assert decision.selected_zone.id == "ZONE-OK"
    assert cand_restricted.composite_score == 0.0
    assert cand_unsafe.composite_score == 0.0


def test_no_qualifying_candidates(baseline_mission: StructuredMission):
    """Verify that when no safe zones exist, ORCA withholds recommendation with clear explanation."""
    cand_all_bad = CandidateZone(
        id="ZONE-STORM",
        location=Coordinate(lat=13.20, lon=80.45),
        distance_km=20.0,
        fishing_score=95.0,
        safety_score=25.0,
        safety_status=SafetyEvaluation.UNSAFE,
    )

    decision = DecisionEngine.evaluate(
        mission=baseline_mission,
        candidates=[cand_all_bad],
    )

    assert decision.selected_zone is None
    assert "No candidate zone" in decision.recommendation_text
    assert "preclude a safe departure" in decision.recommendation_text


def test_trade_off_and_what_if_explanations(baseline_mission: StructuredMission):
    """Verify trade-off comparative analysis and dynamic what-if suggestions."""
    cand1 = CandidateZone(
        id="ZONE-1",
        location=Coordinate(lat=13.15, lon=80.40),
        distance_km=18.0,
        fishing_score=85.0,
        safety_score=90.0,
        safety_status=SafetyEvaluation.SAFE,
        weather_data={"wave_height_m": 1.1, "wind_speed_kmh": 16.0},
        ocean_data={"sst_c": 28.3, "chlorophyll_mg_m3": 3.2},
    )

    cand2 = CandidateZone(
        id="ZONE-2",
        location=Coordinate(lat=13.25, lon=80.55),
        distance_km=32.0,
        fishing_score=92.0,
        safety_score=60.0,
        safety_status=SafetyEvaluation.CAUTION,
        weather_data={"wave_height_m": 1.7, "wind_speed_kmh": 26.0},
    )

    decision = DecisionEngine.evaluate(
        mission=baseline_mission,
        candidates=[cand1, cand2],
    )

    assert decision.selected_zone is not None
    assert decision.selected_zone.id == "ZONE-1"

    # Trade-off text should mention Zone-2
    assert "Zone ZONE-2" in decision.trade_off_analysis
    assert "Higher raw fishing potential" in decision.trade_off_analysis or "risk" in decision.trade_off_analysis

    # What-if suggestions
    assert len(decision.what_if_suggestions) >= 2
    assert any("farther" in s for s in decision.what_if_suggestions)


@pytest.mark.asyncio
async def test_end_to_end_commander_to_decision():
    """Verify end-to-end integration: query -> Commander -> DecisionEngine -> DecisionOutput."""
    commander = CommanderAgent()
    query = (
        "I want to go fishing tomorrow morning from Chennai. "
        "Find the best fishing zone within 35 km, keep the sea risk low, and avoid restricted areas."
    )
    now = datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc)

    # 1. Orchestrate with Commander
    workflow = await commander.execute_query(query=query, now=now)
    assert workflow.workflow_status == "completed"
    assert len(workflow.candidate_zones) > 0

    # 2. Evaluate with DecisionEngine
    decision = DecisionEngine.evaluate(
        mission=workflow.mission,
        candidates=workflow.candidate_zones,
        overall_confidence=workflow.overall_confidence,
        data_provenance=workflow.all_evidence,
    )

    assert isinstance(decision, DecisionOutput)
    assert decision.selected_zone is not None
    assert decision.selected_zone.distance_km <= 35.0
    assert decision.selected_zone.safety_status in (SafetyEvaluation.SAFE, SafetyEvaluation.CAUTION)
    assert decision.overall_confidence > 0.0
    assert len(decision.recommendation_text) > 0
    assert len(decision.trade_off_analysis) > 0
    assert len(decision.what_if_suggestions) > 0
