"""ORCA Commander Entrypoint Agent and Multi-Agent Orchestrator.

The Commander coordinates user intent extraction, specialist capability selection,
ACP message dispatching (Ocean, Weather, Maritime Safety, Evidence), and response aggregation.
"""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

from orca.agents.evidence.agent import EvidenceAgent
from orca.agents.maritime.agent import MaritimeSafetyAgent
from orca.agents.ocean.agent import OceanAgent
from orca.agents.weather.agent import WeatherAgent
from orca.logging.logger import get_logger, set_request_id
from orca.models.agent_contract import AgentRequest, AgentResponse, AgentStatus, AgentWarning
from orca.models.candidate import CandidateZone, SafetyEvaluation
from orca.models.evidence import EvidenceAssessment, EvidenceItem
from orca.models.mission import Coordinate, StructuredMission
from orca.orchestration.acp import ACPRouter
from orca.orchestration.intent_extractor import IntentExtractionResult, IntentExtractor

logger = get_logger(__name__, agent="commander")


class CommanderWorkflowResult(BaseModel):
    """Aggregated output from Commander's multi-agent orchestration workflow."""

    request_id: str = Field(description="Unique workflow trace identifier")
    mission: StructuredMission | None = Field(
        default=None,
        description="The structured mission backing this workflow (if intent extraction succeeded)",
    )
    candidate_zones: list[CandidateZone] = Field(
        default_factory=list,
        description="Candidate marine zones enriched with ocean, weather, and geospatial evaluation",
    )
    ocean_response: AgentResponse | None = Field(default=None)
    weather_response: AgentResponse | None = Field(default=None)
    maritime_response: AgentResponse | None = Field(default=None)
    evidence_assessment: EvidenceAssessment | None = Field(
        default=None,
        description="Unified reliability, freshness, conflict, and confidence assessment",
    )
    all_evidence: list[EvidenceItem] = Field(default_factory=list)
    all_warnings: list[AgentWarning] = Field(default_factory=list)
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    workflow_status: str = Field(default="completed")
    clarification_prompt: str | None = Field(
        default=None,
        description="Populated if user input is ambiguous or missing departure location",
    )
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CommanderAgent:
    """Primary ORCA Entry Agent that translates intent, dispatches via ACP, and aggregates responses."""

    def __init__(
        self,
        router: ACPRouter | None = None,
        intent_extractor: IntentExtractor | None = None,
        ocean_agent: OceanAgent | None = None,
        weather_agent: WeatherAgent | None = None,
        maritime_agent: MaritimeSafetyAgent | None = None,
        evidence_agent: EvidenceAgent | None = None,
    ) -> None:
        self.router = router or ACPRouter()
        self.intent_extractor = intent_extractor or IntentExtractor()

        # Instantiate specialists if not provided
        self.ocean_agent = ocean_agent or OceanAgent()
        self.weather_agent = weather_agent or WeatherAgent()
        self.maritime_agent = maritime_agent or MaritimeSafetyAgent()
        self.evidence_agent = evidence_agent or EvidenceAgent()

        # Register specialists on ACPRouter
        self.router.register_agent("ocean", self.ocean_agent.process)
        self.router.register_agent("weather", self.weather_agent.process)
        self.router.register_agent("maritime", self.maritime_agent.process)
        self.router.register_agent("evidence", self.evidence_agent.process)

    async def execute_query(
        self,
        query: str,
        now: datetime | None = None,
        request_id: str | None = None,
    ) -> CommanderWorkflowResult:
        """Entrypoint for natural-language queries (e.g. from ASI:One).

        Args:
            query: Natural language user request.
            now: Reference time (defaults to utcnow).
            request_id: Optional trace ID.

        Returns:
            CommanderWorkflowResult: Complete aggregated multi-agent outcome.
        """
        # 1. Intent Extraction
        intent_result: IntentExtractionResult = self.intent_extractor.extract(
            text=query,
            now=now,
            request_id=request_id,
        )

        if not intent_result.is_success or intent_result.mission is None:
            # Need clarification
            req_id = request_id or "clarification"
            return CommanderWorkflowResult(
                request_id=req_id,
                mission=None,
                workflow_status="clarification_needed",
                clarification_prompt=intent_result.clarification_prompt,
            )

        # 2. Run orchestration on extracted mission
        return await self.execute_mission(intent_result.mission)

    async def execute_mission(self, mission: StructuredMission) -> CommanderWorkflowResult:
        """Run the full multi-agent orchestration workflow for a StructuredMission.

        Workflow:
          1. ACP -> Ocean Agent: discovers fishing opportunity zones.
          2. ACP -> Weather Agent: checks environmental marine risk for zones & origin.
          3. ACP -> Maritime Safety Agent: evaluates deterministic boundaries & buffers.
          4. Response Aggregation: merges specialist findings into candidate models.
          5. ACP -> Evidence Agent: assesses reliability, freshness, conflict, and confidence.
        """
        trace_id = mission.request_id
        set_request_id(trace_id)

        logger.info(f"Commander orchestrating mission '{trace_id}' from ({mission.origin.lat}, {mission.origin.lon})")

        all_evidence: list[EvidenceItem] = []
        all_warnings: list[AgentWarning] = []

        # -------------------------------------------------------------------
        # Step 1: Ocean Agent (Opportunity)
        # -------------------------------------------------------------------
        ocean_req = AgentRequest(
            request_id=trace_id,
            target_agent="ocean",
            mission=mission,
        )
        ocean_resp = await self.router.send_request("commander", "ocean", ocean_req)
        all_evidence.extend(ocean_resp.evidence)
        all_warnings.extend(ocean_resp.warnings)

        raw_candidates: list[dict[str, Any]] = ocean_resp.data.get("candidate_zones", [])

        # -------------------------------------------------------------------
        # Step 2: Maritime Safety Agent (Spatial Boundaries & Clearances)
        # -------------------------------------------------------------------
        maritime_req = AgentRequest(
            request_id=trace_id,
            target_agent="maritime",
            mission=mission,
            parameters={"candidate_zones": raw_candidates},
        )
        maritime_resp = await self.router.send_request("commander", "maritime", maritime_req)
        all_evidence.extend(maritime_resp.evidence)
        all_warnings.extend(maritime_resp.warnings)

        evaluated_maritime_candidates = maritime_resp.data.get("evaluated_candidate_zones", [])

        # -------------------------------------------------------------------
        # Step 3: Weather & Marine Forecast Agent (Environmental Risks)
        # -------------------------------------------------------------------
        weather_req = AgentRequest(
            request_id=trace_id,
            target_agent="weather",
            mission=mission,
            parameters={"candidate_zones": raw_candidates},
        )
        weather_resp = await self.router.send_request("commander", "weather", weather_req)
        all_evidence.extend(weather_resp.evidence)
        all_warnings.extend(weather_resp.warnings)

        evaluated_weather_candidates = weather_resp.data.get("evaluated_candidate_zones", [])

        # -------------------------------------------------------------------
        # Step 4: Multi-Agent Candidate Aggregation
        # -------------------------------------------------------------------
        aggregated_candidates: list[CandidateZone] = self._aggregate_candidate_zones(
            raw_candidates=raw_candidates,
            maritime_candidates=evaluated_maritime_candidates,
            weather_candidates=evaluated_weather_candidates,
        )

        # -------------------------------------------------------------------
        # Step 5: Evidence & Reliability Agent (Reconciliation & Confidence)
        # -------------------------------------------------------------------
        evidence_req = AgentRequest(
            request_id=trace_id,
            target_agent="evidence",
            mission=mission,
            parameters={
                "evidence_items": [e.model_dump() for e in all_evidence],
                "specialist_responses": [
                    ocean_resp.model_dump(),
                    weather_resp.model_dump(),
                    maritime_resp.model_dump(),
                ],
            },
        )
        evidence_resp = await self.router.send_request("commander", "evidence", evidence_req)
        all_warnings.extend(evidence_resp.warnings)

        assessment_dict = evidence_resp.data.get("assessment")
        evidence_assessment: EvidenceAssessment | None = None
        overall_confidence = 1.0

        if assessment_dict:
            try:
                evidence_assessment = EvidenceAssessment.model_validate(assessment_dict)
                overall_confidence = evidence_assessment.overall_confidence
            except Exception as e:
                logger.warning(f"Could not parse EvidenceAssessment from EvidenceAgent: {e}")

        # Update candidate confidence scores with overall evidence confidence
        for cand in aggregated_candidates:
            cand.confidence_score = round(cand.confidence_score * overall_confidence, 2)

        logger.info(
            f"Commander orchestration completed for '{trace_id}': {len(aggregated_candidates)} candidate zones, "
            f"confidence={overall_confidence:.2f}"
        )

        return CommanderWorkflowResult(
            request_id=trace_id,
            mission=mission,
            candidate_zones=aggregated_candidates,
            ocean_response=ocean_resp,
            weather_response=weather_resp,
            maritime_response=maritime_resp,
            evidence_assessment=evidence_assessment,
            all_evidence=all_evidence,
            all_warnings=all_warnings,
            overall_confidence=overall_confidence,
            workflow_status="completed",
        )

    def _aggregate_candidate_zones(
        self,
        raw_candidates: list[dict[str, Any]],
        maritime_candidates: list[dict[str, Any]],
        weather_candidates: list[dict[str, Any]],
    ) -> list[CandidateZone]:
        """Merge specialist findings into cohesive CandidateZone models."""
        # Index maritime data by candidate id
        maritime_by_id = {c.get("id"): c for c in maritime_candidates if "id" in c}
        weather_by_id = {c.get("id"): c for c in weather_candidates if "id" in c}

        aggregated: list[CandidateZone] = []

        for cand_dict in raw_candidates:
            cid = cand_dict.get("id", "UNKNOWN-ZONE")
            m_data = maritime_by_id.get(cid, {})
            w_data = weather_by_id.get(cid, {})

            # Location and distance
            loc_dict = cand_dict.get("location", {})
            loc = Coordinate(lat=loc_dict.get("lat", 0.0), lon=loc_dict.get("lon", 0.0))
            dist_km = float(cand_dict.get("distance_km", 0.0))

            fishing_score = float(cand_dict.get("fishing_score", 0.0))
            ocean_data = cand_dict.get("ocean_data", {})

            # Safety scores from maritime & weather
            maritime_safety_score = float(m_data.get("safety_score", 100.0))
            weather_safety_score = float(w_data.get("safety_score", 100.0))

            # Safety score is minimum of weather and maritime safety
            safety_score = min(maritime_safety_score, weather_safety_score)

            # Safety status hierarchy: UNSAFE > RESTRICTED > CAUTION > SAFE
            m_status = m_data.get("safety_status", SafetyEvaluation.SAFE)
            w_status = w_data.get("safety_status", SafetyEvaluation.SAFE)

            if m_status == SafetyEvaluation.UNSAFE or w_status == SafetyEvaluation.UNSAFE:
                combined_status = SafetyEvaluation.UNSAFE
            elif m_status == SafetyEvaluation.RESTRICTED:
                combined_status = SafetyEvaluation.RESTRICTED
            elif m_status == SafetyEvaluation.CAUTION or w_status == SafetyEvaluation.CAUTION:
                combined_status = SafetyEvaluation.CAUTION
            else:
                combined_status = SafetyEvaluation.SAFE

            # Accessibility score (inversely proportional to distance)
            accessibility_score = max(20.0, 100.0 - (dist_km * 1.5))

            notes = m_data.get("geospatial_notes", [])
            weather_obs = w_data.get("weather_data", {})

            aggregated.append(
                CandidateZone(
                    id=cid,
                    location=loc,
                    distance_km=dist_km,
                    bearing_degrees=cand_dict.get("bearing_degrees"),
                    fishing_score=fishing_score,
                    safety_score=safety_score,
                    accessibility_score=accessibility_score,
                    confidence_score=float(cand_dict.get("confidence_score", 1.0)),
                    safety_status=combined_status,
                    ocean_data=ocean_data,
                    weather_data=weather_obs,
                    geospatial_notes=notes,
                )
            )

        return aggregated
