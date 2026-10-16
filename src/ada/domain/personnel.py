"""Canonical personnel, assignment, and contact entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import ClassVar
from uuid import uuid4

from ada.domain.common import (
    CanonicalEntity,
    EncryptedNationalIdentifier,
    FieldPolicy,
)


class PersonnelStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SEPARATED = "SEPARATED"
    PENDING = "PENDING"


class AssignmentType(StrEnum):
    PRIMARY = "PRIMARY"
    ATTACHED = "ATTACHED"
    TEMPORARY = "TEMPORARY"
    ADDITIONAL_DUTY = "ADDITIONAL_DUTY"


class ContactType(StrEnum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    ADDRESS = "ADDRESS"
    EMERGENCY = "EMERGENCY"
    OTHER = "OTHER"


@dataclass(frozen=True, kw_only=True)
class Personnel(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "personnel"
    TABLE: ClassVar[str] = "personnel"
    ID_FIELD: ClassVar[str] = "personnel_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "first_name": FieldPolicy.REQUIRED,
        "last_name": FieldPolicy.REQUIRED,
        "status": FieldPolicy.REQUIRED,
        "employee_number": FieldPolicy.RECOMMENDED,
        "primary_email": FieldPolicy.RECOMMENDED,
        "middle_name": FieldPolicy.OPTIONAL,
        "preferred_name": FieldPolicy.OPTIONAL,
        "position_title": FieldPolicy.OPTIONAL,
        "rank_grade": FieldPolicy.OPTIONAL,
        "notes": FieldPolicy.OPTIONAL,
    }

    personnel_id: str = field(default_factory=lambda: str(uuid4()))
    employee_number: str | None = None
    first_name: str
    middle_name: str | None = None
    last_name: str
    preferred_name: str | None = None
    status: PersonnelStatus = PersonnelStatus.ACTIVE
    date_of_birth: date | None = None
    national_identifier: EncryptedNationalIdentifier | None = None
    primary_email: str | None = None
    phone: str | None = None
    position_title: str | None = None
    rank_grade: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.personnel_id.strip():
            raise ValueError("personnel_id is required")
        if not self.first_name.strip() or not self.last_name.strip():
            raise ValueError("first_name and last_name are required")
        if self.national_identifier is not None and not isinstance(
            self.national_identifier, EncryptedNationalIdentifier
        ):
            raise TypeError("national_identifier must be encrypted before persistence")


@dataclass(frozen=True, kw_only=True)
class PersonnelAssignment(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "personnel_assignment"
    TABLE: ClassVar[str] = "personnel_assignments"
    ID_FIELD: ClassVar[str] = "assignment_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "personnel_id": FieldPolicy.REQUIRED,
        "organization_id": FieldPolicy.REQUIRED,
        "assignment_type": FieldPolicy.REQUIRED,
        "start_date": FieldPolicy.REQUIRED,
        "position_title": FieldPolicy.RECOMMENDED,
        "end_date": FieldPolicy.OPTIONAL,
    }

    assignment_id: str = field(default_factory=lambda: str(uuid4()))
    personnel_id: str
    organization_id: str
    assignment_type: AssignmentType = AssignmentType.PRIMARY
    position_title: str | None = None
    is_primary: bool = True
    start_date: date
    end_date: date | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.personnel_id.strip() or not self.organization_id.strip():
            raise ValueError("personnel_id and organization_id are required")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot precede start_date")


@dataclass(frozen=True, kw_only=True)
class PersonnelContact(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "personnel_contact"
    TABLE: ClassVar[str] = "personnel_contacts"
    ID_FIELD: ClassVar[str] = "contact_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "personnel_id": FieldPolicy.REQUIRED,
        "contact_type": FieldPolicy.REQUIRED,
        "value": FieldPolicy.REQUIRED,
        "label": FieldPolicy.OPTIONAL,
    }

    contact_id: str = field(default_factory=lambda: str(uuid4()))
    personnel_id: str
    contact_type: ContactType
    value: str
    label: str | None = None
    is_primary: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.personnel_id.strip() or not self.value.strip():
            raise ValueError("personnel_id and value are required")
