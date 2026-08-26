from __future__ import annotations

from ada.config import AdaConfig
from ada.platform.identity import (
    Permission,
    PIITier,
    Role,
    authorize,
    current_principal,
    filter_record,
)


def test_role_permission_matrix() -> None:
    assert authorize(Role.VIEWER, Permission.READ)
    assert not authorize(Role.VIEWER, Permission.CREATE)
    assert authorize(Role.EDITOR, Permission.UPDATE)
    assert not authorize(Role.EDITOR, Permission.APPROVE)
    assert authorize(Role.APPROVER, Permission.APPROVE)
    assert authorize(Role.ADMIN, Permission.ADMIN)


def test_field_filtering_is_deny_by_default() -> None:
    record = {"name": "Avery", "duty_phone": "555-0101", "home_address": "Example"}
    tiers = {
        "name": PIITier.PUBLIC,
        "duty_phone": PIITier.INTERNAL,
        "home_address": PIITier.SENSITIVE,
    }
    assert filter_record(record, Role.VIEWER, tiers) == {
        "name": "Avery",
        "duty_phone": "[REDACTED]",
        "home_address": "[REDACTED]",
    }
    assert filter_record(record, Role.EDITOR, tiers)["duty_phone"] == "555-0101"
    assert filter_record({"unknown": "secret"}, Role.ADMIN, {})["unknown"] == "secret"


def test_current_principal_from_config() -> None:
    config = AdaConfig.from_env(
        {"ADA__DEV_USER": "user@example.test", "ADA__DEV_ROLE": "approver"}
    )
    principal = current_principal(config)
    assert principal.user == "user@example.test"
    assert principal.role is Role.APPROVER
