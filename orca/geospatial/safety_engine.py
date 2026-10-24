"""Deterministic geospatial safety constraint evaluation engine."""

from orca.geospatial.datasets import MaritimeBoundaryStore
from orca.geospatial.math import calculate_bearing, haversine_distance
from orca.geospatial.models import GeospatialSafetyResult, RestrictionLevel
from orca.models.candidate import CandidateZone, SafetyEvaluation
from orca.models.mission import Coordinate, StructuredMission


class GeospatialSafetyEngine:
    """Evaluates geographic coordinates and candidate marine zones against boundaries and range constraints."""

    def __init__(self, store: MaritimeBoundaryStore | None = None) -> None:
        self.store = store if store is not None else MaritimeBoundaryStore()

    def evaluate_coordinate(
        self,
        target: Coordinate,
        origin: Coordinate | None = None,
        max_distance_km: float | None = None,
    ) -> GeospatialSafetyResult:
        """Deterministically assess safety, violations, clearances, and bearing for a point."""
        distance_km: float | None = None
        bearing_deg: float | None = None
        notes: list[str] = []
        violations: list[str] = []
        buffer_warnings: list[str] = []
        traffic_warnings: list[str] = []

        is_safe = True
        status = SafetyEvaluation.SAFE

        # 1. Evaluate distance and operational radius from origin
        if origin is not None:
            distance_km = haversine_distance(origin, target)
            bearing_deg = calculate_bearing(origin, target)

            if max_distance_km is not None and distance_km > max_distance_km:
                is_safe = False
                status = SafetyEvaluation.UNSAFE
                notes.append(
                    f"Target location ({distance_km:.1f} km) exceeds mission operational limit ({max_distance_km:.1f} km)."
                )
            else:
                notes.append(f"Within operational range: {distance_km:.1f} km (bearing {bearing_deg:.1f}°).")

        # 2. Check strict polygon containment
        containing_zones = self.store.find_zones_containing(target)
        for zone in containing_zones:
            if zone.restriction_level == RestrictionLevel.STRICT_NO_ENTRY:
                is_safe = False
                status = SafetyEvaluation.UNSAFE
                violations.append(f"INSIDE NO-ENTRY ZONE: {zone.name} ({zone.zone_id})")
                notes.append(f"Violates {zone.name}: {zone.description}")

            elif zone.restriction_level == RestrictionLevel.RESTRICTED_FISHING:
                is_safe = False
                if status != SafetyEvaluation.UNSAFE:
                    status = SafetyEvaluation.RESTRICTED
                violations.append(f"INSIDE REGULATED ZONE: {zone.name} ({zone.zone_id})")
                notes.append(f"Restricted fishing in {zone.name}: {zone.description}")

            elif zone.restriction_level == RestrictionLevel.CAUTION_TRAFFIC:
                if status == SafetyEvaluation.SAFE:
                    status = SafetyEvaluation.CAUTION
                traffic_warnings.append(f"INTERSECTS SHIPPING CORRIDOR: {zone.name} ({zone.zone_id})")
                notes.append(f"Traffic hazard in {zone.name}: {zone.description}")

        # 3. Check safety buffer perimeters (only if not already inside the zone)
        containing_ids = {z.zone_id for z in containing_zones}
        buffered_zones = self.store.find_zones_within_buffer(target)

        for zone, dist_km in buffered_zones:
            if zone.zone_id in containing_ids:
                continue

            warning_text = (
                f"Within safety buffer of {zone.name}: {dist_km:.2f} km away "
                f"(perimeter threshold: {zone.buffer_km:.1f} km)"
            )
            buffer_warnings.append(warning_text)

            if zone.restriction_level in (RestrictionLevel.STRICT_NO_ENTRY, RestrictionLevel.RESTRICTED_FISHING):
                if status == SafetyEvaluation.SAFE:
                    status = SafetyEvaluation.CAUTION
                notes.append(f"Buffer warning: {dist_km:.2f} km to boundary of {zone.name}.")

        # 4. Nearest boundary clearance computation
        nearest_zone, min_clearance_km = self.store.get_nearest_boundary_distance(target)
        if nearest_zone and min_clearance_km is not None and not containing_zones:
            notes.append(f"Nearest restricted boundary: {nearest_zone.name} ({min_clearance_km:.1f} km clearance).")

        return GeospatialSafetyResult(
            coordinate=target,
            is_safe=is_safe,
            safety_status=status,
            distance_from_origin_km=distance_km,
            bearing_degrees=bearing_deg,
            zone_violations=violations,
            buffer_warnings=buffer_warnings,
            traffic_warnings=traffic_warnings,
            nearest_boundary_distance_km=min_clearance_km,
            notes=notes,
        )

    def evaluate_mission_candidate(
        self,
        candidate_zone: CandidateZone,
        mission: StructuredMission,
    ) -> CandidateZone:
        """Enrich and evaluate an existing CandidateZone against structured mission constraints."""
        geo_result = self.evaluate_coordinate(
            target=candidate_zone.location,
            origin=mission.origin,
            max_distance_km=mission.max_distance_km,
        )

        candidate_zone.distance_km = geo_result.distance_from_origin_km or 0.0
        candidate_zone.bearing_degrees = geo_result.bearing_degrees
        candidate_zone.safety_status = geo_result.safety_status
        candidate_zone.geospatial_notes = geo_result.notes

        # Adjust safety score deterministically based on geospatial severity
        if geo_result.safety_status == SafetyEvaluation.UNSAFE:
            candidate_zone.safety_score = 0.0
        elif geo_result.safety_status == SafetyEvaluation.RESTRICTED:
            candidate_zone.safety_score = min(candidate_zone.safety_score, 25.0)
        elif geo_result.safety_status == SafetyEvaluation.CAUTION:
            candidate_zone.safety_score = min(candidate_zone.safety_score, 65.0)

        return candidate_zone
