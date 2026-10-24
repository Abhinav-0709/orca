"""Unit tests for INCOIS operational client."""

from datetime import datetime, timezone
import pytest
from orca.data_sources.incois.client import IncoisClient
from orca.models.evidence import DataFreshness
from orca.models.mission import Coordinate


@pytest.mark.asyncio
async def test_incois_fetch_pfz_fallback():
    """Verify INCOIS client retrieves normalized PFZ fallback records with correct metadata."""
    client = IncoisClient(base_url="https://mock-incois.invalid", timeout_seconds=0.1)
    center = Coordinate(lat=13.0827, lon=80.2707)  # Chennai
    now = datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc)

    advisories = await client.fetch_pfz_advisories(center=center, radius_km=30.0, now=now)

    assert len(advisories) >= 2
    for adv in advisories:
        assert adv.distance_km <= 30.0
        assert adv.depth_m > 0
        assert adv.potential_score >= 0.70
        assert adv.evidence.source.startswith("INCOIS")
        assert adv.evidence.freshness in [DataFreshness.LIVE, DataFreshness.RECENT]
        assert adv.reference_landing_center == "Kasimedu Fishing Harbour"


@pytest.mark.asyncio
async def test_incois_fetch_pfz_radius_filtering():
    """Verify radius constraints filter out distant PFZ zones."""
    client = IncoisClient(base_url="https://mock-incois.invalid", timeout_seconds=0.1)
    center = Coordinate(lat=13.0827, lon=80.2707)
    now = datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc)

    # With radius 20km, only zones <= 20km should be returned
    advisories_small = await client.fetch_pfz_advisories(center=center, radius_km=20.0, now=now)
    advisories_large = await client.fetch_pfz_advisories(center=center, radius_km=50.0, now=now)

    assert len(advisories_small) < len(advisories_large)
    for adv in advisories_small:
        assert adv.distance_km <= 20.0


@pytest.mark.asyncio
async def test_incois_fetch_ocean_state_forecast():
    """Verify INCOIS Ocean State Forecast normalization."""
    client = IncoisClient(base_url="https://mock-incois.invalid", timeout_seconds=0.1)
    loc = Coordinate(lat=13.15, lon=80.45)
    now = datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc)

    osf = await client.fetch_ocean_state_forecast(location=loc, valid_at=now)

    assert osf.significant_wave_height_m > 0
    assert osf.swell_height_m > 0
    assert osf.wind_speed_kmh > 0
    assert osf.surface_current_ms > 0
    assert osf.evidence.source.startswith("INCOIS")
    assert osf.forecast_valid_to > now


def test_incois_parse_live_payload():
    """Verify JSON parsing of live INCOIS format."""
    client = IncoisClient()
    now = datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc)
    raw = {
        "features": [
            {
                "properties": {
                    "sector_id": "PFZ-LIVE-01",
                    "lat": 13.25,
                    "lon": 80.50,
                    "depth_m": 45.0,
                    "distance_km": 28.0,
                    "direction": "ENE",
                    "landing_center": "Chennai Port",
                    "sst_c": 28.1,
                    "chlorophyll_mg_m3": 3.6,
                    "potential_score": 0.91,
                    "observed_at": "2026-10-24T08:30:00+00:00",
                    "valid_until": "2026-10-25T08:30:00+00:00",
                }
            }
        ]
    }

    parsed = client._parse_pfz_response(raw, now)
    assert len(parsed) == 1
    item = parsed[0]
    assert item.sector_id == "PFZ-LIVE-01"
    assert item.location.lat == 13.25
    assert item.sst_c == 28.1
    assert item.potential_score == 0.91
    assert item.evidence.freshness == DataFreshness.LIVE
