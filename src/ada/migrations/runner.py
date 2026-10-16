"""Portable, forward-only migration runner with drift detection."""

from __future__ import annotations

import hmac
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from ada.migrations.types import Migration
from ada.migrations.v0001_phase0_foundation import MIGRATION as V0001
from ada.migrations.v0002_canonical_domain import MIGRATION as V0002

MIGRATIONS = (V0001, V0002)
LATEST_VERSION = MIGRATIONS[-1].version
_POSTGRES_LOCK_ID = 6_506_827_216_684_049_409


class MigrationError(RuntimeError):
    """Base migration failure."""


class MigrationDriftError(MigrationError):
    """An already-applied migration no longer matches its checksum."""


class MigrationVersionError(MigrationError):
    """The database or migration package has an unsupported version sequence."""


def _sql(backend: str, statement: str) -> str:
    return statement.replace("?", "%s") if backend == "postgresql" else statement


def _execute(
    connection: Any,
    backend: str,
    statement: str,
    parameters: tuple[Any, ...] = (),
) -> Any:
    return connection.execute(_sql(backend, statement), parameters)


def _ordered(migrations: Iterable[Migration]) -> tuple[Migration, ...]:
    resolved = tuple(sorted(migrations, key=lambda item: item.version))
    expected = tuple(range(1, len(resolved) + 1))
    actual = tuple(item.version for item in resolved)
    if actual != expected:
        raise MigrationVersionError(
            f"Migration versions must be contiguous from 1; found {actual}"
        )
    names = {item.name for item in resolved}
    if len(names) != len(resolved):
        raise MigrationVersionError("Migration names must be unique")
    return resolved


def _begin_locked(connection: Any, backend: str) -> None:
    if backend == "sqlite":
        connection.execute("BEGIN IMMEDIATE")
        return
    if backend == "postgresql":
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (_POSTGRES_LOCK_ID,))
        return
    raise ValueError(f"Unsupported database backend: {backend}")


def _create_ledger(connection: Any) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS ada_schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )


def _legacy_version(connection: Any, backend: str) -> int | None:
    if backend == "sqlite":
        exists = connection.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'schema_version'
            """
        ).fetchone()
    else:
        exists = connection.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_name = 'schema_version'"
        ).fetchone()
    if exists is None:
        return None
    row = connection.execute("SELECT MAX(version) FROM schema_version").fetchone()
    if row is None or row[0] is None:
        return None
    return int(row[0])


def run_migrations(
    connection: Any,
    backend: str,
    *,
    migrations: Iterable[Migration] = MIGRATIONS,
) -> tuple[int, ...]:
    """Apply pending migrations atomically and return their versions."""

    ordered = _ordered(migrations)
    latest = ordered[-1].version if ordered else 0
    _begin_locked(connection, backend)
    try:
        _create_ledger(connection)
        legacy_version = _legacy_version(connection, backend)
        if legacy_version is not None and legacy_version > latest:
            raise MigrationVersionError(
                f"Database legacy version {legacy_version} is newer than supported {latest}"
            )

        rows = connection.execute(
            """
            SELECT version, name, checksum
            FROM ada_schema_migrations
            ORDER BY version
            """
        ).fetchall()
        known = {migration.version: migration for migration in ordered}
        applied_versions: set[int] = set()
        for row in rows:
            version = int(row[0])
            migration = known.get(version)
            if migration is None:
                raise MigrationVersionError(
                    f"Database migration {version} is newer than or absent from this build"
                )
            if str(row[1]) != migration.name or not hmac.compare_digest(
                str(row[2]), migration.checksum
            ):
                raise MigrationDriftError(
                    f"Applied migration {version:04d}_{row[1]} has drifted"
                )
            applied_versions.add(version)

        if applied_versions and applied_versions != set(range(1, max(applied_versions) + 1)):
            raise MigrationVersionError("Applied migration ledger contains a version gap")

        applied_now: list[int] = []
        for migration in ordered:
            if migration.version in applied_versions:
                continue
            for statement in migration.statements:
                connection.execute(statement)
            applied_at = datetime.now(UTC).isoformat()
            _execute(
                connection,
                backend,
                """
                INSERT INTO schema_version (version, applied_at)
                VALUES (?, ?)
                ON CONFLICT (version) DO NOTHING
                """,
                (migration.version, applied_at),
            )
            _execute(
                connection,
                backend,
                """
                INSERT INTO ada_schema_migrations (
                    version, name, checksum, applied_at
                ) VALUES (?, ?, ?, ?)
                """,
                (migration.version, migration.name, migration.checksum, applied_at),
            )
            applied_now.append(migration.version)
        connection.commit()
        return tuple(applied_now)
    except Exception:
        connection.rollback()
        raise
