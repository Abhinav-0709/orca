"""ORCA Evidence & Reliability specialist agent.

The Evidence Agent does not make a marine recommendation.  It checks whether
the evidence supplied by the other specialists is complete, current,
geographically usable, and internally consistent, then calculates a
deterministic confidence score for downstream orchestration.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import fmean
from typing import Any, Callable, Iterable

from pydantic import ValidationError

from orca.config.settings import settings
from orca.data_sources.freshness import evaluate_freshness
from orca.logging.logger import get_logger
from orca.models.agent_contract import AgentError, AgentRequest, AgentResponse, AgentStatus, AgentWarning
from orca.models.evidence import (
    DataFreshness,
    EvidenceAssessment,
    EvidenceConflict,
    EvidenceItem,
)
from orca.storage.evidence_store import EvidenceStore

logger = get_logger(__name__, agent="evidence_agent")


DEFAULT_SOURCE_QUALITY: dict[str, float] = {
    "INCOIS": 0.95,
    "INCOIS_OSF": 0.92,
    "INCOIS_OPERATIONAL_FALLBACK": 0.88,
    "OPEN_METEO_MARINE": 0.95,
    "IMD_BULLETIN": 0.95,
    "IMD_OPERATIONAL_FALLBACK": 0.92,
    "IMD_CYCLONE_WATCH": 0.95,
    "MARITIME_BOUNDARIES_GIS": 1.00,
}


class EvidenceAgent:
    """Assess the reliability of specialist evidence using deterministic rules."""

    def __init__(
        self,
        required_sources: Iterable[str] | None = None,
        source_quality: dict[str, float] | None = None,
        now_provider: Callable[[], datetime] | None = None,
        store: EvidenceStore | None = None,
        store_path: str | None = None,
    ) -> None:
        self.required_sources = tuple(required_sources or ())
        self.source_quality = {**DEFAULT_SOURCE_QUALITY, **(source_quality or {})}
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        configured_store_path = store_path if store_path is not None else settings.evidence_store_path
        self.store = store or (EvidenceStore(configured_store_path) if configured_store_path else None)

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Review evidence or specialist responses carried in ``request.parameters``.

        Supported input forms are:

        - ``evidence``: a list of ``EvidenceItem`` objects or dictionaries;
        - ``agent_responses``: serialized or typed ``AgentResponse`` objects;
        - ``required_sources``: optional source names that must be present;
        - ``observations``: optional comparable observations for conflict checks.
        """
        now = self._normalise_datetime(self._now_provider())
        parameters = request.parameters or {}
        required_sources = tuple(parameters.get("required_sources", self.required_sources))

        evidence, invalid_payloads = self._collect_evidence(parameters)
        failed_agents = self._collect_failed_agents(parameters)
        observations = self._collect_observations(parameters, evidence)

        assessment, reviewed_evidence, warnings = self._assess(
            evidence=evidence,
            invalid_payloads=invalid_payloads,
            failed_agents=failed_agents,
            required_sources=required_sources,
            observations=observations,
            now=now,
        )

        has_reliability_issues = any(
            (
                assessment.missing_sources,
                assessment.missing_fields,
                assessment.stale_sources,
                assessment.invalid_sources,
                assessment.failed_agents,
                assessment.conflicts,
            )
        )

        if not reviewed_evidence:
            status = AgentStatus.UNAVAILABLE
            error = AgentError(
                type="NO_EVIDENCE",
                message="No valid evidence was available for reliability assessment.",
                retryable=bool(failed_agents or invalid_payloads),
                details={"failed_agents": failed_agents, "invalid_payloads": invalid_payloads},
            )
        elif has_reliability_issues:
            status = AgentStatus.PARTIAL
            error = None
        else:
            status = AgentStatus.SUCCESS
            error = None

        persistence: dict[str, Any] = {
            "enabled": self.store is not None,
            "evidence_saved": 0,
            "assessment_saved": False,
        }
        if self.store is not None:
            try:
                persistence["evidence_saved"] = self.store.save_evidence(request.request_id, reviewed_evidence)
                self.store.save_assessment(request.request_id, assessment)
                persistence["assessment_saved"] = True
            except Exception as exc:
                logger.error(
                    f"Evidence persistence failed for request {request.request_id}: {exc}",
                    exc_info=True,
                )
                persistence["error"] = str(exc)
                warnings.append(
                    AgentWarning(
                        code="EVIDENCE_PERSISTENCE_FAILED",
                        message="Reliability results were produced but could not be persisted.",
                        severity="moderate",
                    )
                )
                if status == AgentStatus.SUCCESS:
                    status = AgentStatus.PARTIAL

        return AgentResponse(
            agent="evidence",
            status=status,
            request_id=request.request_id,
            data={
                "assessment": assessment.model_dump(mode="json"),
                "normalized_evidence": [item.model_dump(mode="json") for item in reviewed_evidence],
                "persistence": persistence,
            },
            evidence=reviewed_evidence,
            warnings=warnings,
            confidence=assessment.overall_confidence,
            error=error,
        )

    def _collect_evidence(self, parameters: dict[str, Any]) -> tuple[list[EvidenceItem], list[str]]:
        """Validate evidence items from direct input and specialist responses."""
        raw_items: list[Any] = list(parameters.get("evidence", []))
        for raw_response in parameters.get("agent_responses", []):
            if isinstance(raw_response, AgentResponse):
                raw_items.extend(raw_response.evidence)
            elif isinstance(raw_response, dict):
                raw_items.extend(raw_response.get("evidence", []))

        evidence: list[EvidenceItem] = []
        invalid_payloads: list[str] = []
        for index, raw_item in enumerate(raw_items):
            try:
                evidence.append(EvidenceItem.model_validate(raw_item))
            except (ValidationError, TypeError, ValueError) as exc:
                invalid_payloads.append(f"evidence[{index}]: {exc}")

        return evidence, invalid_payloads

    def _collect_failed_agents(self, parameters: dict[str, Any]) -> list[str]:
        """Extract failed or degraded specialist names without trusting prose."""
        failed_agents: list[str] = []
        for raw_response in parameters.get("agent_responses", []):
            if isinstance(raw_response, AgentResponse):
                agent_name = raw_response.agent
                status = raw_response.status.value
            elif isinstance(raw_response, dict):
                agent_name = str(raw_response.get("agent", raw_response.get("target_agent", "unknown")))
                raw_status = raw_response.get("status", "unknown")
                status = raw_status.value if isinstance(raw_status, AgentStatus) else str(raw_status).lower()
            else:
                continue

            if status != AgentStatus.SUCCESS.value:
                failed_agents.append(agent_name)

        return sorted(set(failed_agents))

    def _collect_observations(
        self,
        parameters: dict[str, Any],
        evidence: list[EvidenceItem],
    ) -> list[dict[str, Any]]:
        """Collect explicit or source-attached observations for conflict checks."""
        observations: list[dict[str, Any]] = []
        for raw in parameters.get("observations", []):
            if isinstance(raw, dict) and raw.get("name") and "value" in raw:
                observations.append(dict(raw))

        for item in evidence:
            attached = item.details.get("observations")
            if isinstance(attached, dict):
                for name, value in attached.items():
                    observations.append({"name": name, "value": value, "source": item.source})
            elif isinstance(attached, list):
                for raw in attached:
                    if isinstance(raw, dict) and raw.get("name") and "value" in raw:
                        observation = dict(raw)
                        observation.setdefault("source", item.source)
                        observations.append(observation)

        return observations

    def _assess(
        self,
        evidence: list[EvidenceItem],
        invalid_payloads: list[str],
        failed_agents: list[str],
        required_sources: tuple[str, ...],
        observations: list[dict[str, Any]],
        now: datetime,
    ) -> tuple[EvidenceAssessment, list[EvidenceItem], list[AgentWarning]]:
        """Build a reliability assessment and warnings from normalized evidence."""
        reviewed_evidence: list[EvidenceItem] = []
        source_scores: list[float] = []
        freshness_scores: list[float] = []
        missing_fields: list[str] = []
        stale_sources: list[str] = []
        invalid_sources: list[str] = []
        issues: list[str] = []
        warnings: list[AgentWarning] = []

        for item in evidence:
            source = item.source.strip()
            if not source:
                invalid_sources.append("<empty>")
                issues.append("Evidence item has no source identifier.")
                continue

            if item.retrieved_at > now + timedelta(minutes=5):
                invalid_sources.append(source)
                issues.append(f"Evidence from {source} has a future retrieval timestamp.")
                continue

            observed_at = item.observed_at or item.issued_at or item.retrieved_at
            freshness, freshness_multiplier = evaluate_freshness(observed_at, item.valid_to, now)
            freshness_scores.append(freshness_multiplier)
            source_scores.append(self._source_quality(source, item.confidence, freshness_multiplier))

            if not item.geographic_coverage:
                missing_fields.append(f"{source}.geographic_coverage")

            if freshness in (DataFreshness.STALE, DataFreshness.EXPIRED, DataFreshness.UNKNOWN):
                stale_sources.append(source)
                issues.append(f"Evidence from {source} is {freshness.value}.")

            reviewed_evidence.append(item.model_copy(update={"freshness": freshness}))

        missing_sources = [
            required
            for required in required_sources
            if not any(self._source_matches(required, item.source) for item in reviewed_evidence)
        ]

        valid_count = len(reviewed_evidence)
        source_quality_score = round(fmean(source_scores), 3) if source_scores else 0.0
        freshness_score = round(fmean(freshness_scores), 3) if freshness_scores else 0.0

        source_completeness = (
            len(required_sources) - len(missing_sources)
        ) / len(required_sources) if required_sources else (1.0 if valid_count else 0.0)
        field_completeness = max(
            0.0,
            1.0 - (len(missing_fields) / max(valid_count, 1)),
        )
        completeness_score = round(source_completeness * field_completeness, 3)
        coverage_score = round(
            sum(bool(item.geographic_coverage) for item in reviewed_evidence) / max(valid_count, 1),
            3,
        )

        conflicts = self._detect_conflicts(observations)
        agreement_score = round(max(0.0, 1.0 - (0.25 * len(conflicts))), 3)

        # Weighted arithmetic scoring keeps the contribution of each reliability
        # dimension visible to the Commander and is deterministic for testing.
        overall_confidence = round(
            (
                (source_quality_score * 0.25)
                + (freshness_score * 0.25)
                + (completeness_score * 0.20)
                + (agreement_score * 0.15)
                + (coverage_score * 0.15)
            ),
            3,
        )

        if failed_agents:
            issues.append(f"Specialist agents reported degraded execution: {', '.join(failed_agents)}.")
            overall_confidence = min(overall_confidence, 0.5)

        if invalid_payloads:
            invalid_sources.extend(f"invalid_payload_{index + 1}" for index, _ in enumerate(invalid_payloads))
            issues.append(f"{len(invalid_payloads)} evidence payload(s) could not be validated.")

        for missing in missing_sources:
            issues.append(f"Required evidence source is missing: {missing}.")
        for missing_field in missing_fields:
            issues.append(f"Evidence field is missing: {missing_field}.")
        for conflict in conflicts:
            issues.append(conflict.message)

        self._add_warnings(warnings, invalid_payloads, invalid_sources, stale_sources, missing_sources, conflicts, failed_agents)

        assessment = EvidenceAssessment(
            evidence_count=len(evidence) + len(invalid_payloads),
            valid_evidence_count=valid_count,
            complete=(
                valid_count > 0
                and not invalid_payloads
                and not invalid_sources
                and not missing_sources
                and not missing_fields
                and not stale_sources
                and not failed_agents
                and not conflicts
            ),
            source_quality_score=source_quality_score,
            freshness_score=freshness_score,
            completeness_score=round(completeness_score, 3),
            agreement_score=agreement_score,
            coverage_score=coverage_score,
            overall_confidence=max(0.0, min(1.0, overall_confidence)),
            missing_sources=sorted(set(missing_sources)),
            missing_fields=sorted(set(missing_fields)),
            stale_sources=sorted(set(stale_sources)),
            invalid_sources=sorted(set(invalid_sources)),
            failed_agents=failed_agents,
            conflicts=conflicts,
            issues=issues,
        )
        return assessment, reviewed_evidence, warnings

    def _detect_conflicts(self, observations: list[dict[str, Any]]) -> list[EvidenceConflict]:
        """Detect disagreements in explicitly comparable observations."""
        grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        for observation in observations:
            name = str(observation.get("name", "")).strip()
            if name:
                grouped[name].append(observation)

        conflicts: list[EvidenceConflict] = []
        for name, entries in grouped.items():
            if len(entries) < 2:
                continue

            values = [entry.get("value") for entry in entries]
            sources = [str(entry.get("source", "unknown")) for entry in entries]
            tolerances = [float(entry.get("tolerance", 0.0)) for entry in entries]
            tolerance = max(tolerances, default=0.0)

            numeric_values = [
                value
                for value in values
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            ]
            numeric_conflict = (
                len(numeric_values) == len(values)
                and max(numeric_values) - min(numeric_values) > tolerance
            )
            categorical_conflict = (
                len(numeric_values) != len(values)
                and len({repr(value) for value in values}) > 1
            )

            if numeric_conflict or categorical_conflict:
                conflicts.append(
                    EvidenceConflict(
                        observation=name,
                        sources=sources,
                        values=values,
                        tolerance=tolerance,
                        message=(
                            f"Conflicting observations for '{name}' from "
                            f"{', '.join(sources)}."
                        ),
                    )
                )

        return conflicts

    def _source_quality(self, source: str, evidence_confidence: float, freshness_multiplier: float) -> float:
        """Resolve source quality while avoiding double-counting freshness."""
        configured = next(
            (quality for name, quality in self.source_quality.items() if source == name),
            None,
        )
        if configured is None:
            configured = min(evidence_confidence, 0.75)

        # Existing clients include freshness in EvidenceItem.confidence.  Use
        # the configured base quality here, while freshness is scored separately.
        if freshness_multiplier > 0.0 and evidence_confidence < configured:
            configured = max(evidence_confidence / freshness_multiplier, 0.0)
        return round(max(0.0, min(1.0, configured)), 3)

    @staticmethod
    def _source_matches(required: str, actual: str) -> bool:
        """Allow a family requirement such as ``INCOIS`` to match its fallback."""
        return actual == required or actual.startswith(f"{required}_")

    @staticmethod
    def _normalise_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _add_warnings(
        warnings: list[AgentWarning],
        invalid_payloads: list[str],
        invalid_sources: list[str],
        stale_sources: list[str],
        missing_sources: list[str],
        conflicts: list[EvidenceConflict],
        failed_agents: list[str],
    ) -> None:
        if invalid_payloads or invalid_sources:
            warnings.append(
                AgentWarning(
                    code="EVIDENCE_INVALID",
                    message="One or more evidence records failed source or timestamp validation.",
                    severity="critical" if not stale_sources and not missing_sources else "moderate",
                )
            )
        if stale_sources:
            warnings.append(
                AgentWarning(
                    code="EVIDENCE_STALE",
                    message=f"Stale or expired evidence detected from: {', '.join(sorted(set(stale_sources)))}.",
                    severity="moderate",
                )
            )
        if missing_sources:
            warnings.append(
                AgentWarning(
                    code="EVIDENCE_MISSING",
                    message=f"Required evidence sources are missing: {', '.join(missing_sources)}.",
                    severity="critical",
                )
            )
        if conflicts:
            warnings.append(
                AgentWarning(
                    code="EVIDENCE_CONFLICT",
                    message=f"{len(conflicts)} conflicting observation group(s) require reconciliation.",
                    severity="moderate",
                )
            )
        if failed_agents:
            warnings.append(
                AgentWarning(
                    code="SPECIALIST_DEGRADED",
                    message=f"Specialist response degraded: {', '.join(failed_agents)}.",
                    severity="critical",
                )
            )
