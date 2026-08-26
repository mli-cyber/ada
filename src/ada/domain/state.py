"""Reference-envelope contract for future durable workflows.

``AdaState`` carries identifiers, scoped working context, and provenance references.
It intentionally never carries whole domain datasets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdaState:
    """Serializable handoff envelope; Phase 1 will formalize domain-specific references."""

    workflow_id: str | None = None
    conversation_id: str | None = None
    principal_id: str | None = None
    profile: str = "military"
    request: dict[str, Any] = field(default_factory=dict)
    working_context: dict[str, Any] = field(default_factory=dict)
    entity_refs: list[str] = field(default_factory=list)
    document_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)
    validation_issues: list[dict[str, Any]] = field(default_factory=list)
    unresolved_questions: list[dict[str, Any]] = field(default_factory=list)
