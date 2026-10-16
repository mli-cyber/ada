from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ada.config import AdaConfig
from ada.domain import Personnel, deterministic_id
from ada.platform.audit import read_events
from ada.platform.demo import (
    DEMO_SUPERUSER_DISPLAY,
    DEMO_SUPERUSER_USER,
    DemoModeError,
    demo_status,
    is_demo_active,
    resolve_demo_principal,
)
from ada.platform.identity import (
    Permission,
    Principal,
    Role,
    authorize,
    current_principal,
)
from ada.seed import seed_phase1
from ada.services import CanonicalService, OrganizationScopeService, RollupService


def _demo_config(tmp_path: Path, **overrides: str) -> AdaConfig:
    demo_dir = tmp_path / "demo"
    env = {
        "ADA__DEMO_DATA_DIR": str(demo_dir),
        "ADA__DATA_PATH": str(demo_dir / "data"),
        "ADA__DB_URL": f"sqlite:///{demo_dir / 'data' / 'ada.db'}",
        "ADA__CHROMA_PATH": str(demo_dir / "chroma"),
        "ADA__OBJECT_STORE_PATH": str(demo_dir / "objects"),
        "ADA__SECRETS_BACKEND": "env",
        "ADA__DEMO_MODE": "1",
    }
    env.update(overrides)
    return AdaConfig.from_env(env)


# 1. Demo mode is disabled by default.
def test_demo_mode_is_disabled_by_default() -> None:
    config = AdaConfig.from_env({})
    assert config.demo_mode is False
    assert is_demo_active(config) is False
    assert resolve_demo_principal(config) is None

    principal = current_principal(config)
    assert principal.user != DEMO_SUPERUSER_USER
    assert principal.role is not Role.DEMO_SUPERUSER


# 2. Demo identity is activated only under approved conditions.
def test_demo_identity_activates_only_when_isolated(tmp_path: Path) -> None:
    isolated = _demo_config(tmp_path)
    assert is_demo_active(isolated) is True
    principal = current_principal(isolated)
    assert principal == Principal(DEMO_SUPERUSER_USER, Role.DEMO_SUPERUSER)

    # Flag set but secrets backend is not the isolated environment backend.
    not_isolated = _demo_config(tmp_path, ADA__SECRETS_BACKEND="aws-secrets-manager")
    assert is_demo_active(not_isolated) is False
    with pytest.raises(DemoModeError):
        resolve_demo_principal(not_isolated)


# 3. The demo principal can exercise all supported demo permissions.
def test_demo_principal_has_every_permission(tmp_path: Path) -> None:
    principal = current_principal(_demo_config(tmp_path))
    assert all(authorize(principal.role, permission) for permission in Permission)


# 4. The demo principal can access synthetic organizations across the demo hierarchy.
def test_demo_principal_accesses_full_demo_hierarchy(tmp_path: Path) -> None:
    config = _demo_config(tmp_path)
    seed_phase1(config)
    principal = current_principal(config)

    root_id = deterministic_id("organization", "ada-command")
    scope = OrganizationScopeService(config, principal=principal)
    organization_ids = scope.organization_ids(root_id)
    assert len(organization_ids) == 4

    rollup = RollupService(config, principal=principal).personnel(root_id)
    assert rollup.total_personnel == 4


# 5. Ordinary users retain their existing role restrictions.
def test_ordinary_users_retain_restrictions() -> None:
    viewer = AdaConfig.from_env({"ADA__DEV_ROLE": "viewer"})
    principal = current_principal(viewer)
    assert principal.role is Role.VIEWER
    assert authorize(principal.role, Permission.READ) is True
    assert authorize(principal.role, Permission.CREATE) is False
    assert authorize(Role.EDITOR, Permission.APPROVE) is False


# Isolation hardening: a dedicated, disposable demo directory is required.
def test_demo_requires_dedicated_demo_directory(tmp_path: Path) -> None:
    config = _demo_config(tmp_path, ADA__DEMO_DATA_DIR="")
    assert config.demo_data_dir is None
    assert is_demo_active(config) is False
    status = demo_status(config)
    assert any("ADA__DEMO_DATA_DIR" in finding for finding in status.findings)
    with pytest.raises(DemoModeError):
        resolve_demo_principal(config)


# Isolation hardening: an existing database outside the demo directory is rejected.
def test_demo_rejects_database_outside_demo_directory(tmp_path: Path) -> None:
    operational = tmp_path / "operational" / "ada.db"
    config = _demo_config(tmp_path, ADA__DB_URL=f"sqlite:///{operational}")
    assert is_demo_active(config) is False
    status = demo_status(config)
    assert any("outside the declared demo directory" in finding for finding in status.findings)
    with pytest.raises(DemoModeError):
        resolve_demo_principal(config)


