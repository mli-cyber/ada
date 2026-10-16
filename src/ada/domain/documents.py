"""Canonical document metadata extending the Phase 0 intake registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, ClassVar
from uuid import uuid4

from ada.domain.common import CanonicalEntity, FieldPolicy


class DocumentStatus(StrEnum):
    REGISTERED = "REGISTERED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class DocumentPIILevel(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"


@dataclass(frozen=True, kw_only=True)
class DocumentRecord(CanonicalEntity):
    ENTITY_TYPE: ClassVar[str] = "document"
    TABLE: ClassVar[str] = "documents"
    ID_FIELD: ClassVar[str] = "document_id"
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {
        "filename": FieldPolicy.REQUIRED,
        "storage_location": FieldPolicy.REQUIRED,
        "hash": FieldPolicy.REQUIRED,
        "pii_level": FieldPolicy.REQUIRED,
        "uploaded_by": FieldPolicy.REQUIRED,
        "upload_date": FieldPolicy.REQUIRED,
        "status": FieldPolicy.REQUIRED,
        "title": FieldPolicy.DEFAULTABLE,
        "document_type": FieldPolicy.RECOMMENDED,
        "source_system": FieldPolicy.RECOMMENDED,
        "review_request_id": FieldPolicy.OPTIONAL,
    }

    document_id: str = field(default_factory=lambda: str(uuid4()))
    filename: str
    storage_location: str
    hash: str
    pii_level: DocumentPIILevel
    uploaded_by: str
    upload_date: datetime
    status: DocumentStatus = DocumentStatus.REGISTERED
    review_request_id: str | None = None
    title: str | None = None
    document_type: str | None = None
    source_system: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        required = (
            self.document_id,
            self.filename,
            self.storage_location,
            self.hash,
            self.uploaded_by,
        )
        if any(not value.strip() for value in required):
            raise ValueError("document ID, filename, location, hash, and uploader are required")
        if self.upload_date.tzinfo is None:
            raise ValueError("upload_date must be timezone-aware")
