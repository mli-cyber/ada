"""Deterministic identity, authorization, and field-level PII controls."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ada.config import AdaConfig


class Role(StrEnum):
    VIEWER = "viewer"
    EDITOR = "editor"
    APPROVER = "approver"
    ADMIN = "admin"


class Permission(StrEnum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DEACTIVATE = "deactivate"
    APPROVE = "approve"
    EXPORT = "export"
    BULK_WRITE = "bulk_write"
    ADMIN = "admin"


class PIITier(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: frozenset({Permission.READ}),
    Role.EDITOR: frozenset(
        {
            Permission.READ,
            Permission.CREATE,
            Permission.UPDATE,
            Permission.DEACTIVATE,
            Permission.EXPORT,
        }
    ),
    Role.APPROVER: frozenset(
        {
            Permission.READ,
            Permission.CREATE,
            Permission.UPDATE,
            Permission.DEACTIVATE,
            Permission.APPROVE,
            Permission.EXPORT,
            Permission.BULK_WRITE,
        }
    ),
    Role.ADMIN: frozenset(Permission),
}

ROLE_PII_ACCESS: dict[Role, frozenset[PIITier]] = {
    Role.VIEWER: frozenset({PIITier.PUBLIC}),
    Role.EDITOR: frozenset({PIITier.PUBLIC, PIITier.INTERNAL}),
    Role.APPROVER: frozenset(PIITier),
    Role.ADMIN: frozenset(PIITier),
}


@dataclass(frozen=True)
class Principal:
    user: str
    role: Role


def _role(role: Role | str) -> Role:
    return role if isinstance(role, Role) else Role(role.lower())


def _permission(permission: Permission | str) -> Permission:
    return permission if isinstance(permission, Permission) else Permission(permission.lower())


def authorize(role: Role | str, permission: Permission | str) -> bool:
    """Return a deterministic role × permission decision."""

    try:
        return _permission(permission) in ROLE_PERMISSIONS[_role(role)]
    except ValueError:
        return False


def current_principal(config: AdaConfig) -> Principal:
    try:
        role = Role(config.dev_role)
    except ValueError as exc:
        raise ValueError(f"Invalid ADA__DEV_ROLE: {config.dev_role!r}") from exc
    return Principal(user=config.dev_user, role=role)


def can_access_field(role: Role | str, tier: PIITier | str) -> bool:
    try:
        resolved_tier = tier if isinstance(tier, PIITier) else PIITier(tier.lower())
        return resolved_tier in ROLE_PII_ACCESS[_role(role)]
    except ValueError:
        return False


def filter_record(
    record: dict[str, Any],
    role: Role | str,
    field_tiers: dict[str, PIITier | str],
    *,
    redacted_value: str = "[REDACTED]",
) -> dict[str, Any]:
    """Return a copy with fields above the role's PII tier redacted."""

    return {
        field: (
            value
            if can_access_field(role, field_tiers.get(field, PIITier.SENSITIVE))
            else redacted_value
        )
        for field, value in record.items()
    }


def authenticate_oidc(*args: Any, **kwargs: Any) -> Principal:
    raise NotImplementedError("Application-user OIDC is implemented in Phase 19")
