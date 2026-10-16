"""Canonical due-out schema; recurrence and escalation remain Phase 9."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import ClassVar
from uuid import uuid4

from ada.domain.common import CanonicalEntity, FieldPolicy


class DueOutStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_ON_PERSON = "WAITING_ON_PERSON"
    WAITING_ON_EXTERNAL = "WAITING_ON_EXTERNAL"
    SUBMITTED = "SUBMITTED"
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION"
    SCHEDULED = "SCHEDULED"
    BLOCKED = "BLOCKED"
    COMPLETE = "COMPLETE"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class DueOutType(StrEnum):
    BOOLEAN = "BOOLEAN"
    COUNT = "COUNT"
    RATIO = "RATIO"
    PERCENTAGE = "PERCENTAGE"
    TEXT = "TEXT"
    DATE = "DATE"
    DOCUMENT = "DOCUMENT"
    PERSON_LIST = "PERSON_LIST"
    PERSON_ACTION = "PERSON_ACTION"
    DATASET = "DATASET"
    CHECKLIST = "CHECKLIST"


class DueOutPriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


CANONICAL_STATUSES = tuple(status.value for status in DueOutStatus)
DUE_OUT_TYPES = tuple(due_out_type.value for due_out_type in DueOutType)


@dataclass(frozen=True, kw_only=True)
class DueOut(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "due_out"
    TABLE: ClassVar[str] = "due_outs"
    ID_FIELD: ClassVar[str] = "due_out_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "title": FieldPolicy.REQUIRED,
        "due_out_type": FieldPolicy.REQUIRED,
        "status": FieldPolicy.REQUIRED,
        "priority": FieldPolicy.DEFAULTABLE,
        "description": FieldPolicy.RECOMMENDED,
        "due_at": FieldPolicy.RECOMMENDED,
        "owner_organization_id": FieldPolicy.RECOMMENDED,
    }

    due_out_id: str = field(default_factory=lambda: str(uuid4()))
    title: str
    description: str | None = None
    due_out_type: DueOutType = DueOutType.TEXT
    status: DueOutStatus = DueOutStatus.NOT_STARTED
    due_at: datetime | None = None
    priority: DueOutPriority = DueOutPriority.NORMAL
    owner_organization_id: str | None = None
    created_by_principal: str

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.title.strip() or not self.created_by_principal.strip():
            raise ValueError("title and created_by_principal are required")
        if self.due_at is not None and self.due_at.tzinfo is None:
            raise ValueError("due_at must be timezone-aware")


@dataclass(frozen=True, kw_only=True)
class DueOutAssignment(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "due_out_assignment"
    TABLE: ClassVar[str] = "due_out_assignments"
    ID_FIELD: ClassVar[str] = "assignment_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "due_out_id": FieldPolicy.REQUIRED,
        "status": FieldPolicy.REQUIRED,
        "assignee_personnel_id": FieldPolicy.OPTIONAL,
        "assignee_organization_id": FieldPolicy.OPTIONAL,
        "completed_at": FieldPolicy.OPTIONAL,
        "response_text": FieldPolicy.OPTIONAL,
    }

    assignment_id: str = field(default_factory=lambda: str(uuid4()))
    due_out_id: str
    assignee_personnel_id: str | None = None
    assignee_organization_id: str | None = None
    status: DueOutStatus = DueOutStatus.NOT_STARTED
    completed_at: datetime | None = None
    response_text: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.due_out_id.strip():
            raise ValueError("due_out_id is required")
        assignees = bool(self.assignee_personnel_id) + bool(self.assignee_organization_id)
        if assignees != 1:
            raise ValueError("exactly one personnel or organization assignee is required")
        if self.completed_at is not None and self.completed_at.tzinfo is None:
            raise ValueError("completed_at must be timezone-aware")
