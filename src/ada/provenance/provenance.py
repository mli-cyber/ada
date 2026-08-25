"""Provenance and evidence engine (scaffold stub).

Tracks source document, page/row/section, extraction method, confidence, timestamp,
user, agent, and original vs. modified value. Roadmap: Phase 7.
"""

from __future__ import annotations

from typing import Any


def record_provenance(entity_type: str, entity_id: str, evidence: dict[str, Any]) -> None:
    """Attach evidence/provenance to a record. Scaffold stub - see roadmap Phase 7."""

    raise NotImplementedError("Provenance engine is implemented in roadmap Phase 7.")
