"""Unit tests for ORCA deterministic geospatial safety layer."""

import pytest
from shapely.geometry import Point

from orca.geospatial import (
    DEFAULT_MARITIME_ZONES,
    GeospatialSafetyEngine,
    GeospatialSafetyResult,
    MaritimeBoundaryStore,
    MaritimeZone,
    RestrictionLevel,
    ZoneType,
    bounding_box,
    calculate_bearing,
    destination_point,
    haversine_distance,
    haversine_distance_nm,
)
from orca.models.candidate import CandidateZone, SafetyEvaluation
from orca.models.mission import Coordinate, StructuredMission, TimeWindow


# ---------------------------------------------------------------------------
# Geodesic Math Tests
# ---------------------------------------------------------------------------

def test_haversine_distance_same_point():
    p = Coordinate(lat=13.0827, lon=80.2707)
    assert haversine_distance(p, p) == 0.0
    assert haversine_distance_nm(p, p) == 0.0


def test_haversine_distance_known():
    # Distance between Chennai (13.0827, 80.2707) and Mahabalipuram (12.6269, 80.1927) ~51-52 km
    p1 = Coordinate(lat=13.0827, lon=80.2707)
    p2 = Coordinate(lat=12.6269, lon=80.1927)
    dist = haversine_distance(p1, p2)
    assert 50.0 < dist < 53.0
    dist_nm = haversine_distance_nm(p1, p2)
    assert 26.0 < dist_nm < 29.0


def test_calculate_bearing_cardinal():
    origin = Coordinate(lat=0.0, lon=0.0)
    north = Coordinate(lat=1.0, lon=0.0)
    east = Coordinate(lat=0.0, lon=1.0)
    south = Coordinate(lat=-1.0, lon=0.0)
    west = Coordinate(lat=0.0, lon=-1.0)

    assert calculate_bearing(origin, north) == pytest.approx(0.0, abs=0.5)
    assert calculate_bearing(origin, east) == pytest.approx(90.0, abs=0.5)
    assert calculate_bearing(origin, south) == pytest.approx(180.0, abs=0.5)
    assert calculate_bearing(origin, west) == pytest.approx(270.0, abs=0.5)


def test_destination_point_and_bounding_box():
    origin = Coordinate(lat=13.0, lon=80.0)
    # Travel 20 km East (bearing 90°)
    dest = destination_point(origin, bearing_degrees=90.0, distance_km=20.0)
    assert dest.lat == pytest.approx(13.0, abs=0.01)
    assert dest.lon > origin.lon
    assert haversine_distance(origin, dest) == pytest.approx(20.0, abs=0.1)

    # Bounding box test
    sw, ne = bounding_box(origin, radius_km=25.0)
    assert sw.lat < origin.lat < ne.lat
    assert sw.lon < origin.lon < ne.lon


# ---------------------------------------------------------------------------
# MaritimeZone & Boundary Store Tests
# ---------------------------------------------------------------------------

def test_maritime_zone_polygon_creation():
    zone = MaritimeZone(
        zone_id="TEST-ZONE",
        name="Test Protected Area",
        zone_type=ZoneType.MARINE_PROTECTED_AREA,
        restriction_level=RestrictionLevel.STRICT_NO_ENTRY,
        description="Test polygon",
        coordinates=[(10.0, 80.0), (10.0, 81.0), (11.0, 81.0), (11.0, 80.0)],
        buffer_km=2.0,
    )
    poly = zone.to_polygon()
    assert poly.is_valid
    # Point inside (lon=80.5, lat=10.5)
    assert poly.contains(Point(80.5, 10.5))
    # Point outside
    assert not poly.contains(Point(82.0, 10.5))


def test_maritime_zone_validation_error():
    with pytest.raises(ValueError):
        zone = MaritimeZone(
            zone_id="INVALID",
            name="Invalid",
            zone_type=ZoneType.EEZ,
            restriction_level=RestrictionLevel.ADVISORY,
            description="Too few points",
            coordinates=[(10.0, 80.0), (11.0, 80.0)],
        )
        zone.to_polygon()


