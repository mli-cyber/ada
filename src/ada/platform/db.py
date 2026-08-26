"""Local-first relational database boundary."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ada.config import AdaConfig

SCHEMA_VERSION = 1


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
    """Create Phase 0 platform tables idempotently."""

    connection = get_connection(config)
    try:
        statements = (
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS review_requests (
                request_id TEXT PRIMARY KEY,
                subject_type TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                requested_by TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS approval_decisions (
                decision_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                action TEXT NOT NULL,
                decided_by TEXT NOT NULL,
                comment TEXT,
                decided_at TEXT NOT NULL,
                FOREIGN KEY (request_id) REFERENCES review_requests(request_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                storage_location TEXT NOT NULL,
                hash TEXT NOT NULL UNIQUE,
                classification TEXT NOT NULL,
                pii_level TEXT NOT NULL,
                uploaded_by TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                status TEXT NOT NULL,
                review_request_id TEXT,
                FOREIGN KEY (review_request_id) REFERENCES review_requests(request_id)
            )
            """,
        )
        for statement in statements:
            connection.execute(statement)
        execute(
            connection,
            config,
            """
            INSERT INTO schema_version (version, applied_at)
            VALUES (?, ?)
            ON CONFLICT (version) DO NOTHING
            """,
            (SCHEMA_VERSION, _utc_now()),
        )
        connection.commit()
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


def _utc_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()
