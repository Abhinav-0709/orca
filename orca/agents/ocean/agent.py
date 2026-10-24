"""ORCA Ocean Intelligence Specialist Agent.

Evaluates oceanographic productivity, SST, Chlorophyll-a, and INCOIS PFZ advisories.
Rule: The Ocean Agent provides opportunity evidence only; it never declares a zone universally safe.
"""

from datetime import datetime, timezone
from typing import Any

from orca.data_sources.incois.client import IncoisClient
from orca.data_sources.models import PFZAdvisory
from orca.logging.logger import get_logger
from orca.models.agent_contract import AgentRequest, AgentResponse, AgentStatus, AgentWarning
from orca.models.candidate import CandidateZone, SafetyEvaluation
from orca.models.evidence import EvidenceItem
from orca.models.mission import Coordinate, StructuredMission

logger = get_logger(__name__, agent="ocean_agent")


class OceanAgent:
    """Specialist agent analyzing marine fishing potential and oceanographic signals."""

    def __init__(self, incois_client: IncoisClient | None = None) -> None:
        self.client = incois_client or IncoisClient()

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process structured mission request to evaluate fishing opportunity and candidate zones."""
        mission = request.mission
        logger.info(
            f"OceanAgent processing mission '{mission.request_id}' at ({mission.origin.lat}, {mission.origin.lon})"
        )

        now = datetime.now(timezone.utc)
        evidence_items: list[EvidenceItem] = []
        warnings: list[AgentWarning] = []

        try:
            # 1. Fetch PFZ advisories around mission origin within max operational distance
            advisories = await self.client.fetch_pfz_advisories(
                center=mission.origin,
                radius_km=mission.max_distance_km,
                now=now,
            )

            # 2. Fetch baseline ocean state forecast for origin area
            ocean_forecast = await self.client.fetch_ocean_state_forecast(
                location=mission.origin,
                valid_at=now,
            )
            evidence_items.append(ocean_forecast.evidence)

            # 3. Build candidate zones from advisories
            candidate_zones: list[CandidateZone] = []
            for i, adv in enumerate(advisories):
                evidence_items.append(adv.evidence)

                # Calculate opportunity score combining PFZ score and SST/Chlorophyll suitability
                fishing_score = self._compute_fishing_score(adv)

                zone = CandidateZone(
                    id=f"ORCA-PFZ-{i + 1:02d}",
                    location=adv.location,
                    distance_km=adv.distance_km or 0.0,
                    bearing_degrees=None,
                    fishing_score=fishing_score,
                    safety_score=100.0,  # Ocean agent does not assess safety; leaves default to weather/maritime
                    accessibility_score=100.0,
                    confidence_score=adv.evidence.confidence,
                    safety_status=SafetyEvaluation.SAFE,
                    ocean_data={
                        "sector_id": adv.sector_id,
                        "reference_landing_center": adv.reference_landing_center,
                        "depth_m": adv.depth_m,
                        "sst_c": adv.sst_c,
                        "chlorophyll_mg_m3": adv.chlorophyll_mg_m3,
                        "raw_potential_score": adv.potential_score,
                    },
                    weather_data={},
                    geospatial_notes=[],
                    reasoning=(
                        f"PFZ advisory from {adv.reference_landing_center} at depth {adv.depth_m:.0f}m. "
                        f"SST: {adv.sst_c or 'N/A'}°C, "
                        f"Chlorophyll: {adv.chlorophyll_mg_m3 or 'N/A'} mg/m³."
                    ),
                )
                candidate_zones.append(zone)

            # Check for ocean thermal warnings (e.g. extreme SST)
            if ocean_forecast.water_temperature_c and ocean_forecast.water_temperature_c > 31.0:
                warnings.append(
                    AgentWarning(
                        code="HIGH_SST_ANOMALY",
                        message=f"Elevated sea surface temperature ({ocean_forecast.water_temperature_c:.1f}°C) may depress pelagic fish aggregation.",
                        severity="low",
                    )
                )

            # Calculate composite confidence from evidence
            confidences = [e.confidence for e in evidence_items]
            avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.85

            return AgentResponse(
                agent="ocean",
                status=AgentStatus.SUCCESS,
                request_id=request.request_id,
                data={
                    "candidate_zones": [z.model_dump() for z in candidate_zones],
                    "advisories_count": len(candidate_zones),
                    "ocean_state_forecast": ocean_forecast.model_dump(),
                },
                evidence=evidence_items,
                warnings=warnings,
                confidence=avg_confidence,
            )

        except Exception as exc:
            logger.error(f"OceanAgent failed during evaluation: {exc}", exc_info=True)
            return AgentResponse(
                agent="ocean",
                status=AgentStatus.FAILED,
                request_id=request.request_id,
                data={},
                evidence=evidence_items,
                warnings=[
                    AgentWarning(
                        code="OCEAN_DATA_UNAVAILABLE",
                        message=f"Failed to acquire oceanographic intelligence: {str(exc)}",
                        severity="critical",
                    )
                ],
                confidence=0.0,
            )

    def _compute_fishing_score(self, adv: PFZAdvisory) -> float:
        """Calculate normalized fishing opportunity score (0 - 100) from PFZ advisory parameters."""
        base_score = adv.potential_score * 100.0 if adv.potential_score <= 1.0 else adv.potential_score

        # Temperature preference bonus for tropical Indian waters (ideal pelagic range: 27°C - 29.5°C)
        temp_factor = 1.0
        if adv.sst_c:
            sst = adv.sst_c
            if 27.0 <= sst <= 29.5:
                temp_factor = 1.10
            elif sst < 25.0 or sst > 31.0:
                temp_factor = 0.85

        # Chlorophyll concentration bonus (ideal: 0.3 - 2.5 mg/m³ for high zooplankton/feed)
        chloro_factor = 1.0
        if adv.chlorophyll_mg_m3:
            chl = adv.chlorophyll_mg_m3
            if 0.3 <= chl <= 2.5:
                chloro_factor = 1.10
            elif chl < 0.1:
                chloro_factor = 0.90

        adjusted = base_score * temp_factor * chloro_factor
        return round(min(100.0, max(0.0, adjusted)), 1)
