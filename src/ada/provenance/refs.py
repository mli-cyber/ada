"""Stable, serializable references used before the full evidence engine lands."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def _id() -> str:
    return str(uuid4())


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class SourceRef:
    source_type: str
    source_id: str
    location: str | None = None
    source_ref_id: str = field(default_factory=_id)


@dataclass(frozen=True)
class EvidenceRef:
    source_ref_id: str
    locator: str
    excerpt_hash: str | None = None
    evidence_ref_id: str = field(default_factory=_id)


@dataclass(frozen=True)
class ProvenanceRef:
    source_ref_id: str
    evidence_ref_ids: tuple[str, ...] = ()
    method: str = "user_supplied"
    confidence: float | None = None
    created_at: str = field(default_factory=_now)
    provenance_ref_id: str = field(default_factory=_id)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
