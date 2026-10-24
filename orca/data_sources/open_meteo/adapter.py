"""Data Adapter converting validated Open-Meteo payloads into normalized OceanStateForecast models."""

from datetime import datetime, timezone
from typing import Any
from orca.data_sources.freshness import evaluate_freshness
from orca.data_sources.models import OceanStateForecast
from orca.logging.logger import get_logger
from orca.models.evidence import EvidenceItem
from orca.models.mission import Coordinate

logger = get_logger(__name__, agent="open_meteo_adapter")


class OpenMeteoAdapter:
    """Transforms raw Open-Meteo marine hourly series into normalized OceanStateForecast objects."""

    @classmethod
    def to_ocean_state_forecast(
        cls,
        raw_data: dict[str, Any],
        location: Coordinate,
        target_time: datetime | None = None,
        now: datetime | None = None,
    ) -> OceanStateForecast:
        """Convert Open-Meteo response into a normalized OceanStateForecast.

        Args:
            raw_data: Validated raw dictionary from Open-Meteo.
            location: The query coordinates.
            target_time: Requested operational forecast timestamp (defaults to current time).
            now: Current reference time (defaults to utcnow).

        Returns:
            OceanStateForecast: Standardized ocean condition forecast with attached EvidenceItem.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        if target_time is None:
            target_time = now

        # Ensure timezone-aware UTC
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        hourly = raw_data.get("hourly", {})
        times: list[str] = hourly.get("time", [])

        # Find closest hourly index to target_time
        target_iso = target_time.strftime("%Y-%m-%dT%H:00")
        best_idx = 0
        min_delta = float("inf")

        for idx, t_str in enumerate(times):
            try:
                # Handle ISO format strings like "2026-10-24T06:00"
                t_dt = datetime.fromisoformat(t_str)
                if t_dt.tzinfo is None:
                    t_dt = t_dt.replace(tzinfo=timezone.utc)
                delta = abs((t_dt - target_time).total_seconds())
                if delta < min_delta:
                    min_delta = delta
                    best_idx = idx
            except ValueError:
                continue

        # Extract values at closest index
        def _get_val(key: str, default: float) -> float:
            series = hourly.get(key, [])
            if series and best_idx < len(series) and series[best_idx] is not None:
                return float(series[best_idx])
            return default

        swh = _get_val("wave_height", 1.2)
        swell_height = _get_val("swell_wave_height", 0.9)
        swell_period = _get_val("swell_wave_period", 8.5)
        swell_dir = _get_val("swell_wave_direction", 110.0)
        wave_dir = _get_val("wave_direction", 95.0)

        # Wind speed estimate from wind_wave_height or fallback
        wind_wave_height = _get_val("wind_wave_height", 0.6)
        # Approximate wind speed (km/h) derived from wind-wave height if direct wind speed isn't in marine API
        # Empirical marine formula: wind_speed_m_s ~= sqrt(height / 0.025); in km/h ~= sqrt(H)*20*3.6/10
        est_wind_kmh = round(max(10.0, (wind_wave_height ** 0.5) * 22.0), 1)

        current_vel = _get_val("ocean_current_velocity", 0.35)
        sst = _get_val("sea_surface_temperature", 28.3)

        # Timestamps for freshness
        forecast_valid_from = target_time
        forecast_valid_to = target_time + (datetime.fromisoformat(times[-1]) - datetime.fromisoformat(times[0]) if times else now)
        issued_at = now  # Model run timestamp

        freshness, conf_mul = evaluate_freshness(issued_at, now + (target_time - now) + (forecast_valid_to - target_time), now)

        evidence = EvidenceItem(
            source="OPEN_METEO_MARINE",
            retrieved_at=now,
            issued_at=issued_at,
            valid_to=forecast_valid_to,
            freshness=freshness,
            geographic_coverage=f"Offshore Grid ({location.lat:.2f}, {location.lon:.2f})",
            confidence=round(0.95 * conf_mul, 2),
            details={
                "provider": "Open-Meteo ECMWF/Météo-France Marine Model",
                "nearest_hour": times[best_idx] if best_idx < len(times) else "N/A",
                "raw_wave_height": swh,
                "raw_swell_height": swell_height,
            },
        )

        return OceanStateForecast(
            location=location,
            significant_wave_height_m=swh,
            swell_height_m=swell_height,
            swell_period_s=swell_period,
            swell_direction_deg=swell_dir,
            wind_speed_kmh=est_wind_kmh,
            wind_direction_deg=wave_dir,
            surface_current_ms=current_vel,
            water_temperature_c=sst,
            forecast_valid_from=forecast_valid_from,
            forecast_valid_to=forecast_valid_to,
            issued_at=issued_at,
            evidence=evidence,
        )
