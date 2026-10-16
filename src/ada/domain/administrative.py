"""Canonical administrative-action and absence entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import ClassVar
from uuid import uuid4

from ada.domain.common import CanonicalEntity, FieldPolicy


class AdministrativeStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"


class AbsenceStatus(StrEnum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, kw_only=True)
class AdministrativeAction(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "administrative_action"
    TABLE: ClassVar[str] = "administrative_actions"
    ID_FIELD: ClassVar[str] = "action_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "personnel_id": FieldPolicy.REQUIRED,
        "action_type": FieldPolicy.REQUIRED,
        "status": FieldPolicy.REQUIRED,
        "summary": FieldPolicy.REQUIRED,
        "effective_from": FieldPolicy.RECOMMENDED,
        "effective_to": FieldPolicy.OPTIONAL,
        "review_request_id": FieldPolicy.OPTIONAL,
    }

    action_id: str = field(default_factory=lambda: str(uuid4()))
    personnel_id: str
    action_type: str
    status: AdministrativeStatus = AdministrativeStatus.DRAFT
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    summary: str
    review_request_id: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if (
            not self.personnel_id.strip()
            or not self.action_type.strip()
            or not self.summary.strip()
        ):
            raise ValueError("personnel_id, action_type, and summary are required")
        for name in ("effective_from", "effective_to"):
            value = getattr(self, name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError("effective_to cannot precede effective_from")


@dataclass(frozen=True, kw_only=True)
class Absence(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "absence"
    TABLE: ClassVar[str] = "absences"
    ID_FIELD: ClassVar[str] = "absence_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "personnel_id": FieldPolicy.REQUIRED,
        "absence_type": FieldPolicy.REQUIRED,
        "start_at": FieldPolicy.REQUIRED,
        "end_at": FieldPolicy.REQUIRED,
        "status": FieldPolicy.REQUIRED,
        "notes": FieldPolicy.OPTIONAL,
        "administrative_action_id": FieldPolicy.OPTIONAL,
    }

    absence_id: str = field(default_factory=lambda: str(uuid4()))
    personnel_id: str
    absence_type: str
    start_at: datetime
    end_at: datetime
    status: AbsenceStatus = AbsenceStatus.REQUESTED
    notes: str | None = None
    administrative_action_id: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.personnel_id.strip() or not self.absence_type.strip():
            raise ValueError("personnel_id and absence_type are required")
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError("absence timestamps must be timezone-aware")
        if self.end_at < self.start_at:
            raise ValueError("end_at cannot precede start_at")
