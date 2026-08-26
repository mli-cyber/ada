"""Minimum-necessary field gating before data reaches an LLM."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import StrEnum
from typing import Any

from ada.platform.identity import PIITier, Principal, can_access_field


class LLMAccess(StrEnum):
    ALLOW = "ALLOW"
    MASK = "MASK"
    REDACT = "REDACT"
    DENY = "DENY"


@dataclass(frozen=True)
class FieldDefinition:
    entity: str
    field: str
    sensitivity: PIITier
    pii_category: str | None = None
    llm_access: LLMAccess = LLMAccess.DENY
    purposes: frozenset[str] = dataclass_field(default_factory=frozenset)
    mask_policy: str = "last4"
    export_policy: str = "role_based"
    audit_policy: str = "access"


def _mask(value: Any, policy: str) -> str:
    text = str(value)
    if not text:
        return ""
    if policy == "email" and "@" in text:
        local, domain = text.split("@", 1)
        return f"{local[:1]}***@{domain}"
    if policy == "phone":
        digits = "".join(character for character in text if character.isdigit())
        return f"***-***-{digits[-4:]}" if digits else "[MASKED]"
    if policy == "fixed":
        return "[MASKED]"
    return f"***{text[-4:]}" if len(text) > 4 else "[MASKED]"


def decision_for(
    definition: FieldDefinition,
    purpose: str,
    principal: Principal,
) -> LLMAccess:
    if not can_access_field(principal.role, definition.sensitivity):
        return LLMAccess.DENY
    if definition.purposes and purpose not in definition.purposes:
        return LLMAccess.DENY
    return definition.llm_access


def guard_fields(
    record: dict[str, Any],
    purpose: str,
    principal: Principal,
    definitions: dict[str, FieldDefinition],
) -> dict[str, Any]:
    """Return a deny-by-default, minimum-necessary model-context record."""

    guarded: dict[str, Any] = {}
    for name, value in record.items():
        definition = definitions.get(name)
        if definition is None:
            continue
        decision = decision_for(definition, purpose, principal)
        if decision is LLMAccess.ALLOW:
            guarded[name] = value
        elif decision is LLMAccess.MASK:
            guarded[name] = _mask(value, definition.mask_policy)
        elif decision is LLMAccess.REDACT:
            guarded[name] = "[REDACTED]"
    return guarded
