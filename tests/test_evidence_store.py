"""Tests for durable evidence persistence."""

from datetime import datetime, timedelta, timezone

from orca.models.evidence import EvidenceAssessment, EvidenceItem
from orca.storage import EvidenceStore


def test_evidence_store_round_trips_evidence_and_assessment(tmp_path):
    now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
    item = EvidenceItem(
        source="OPEN_METEO_MARINE",
        retrieved_at=now,
        observed_at=now,
        valid_to=now + timedelta(hours=6),
        geographic_coverage="Tamil Nadu coastal waters",
        confidence=0.95,
    )
    assessment = EvidenceAssessment(
        evidence_count=1,
        valid_evidence_count=1,
        complete=True,
        source_quality_score=0.95,
        freshness_score=1.0,
        completeness_score=1.0,
        agreement_score=1.0,
        coverage_score=1.0,
        overall_confidence=0.98,
    )
    path = tmp_path / "evidence.sqlite3"

    store = EvidenceStore(path)
    assert store.save_evidence("request-1", [item]) == 1
    assert store.save_evidence("request-1", [item]) == 0
    store.save_assessment("request-1", assessment)
    store.close()

    reopened = EvidenceStore(path)
    records = reopened.get_evidence("request-1")
    restored_assessment = reopened.get_assessment("request-1")

    assert len(records) == 1
    assert records[0].source == item.source
    assert records[0].retrieved_at == item.retrieved_at
    assert restored_assessment is not None
    assert restored_assessment.overall_confidence == 0.98
    reopened.close()
