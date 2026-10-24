"""Unit tests for IMD marine warnings client."""

from datetime import datetime, timezone
import pytest
from orca.data_sources.imd.client import ImdClient
from orca.data_sources.models import WarningSeverity, WarningType
from orca.models.evidence import DataFreshness


@pytest.mark.asyncio
async def test_imd_fetch_fishermen_warnings_fallback():
    """Verify IMD fishermen warnings fallback correctly parses operational alerts."""
    client = ImdClient(base_url="https://mock-imd.invalid", timeout_seconds=0.1)
    now = datetime(2026, 10, 24, 7, 0, tzinfo=timezone.utc)

    warnings = await client.fetch_fishermen_warnings(coast_region="Tamil Nadu Coast", now=now)

    assert len(warnings) >= 1
    w = warnings[0]
    assert w.warning_type == WarningType.FISHERMEN_WARNING
    assert w.severity in [WarningSeverity.GREEN, WarningSeverity.YELLOW, WarningSeverity.ORANGE, WarningSeverity.RED]
    assert "Tamil Nadu" in w.affected_coast
    assert len(w.advice_for_fishermen) > 0
    assert w.evidence.source.startswith("IMD")
    assert w.evidence.freshness in [DataFreshness.LIVE, DataFreshness.RECENT]


@pytest.mark.asyncio
async def test_imd_fetch_cyclone_warnings_fallback():
    """Verify IMD cyclone warning operational fallback."""
    client = ImdClient(base_url="https://mock-imd.invalid", timeout_seconds=0.1)
    now = datetime(2026, 10, 24, 7, 0, tzinfo=timezone.utc)

    cyclone_reports = await client.fetch_cyclone_warnings(basin="Bay of Bengal", now=now)

    assert len(cyclone_reports) >= 1
    c = cyclone_reports[0]
    assert c.warning_type == WarningType.CYCLONE_ALERT
    assert c.evidence.source.startswith("IMD")
    assert c.cyclone_info is not None
    assert c.cyclone_info["active_cyclone"] is False


def test_imd_parse_live_warning():
    """Verify parsing of live IMD bulletin structure."""
    client = ImdClient()
    now = datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc)
    raw = {
        "bulletins": [
            {
                "id": "IMD-TN-SQUALL-01",
                "severity": "ORANGE",
                "affected_coast": "South Andhra & North Tamil Nadu Coast",
                "description": "Squally winds 45-55 kmph gusting to 65 kmph likely.",
                "advice": "Total suspension of small fishing vessel operations.",
                "issued_at": "2026-10-24T08:00:00+00:00",
                "valid_until": "2026-10-24T20:00:00+00:00",
            }
        ]
    }

    parsed = client._parse_warnings_response(raw, WarningType.COASTAL_BULLETIN, now)
    assert len(parsed) == 1
    w = parsed[0]
    assert w.warning_type == WarningType.COASTAL_BULLETIN
    assert w.severity == WarningSeverity.ORANGE
    assert "Total suspension" in w.advice_for_fishermen
    assert w.evidence.freshness == DataFreshness.LIVE