def test_default_boundary_store_loads():
    store = MaritimeBoundaryStore()
    zones = store.get_all_zones()
    assert len(zones) >= 5
    assert store.get_zone("IN-MPA-GULF-MANNAR") is not None
    assert store.get_zone("IN-BORDER-IMBL") is not None
    assert store.get_zone("IN-TSS-CHENNAI") is not None


def test_store_containment_and_buffer():
    store = MaritimeBoundaryStore()

    # Point deep inside Gulf of Mannar MPA: (lat=9.05, lon=78.60)
    inside_mpa = Coordinate(lat=9.05, lon=78.60)
    matched = store.find_zones_containing(inside_mpa)
    assert any(z.zone_id == "IN-MPA-GULF-MANNAR" for z in matched)

    # Point safely offshore Chennai away from protected zones: (lat=12.95, lon=80.30)
    safe_coord = Coordinate(lat=12.95, lon=80.30)
    assert len(store.find_zones_containing(safe_coord)) == 0


# ---------------------------------------------------------------------------
# Geospatial Safety Engine Tests
# ---------------------------------------------------------------------------

def test_engine_safe_offshore_coordinate():
    engine = GeospatialSafetyEngine()
    origin = Coordinate(lat=13.00, lon=80.25)  # Coastal Chennai
    safe_target = Coordinate(lat=13.00, lon=80.30)  # ~5.4 km directly offshore

    result = engine.evaluate_coordinate(target=safe_target, origin=origin, max_distance_km=30.0)
    assert result.is_safe is True
    assert result.safety_status == SafetyEvaluation.SAFE
    assert result.distance_from_origin_km is not None
    assert result.distance_from_origin_km < 10.0
    assert len(result.zone_violations) == 0


def test_engine_exceeding_max_range():
    engine = GeospatialSafetyEngine()
    origin = Coordinate(lat=13.00, lon=80.25)
    far_target = Coordinate(lat=13.00, lon=81.00)  # ~81 km offshore

    result = engine.evaluate_coordinate(target=far_target, origin=origin, max_distance_km=25.0)
    assert result.is_safe is False
    assert result.safety_status == SafetyEvaluation.UNSAFE
    assert "exceeds mission operational limit" in result.notes[0]


def test_engine_inside_no_entry_mpa():
    engine = GeospatialSafetyEngine()
    # Point inside Gulf of Mannar core
    mpa_point = Coordinate(lat=9.05, lon=78.60)
    result = engine.evaluate_coordinate(target=mpa_point)

    assert result.is_safe is False
    assert result.safety_status == SafetyEvaluation.UNSAFE
    assert any("IN-MPA-GULF-MANNAR" in v for v in result.zone_violations)


def test_engine_inside_shipping_corridor():
    engine = GeospatialSafetyEngine()
    # Point inside Chennai Port Shipping fairway (lat=13.20, lon=80.40)
    tss_point = Coordinate(lat=13.20, lon=80.40)
    result = engine.evaluate_coordinate(target=tss_point)

    assert result.safety_status == SafetyEvaluation.CAUTION
    assert any("IN-TSS-CHENNAI" in t for t in result.traffic_warnings)


def test_engine_candidate_zone_enrichment():
    engine = GeospatialSafetyEngine()
    mission = StructuredMission(
        request_id="trace-geo-01",
        activity="fishing",
        origin=Coordinate(lat=13.00, lon=80.25),
        time_window=TimeWindow(
            start="2026-10-24T06:00:00Z",
            end="2026-10-24T18:00:00Z",
        ),
        max_distance_km=20.0,
    )

    candidate = CandidateZone(
        id="ORCA-TEST-Z1",
        location=Coordinate(lat=13.00, lon=80.32),  # ~7.6 km offshore
        distance_km=0.0,
        fishing_score=85.0,
        safety_score=100.0,
    )

    enriched = engine.evaluate_mission_candidate(candidate, mission)
    assert enriched.distance_km > 0.0
    assert enriched.bearing_degrees is not None
    assert enriched.safety_status in (SafetyEvaluation.SAFE, SafetyEvaluation.CAUTION)
    assert len(enriched.geospatial_notes) > 0
