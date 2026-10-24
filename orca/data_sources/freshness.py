"""Freshness evaluation utility for marine and meteorological evidence."""

from datetime import datetime, timezone
from orca.models.evidence import DataFreshness


def evaluate_freshness(
    observed_at: datetime | None,
    valid_to: datetime | None,
    now: datetime | None = None,
    live_threshold_hours: float = 3.0,
    recent_threshold_hours: float = 24.0,
) -> tuple[DataFreshness, float]:
    """Evaluate data freshness and calculate a confidence multiplier.

    Args:
        observed_at: When the raw measurement or satellite pass was taken.
        valid_to: Expiration timestamp of the forecast or advisory bulletin.
        now: Current time (defaults to utcnow).
        live_threshold_hours: Maximum hours to be considered 'live' (default 3h).
        recent_threshold_hours: Maximum hours to be considered 'recent' (default 24h).

    Returns:
        tuple[DataFreshness, float]: (Freshness category, Confidence multiplier between 0.1 and 1.0)
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # If timezone naive, assume UTC
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # Check expiration first if valid_to is known
    if valid_to is not None:
        if valid_to.tzinfo is None:
            valid_to = valid_to.replace(tzinfo=timezone.utc)
        if now > valid_to:
            return DataFreshness.EXPIRED, 0.2

    if observed_at is None:
        return DataFreshness.UNKNOWN, 0.5

    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)

    age_seconds = (now - observed_at).total_seconds()
    age_hours = max(0.0, age_seconds / 3600.0)

    if age_hours <= live_threshold_hours:
        # 0 to 3 hours old -> Live data (multiplier 1.0)
        return DataFreshness.LIVE, 1.0
    elif age_hours <= recent_threshold_hours:
        # 3 to 24 hours old -> Linear decay between 0.95 and 0.70
        decay = 0.95 - ((age_hours - live_threshold_hours) / (recent_threshold_hours - live_threshold_hours)) * 0.25
        return DataFreshness.RECENT, round(decay, 2)
    else:
        # > 24 hours old -> Stale data (multiplier 0.40 or lower)
        decay = max(0.10, 0.40 - ((age_hours - recent_threshold_hours) / 48.0) * 0.30)
        return DataFreshness.STALE, round(decay, 2)
