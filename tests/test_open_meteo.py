"""Unit tests for Open-Meteo Marine API validator, adapter, and client."""

from datetime import datetime, timedelta, timezone
import pytest

from orca.data_sources.open_meteo.adapter import OpenMeteoAdapter
from orca.data_sources.open_meteo.client import OpenMeteoClient
from orca.data_sources.open_meteo.validator import OpenMeteoValidator
from orca.models.evidence import DataFreshness
from orca.models.mission import Coordinate


def test_validator_valid_payload():
    """Verify standard Open-Meteo response passes validation cleanly."""
    coord = Coordinate(lat=13.10, lon=80.30)
    raw = {
        "latitude": 13.10,
        "longitude": 80.30,
        "hourly": {
            "time": ["2026-10-24T06:00", "2026-10-24T07:00"],
            "wave_height": [1.2, 1.4],
            "wave_direction": [105.0, 110.0],
            "wave_period": [8.0, 8.2],
            "wind_wave_height": [0.5, 0.6],
            "swell_wave_height": [0.9, 1.0],
            "ocean_current_velocity": [0.3, 0.35],
            "sea_surface_temperature": [28.2, 28.3],
        },
    }

    result = OpenMeteoValidator.validate(raw, coord)
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_validator_missing_hourly():
    """Verify validator flags missing hourly key as fatal error."""
    coord = Coordinate(lat=13.10, lon=80.30)
    raw = {"latitude": 13.10, "longitude": 80.30}

    result = OpenMeteoValidator.validate(raw, coord)
    assert result.is_valid is False
    assert any("hourly" in err for err in result.errors)


def test_validator_out_of_bounds_physical_values():
    """Verify validator warns on implausible physical values (e.g. 50m waves)."""
    coord = Coordinate(lat=13.10, lon=80.30)
    raw = {
        "latitude": 13.10,
        "longitude": 80.30,
        "hourly": {
            "time": ["2026-10-24T06:00"],
            "wave_height": [65.0],  # Out of range!
            "wave_direction": [100.0],
            "wave_period": [8.0],
            "wind_wave_height": [0.5],
            "swell_wave_height": [0.9],
            "ocean_current_velocity": [0.3],
            "sea_surface_temperature": [28.0],
        },
    }

    result = OpenMeteoValidator.validate(raw, coord)
    assert result.is_valid is True  # Schema is valid, but triggers warning
    assert any("outside expected physical range" in w for w in result.warnings)


def test_adapter_closest_hour_selection():
    """Verify adapter picks the forecast index matching target_time."""
    coord = Coordinate(lat=13.10, lon=80.30)
    raw = {
        "latitude": 13.10,
        "longitude": 80.30,
        "hourly": {
            "time": ["2026-10-24T06:00", "2026-10-24T07:00", "2026-10-24T08:00"],
            "wave_height": [1.0, 1.8, 2.5],
            "wave_direction": [90.0, 95.0, 100.0],
            "wave_period": [7.0, 8.5, 9.0],
            "wind_wave_height": [0.4, 0.7, 1.1],
            "swell_wave_height": [0.8, 1.3, 1.8],
            "swell_wave_direction": [100.0, 105.0, 110.0],
            "swell_wave_period": [8.0, 9.0, 9.5],
            "ocean_current_velocity": [0.2, 0.4, 0.6],
            "sea_surface_temperature": [28.0, 28.2, 28.5],
        },
    }

    # Query target at 07:15 -> Should pick index 1 (07:00) with wave_height 1.8
    target = datetime(2026, 10, 24, 7, 15, tzinfo=timezone.utc)
    now = datetime(2026, 10, 24, 6, 30, tzinfo=timezone.utc)

    forecast = OpenMeteoAdapter.to_ocean_state_forecast(raw, coord, target_time=target, now=now)

    assert forecast.significant_wave_height_m == 1.8
    assert forecast.swell_height_m == 1.3
    assert forecast.surface_current_ms == 0.4
    assert forecast.water_temperature_c == 28.2
    assert forecast.evidence.source == "OPEN_METEO_MARINE"
    assert forecast.evidence.freshness == DataFreshness.LIVE


@pytest.mark.asyncio
async def test_client_fetch_marine_forecast_fallback():
    """Verify OpenMeteoClient fetches normalized forecast via fallback when offline."""
    client = OpenMeteoClient(base_url="https://mock-meteo.invalid", timeout_seconds=0.1)
    coord = Coordinate(lat=13.15, lon=80.40)
    target = datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc)

    forecast = await client.fetch_marine_forecast(location=coord, target_time=target)

    assert forecast.location.lat == 13.15
    assert forecast.significant_wave_height_m > 0
    assert forecast.swell_height_m > 0
    assert forecast.wind_speed_kmh > 0
    assert forecast.surface_current_ms > 0
    assert forecast.evidence.source == "OPEN_METEO_MARINE"
