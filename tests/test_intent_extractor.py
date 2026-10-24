"""Unit tests for Natural Language Intent Extractor."""

from datetime import datetime, timezone
from orca.orchestration.intent_extractor import IntentExtractor


def test_extract_valid_chennai_query():
    """Verify standard hackathon demo prompt extracts all entities accurately."""
    extractor = IntentExtractor()
    query = "I want to go fishing tomorrow morning from Chennai. Find the best fishing zone within 30 km, keep the sea risk low, and avoid restricted areas."
    now = datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc)

    result = extractor.extract(text=query, now=now, request_id="demo-test-01")

    assert result.is_success is True
    assert result.mission is not None
    assert result.mission.request_id == "demo-test-01"
    assert result.mission.activity == "fishing"
    assert result.mission.origin.lat == 13.0827
    assert result.mission.origin.lon == 80.2707
    assert result.mission.max_distance_km == 30.0
    assert result.mission.time_window.start > now
    assert "avoid_restricted_zones" in result.mission.constraints


def test_extract_kasimedu_custom_distance():
    """Verify coastal landing center Kasimedu with custom distance (25 km)."""
    extractor = IntentExtractor()
    query = "Find fishing spots from Kasimedu within 25 km at 6 am tomorrow."
    now = datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc)

    result = extractor.extract(text=query, now=now)

    assert result.is_success is True
    assert result.mission is not None
    assert result.mission.origin.lat == 13.1264
    assert result.mission.max_distance_km == 25.0
    assert result.mission.time_window.start.hour == 6


def test_extract_explicit_lat_lon():
    """Verify explicit coordinate extraction."""
    extractor = IntentExtractor()
    query = "Fish near 13.15, 80.35 within 15 km today afternoon."
    now = datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc)

    result = extractor.extract(text=query, now=now)

    assert result.is_success is True
    assert result.mission is not None
    assert result.mission.origin.lat == 13.15
    assert result.mission.origin.lon == 80.35
    assert result.mission.max_distance_km == 15.0


def test_extract_missing_origin_triggers_clarification():
    """Verify query lacking origin produces a single targeted clarification prompt."""
    extractor = IntentExtractor()
    query = "Where should I go fishing tomorrow within 20 km?"
    now = datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc)

    result = extractor.extract(text=query, now=now)

    assert result.is_success is False
    assert result.mission is None
    assert result.clarification_prompt is not None
    assert "departure port or coastal origin" in result.clarification_prompt
