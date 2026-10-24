"""Natural Language Intent Extractor converting user requests into StructuredMission objects."""

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from orca.logging.logger import get_logger
from orca.models.mission import Coordinate, StructuredMission, TimeWindow

logger = get_logger(__name__, agent="intent_extractor")

# Known coastal landmarks, fishing harbours, and ports along the Indian coastline
KNOWN_COASTAL_LOCATIONS: dict[str, Coordinate] = {
    "chennai": Coordinate(lat=13.0827, lon=80.2707),
    "kasimedu": Coordinate(lat=13.1264, lon=80.2982),
    "madras": Coordinate(lat=13.0827, lon=80.2707),
    "ennore": Coordinate(lat=13.2000, lon=80.3200),
    "mahabalipuram": Coordinate(lat=12.6200, lon=80.1900),
    "mamallapuram": Coordinate(lat=12.6200, lon=80.1900),
    "cuddalore": Coordinate(lat=11.7500, lon=79.7700),
    "nagapattinam": Coordinate(lat=10.7600, lon=79.8400),
    "rameswaram": Coordinate(lat=9.2800, lon=79.3100),
    "thoothukudi": Coordinate(lat=8.7600, lon=78.1300),
    "tuticorin": Coordinate(lat=8.7600, lon=78.1300),
    "kanyakumari": Coordinate(lat=8.0800, lon=77.5500),
    "kochi": Coordinate(lat=9.9312, lon=76.2673),
    "cochin": Coordinate(lat=9.9312, lon=76.2673),
    "visakhapatnam": Coordinate(lat=17.6868, lon=83.2185),
    "vizag": Coordinate(lat=17.6868, lon=83.2185),
    "mumbai": Coordinate(lat=18.9220, lon=72.8347),
    "mangalore": Coordinate(lat=12.8700, lon=74.8400),
    "goa": Coordinate(lat=15.4900, lon=73.8200),
    "paradip": Coordinate(lat=20.3160, lon=86.6110),
    "puri": Coordinate(lat=19.8135, lon=85.8312),
}


class IntentExtractionResult:
    """Result of intent parsing with extracted mission or clarification request."""

    def __init__(
        self,
        is_success: bool,
        mission: StructuredMission | None = None,
        clarification_prompt: str | None = None,
        extracted_entities: dict[str, Any] | None = None,
    ) -> None:
        self.is_success = is_success
        self.mission = mission
        self.clarification_prompt = clarification_prompt
        self.extracted_entities = extracted_entities or {}


