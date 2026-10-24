"""ORCA Weather & Marine Forecast Specialist Agent.

Evaluates marine meteorological risk: wave height, swell period, wind speeds,
ocean currents via Open-Meteo Marine API, and coastal storm/fishermen bulletins via IMD.
Rule: Weather risk is an independent dimension; high opportunity zones are penalized if weather is unsafe.
"""

from datetime import datetime, timezone
from typing import Any

from orca.data_sources.imd.client import ImdClient
from orca.data_sources.models import MarineWarning, OceanStateForecast, WarningSeverity
from orca.data_sources.open_meteo.client import OpenMeteoClient
from orca.logging.logger import get_logger
from orca.models.agent_contract import AgentRequest, AgentResponse, AgentStatus, AgentWarning
from orca.models.candidate import CandidateZone, SafetyEvaluation
from orca.models.evidence import EvidenceItem
from orca.models.mission import Coordinate

logger = get_logger(__name__, agent="weather_agent")


class WeatherAgent:
    """Specialist agent assessing environmental marine operating risks."""

    def __init__(
        self,
        open_meteo_client: OpenMeteoClient | None = None,
        imd_client: ImdClient | None = None,
    ) -> None:
        self.meteo_client = open_meteo_client or OpenMeteoClient()
        self.imd_client = imd_client or ImdClient()

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process structured mission to evaluate weather hazards and marine forecasts."""
        mission = request.mission
        logger.info(
            f"WeatherAgent assessing risks for mission '{mission.request_id}' during {mission.time_window.start}"
        )

        now = datetime.now(timezone.utc)
        evidence_items: list[EvidenceItem] = []
        warnings: list[AgentWarning] = []

        try:
            coast_region = request.parameters.get("coast_region", "Tamil Nadu Coast")
            basin = request.parameters.get("basin", "Bay of Bengal")
            imd_warnings = await self.imd_client.fetch_fishermen_warnings(coast_region=coast_region, now=now)
            cyclone_warnings = await self.imd_client.fetch_cyclone_warnings(basin=basin, now=now)

            all_bulletins = imd_warnings + cyclone_warnings
            for b in all_bulletins:
                evidence_items.append(b.evidence)
                if b.severity in (WarningSeverity.RED, WarningSeverity.ORANGE):
                    warnings.append(
                        AgentWarning(
                            code=f"IMD_{b.severity.value}_BULLETIN",
                            message=f"{b.headline}: {b.description}",
                            severity="critical" if b.severity == WarningSeverity.RED else "moderate",
                        )
                    )

            # 2. Determine target coordinates to evaluate
            candidate_dicts = request.parameters.get("candidate_zones", [])
            coordinates_to_evaluate: list[tuple[str, Coordinate]] = []

            if candidate_dicts:
                for c in candidate_dicts:
                    cid = c.get("id", "UNKNOWN")
                    loc = c.get("location", {})
                    coordinates_to_evaluate.append((cid, Coordinate(lat=loc["lat"], lon=loc["lon"])))
            else:
                # Fallback to origin if no candidate coordinates provided yet
                coordinates_to_evaluate.append(("ORIGIN", mission.origin))

            # 3. Query Open-Meteo for each coordinate and compute deterministic weather score
            weather_evaluations: list[dict[str, Any]] = []
            lowest_safety_score = 100.0

            for cid, coord in coordinates_to_evaluate:
                forecast = await self.meteo_client.fetch_marine_forecast(
                    location=coord,
                    target_time=mission.time_window.start,
                    now=now,
                )
                evidence_items.append(forecast.evidence)

                score, safety_status, hazard_notes = self._calculate_weather_safety(forecast, all_bulletins)
                lowest_safety_score = min(lowest_safety_score, score)

                # Check for swell breaker hazard
                if (
                    forecast.swell_height_m
                    and forecast.swell_height_m > 1.8
                    and forecast.swell_period_s
                    and forecast.swell_period_s > 12.0
                ):
                    warnings.append(
                        AgentWarning(
                            code="HIGH_SWELL_SURGE_RISK",
                            message=(
                                f"Zone {cid}: High long-period swell ({forecast.swell_height_m:.1f}m, "
                                f"{forecast.swell_period_s:.0f}s) creates dangerous coastal breaker conditions."
                            ),
                            severity="moderate",
                        )
                    )

                weather_evaluations.append(
                    {
                        "zone_id": cid,
                        "location": coord.model_dump(),
                        "weather_safety_score": score,
                        "safety_status": safety_status.value,
                        "significant_wave_height_m": forecast.significant_wave_height_m,
                        "swell_height_m": forecast.swell_height_m,
                        "swell_period_s": forecast.swell_period_s,
                        "wind_speed_kmh": forecast.wind_speed_kmh,
                        "surface_current_ms": forecast.surface_current_ms,
                        "hazard_notes": hazard_notes,
                    }
                )

            # Overall execution confidence
            confidences = [e.confidence for e in evidence_items]
            avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.90

            return AgentResponse(
                agent="weather",
                status=AgentStatus.SUCCESS,
                request_id=request.request_id,
                data={
                    "weather_evaluations": weather_evaluations,
                    "overall_lowest_safety_score": lowest_safety_score,
                    "active_imd_bulletins_count": len(all_bulletins),
                },
                evidence=evidence_items,
                warnings=warnings,
                confidence=avg_confidence,
            )

        except Exception as exc:
            logger.error(f"WeatherAgent failed during evaluation: {exc}", exc_info=True)
            return AgentResponse(
                agent="weather",
                status=AgentStatus.FAILED,
                request_id=request.request_id,
                data={},
                evidence=evidence_items,
                warnings=[
                    AgentWarning(
                        code="WEATHER_DATA_UNAVAILABLE",
                        message=f"Failed to acquire marine weather telemetry: {str(exc)}",
                        severity="critical",
                    )
                ],
                confidence=0.0,
            )

    def _calculate_weather_safety(
        self,
        forecast: OceanStateForecast,
        bulletins: list[MarineWarning],
    ) -> tuple[float, SafetyEvaluation, list[str]]:
        """Calculate deterministic weather safety score (0 - 100) and identify hazard notes."""
        notes: list[str] = []
        score = 100.0

        # 1. Wave height penalty
        waves = forecast.significant_wave_height_m or 0.8
        if waves <= 1.0:
            notes.append(f"Calm seas (wave height: {waves:.1f} m)")
        elif waves <= 1.5:
            score -= 20.0
            notes.append(f"Moderate sea state (wave height: {waves:.1f} m)")
        elif waves <= 2.0:
            score -= 45.0
            notes.append(f"Rough seas (wave height: {waves:.1f} m)")
        elif waves <= 2.5:
            score -= 75.0
            notes.append(f"Very rough seas (wave height: {waves:.1f} m)")
        else:
            score = 0.0
            notes.append(f"DANGEROUS SEAS: Wave height {waves:.1f} m exceeds small craft seaworthiness")

        # 2. Wind speed penalty
        wind = forecast.wind_speed_kmh or 15.0
        if wind > 50.0:
            score = min(score, 10.0)
            notes.append(f"Gale-force winds ({wind:.1f} km/h)")
        elif wind > 38.0:
            score -= 30.0
            notes.append(f"Strong coastal winds ({wind:.1f} km/h)")
        elif wind > 28.0:
            score -= 15.0
            notes.append(f"Breezy conditions ({wind:.1f} km/h)")

        # 3. IMD bulletin penalties
        has_red = any(b.severity == WarningSeverity.RED for b in bulletins)
        has_orange = any(b.severity == WarningSeverity.ORANGE for b in bulletins)
        has_yellow = any(b.severity == WarningSeverity.YELLOW for b in bulletins)

        if has_red:
            score = 0.0
            notes.append("CRITICAL: IMD RED Cyclone / Gale alert in effect.")
        elif has_orange:
            score = min(score, 30.0)
            notes.append("CAUTION: IMD ORANGE Squall advisory in effect.")
        elif has_yellow:
            score = min(score, 65.0)
            notes.append("NOTICE: IMD YELLOW advisory in effect.")

        score = max(0.0, round(score, 1))

        if score < 30.0:
            status = SafetyEvaluation.UNSAFE
        elif score < 60.0:
            status = SafetyEvaluation.CAUTION
        else:
            status = SafetyEvaluation.SAFE

        return (score, status, notes)
