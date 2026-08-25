"""Canonical Ada state (scaffold stub).

A common, serializable, provenance-carrying state shared across agents (people,
organizations, assignments, courses, training, due-outs, evidence, provenance, etc.).
Roadmap: Phase 1 (Canonical Domain Model), Section 6.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdaState:
    """Placeholder for the canonical cross-agent state container.

    Fields will be filled out in Phase 1. Kept as loose lists for now so the shape is
    visible without committing to entity classes before the schema phase.
    """

    people: list[dict[str, Any]] = field(default_factory=list)
    organizations: list[dict[str, Any]] = field(default_factory=list)
    positions: list[dict[str, Any]] = field(default_factory=list)
    assignments: list[dict[str, Any]] = field(default_factory=list)
    courses: list[dict[str, Any]] = field(default_factory=list)
    training_requirements: list[dict[str, Any]] = field(default_factory=list)
    training_records: list[dict[str, Any]] = field(default_factory=list)
    due_out_templates: list[dict[str, Any]] = field(default_factory=list)
    due_outs: list[dict[str, Any]] = field(default_factory=list)
    due_out_responses: list[dict[str, Any]] = field(default_factory=list)
    due_out_actions: list[dict[str, Any]] = field(default_factory=list)
    due_out_blockers: list[dict[str, Any]] = field(default_factory=list)
    reporting_cycles: list[dict[str, Any]] = field(default_factory=list)
    administrative_actions: list[dict[str, Any]] = field(default_factory=list)
    absences: list[dict[str, Any]] = field(default_factory=list)
    documents: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    validation_issues: list[dict[str, Any]] = field(default_factory=list)
    unresolved_questions: list[dict[str, Any]] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)
