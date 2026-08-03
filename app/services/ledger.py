# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The claims ledger — the product's system of record.

Append-only provenance: what was checked, against which source, what the human
decided, and why. Two implementations behind one interface:

- `InMemoryLedger` — default, for local dev and the walking skeleton.
- `BigQueryLedger`  — used when `BIGQUERY_DATASET` is set.

Callers never branch on which is active; `get_ledger()` decides once.
"""

from __future__ import annotations

import logging
import os
from typing import Protocol

from app.models import RevisionEntry, Scene

logger = logging.getLogger(__name__)

BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE", "claims_ledger")


class Ledger(Protocol):
    def save_scene(self, scene: Scene) -> None: ...
    def get_scene(self, scene_id: str) -> Scene | None: ...
    def list_scenes(self) -> list[Scene]: ...
    def append_revision(self, entry: RevisionEntry) -> None: ...
    def revisions(self, scene_id: str) -> list[RevisionEntry]: ...
    @property
    def backend(self) -> str: ...


class InMemoryLedger:
    """Process-local. Fine for a single-instance demo; loses state on restart."""

    def __init__(self) -> None:
        self._scenes: dict[str, Scene] = {}
        self._revisions: list[RevisionEntry] = []

    def save_scene(self, scene: Scene) -> None:
        self._scenes[scene.id] = scene

    def get_scene(self, scene_id: str) -> Scene | None:
        return self._scenes.get(scene_id)

    def list_scenes(self) -> list[Scene]:
        return list(self._scenes.values())

    def append_revision(self, entry: RevisionEntry) -> None:
        self._revisions.append(entry)

    def revisions(self, scene_id: str) -> list[RevisionEntry]:
        return [r for r in self._revisions if r.scene_id == scene_id]

    @property
    def backend(self) -> str:
        return "in-memory"


class BigQueryLedger(InMemoryLedger):
    """Durable ledger. Keeps an in-memory read cache and streams every write to
    BigQuery, so the audit trail survives restarts and is queryable by the
    standards desk after the fact.

    Inherits the in-memory reads deliberately: at scene scale, re-querying
    BigQuery to render the UI would add latency for no benefit. BigQuery is the
    record; memory is the view.
    """

    def __init__(self) -> None:
        super().__init__()
        from google.cloud import bigquery  # imported lazily; optional dependency

        self._client = bigquery.Client()
        self._table = f"{self._client.project}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"
        self._ensure_table()

    def _ensure_table(self) -> None:
        from google.cloud import bigquery

        schema = [
            bigquery.SchemaField("scene_id", "STRING"),
            bigquery.SchemaField("revision", "INT64"),
            bigquery.SchemaField("claim_id", "STRING"),
            bigquery.SchemaField("what_changed", "STRING"),
            bigquery.SchemaField("why", "STRING"),
            bigquery.SchemaField("disposition", "STRING"),
            bigquery.SchemaField("sources", "STRING"),  # JSON blob
            bigquery.SchemaField("recorded_at", "TIMESTAMP"),
        ]
        table = bigquery.Table(self._table, schema=schema)
        self._client.create_table(table, exists_ok=True)

    def append_revision(self, entry: RevisionEntry) -> None:
        super().append_revision(entry)
        import json

        row = {
            "scene_id": entry.scene_id,
            "revision": entry.revision,
            "claim_id": entry.claim_id,
            "what_changed": entry.what_changed,
            "why": entry.why,
            "disposition": entry.disposition.value if entry.disposition else None,
            "sources": json.dumps([s.model_dump() for s in entry.sources]),
            "recorded_at": "AUTO",
        }
        row["recorded_at"] = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat()
        errors = self._client.insert_rows_json(self._table, [row])
        if errors:
            # Never fail the user's request because the audit write failed —
            # log loudly instead. The in-memory copy still has it.
            logger.error("BigQuery ledger insert failed: %s", errors)

    @property
    def backend(self) -> str:
        return f"bigquery:{self._table}"


_ledger: Ledger | None = None


def get_ledger() -> Ledger:
    """Singleton. Falls back to in-memory if BigQuery can't be reached, so a
    misconfigured dataset degrades the audit trail rather than the product."""
    global _ledger
    if _ledger is not None:
        return _ledger

    if BIGQUERY_DATASET:
        try:
            _ledger = BigQueryLedger()
            logger.info("Ledger backend: %s", _ledger.backend)
            return _ledger
        except Exception as exc:
            logger.warning("BigQuery ledger unavailable (%s); using in-memory", exc)

    _ledger = InMemoryLedger()
    return _ledger