class IntentExtractor:
    """Extracts structured marine mission parameters from natural language prompts."""

    def __init__(self, default_origin: Coordinate | None = None) -> None:
        # Default fallback origin is Chennai Port if not specified
        self.default_origin = default_origin or Coordinate(lat=13.0827, lon=80.2707)

    def extract(
        self,
        text: str,
        now: datetime | None = None,
        request_id: str | None = None,
    ) -> IntentExtractionResult:
        """Parse natural language query into a StructuredMission.

        Args:
            text: Raw input query (e.g. "I want to go fishing tomorrow morning from Chennai within 30 km").
            now: Reference current time (defaults to utcnow).
            request_id: Optional trace ID; generates a new UUID if not provided.

        Returns:
            IntentExtractionResult: Parsed StructuredMission or single targeted clarification request.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        trace_id = request_id or f"req-{uuid.uuid4().hex[:12]}"
        normalized_text = text.lower().strip()

        entities: dict[str, Any] = {}

        # 1. Location / Origin Extraction
        origin_coord: Coordinate | None = None
        matched_loc_name: str | None = None
        for loc_name, coord in KNOWN_COASTAL_LOCATIONS.items():
            # Match whole word
            if re.search(rf"\b{re.escape(loc_name)}\b", normalized_text):
                origin_coord = coord
                matched_loc_name = loc_name
                break

        # Check for explicit lat/lon coordinates (e.g. "13.08, 80.27" or "lat 13.08 lon 80.27")
        coord_match = re.search(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", normalized_text)
        if coord_match:
            try:
                lat = float(coord_match.group(1))
                lon = float(coord_match.group(2))
                origin_coord = Coordinate(lat=lat, lon=lon)
                matched_loc_name = f"({lat}, {lon})"
            except ValueError:
                pass

        if not origin_coord:
            # If no location mentioned at all, check if fishing intent is present
            if any(k in normalized_text for k in ["fish", "boat", "sea", "ocean", "zone"]):
                # Apply standard single clarification prompt per ORCA clarification rules
                return IntentExtractionResult(
                    is_success=False,
                    clarification_prompt="What is your departure port or coastal origin (e.g. Chennai, Kasimedu, Visakhapatnam)?",
                    extracted_entities={"text": text},
                )
            else:
                return IntentExtractionResult(
                    is_success=False,
                    clarification_prompt="Please specify your intended coastal departure location and marine activity.",
                    extracted_entities={"text": text},
                )

        entities["origin"] = matched_loc_name
        entities["origin_coord"] = origin_coord.to_tuple()

        # 2. Distance Extraction (e.g. "within 30 km", "25km", "radius 40 km", "up to 50 km")
        max_dist_km = 30.0  # default
        dist_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers|kilometres)", normalized_text)
        if dist_match:
            try:
                max_dist_km = float(dist_match.group(1))
                if max_dist_km <= 0 or max_dist_km > 300:
                    max_dist_km = 30.0
            except ValueError:
                pass
        entities["max_distance_km"] = max_dist_km

        # 3. Time Window Extraction
        # Look for "tomorrow", "today", "morning", "afternoon", "evening"
        is_tomorrow = "tomorrow" in normalized_text
        start_date = now + timedelta(days=1) if is_tomorrow else now

        start_hour = 5
        duration_hours = 6

        if "afternoon" in normalized_text:
            start_hour = 12
            duration_hours = 6
        elif "evening" in normalized_text:
            start_hour = 17
            duration_hours = 5
        elif "night" in normalized_text:
            start_hour = 20
            duration_hours = 8
        elif "morning" in normalized_text or "early" in normalized_text or "dawn" in normalized_text:
            start_hour = 5
            duration_hours = 6

        # Check for explicit hour e.g. "at 6 am" or "at 5:00"
        time_match = re.search(r"\bat\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", normalized_text)
        if time_match:
            h = int(time_match.group(1))
            ampm = time_match.group(3)
            if ampm == "pm" and h < 12:
                h += 12
            elif ampm == "am" and h == 12:
                h = 0
            start_hour = h

        start_time = start_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        # If today and the hour has already passed, shift to next available window
        if not is_tomorrow and start_time < now:
            start_time = now + timedelta(hours=1)

        end_time = start_time + timedelta(hours=duration_hours)
        time_window = TimeWindow(start=start_time, end=end_time)
        entities["time_window"] = {"start": start_time.isoformat(), "end": end_time.isoformat()}

        # 4. Activity & Objectives
        activity = "fishing"
        objective = "high_fishing_potential"
        if "safest" in normalized_text or "safety first" in normalized_text or "minimize risk" in normalized_text:
            objective = "safest"
        elif "balanced" in normalized_text:
            objective = "balanced"
        entities["objective"] = objective

        # 5. Constraints
        constraints: list[str] = ["low_weather_risk", "avoid_restricted_zones"]
        if "avoid restricted" in normalized_text or "restricted area" in normalized_text or "sanctuary" in normalized_text:
            if "avoid_restricted_zones" not in constraints:
                constraints.append("avoid_restricted_zones")
        if "boundary" in normalized_text or "imbl" in normalized_text or "eez" in normalized_text:
            constraints.append("avoid_boundary_proximity")
        if "low wave" in normalized_text or "calm" in normalized_text or "low sea risk" in normalized_text:
            constraints.append("low_wave_height")
        entities["constraints"] = constraints

        # Construct validated StructuredMission
        mission = StructuredMission(
            request_id=trace_id,
            activity=activity,
            origin=origin_coord,
            time_window=time_window,
            max_distance_km=max_dist_km,
            objective=objective,
            constraints=constraints,
        )

        logger.info(
            f"Successfully parsed mission '{trace_id}': origin={entities['origin']}, "
            f"distance={max_dist_km}km, window={time_window.start.strftime('%Y-%m-%d %H:%M')}"
        )

        return IntentExtractionResult(
            is_success=True,
            mission=mission,
            extracted_entities=entities,
        )