# Isolation hardening: a symlink that escapes the demo directory is rejected.
def test_demo_rejects_symlink_escaping_demo_directory(tmp_path: Path) -> None:
    demo_dir = tmp_path / "demo"
    (demo_dir / "data").mkdir(parents=True)
    (demo_dir / "chroma").mkdir()
    (demo_dir / "objects").mkdir()
    outside = tmp_path / "operational"
    outside.mkdir()
    escaping_db = demo_dir / "data" / "ada.db"
    escaping_db.symlink_to(outside / "prod.db")

    config = _demo_config(tmp_path, ADA__DB_URL=f"sqlite:///{escaping_db}")
    assert is_demo_active(config) is False
    with pytest.raises(DemoModeError, match="outside the declared demo directory"):
        resolve_demo_principal(config)


# 6. Demo mode cannot access production databases or resources.
def test_demo_mode_rejects_operational_database(tmp_path: Path) -> None:
    config = _demo_config(tmp_path, ADA__DB_URL="postgresql://db.internal/ada_prod")
    assert is_demo_active(config) is False
    status = demo_status(config)
    assert any("SQLite" in finding for finding in status.findings)
    with pytest.raises(DemoModeError, match="operational databases"):
        resolve_demo_principal(config)
    # Fail closed through the shared identity entry point as well.
    with pytest.raises(DemoModeError):
        current_principal(config)


# 7. Demo sessions cannot escalate into operational accounts.
def test_demo_role_cannot_be_selected_without_demo_mode() -> None:
    config = AdaConfig.from_env({"ADA__DEV_ROLE": "demo_superuser"})
    assert config.demo_mode is False
    with pytest.raises(ValueError, match="verified demo mode"):
        current_principal(config)


def test_demo_principal_is_not_production_admin(tmp_path: Path) -> None:
    principal = current_principal(_demo_config(tmp_path))
    assert principal.role is Role.DEMO_SUPERUSER
    assert principal.role is not Role.ADMIN
    assert principal.user == DEMO_SUPERUSER_USER


# 8. Audit records identify Demo Superuser actions.
def test_audit_identifies_demo_superuser_actions(tmp_path: Path) -> None:
    config = _demo_config(tmp_path)
    principal = current_principal(config)
    service = CanonicalService(config, Personnel, principal=principal)
    result = service.create(Personnel(first_name="Demo", last_name="Person"))

    events = read_events(config)
    create_events = [event for event in events if event.action == "CREATE"]
    assert create_events, "expected a CREATE audit event"
    assert create_events[-1].user == DEMO_SUPERUSER_USER
    assert result.record["first_name"] == "Demo"


# 9. Demo identity persists across Streamlit navigation.
def test_demo_identity_persists_across_pages(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    demo_root = tmp_path / "demo"
    monkeypatch.setenv("ADA__DEMO_DATA_DIR", str(demo_root))
    monkeypatch.setenv("ADA__DATA_PATH", str(demo_root / "data"))
    monkeypatch.setenv("ADA__DB_URL", f"sqlite:///{demo_root / 'data' / 'ada.db'}")
    monkeypatch.setenv("ADA__CHROMA_PATH", str(demo_root / "chroma"))
    monkeypatch.setenv("ADA__OBJECT_STORE_PATH", str(demo_root / "objects"))
    monkeypatch.setenv("ADA__SECRETS_BACKEND", "env")
    monkeypatch.setenv("ADA__DEMO_MODE", "1")
    seed_phase1(AdaConfig.from_env())

    repository_root = Path(__file__).resolve().parents[1]
    personnel = AppTest.from_file(repository_root / "app/pages/3_Personnel.py").run(timeout=30)
    organization = AppTest.from_file(
        repository_root / "app/pages/4_Organization.py"
    ).run(timeout=30)

    assert not personnel.exception
    assert not organization.exception
    assert any(
        DEMO_SUPERUSER_DISPLAY in warning.value for warning in personnel.warning
    )
    assert any(
        DEMO_SUPERUSER_DISPLAY in warning.value for warning in organization.warning
    )


# 10. Existing authorization regression tests still pass.
def test_existing_authorization_matrix_is_unchanged() -> None:
    assert authorize(Role.VIEWER, Permission.READ) is True
    assert authorize(Role.VIEWER, Permission.CREATE) is False
    assert authorize(Role.EDITOR, Permission.UPDATE) is True
    assert authorize(Role.EDITOR, Permission.APPROVE) is False
    assert authorize(Role.APPROVER, Permission.APPROVE) is True
    assert authorize(Role.ADMIN, Permission.ADMIN) is True
    # Default development identity is unaffected by the new role.
    assert current_principal(AdaConfig.from_env({})).role is Role.ADMIN
