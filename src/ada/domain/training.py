"""Canonical training course, requirement, and completion entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import ClassVar
from uuid import uuid4

from ada.domain.common import CanonicalEntity, FieldPolicy


class CourseStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    RETIRED = "RETIRED"


class RequirementType(StrEnum):
    INITIAL = "INITIAL"
    RECURRING = "RECURRING"
    POSITION = "POSITION"
    ORGANIZATION = "ORGANIZATION"


class CompletionStatus(StrEnum):
    COMPLETE = "COMPLETE"
    EXPIRED = "EXPIRED"
    WAIVED = "WAIVED"
    REVOKED = "REVOKED"


@dataclass(frozen=True, kw_only=True)
class TrainingCourse(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "training_course"
    TABLE: ClassVar[str] = "training_courses"
    ID_FIELD: ClassVar[str] = "course_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "code": FieldPolicy.REQUIRED,
        "title": FieldPolicy.REQUIRED,
        "status": FieldPolicy.REQUIRED,
        "description": FieldPolicy.RECOMMENDED,
        "provider": FieldPolicy.RECOMMENDED,
        "validity_days": FieldPolicy.OPTIONAL,
    }

    course_id: str = field(default_factory=lambda: str(uuid4()))
    code: str
    title: str
    description: str | None = None
    provider: str | None = None
    validity_days: int | None = None
    status: CourseStatus = CourseStatus.ACTIVE

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.code.strip() or not self.title.strip():
            raise ValueError("course code and title are required")
        if self.validity_days is not None and self.validity_days < 0:
            raise ValueError("validity_days cannot be negative")


@dataclass(frozen=True, kw_only=True)
class TrainingRequirement(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "training_requirement"
    TABLE: ClassVar[str] = "training_requirements"
    ID_FIELD: ClassVar[str] = "requirement_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "course_id": FieldPolicy.REQUIRED,
        "requirement_type": FieldPolicy.REQUIRED,
        "effective_from": FieldPolicy.REQUIRED,
        "organization_id": FieldPolicy.OPTIONAL,
        "personnel_id": FieldPolicy.OPTIONAL,
        "due_within_days": FieldPolicy.DEFAULTABLE,
        "effective_to": FieldPolicy.OPTIONAL,
    }

    requirement_id: str = field(default_factory=lambda: str(uuid4()))
    course_id: str
    organization_id: str | None = None
    personnel_id: str | None = None
    requirement_type: RequirementType = RequirementType.ORGANIZATION
    due_within_days: int | None = None
    is_mandatory: bool = True
    inherits_to_descendants: bool = True
    effective_from: date
    effective_to: date | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.course_id.strip():
            raise ValueError("course_id is required")
        if not self.organization_id and not self.personnel_id:
            raise ValueError("a requirement needs an organization or personnel scope")
        if self.due_within_days is not None and self.due_within_days < 0:
            raise ValueError("due_within_days cannot be negative")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot precede effective_from")


@dataclass(frozen=True, kw_only=True)
class TrainingCompletion(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "training_completion"
    TABLE: ClassVar[str] = "training_completions"
    ID_FIELD: ClassVar[str] = "completion_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "personnel_id": FieldPolicy.REQUIRED,
        "course_id": FieldPolicy.REQUIRED,
        "completed_on": FieldPolicy.REQUIRED,
        "status": FieldPolicy.REQUIRED,
        "expires_on": FieldPolicy.OPTIONAL,
        "certificate_document_id": FieldPolicy.OPTIONAL,
        "score": FieldPolicy.OPTIONAL,
    }

    completion_id: str = field(default_factory=lambda: str(uuid4()))
    personnel_id: str
    course_id: str
    completed_on: date
    expires_on: date | None = None
    status: CompletionStatus = CompletionStatus.COMPLETE
    certificate_document_id: str | None = None
    score: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.personnel_id.strip() or not self.course_id.strip():
            raise ValueError("personnel_id and course_id are required")
        if self.expires_on is not None and self.expires_on < self.completed_on:
            raise ValueError("expires_on cannot precede completed_on")
