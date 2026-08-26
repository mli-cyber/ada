from __future__ import annotations

from ada.platform.dataguard import FieldDefinition, LLMAccess, guard_fields
from ada.platform.identity import PIITier, Principal, Role


def test_training_context_is_minimum_necessary() -> None:
    record = {
        "name": "Avery Morgan",
        "unit": "HHC",
        "status": "OVERDUE",
        "official_email": "avery.morgan@example.test",
        "ssn": "900-12-3456",
        "home_address": "101 Example Lane",
        "unregistered": "must not pass",
    }
    purposes = frozenset({"training_status"})
    definitions = {
        "name": FieldDefinition(
            "person",
            "name",
            PIITier.PUBLIC,
            llm_access=LLMAccess.ALLOW,
            purposes=purposes,
        ),
        "unit": FieldDefinition(
            "person",
            "unit",
            PIITier.PUBLIC,
            llm_access=LLMAccess.ALLOW,
            purposes=purposes,
        ),
        "status": FieldDefinition(
            "training",
            "status",
            PIITier.INTERNAL,
            llm_access=LLMAccess.ALLOW,
            purposes=purposes,
        ),
        "official_email": FieldDefinition(
            "person",
            "official_email",
            PIITier.INTERNAL,
            llm_access=LLMAccess.MASK,
            purposes=purposes,
            mask_policy="email",
        ),
        "ssn": FieldDefinition(
            "person",
            "ssn",
            PIITier.SENSITIVE,
            llm_access=LLMAccess.DENY,
            purposes=purposes,
        ),
        "home_address": FieldDefinition(
            "person",
            "home_address",
            PIITier.SENSITIVE,
            llm_access=LLMAccess.REDACT,
            purposes=purposes,
        ),
    }
    principal = Principal("approver@example.test", Role.APPROVER)
    guarded = guard_fields(record, "training_status", principal, definitions)
    assert guarded == {
        "name": "Avery Morgan",
        "unit": "HHC",
        "status": "OVERDUE",
        "official_email": "a***@example.test",
        "home_address": "[REDACTED]",
    }
