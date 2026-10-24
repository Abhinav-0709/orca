"""What-If Simulation Engine for ORCA.

Enables dynamic constraint modification, true deterministic recomputation,
and side-by-side trade-off comparison between baseline and modified decisions.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from pydantic import BaseModel, Field

from orca.decision.engine import DecisionEngine
from orca.logging.logger import get_logger
from orca.models.candidate import CandidateZone, DecisionOutput
from orca.models.mission import Coordinate, StructuredMission, TimeWindow

logger = get_logger(__name__, agent="what_if_engine")


class WhatIfModification(BaseModel):
    """Specific constraint change made to a baseline mission."""

    field_modified: str = Field(description="Name of the parameter modified (e.g. max_distance_km, objective)")
    old_value: Any = Field(description="Value in baseline mission")
    new_value: Any = Field(description="Value in modified mission")
    explanation: str = Field(description="Human-readable description of this parameter shift")


class WhatIfComparison(BaseModel):
    """Side-by-side comparative analysis between baseline and recomputed decisions."""

    request_id: str = Field(description="Trace ID of the what-if simulation")
    modifications: list[WhatIfModification] = Field(description="All modifications applied")
    baseline_mission: StructuredMission = Field(description="Original mission parameters")
    modified_mission: StructuredMission = Field(description="Updated mission parameters")
    baseline_decision: DecisionOutput = Field(description="Original decision output")
    new_decision: DecisionOutput = Field(description="Recomputed decision output")
    selected_zone_changed: bool = Field(description="True if the recommended winner changed")
    composite_score_delta: float = Field(description="New composite score - Baseline composite score")
    safety_score_delta: float = Field(description="New safety score - Baseline safety score")
    fishing_score_delta: float = Field(description="New fishing score - Baseline fishing score")
    distance_delta_km: float = Field(description="New distance - Baseline distance")
    summary_markdown: str = Field(description="Markdown report comparing the two outcomes")
    interactive_actions: list[dict[str, str]] = Field(
        default_factory=list,
        description="Suggested follow-up action buttons/cards for the user interface",
    )


class WhatIfEngine:
    """Core engine for parsing what-if intent, recomputing decisions, and evaluating trade-offs."""

    @classmethod
    def parse_modification(
        cls,
        baseline_mission: StructuredMission,
        query: str,
        now: datetime | None = None,
    ) -> tuple[StructuredMission, list[WhatIfModification]]:
        """Parse natural language what-if query into modified StructuredMission and modification records.

        Args:
            baseline_mission: The original active mission.
            query: The user's what-if exploration query (e.g. 'What if I go 15 km farther?').
            now: Current reference time.

        Returns:
            tuple[StructuredMission, list[WhatIfModification]]: Modified mission and recorded changes.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        normalized = query.lower().strip()
        modifications: list[WhatIfModification] = []

        # Clone baseline attributes
        new_dist = baseline_mission.max_distance_km
        new_objective = baseline_mission.objective
        new_time_window = TimeWindow(
            start=baseline_mission.time_window.start,
            end=baseline_mission.time_window.end,
        )
        new_constraints = list(baseline_mission.constraints)

        # -------------------------------------------------------------------
        # 1. Distance Modifications
        # -------------------------------------------------------------------
        # Relative: "15 km farther", "10 km more", "5 km closer", "less by 10 km"
        rel_farther = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kms)?\s*(?:farther|further|more|extra|deeper|beyond)", normalized)
        rel_closer = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kms)?\s*(?:closer|less|nearer|shorter)", normalized)

        # Absolute: "within 45 km", "to 50 km", "40 km radius", "max 60 km"
        abs_dist = re.search(r"(?:within|to|radius|up to|max|reach|limit|distance of)\s*(\d+(?:\.\d+)?)\s*(?:km|kms)", normalized)
        simple_dist = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:km|kms)\b", normalized)

        if rel_farther:
            delta = float(rel_farther.group(1))
            updated_dist = min(200.0, baseline_mission.max_distance_km + delta)
            modifications.append(
                WhatIfModification(
                    field_modified="max_distance_km",
                    old_value=baseline_mission.max_distance_km,
                    new_value=updated_dist,
                    explanation=f"Extended operating radius by +{delta:.1f} km (from {baseline_mission.max_distance_km:.1f} km to {updated_dist:.1f} km)",
                )
            )
            new_dist = updated_dist
        elif rel_closer:
            delta = float(rel_closer.group(1))
            updated_dist = max(5.0, baseline_mission.max_distance_km - delta)
            modifications.append(
                WhatIfModification(
                    field_modified="max_distance_km",
                    old_value=baseline_mission.max_distance_km,
                    new_value=updated_dist,
                    explanation=f"Reduced operating radius by -{delta:.1f} km (from {baseline_mission.max_distance_km:.1f} km to {updated_dist:.1f} km)",
                )
            )
            new_dist = updated_dist
        elif abs_dist:
            val = float(abs_dist.group(1))
            if 5.0 <= val <= 250.0 and val != baseline_mission.max_distance_km:
                modifications.append(
                    WhatIfModification(
                        field_modified="max_distance_km",
                        old_value=baseline_mission.max_distance_km,
                        new_value=val,
                        explanation=f"Adjusted search radius to {val:.1f} km (previously {baseline_mission.max_distance_km:.1f} km)",
                    )
                )
                new_dist = val
        elif "farther" in normalized or "further" in normalized:
            # Default step increase
            updated_dist = min(200.0, baseline_mission.max_distance_km + 15.0)
            modifications.append(
                WhatIfModification(
                    field_modified="max_distance_km",
                    old_value=baseline_mission.max_distance_km,
                    new_value=updated_dist,
                    explanation=f"Extended search radius offshore to {updated_dist:.1f} km (+15.0 km)",
                )
            )
            new_dist = updated_dist
        elif simple_dist and not any(k in normalized for k in ["am", "pm", "hour"]):
            val = float(simple_dist.group(1))
            if 5.0 <= val <= 250.0 and val != baseline_mission.max_distance_km:
                modifications.append(
                    WhatIfModification(
                        field_modified="max_distance_km",
                        old_value=baseline_mission.max_distance_km,
                        new_value=val,
                        explanation=f"Changed operational distance limit to {val:.1f} km",
                    )
                )
                new_dist = val

        # -------------------------------------------------------------------
        # 2. Objective Modifications
        # -------------------------------------------------------------------
        if any(k in normalized for k in ["prioritize safety", "maximum safety", "safest", "minimize risk", "safety over"]):
            if baseline_mission.objective != "safest":
                modifications.append(
                    WhatIfModification(
                        field_modified="objective",
                        old_value=baseline_mission.objective,
                        new_value="safest",
                        explanation="Switched mission objective to 'safest' (heavily weighting sheltered calm waters & low wave risk)",
                    )
                )
                new_objective = "safest"
        elif any(k in normalized for k in ["prioritize fishing", "maximize catch", "highest potential", "catch volume", "productivity over"]):
            if baseline_mission.objective != "high_fishing_potential":
                modifications.append(
                    WhatIfModification(
                        field_modified="objective",
                        old_value=baseline_mission.objective,
                        new_value="high_fishing_potential",
                        explanation="Switched mission objective to 'high_fishing_potential' (maximizing chlorophyll & INCOIS PFZ yield)",
                    )
                )
                new_objective = "high_fishing_potential"
        elif "balanced" in normalized and baseline_mission.objective != "balanced":
            modifications.append(
                WhatIfModification(
                    field_modified="objective",
                    old_value=baseline_mission.objective,
                    new_value="balanced",
                    explanation="Switched mission objective to 'balanced' (equal weight to distance, catch potential, and sea state)",
                )
            )
            new_objective = "balanced"

        # -------------------------------------------------------------------
        # 3. Departure Time Modifications
        # -------------------------------------------------------------------
        time_match = re.search(r"\b(?:at|leave at|depart at)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", normalized)
        if time_match:
            h = int(time_match.group(1))
            ampm = time_match.group(3)
            if ampm == "pm" and h < 12:
                h += 12
            elif ampm == "am" and h == 12:
                h = 0
            
            cur_start = baseline_mission.time_window.start
            new_start = cur_start.replace(hour=h, minute=0, second=0, microsecond=0)
            dur = baseline_mission.time_window.duration_hours
            new_end = new_start + timedelta(hours=dur)
            new_time_window = TimeWindow(start=new_start, end=new_end)
            modifications.append(
                WhatIfModification(
                    field_modified="time_window",
                    old_value=f"{cur_start.strftime('%H:%M')} UTC",
                    new_value=f"{new_start.strftime('%H:%M')} UTC",
                    explanation=f"Shifted departure time to {new_start.strftime('%H:%M')} UTC ({dur:.0f}-hour window)",
                )
            )
        elif "tomorrow morning" in normalized:
            tomorrow = now + timedelta(days=1)
            new_start = tomorrow.replace(hour=5, minute=0, second=0, microsecond=0)
            new_end = new_start + timedelta(hours=6)
            new_time_window = TimeWindow(start=new_start, end=new_end)
            modifications.append(
                WhatIfModification(
                    field_modified="time_window",
                    old_value=baseline_mission.time_window.start.strftime("%Y-%m-%d %H:%M"),
                    new_value=new_start.strftime("%Y-%m-%d %H:%M"),
                    explanation="Shifted mission departure to tomorrow morning at 05:00 UTC",
                )
            )

        # -------------------------------------------------------------------
        # 4. Constraints / Sea Risk Tolerance
        # -------------------------------------------------------------------
        if any(k in normalized for k in ["lower wave", "calmer sea", "strict wave", "lower risk"]):
            if "strict_low_wave_height" not in new_constraints:
                new_constraints.append("strict_low_wave_height")
                modifications.append(
                    WhatIfModification(
                        field_modified="constraints",
                        old_value=baseline_mission.constraints,
                        new_value=new_constraints,
                        explanation="Enforced strict low wave height constraint (capping wave exposure under 1.2m)",
                    )
                )
        elif any(k in normalized for k in ["accept moderate", "accept wave", "accept rougher"]):
            if "strict_low_wave_height" in new_constraints:
                new_constraints.remove("strict_low_wave_height")
            if "accept_moderate_wave_risk" not in new_constraints:
                new_constraints.append("accept_moderate_wave_risk")
                modifications.append(
                    WhatIfModification(
                        field_modified="constraints",
                        old_value=baseline_mission.constraints,
                        new_value=new_constraints,
                        explanation="Relaxed wave tolerance to accept moderate sea states up to 1.8m",
                    )
                )

        # Fallback if no specific parameter matched: default to +15km exploration
        if not modifications:
            updated_dist = baseline_mission.max_distance_km + 15.0
            modifications.append(
                WhatIfModification(
                    field_modified="max_distance_km",
                    old_value=baseline_mission.max_distance_km,
                    new_value=updated_dist,
                    explanation=f"Simulated extending search radius by +15.0 km (from {baseline_mission.max_distance_km:.1f} km to {updated_dist:.1f} km)",
                )
            )
            new_dist = updated_dist

        modified_mission = StructuredMission(
            request_id=f"whatif-{uuid.uuid4().hex[:8]}",
            activity=baseline_mission.activity,
            origin=baseline_mission.origin,
            time_window=new_time_window,
            max_distance_km=new_dist,
            objective=new_objective,
            constraints=new_constraints,
        )

        return modified_mission, modifications

    @classmethod
    def compare(
        cls,
        baseline_mission: StructuredMission,
        modified_mission: StructuredMission,
        baseline_decision: DecisionOutput,
        new_decision: DecisionOutput,
        modifications: list[WhatIfModification],
    ) -> WhatIfComparison:
        """Deterministically compare baseline decision and recomputed decision."""
        base_zone = baseline_decision.selected_zone
        new_zone = new_decision.selected_zone

        base_zone_id = base_zone.id if base_zone else "None"
        new_zone_id = new_zone.id if new_zone else "None"
        zone_changed = (base_zone_id != new_zone_id)

        base_comp = base_zone.composite_score if base_zone else 0.0
        new_comp = new_zone.composite_score if new_zone else 0.0
        comp_delta = round(new_comp - base_comp, 1)

        base_safety = base_zone.safety_score if base_zone else 0.0
        new_safety = new_zone.safety_score if new_zone else 0.0
        safety_delta = round(new_safety - base_safety, 1)

        base_fish = base_zone.fishing_score if base_zone else 0.0
        new_fish = new_zone.fishing_score if new_zone else 0.0
        fish_delta = round(new_fish - base_fish, 1)

        base_dist = base_zone.distance_km if base_zone else 0.0
        new_dist = new_zone.distance_km if new_zone else 0.0
        dist_delta = round(new_dist - base_dist, 1)

        # Generate comparative markdown report
        md = cls._generate_comparison_markdown(
            baseline_mission=baseline_mission,
            modified_mission=modified_mission,
            base_zone=base_zone,
            new_zone=new_zone,
            modifications=modifications,
            comp_delta=comp_delta,
            safety_delta=safety_delta,
            fish_delta=fish_delta,
            dist_delta=dist_delta,
            zone_changed=zone_changed,
        )

        # Generate next interactive action cards / suggestion buttons
        interactive_actions = cls._generate_interactive_actions(modified_mission)

        return WhatIfComparison(
            request_id=new_decision.request_id,
            modifications=modifications,
            baseline_mission=baseline_mission,
            modified_mission=modified_mission,
            baseline_decision=baseline_decision,
            new_decision=new_decision,
            selected_zone_changed=zone_changed,
            composite_score_delta=comp_delta,
            safety_score_delta=safety_delta,
            fishing_score_delta=fish_delta,
            distance_delta_km=dist_delta,
            summary_markdown=md,
            interactive_actions=interactive_actions,
        )

    @classmethod
    def _generate_comparison_markdown(
        cls,
        baseline_mission: StructuredMission,
        modified_mission: StructuredMission,
        base_zone: CandidateZone | None,
        new_zone: CandidateZone | None,
        modifications: list[WhatIfModification],
        comp_delta: float,
        safety_delta: float,
        fish_delta: float,
        dist_delta: float,
        zone_changed: bool,
    ) -> str:
        lines: list[str] = [
            "### 🔄 ORCA What-If Recomputation & Trade-Off Analysis",
            "",
            "#### ⚙️ Simulated Modifications",
        ]
        for mod in modifications:
            lines.append(f"- **{mod.field_modified}:** {mod.explanation}")
        lines.append("")

        lines.append("#### 📊 Comparative Decision Delta")
        lines.append("| Dimension | Baseline | What-If Simulation | Delta |")
        lines.append("| :--- | :--- | :--- | :--- |")

        base_id = base_zone.id if base_zone else "No qualifying zone"
        new_id = new_zone.id if new_zone else "No qualifying zone"
        winner_status = "✨ New Winner" if zone_changed else "Unchanged Winner"
        lines.append(f"| **Recommended Zone** | `{base_id}` | `{new_id}` | {winner_status} |")

        base_score = f"{base_zone.composite_score:.1f}" if base_zone else "0.0"
        new_score = f"{new_zone.composite_score:.1f}" if new_zone else "0.0"
        sign_comp = f"+{comp_delta}" if comp_delta > 0 else f"{comp_delta}"
        lines.append(f"| **Composite Score** | {base_score}/100 | {new_score}/100 | **{sign_comp}** |")

        base_f = f"{base_zone.fishing_score:.1f}" if base_zone else "0.0"
        new_f = f"{new_zone.fishing_score:.1f}" if new_zone else "0.0"
        sign_fish = f"+{fish_delta}" if fish_delta > 0 else f"{fish_delta}"
        lines.append(f"| **Fishing Potential** | {base_f}/100 | {new_f}/100 | {sign_fish} |")

        base_s = f"{base_zone.safety_score:.1f}" if base_zone else "0.0"
        new_s = f"{new_zone.safety_score:.1f}" if new_zone else "0.0"
        sign_safe = f"+{safety_delta}" if safety_delta > 0 else f"{safety_delta}"
        lines.append(f"| **Safety Score** | {base_s}/100 | {new_s}/100 | {sign_safe} |")

        base_d = f"{base_zone.distance_km:.1f} km" if base_zone else "0.0 km"
        new_d = f"{new_zone.distance_km:.1f} km" if new_zone else "0.0 km"
        sign_dist = f"+{dist_delta:.1f} km" if dist_delta > 0 else f"{dist_delta:.1f} km"
        lines.append(f"| **Transit Distance** | {base_d} | {new_d} | {sign_dist} |")
        lines.append("")

        lines.append("#### ⚖️ Trade-Off Verdict")
        if not new_zone:
            lines.append(
                "> ⚠️ **Simulation Result:** The new constraint set leaves no qualifying safe zones. "
                "Conditions either exceed wave limits or violate boundary clearances."
            )
        elif zone_changed:
            if comp_delta > 0:
                lines.append(
                    f"> 🟢 **Favorable Shift:** Modifying constraints unlocks **{new_zone.id}**, delivering "
                    f"a higher risk-adjusted return ({new_score} vs {base_score}). "
                    f"Extra transit of {dist_delta:.1f} km is offset by superior productivity."
                )
            else:
                lines.append(
                    f"> 🟡 **Trade-off Shift:** While **{new_zone.id}** satisfies the modified constraints, "
                    f"overall composite score shifts by {comp_delta}. Evaluate transit fuel versus expected catch."
                )
        else:
            lines.append(
                f"> 🔵 **Zone Retained:** **{new_zone.id}** remains the top-ranked recommendation. "
                "Its high margin of safety and productivity make it resilient against the simulated constraint shift."
            )

        return "\n".join(lines)

    @classmethod
    def _generate_interactive_actions(cls, mission: StructuredMission) -> list[dict[str, str]]:
        """Generate clickable action prompts or card buttons for ASI:One chat."""
        actions: list[dict[str, str]] = []

        cur_dist = mission.max_distance_km
        if cur_dist < 60.0:
            actions.append({
                "title": f"Expand to {int(cur_dist + 15)} km",
                "prompt": f"What if I travel {int(cur_dist + 15)} km farther?",
                "type": "distance_expansion",
            })
        if cur_dist > 25.0:
            actions.append({
                "title": f"Limit to {int(cur_dist - 10)} km",
                "prompt": f"What if I stay within {int(cur_dist - 10)} km?",
                "type": "distance_reduction",
            })

        if mission.objective != "safest":
            actions.append({
                "title": "Prioritize Maximum Safety",
                "prompt": "What if I prioritize maximum safety over catch volume?",
                "type": "objective_safety",
            })
        else:
            actions.append({
                "title": "Maximize Catch Yield",
                "prompt": "What if I prioritize high fishing potential?",
                "type": "objective_yield",
            })

        actions.append({
            "title": "Early Morning 5 AM Departure",
            "prompt": "What if I leave at 5:00 AM instead?",
            "type": "time_shift",
        })

        return actions
