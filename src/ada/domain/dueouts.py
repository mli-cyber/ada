"""Due-out / suspense domain models (scaffold stub).

DueOutTemplate, DueOut, DueOutResponse, DueOutAction, DueOutBlocker, DueOutDependency,
ReportingCycle, plus typed outputs and canonical statuses. Roadmap: Phase 9,
Section 5.6.
"""

from __future__ import annotations

# Canonical due-out statuses (normalize free text, preserve original). Defined here for
# reference; the engine that uses them lands in Phase 9.
CANONICAL_STATUSES = (
    "NOT_STARTED",
    "IN_PROGRESS",
    "WAITING_ON_PERSON",
    "WAITING_ON_EXTERNAL",
    "SUBMITTED",
    "RETURNED_FOR_CORRECTION",
    "SCHEDULED",
    "BLOCKED",
    "COMPLETE",
    "OVERDUE",
    "CANCELLED",
    "NOT_APPLICABLE",
    "NEEDS_REVIEW",
)

DUE_OUT_TYPES = (
    "BOOLEAN",
    "COUNT",
    "RATIO",
    "PERCENTAGE",
    "TEXT",
    "DATE",
    "DOCUMENT",
    "PERSON_LIST",
    "PERSON_ACTION",
    "DATASET",
    "CHECKLIST",
)
