"""Local-first relational database boundary."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ada.config import AdaConfig
from ada.migrations import LATEST_VERSION, run_migrations

SCHEMA_VERSION = LATEST_VERSION


def sqlite_path(db_url: str) -> Path | None:
    if not db_url.startswith("sqlite:///"):
        return None
    value = db_url.removeprefix("sqlite:///")
    if value == ":memory:":
        return None
    return Path(value)


def get_connection(config: AdaConfig) -> Any:
    """Open a DB-API connection selected by ``ADA__DB_URL``."""

    if config.db_url.startswith("sqlite:///"):
        value = config.db_url.removeprefix("sqlite:///")
        if value != ":memory:":
            path = Path(value)
            path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(value)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
    if config.db_url.startswith(("postgresql://", "postgres://")):
        try:
            import psycopg  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "PostgreSQL requires the optional dependency: uv sync --extra postgres"
            ) from exc
        return psycopg.connect(config.db_url)
    raise ValueError("ADA__DB_URL must use sqlite:/// or postgresql://")


def _sql(config: AdaConfig, statement: str) -> str:
    if config.db_backend == "postgresql":
        return statement.replace("?", "%s")
    return statement


def execute(
    connection: Any,
    config: AdaConfig,
    statement: str,
    parameters: Sequence[Any] = (),
) -> Any:
    """Execute platform-owned SQL with portable placeholders."""

    return connection.execute(_sql(config, statement), tuple(parameters))


def init_db(config: AdaConfig) -> None:
    """Upgrade the configured database to the latest immutable schema."""

    connection = get_connection(config)
    try:
        run_migrations(connection, config.db_backend)
    finally:
        connection.close()


def healthcheck(config: AdaConfig) -> bool:
    connection: Any | None = None
    try:
        connection = get_connection(config)
        connection.execute("SELECT 1")
        return True
    except Exception:
        return False
    finally:
        if connection is not None:
            connection.close()
