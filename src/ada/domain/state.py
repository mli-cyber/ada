"""Reference-envelope contract for future durable workflows.

``AdaState`` carries identifiers, scoped working context, and provenance references.
It intentionally never carries whole domain datasets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EntityRef:
    """Version-aware pointer to a canonical entity."""

    entity_type: str
    entity_id: str
    version: int

    def __post_init__(self) -> None:
        if not self.entity_type.strip() or not self.entity_id.strip():
            raise ValueError("entity_type and entity_id are required")
        if self.version < 1:
            raise ValueError("entity version must be at least 1")


@dataclass
class AdaState:
    """Serializable handoff envelope containing references, never domain datasets."""

    workflow_id: str | None = None
    conversation_id: str | None = None
    principal_id: str | None = None
    profile: str = "military"
    request: dict[str, Any] = field(default_factory=dict)
    working_context: dict[str, Any] = field(default_factory=dict)
    entity_refs: list[EntityRef] = field(default_factory=list)
    document_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)
    validation_issues: list[dict[str, Any]] = field(default_factory=list)
    unresolved_questions: list[dict[str, Any]] = field(default_factory=list)

    def add_entity_ref(self, entity_type: str, entity_id: str, version: int) -> EntityRef:
        reference = EntityRef(entity_type, entity_id, version)
        if reference not in self.entity_refs:
            self.entity_refs.append(reference)
        return reference

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
