"""Data Validator for Open-Meteo Marine API responses."""

from datetime import datetime, timezone
from typing import Any
from orca.logging.logger import get_logger
from orca.models.mission import Coordinate

logger = get_logger(__name__, agent="data_validator")


class ValidationResult:
    """Outcome of validating an external data source payload."""

    def __init__(self, is_valid: bool, errors: list[str], warnings: list[str], validated_data: dict[str, Any]):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        self.validated_data = validated_data


class OpenMeteoValidator:
    """Validates Open-Meteo schema, coordinates, physical ranges, and timestamps."""

    # Plausible physical bounds for marine variables
    RANGES = {
        "wave_height": (0.0, 25.0),            # meters
        "wave_direction": (0.0, 360.0),        # degrees
        "wave_period": (0.0, 30.0),            # seconds
        "swell_wave_height": (0.0, 20.0),      # meters
        "swell_wave_direction": (0.0, 360.0),  # degrees
        "swell_wave_period": (0.0, 30.0),      # seconds
        "wind_wave_height": (0.0, 20.0),       # meters
        "ocean_current_velocity": (0.0, 10.0), # m/s or km/h
        "sea_surface_temperature": (-2.0, 45.0), # Celsius
    }

    @classmethod
    def validate(cls, raw: dict[str, Any], query_coord: Coordinate) -> ValidationResult:
        """Validate raw Open-Meteo response dictionary.

        Args:
            raw: Raw JSON dictionary from Open-Meteo.
            query_coord: Original target coordinate.

        Returns:
            ValidationResult containing status, errors, and warnings.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if not isinstance(raw, dict):
            return ValidationResult(False, ["Payload must be a dictionary"], warnings, {})

        # 1. Schema check
        if "hourly" not in raw or not isinstance(raw["hourly"], dict):
            errors.append("Missing or invalid 'hourly' object in Open-Meteo response")
            return ValidationResult(False, errors, warnings, raw)

        hourly = raw["hourly"]
        time_series = hourly.get("time", [])
        if not time_series or not isinstance(time_series, list):
            errors.append("Empty or missing 'hourly.time' series in payload")
            return ValidationResult(False, errors, warnings, raw)

        # 2. Coordinate proximity check (within 0.5 degrees of query)
        resp_lat = raw.get("latitude")
        resp_lon = raw.get("longitude")
        if resp_lat is not None and resp_lon is not None:
            lat_diff = abs(resp_lat - query_coord.lat)
            lon_diff = abs(resp_lon - query_coord.lon)
            if lat_diff > 0.5 or lon_diff > 0.5:
                warnings.append(
                    f"Open-Meteo resolved coordinate ({resp_lat}, {resp_lon}) is offset from target ({query_coord.lat}, {query_coord.lon})"
                )
        else:
            warnings.append("Open-Meteo response lacks top-level latitude/longitude metadata")

        # 3. Numeric range checks on hourly fields
        series_len = len(time_series)
        for var_name, (min_val, max_val) in cls.RANGES.items():
            if var_name in hourly:
                vals = hourly[var_name]
                if not isinstance(vals, list) or len(vals) != series_len:
                    warnings.append(f"Field '{var_name}' series length mismatch with time array")
                    continue

                # Check non-null values against bounds
                out_of_bounds_count = 0
                for v in vals:
                    if v is not None and not (min_val <= float(v) <= max_val):
                        out_of_bounds_count += 1

                if out_of_bounds_count > 0:
                    warnings.append(
                        f"Field '{var_name}' has {out_of_bounds_count} values outside expected physical range [{min_val}, {max_val}]"
                    )

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, raw)
