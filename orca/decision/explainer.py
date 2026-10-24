"""Decision Explainer producing human-readable trade-off reasoning and advisories."""

from orca.models.candidate import CandidateZone, SafetyEvaluation
from orca.models.mission import StructuredMission


class DecisionExplainer:
    """Generates transparent, evidence-backed explanations for ORCA recommendations."""

    @classmethod
    def generate_recommendation(
        cls,
        selected: CandidateZone | None,
        mission: StructuredMission,
    ) -> str:
        """Synthesize why the primary candidate was selected."""
        if not selected:
            return (
                f"No candidate zone within the {mission.max_distance_km} km radius currently satisfies "
                "all safety and operational constraints. Marine conditions or boundary restrictions in this sector "
                "preclude a safe departure."
            )

        w_data = selected.weather_data or {}
        o_data = selected.ocean_data or {}

        wave_h = w_data.get("wave_height_m", "N/A")
        wind_spd = w_data.get("wind_speed_kmh", "N/A")
        sst = o_data.get("sst_c", "N/A")
        chlo = o_data.get("chlorophyll_mg_m3", "N/A")

        bearing_str = f" at bearing {selected.bearing_degrees:.0f}°" if selected.bearing_degrees is not None else ""

        return (
            f"RECOMMENDATION: Zone {selected.id} located {selected.distance_km:.1f} km from your departure origin{bearing_str}. "
            f"Composite Score: {selected.composite_score:.1f}/100. "
            f"Expected Sea Conditions: Wave height ~{wave_h}m, Wind speed ~{wind_spd} km/h. "
            f"Ocean Productivity: Sea Surface Temp {sst}°C, Chlorophyll {chlo} mg/m³. "
            "This zone represents the optimal balance of high fishing potential and calm, safe marine conditions."
        )

    @classmethod
    def generate_trade_offs(
        cls,
        selected: CandidateZone | None,
        alternatives: list[CandidateZone],
    ) -> str:
        """Explain comparative trade-offs between the chosen zone and alternatives."""
        if not alternatives:
            return "No alternative offshore candidate zones were identified within the target search radius."

        trade_off_lines: list[str] = []

        for alt in alternatives[:3]:  # Top 3 alternatives
            if alt.safety_status == SafetyEvaluation.UNSAFE:
                reason = "Rejected due to critical environmental hazards (unsafe wave heights or storm squalls)."
            elif alt.safety_status == SafetyEvaluation.RESTRICTED:
                reason = "Disqualified due to proximity to configured restricted zones or maritime boundaries."
            elif selected and alt.fishing_score > selected.fishing_score:
                reason = (
                    f"Higher raw fishing potential ({alt.fishing_score:.1f} vs {selected.fishing_score:.1f}), "
                    f"but significantly higher operating risk (Safety: {alt.safety_score:.1f}/100 vs {selected.safety_score:.1f}/100)."
                )
            elif selected and alt.distance_km > selected.distance_km:
                reason = (
                    f"Located further offshore ({alt.distance_km:.1f} km vs {selected.distance_km:.1f} km) "
                    "requiring greater fuel and transit time without proportional opportunity gains."
                )
            else:
                reason = f"Ranked lower with composite score {alt.composite_score:.1f}/100."

            trade_off_lines.append(f"• Zone {alt.id} ({alt.distance_km:.1f} km): {reason}")

        return "\n".join(trade_off_lines)

    @classmethod
    def generate_safety_advisory(
        cls,
        selected: CandidateZone | None,
        alternatives: list[CandidateZone],
    ) -> str:
        """Generate operational safety advisory and official disclaimer."""
        advisories: list[str] = [
            "OPERATIONAL SAFETY ADVISORY:",
            "- Always monitor VHF channel 16 and verify local port control warnings before casting off.",
            "- Ensure life jackets, emergency flares, and communication gear are onboard.",
        ]

        if selected and selected.safety_status == SafetyEvaluation.CAUTION:
            advisories.append(
                "- CAUTION: Moderate swell conditions forecasted in this sector. Experienced skippers only."
            )

        advisories.append(
            "DISCLAIMER: ORCA is a decision-support prototype. It is not an official legal clearance or certified navigation authority."
        )

        return "\n".join(advisories)

    @classmethod
    def generate_what_if_suggestions(
        cls,
        selected: CandidateZone | None,
        mission: StructuredMission,
    ) -> list[str]:
        """Proactively suggest actionable What-If exploration scenarios."""
        suggestions: list[str] = []
        current_dist = mission.max_distance_km

        # Suggest distance adjustment
        if current_dist < 60.0:
            suggestions.append(f"What if I travel {int(current_dist + 15)} km farther offshore?")

        # Suggest objective change
        if mission.objective == "high_fishing_potential":
            suggestions.append("What if I prioritize maximum safety over fishing productivity?")
        else:
            suggestions.append("What if I prioritize high fishing potential?")

        # Suggest departure time adjustment
        suggestions.append("What if I leave at 5:00 AM instead?")

        return suggestions
