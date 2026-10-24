"""SQLite-backed persistence for evidence and reliability assessments.

SQLite keeps the V1 storage adapter dependency-free and portable.  The store
can later be replaced by PostgreSQL/PostGIS without changing the Evidence
Agent contract because callers use this small persistence interface.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from orca.models.evidence import EvidenceAssessment, EvidenceItem


class EvidenceStore:
    """Persist evidence records and assessments by request ID."""

    def __init__(self, path: str | Path) -> None:
        self._raw_path = str(path)
        self.path = Path(path)
        self._memory_connection: sqlite3.Connection | None = None

        if self._raw_path == ":memory:":
            self._memory_connection = sqlite3.connect(":memory:")
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)

        self._initialise()

    def save_evidence(self, request_id: str, evidence: Iterable[EvidenceItem]) -> int:
        """Persist evidence idempotently and return the number of new records."""
        stored_at = datetime.now(timezone.utc).isoformat()
        inserted = 0
        with self._connection() as connection:
            for item in evidence:
                payload = item.model_dump(mode="json")
                payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
                record_id = hashlib.sha256(
                    f"{request_id}:{payload_json}".encode("utf-8")
                ).hexdigest()
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO evidence_records
                        (record_id, request_id, source, retrieved_at, payload, stored_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record_id,
                        request_id,
                        item.source,
                        item.retrieved_at.isoformat(),
                        payload_json,
                        stored_at,
                    ),
                )
                inserted += max(cursor.rowcount, 0)
        return inserted

    def save_assessment(self, request_id: str, assessment: EvidenceAssessment) -> None:
        """Upsert the latest reliability assessment for a request."""
        payload_json = json.dumps(assessment.model_dump(mode="json"), sort_keys=True)
        stored_at = datetime.now(timezone.utc).isoformat()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO assessments (request_id, payload, stored_at)
                VALUES (?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    payload = excluded.payload,
                    stored_at = excluded.stored_at
                """,
                (request_id, payload_json, stored_at),
            )

    def get_evidence(self, request_id: str) -> list[EvidenceItem]:
        """Read all persisted evidence for a request in retrieval order."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT payload
                FROM evidence_records
                WHERE request_id = ?
                ORDER BY retrieved_at ASC, record_id ASC
                """,
                (request_id,),
            ).fetchall()
        return [EvidenceItem.model_validate(json.loads(row[0])) for row in rows]

    def get_assessment(self, request_id: str) -> EvidenceAssessment | None:
        """Read the latest persisted reliability assessment for a request."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload FROM assessments WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            return None
        return EvidenceAssessment.model_validate(json.loads(row[0]))

    def close(self) -> None:
        """Close the in-memory connection, if this store uses one."""
        if self._memory_connection is not None:
            self._memory_connection.close()
            self._memory_connection = None

    def _initialise(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS evidence_records (
                    record_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    stored_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_evidence_request
                    ON evidence_records (request_id, retrieved_at);

                CREATE TABLE IF NOT EXISTS assessments (
                    request_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    stored_at TEXT NOT NULL
                );
                """
            )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        if self._memory_connection is not None:
            try:
                yield self._memory_connection
                self._memory_connection.commit()
            except Exception:
                self._memory_connection.rollback()
                raise
            return

        connection = sqlite3.connect(self.path)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
