"""ORCA Maritime Safety Specialist Agent.

Evaluates deterministic boundary geometry, territorial-sea limits, MPAs,
military exclusion zones, buffer perimeters, and candidate range endurance.
Rule: Uses actual Shapely polygon calculations; never asks an LLM to calculate geometry.
"""

from datetime import datetime, timezone
from typing import Any

from orca.geospatial.models import GeospatialSafetyResult, RestrictionLevel
from orca.geospatial.safety_engine import GeospatialSafetyEngine
from orca.logging.logger import get_logger
from orca.models.agent_contract import AgentRequest, AgentResponse, AgentStatus, AgentWarning
from orca.models.candidate import CandidateZone, SafetyEvaluation
from orca.models.evidence import DataFreshness, EvidenceItem
from orca.models.mission import Coordinate

logger = get_logger(__name__, agent="maritime_agent")


class MaritimeSafetyAgent:
    """Specialist agent assessing deterministic geospatial constraints and maritime boundaries."""

    def __init__(self, safety_engine: GeospatialSafetyEngine | None = None) -> None:
        self.engine = safety_engine or GeospatialSafetyEngine()

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process structured mission to evaluate maritime boundary constraints and clearances."""
        mission = request.mission
        logger.info(
            f"MaritimeSafetyAgent evaluating geospatial constraints for mission '{mission.request_id}'"
        )

        evidence_items: list[EvidenceItem] = []
        warnings: list[AgentWarning] = []

        try:
            # 1. Register deterministic GIS evidence source
            evidence_items.append(
                EvidenceItem(
                    source="MARITIME_BOUNDARIES_GIS",
                    retrieved_at=datetime.now(timezone.utc),
                    observed_at=datetime.now(timezone.utc),
                    freshness=DataFreshness.LIVE,
                    geographic_coverage="Indian Maritime Waters / Tamil Nadu & Bay of Bengal",
                    confidence=1.0,
                    details={
                        "engine": "Shapely Deterministic Boundary Engine",
                        "geodesic_model": "WGS84 / Spherical Earth (Haversine)",
                    },
                )
            )

            # 2. Extract candidate zones or coordinates to evaluate
            candidate_dicts = request.parameters.get("candidate_zones", [])
            evaluated_candidates: list[dict[str, Any]] = []
            violation_count = 0

            if candidate_dicts:
                for c_dict in candidate_dicts:
                    candidate = CandidateZone.model_validate(c_dict)
                    geo_result: GeospatialSafetyResult = self.engine.evaluate_coordinate(
                        target=candidate.location,
                        origin=mission.origin,
                        max_distance_km=mission.max_distance_km,
                    )

                    # Update candidate with geospatial results
                    candidate.distance_km = geo_result.distance_from_origin_km or 0.0
                    candidate.bearing_degrees = geo_result.bearing_degrees
                    candidate.safety_status = geo_result.safety_status
                    candidate.geospatial_notes = geo_result.notes

                    # Adjust candidate safety score based on geospatial findings
                    if geo_result.safety_status == SafetyEvaluation.UNSAFE:
                        candidate.safety_score = 0.0
                        violation_count += 1
                    elif geo_result.safety_status == SafetyEvaluation.RESTRICTED:
                        candidate.safety_score = min(candidate.safety_score, 25.0)
                        violation_count += 1
                    elif geo_result.safety_status == SafetyEvaluation.CAUTION:
                        candidate.safety_score = min(candidate.safety_score, 65.0)

                    # Surface any warnings
                    for v in geo_result.zone_violations:
                        warnings.append(AgentWarning(code="RESTRICTED_ZONE_VIOLATION", message=v, severity="critical"))
                    for bw in geo_result.buffer_warnings:
                        warnings.append(AgentWarning(code="ZONE_BUFFER_PROXIMITY", message=bw, severity="moderate"))
                    for tw in geo_result.traffic_warnings:
                        warnings.append(AgentWarning(code="SHIPPING_LANE_INTERFERENCE", message=tw, severity="moderate"))

                    evaluated_candidates.append(candidate.model_dump())

            else:
                # If no candidate zones passed, evaluate the mission origin coordinate directly
                origin_eval = self.engine.evaluate_coordinate(target=mission.origin)
                evaluated_candidates.append(
                    {
                        "zone_id": "ORIGIN",
                        "location": mission.origin.model_dump(),
                        "safety_status": origin_eval.safety_status.value,
                        "notes": origin_eval.notes,
                        "is_safe": origin_eval.is_safe,
                    }
                )

            return AgentResponse(
                agent="maritime",
                status=AgentStatus.SUCCESS,
                request_id=request.request_id,
                data={
                    "evaluated_candidates": evaluated_candidates,
                    "violations_detected": violation_count,
                    "total_evaluated": len(evaluated_candidates),
                },
                evidence=evidence_items,
                warnings=warnings,
                confidence=1.0,  # GIS boundaries are deterministic
            )

        except Exception as exc:
            logger.error(f"MaritimeSafetyAgent failed during spatial analysis: {exc}", exc_info=True)
            return AgentResponse(
                agent="maritime",
                status=AgentStatus.FAILED,
                request_id=request.request_id,
                data={},
                evidence=evidence_items,
                warnings=[
                    AgentWarning(
                        code="GEOSPATIAL_ANALYSIS_FAILED",
                        message=f"Spatial boundary verification failed: {str(exc)}",
                        severity="critical",
                    )
                ],
                confidence=0.0,
            )
