"""Canonical organization and hierarchy relationship entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import ClassVar
from uuid import uuid4

from ada.domain.common import CanonicalEntity, FieldPolicy


class OrganizationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISBANDED = "DISBANDED"


class RelationshipType(StrEnum):
    REPORTS_TO = "REPORTS_TO"
    ATTACHED_TO = "ATTACHED_TO"
    SUPPORTED_BY = "SUPPORTED_BY"


@dataclass(frozen=True, kw_only=True)
class Organization(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "organization"
    TABLE: ClassVar[str] = "organizations"
    ID_FIELD: ClassVar[str] = "organization_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "code": FieldPolicy.REQUIRED,
        "name": FieldPolicy.REQUIRED,
        "organization_type": FieldPolicy.REQUIRED,
        "status": FieldPolicy.REQUIRED,
        "short_name": FieldPolicy.RECOMMENDED,
        "description": FieldPolicy.OPTIONAL,
    }

    organization_id: str = field(default_factory=lambda: str(uuid4()))
    code: str
    name: str
    short_name: str | None = None
    organization_type: str
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    description: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.organization_id.strip() or not self.code.strip() or not self.name.strip():
            raise ValueError("organization_id, code, and name are required")
        if not self.organization_type.strip():
            raise ValueError("organization_type is required")


@dataclass(frozen=True, kw_only=True)
class OrganizationRelationship(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "organization_relationship"
    TABLE: ClassVar[str] = "organization_relationships"
    ID_FIELD: ClassVar[str] = "relationship_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "parent_organization_id": FieldPolicy.REQUIRED,
        "child_organization_id": FieldPolicy.REQUIRED,
        "relationship_type": FieldPolicy.REQUIRED,
        "start_date": FieldPolicy.REQUIRED,
        "end_date": FieldPolicy.OPTIONAL,
    }

    relationship_id: str = field(default_factory=lambda: str(uuid4()))
    parent_organization_id: str
    child_organization_id: str
    relationship_type: RelationshipType = RelationshipType.REPORTS_TO
    is_primary: bool = True
    start_date: date
    end_date: date | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.parent_organization_id == self.child_organization_id:
            raise ValueError("an organization cannot be its own parent")
        if not self.parent_organization_id.strip() or not self.child_organization_id.strip():
            raise ValueError("parent and child organization IDs are required")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot precede start_date")
