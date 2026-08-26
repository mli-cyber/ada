"""Guarded local reset utility."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any

from ada.config import AdaConfig
from ada.platform.audit import AuditEvent, record_event
from ada.platform.db import init_db, sqlite_path
from ada.platform.identity import Permission, Principal, authorize, current_principal


def _safe_remove(path: Path) -> bool:
    resolved = path.resolve()
    forbidden = {Path("/").resolve(), Path.home().resolve(), Path.cwd().resolve()}
    if resolved in forbidden or len(resolved.parts) < 3:
        raise ValueError(f"Refusing to remove unsafe path: {resolved}")
    if resolved.is_dir():
        shutil.rmtree(resolved)
        return True
    if resolved.exists():
        resolved.unlink()
        return True
    return False


def reset_local(
    config: AdaConfig | None = None,
    *,
    confirm: bool = False,
    principal: Principal | None = None,
) -> dict[str, Any]:
    """Clear local SQLite, Chroma, and object storage, then reinitialize."""

    if not confirm:
        raise ValueError("Local reset requires explicit confirmation")
    resolved_config = config or AdaConfig.from_env()
    resolved_principal = principal or current_principal(resolved_config)
    if not authorize(resolved_principal.role, Permission.ADMIN):
        raise PermissionError("Local reset requires the admin permission")
    if resolved_config.db_backend != "sqlite":
        raise ValueError("reset_local only supports the local SQLite backend")

    removed: dict[str, bool] = {}
    db_path = sqlite_path(resolved_config.db_url)
    if db_path is not None:
        removed["sqlite"] = _safe_remove(db_path)
    removed["chroma"] = _safe_remove(resolved_config.chroma_path)
    removed["objects"] = _safe_remove(resolved_config.object_store_path)
    init_db(resolved_config)
    record_event(
        AuditEvent(
            user=resolved_principal.user,
            action="RESET_LOCAL",
            entity_type="platform",
            entity_id="local-stores",
            source="maintenance",
            new_value=removed,
        ),
        resolved_config,
    )
    return {"removed": removed, "reinitialized": True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ada local maintenance")
    subparsers = parser.add_subparsers(dest="command", required=True)
    reset = subparsers.add_parser("reset", help="Clear and reinitialize local stores")
    reset.add_argument("--yes", action="store_true", help="Confirm the destructive reset")
    arguments = parser.parse_args(argv)
    if arguments.command == "reset":
        if not arguments.yes:
            parser.error("reset requires --yes")
        summary = reset_local(confirm=True)
        print(summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
