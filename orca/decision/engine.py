"""ORCA Risk-Adjusted Decision Engine.

Transforms multi-agent evidence into deterministic, traceable candidate rankings
based on the core principle:
Risk-Adjusted Decision = Opportunity × Safety × Accessibility × Data Confidence.
Safety strictly outranks fishing potential.
"""

from datetime import datetime, timezone
from typing import Any

from orca.logging.logger import get_logger
from orca.models.candidate import CandidateZone, DecisionOutput, SafetyEvaluation
from orca.models.evidence import EvidenceItem
from orca.models.mission import StructuredMission

logger = get_logger(__name__, agent="decision_engine")


class DecisionEngine:
    """Computes risk-adjusted composite scores and ranks candidate zones deterministically."""

    # Weights for different mission objectives
    OBJECTIVE_WEIGHTS = {
        "high_fishing_potential": {"opportunity": 0.70, "accessibility": 0.30},
        "safest": {"opportunity": 0.35, "accessibility": 0.65},
        "balanced": {"opportunity": 0.50, "accessibility": 0.50},
    }

    # Minimum safety score threshold to qualify as a valid top recommendation
    MIN_QUALIFYING_SAFETY_SCORE = 50.0

    @classmethod
    def evaluate(
        cls,
        mission: StructuredMission,
        candidates: list[CandidateZone],
        overall_confidence: float = 1.0,
        data_provenance: list[EvidenceItem] | None = None,
    ) -> DecisionOutput:
        """Evaluate and rank candidates into a structured DecisionOutput.

        Args:
            mission: The originating StructuredMission contract.
            candidates: Aggregated candidate zones from Commander.
            overall_confidence: Reliability factor from EvidenceAgent [0.0 - 1.0].
            data_provenance: List of underlying evidence items.

        Returns:
            DecisionOutput: Risk-adjusted decision package.
        """
        logger.info(
            f"DecisionEngine evaluating {len(candidates)} candidates for mission '{mission.request_id}' "
            f"with confidence {overall_confidence:.2f}"
        )

        provenance = data_provenance or []
        objective_key = mission.objective.lower()
        weights = cls.OBJECTIVE_WEIGHTS.get(objective_key, cls.OBJECTIVE_WEIGHTS["high_fishing_potential"])

        opp_w = weights["opportunity"]
        acc_w = weights["accessibility"]

        # 1. Score each candidate
        scored_candidates: list[CandidateZone] = []
        for cand in candidates:
            # Deterministic composite score calculation
            comp_score = cls._compute_composite_score(
                cand=cand,
                opp_w=opp_w,
                acc_w=acc_w,
                overall_confidence=overall_confidence,
            )
            cand.composite_score = comp_score
            scored_candidates.append(cand)

        # 2. Sort descending by composite score
        scored_candidates.sort(key=lambda c: c.composite_score, reverse=True)

        # 3. Filter qualifying candidates (must have safety status SAFE or CAUTION and safety_score >= MIN)
        qualifying = [
            c for c in scored_candidates
            if c.safety_status in (SafetyEvaluation.SAFE, SafetyEvaluation.CAUTION)
            and c.safety_score >= cls.MIN_QUALIFYING_SAFETY_SCORE
        ]

        selected_zone: CandidateZone | None = qualifying[0] if qualifying else None

        # Alternatives are remaining candidates
        alternatives: list[CandidateZone] = [
            c for c in scored_candidates if selected_zone is None or c.id != selected_zone.id
        ]

        # 4. Generate structured explanations
        from orca.decision.explainer import DecisionExplainer

        rec_text = DecisionExplainer.generate_recommendation(selected_zone, mission)
        trade_off_text = DecisionExplainer.generate_trade_offs(selected_zone, alternatives)
        safety_text = DecisionExplainer.generate_safety_advisory(selected_zone, alternatives)
        what_ifs = DecisionExplainer.generate_what_if_suggestions(selected_zone, mission)

        return DecisionOutput(
            request_id=mission.request_id,
            selected_zone=selected_zone,
            alternative_zones=alternatives,
            overall_confidence=overall_confidence,
            recommendation_text=rec_text,
            trade_off_analysis=trade_off_text,
            safety_advisory=safety_text,
            data_provenance=provenance,
            what_if_suggestions=what_ifs,
            generated_at=datetime.now(timezone.utc),
        )

    @classmethod
    def _compute_composite_score(
        cls,
        cand: CandidateZone,
        opp_w: float,
        acc_w: float,
        overall_confidence: float,
    ) -> float:
        """Calculate deterministic risk-adjusted score.

        Formula:
          Base Opportunity = (opp_w * fishing_score + acc_w * accessibility_score)
          Safety Multiplier =
            - 0.0 if UNSAFE or RESTRICTED
            - safety_score / 100.0 if CAUTION or moderate
            - 1.0 if safety_score >= 85.0
          Confidence Multiplier = (cand.confidence_score * overall_confidence)
          Composite Score = Base Opportunity * Safety Multiplier * Confidence Multiplier
        """
        # Critical safety disqualifications
        if cand.safety_status == SafetyEvaluation.UNSAFE or cand.safety_status == SafetyEvaluation.RESTRICTED:
            return 0.0
        if cand.safety_score < 30.0:
            return 0.0

        # Base opportunity combined with accessibility
        base_opportunity = (opp_w * cand.fishing_score) + (acc_w * cand.accessibility_score)

        # Non-linear safety multiplier (safety dominates opportunity)
        if cand.safety_score >= 85.0:
            safety_mult = 1.0
        elif cand.safety_score >= 60.0:
            # Gradual linear decay between 0.75 and 1.0
            safety_mult = 0.75 + ((cand.safety_score - 60.0) / 25.0) * 0.25
        else:
            # Steep penalty for low safety
            safety_mult = max(0.10, (cand.safety_score / 100.0) ** 1.5)

        # Confidence factor
        effective_conf = max(0.10, min(1.0, cand.confidence_score * overall_confidence))

        composite = base_opportunity * safety_mult * effective_conf
        return round(composite, 2)
