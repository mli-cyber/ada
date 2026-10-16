"""Shared canonical entity, field-policy, validation, and identifier contracts."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import UTC, datetime
from enum import StrEnum
from typing import ClassVar, Protocol
from uuid import UUID, uuid5

ADA_UUID_NAMESPACE = UUID("9f9e3a26-0dd8-5df2-a51f-df42f7095084")


def utc_now() -> datetime:
    return datetime.now(UTC)


def deterministic_id(entity_type: str, natural_key: str) -> str:
    """Return a reproducible UUIDv5 for fixtures and idempotent imports."""

    normalized_type = entity_type.strip().lower()
    normalized_key = natural_key.strip().lower()
    if not normalized_type or not normalized_key:
        raise ValueError("entity_type and natural_key are required")
    return str(uuid5(ADA_UUID_NAMESPACE, f"{normalized_type}:{normalized_key}"))


class Classification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"


class FieldPolicy(StrEnum):
    REQUIRED = "REQUIRED"
    RECOMMENDED = "RECOMMENDED"
    OPTIONAL = "OPTIONAL"
    DEFAULTABLE = "DEFAULTABLE"


class ValidationSeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    code: str
    message: str
    severity: ValidationSeverity


@dataclass(frozen=True, kw_only=True)
class CanonicalEntity:
    """Lifecycle metadata shared by every mutable canonical entity."""

    ENTITY_TYPE: ClassVar[str]
    TABLE: ClassVar[str]
    ID_FIELD: ClassVar[str]
    FIELD_POLICIES: ClassVar[dict[str, FieldPolicy]] = {}

    version: int = 1
    classification: Classification = Classification.INTERNAL
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    valid_from: datetime = field(default_factory=utc_now)
    valid_to: datetime | None = None
    deleted_at: datetime | None = None
    created_by: str = "system"
    updated_by: str = "system"

    @property
    def entity_id(self) -> str:
        return str(getattr(self, self.ID_FIELD))

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("version must be at least 1")
        if not self.created_by.strip() or not self.updated_by.strip():
            raise ValueError("created_by and updated_by are required")
        for name in ("created_at", "updated_at", "valid_from", "valid_to", "deleted_at"):
            value = getattr(self, name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
def validate_field_policy(entity: CanonicalEntity) -> tuple[ValidationIssue, ...]:
    """Evaluate required/recommended fields without mutating source values."""

    known_fields = {item.name for item in fields(entity)}
    issues: list[ValidationIssue] = []
    for name, policy in entity.FIELD_POLICIES.items():
        if name not in known_fields:
            raise ValueError(f"Unknown field policy {entity.ENTITY_TYPE}.{name}")
        value = getattr(entity, name)
        missing = value is None or (isinstance(value, str) and not value.strip())
        if not missing:
            continue
        if policy is FieldPolicy.REQUIRED:
            issues.append(
                ValidationIssue(
                    field=name,
                    code="required",
                    message=f"{name} is required",
                    severity=ValidationSeverity.ERROR,
                )
            )
        elif policy is FieldPolicy.RECOMMENDED:
            issues.append(
                ValidationIssue(
                    field=name,
                    code="recommended",
                    message=f"{name} is recommended",
                    severity=ValidationSeverity.WARNING,
                )
            )
    return tuple(issues)


@dataclass(frozen=True)
class EncryptedNationalIdentifier:
    """Opaque national-identifier value safe for canonical persistence."""

    ciphertext: str
    last4: str
    key_id: str
    algorithm: str

    def __post_init__(self) -> None:
        if not self.ciphertext.strip():
            raise ValueError("ciphertext is required")
        if len(self.last4) != 4 or not self.last4.isdigit():
            raise ValueError("last4 must contain four digits")
        if not self.key_id.strip() or not self.algorithm.strip():
            raise ValueError("key_id and algorithm are required")


class NationalIdentifierCodec(Protocol):
    """Encryption boundary supplied by a secrets/KMS-backed adapter."""

    key_id: str
    algorithm: str

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a validated identifier without persisting plaintext."""


def protect_national_identifier(
    plaintext: str,
    codec: NationalIdentifierCodec,
) -> EncryptedNationalIdentifier:
    normalized = "".join(character for character in plaintext if character.isdigit())
    if len(normalized) < 4:
        raise ValueError("national identifier must contain at least four digits")
    ciphertext = codec.encrypt(normalized)
    if not ciphertext or ciphertext == normalized or normalized in ciphertext:
        raise ValueError("codec returned plaintext or an unsafe ciphertext")
    return EncryptedNationalIdentifier(
        ciphertext=ciphertext,
        last4=normalized[-4:],
        key_id=codec.key_id,
        algorithm=codec.algorithm,
    )
