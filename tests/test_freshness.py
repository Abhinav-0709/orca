"""Unit tests for timestamp evaluation and freshness decay."""

from datetime import datetime, timedelta, timezone
from orca.data_sources.freshness import evaluate_freshness
from orca.models.evidence import DataFreshness


def test_freshness_live():
    """Verify observations under 3 hours are classified as LIVE with full confidence."""
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    observed = now - timedelta(hours=1.5)
    valid_until = now + timedelta(hours=10)

    freshness, multiplier = evaluate_freshness(observed, valid_until, now)
    assert freshness == DataFreshness.LIVE
    assert multiplier == 1.0


def test_freshness_recent_decay():
    """Verify observations between 3h and 24h are classified as RECENT with linear decay."""
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    observed = now - timedelta(hours=12)
    valid_until = now + timedelta(hours=6)

    freshness, multiplier = evaluate_freshness(observed, valid_until, now)
    assert freshness == DataFreshness.RECENT
    assert 0.70 <= multiplier <= 0.95


def test_freshness_stale():
    """Verify observations older than 24 hours are classified as STALE with heavy penalty."""
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    observed = now - timedelta(hours=36)
    valid_until = now + timedelta(hours=2)

    freshness, multiplier = evaluate_freshness(observed, valid_until, now)
    assert freshness == DataFreshness.STALE
    assert multiplier <= 0.40


def test_freshness_expired():
    """Verify data past valid_to expiration timestamp is marked EXPIRED immediately."""
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    observed = now - timedelta(hours=2)  # recently observed...
    valid_until = now - timedelta(minutes=15)  # ...but valid window has passed

    freshness, multiplier = evaluate_freshness(observed, valid_until, now)
    assert freshness == DataFreshness.EXPIRED
    assert multiplier == 0.2


def test_freshness_unknown():
    """Verify missing observed_at timestamp returns UNKNOWN."""
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    freshness, multiplier = evaluate_freshness(None, None, now)
    assert freshness == DataFreshness.UNKNOWN
    assert multiplier == 0.5
