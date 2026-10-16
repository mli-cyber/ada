"""Controlled Demo Superuser Mode.

Demo mode lets a presenter exercise every implemented feature without ordinary
role restrictions, but only inside a verifiably isolated, synthetic environment.

Safety contract:

- Disabled by default (``ADA__DEMO_MODE`` is false).
- The opt-in flag is necessary but never sufficient: the environment must also be
  verified isolated (local SQLite + environment secrets backend).
- Operational PostgreSQL databases and non-environment secret backends are rejected,
  so demo mode can never run against production data or credentials.
- Resolution fails closed: if demo mode is requested but the environment cannot be
  verified isolated, no principal is issued.
- The demo principal is not a production account; its role is gated and cannot be
  selected through ``ADA__DEV_ROLE``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ada.config import AdaConfig
from ada.platform.db import sqlite_path
from ada.platform.identity import Principal, Role

DEMO_SUPERUSER_USER = "demo_superuser"
DEMO_SUPERUSER_DISPLAY = "Demo Superuser"


class DemoModeError(RuntimeError):
    """Demo mode was requested in an environment that is not verifiably isolated."""


def _within(target: Path, root: Path) -> bool:
    """Return whether ``target`` resolves (symlinks included) inside ``root``.

    ``os.path.realpath`` resolves symlinks across the existing path prefix even when the
    leaf does not yet exist, so a symlink that escapes the demo directory is rejected.
    """

    real_target = Path(os.path.realpath(target))
    return real_target == root or root in real_target.parents


@dataclass(frozen=True)
class DemoStatus:
    """Summary of demo activation and the reasons it is or is not isolated."""

    requested: bool
    active: bool
    user: str
    display_name: str
    findings: tuple[str, ...]


def isolation_findings(config: AdaConfig) -> list[str]:
    """Return reasons the environment is not an isolated demo environment.

    An empty list means the environment is verifiably isolated. This never
    considers the opt-in flag; it only inspects the surrounding environment.
    """

    findings: list[str] = []
    if config.db_backend != "sqlite":
        findings.append(
            f"database backend {config.db_backend!r} is not an isolated local SQLite store; "
            "demo mode refuses to run against operational databases"
        )
    if config.secrets_backend != "env":
        findings.append(
            f"secrets backend {config.secrets_backend!r} may expose production credentials; "
            "demo mode requires the environment secrets backend"
        )

    # A dedicated, disposable location must be declared, and every local store (including
    # the SQLite file) must resolve inside it. This prevents an existing operational
    # SQLite database, a database path override, or a symlink from being selected.
    if config.demo_data_dir is None:
        findings.append(
            "ADA__DEMO_DATA_DIR must declare a dedicated, disposable demo directory"
        )
    else:
        root = Path(os.path.realpath(config.demo_data_dir))
        stores: dict[str, Path] = {
            "data path": config.data_path,
            "chroma path": config.chroma_path,
            "object store path": config.object_store_path,
        }
        if config.db_backend == "sqlite":
            db_file = sqlite_path(config.db_url)
            if db_file is not None:
                stores["database"] = db_file
        for label, target in stores.items():
            if not _within(target, root):
                findings.append(
                    f"{label} {os.path.realpath(target)} is outside the declared demo "
                    f"directory {root}; demo mode refuses shared or operational paths"
                )
    return findings


def verify_demo_isolation(config: AdaConfig) -> None:
    """Raise :class:`DemoModeError` if the environment is not verifiably isolated."""

    findings = isolation_findings(config)
    if findings:
        raise DemoModeError(
            "Demo mode cannot be activated: " + "; ".join(findings)
        )


def is_demo_active(config: AdaConfig) -> bool:
    """Return whether demo mode is both requested and verifiably isolated."""

    return config.demo_mode and not isolation_findings(config)


def demo_principal() -> Principal:
    """Return the dedicated, demonstration-only superuser principal."""

    return Principal(user=DEMO_SUPERUSER_USER, role=Role.DEMO_SUPERUSER)


def resolve_demo_principal(config: AdaConfig) -> Principal | None:
    """Return the demo principal when demo mode is active, else ``None``.

    Fails closed: if demo mode is requested but the environment is not verifiably
    isolated, this raises :class:`DemoModeError` rather than issuing a principal.
    """

    if not config.demo_mode:
        return None
    verify_demo_isolation(config)
    return demo_principal()


def demo_status(config: AdaConfig) -> DemoStatus:
    """Return a UI-friendly summary of the current demo activation state."""

    findings = tuple(isolation_findings(config))
    return DemoStatus(
        requested=config.demo_mode,
        active=config.demo_mode and not findings,
        user=DEMO_SUPERUSER_USER,
        display_name=DEMO_SUPERUSER_DISPLAY,
        findings=findings,
    )
