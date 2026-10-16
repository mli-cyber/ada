from __future__ import annotations

import sqlite3

import pytest

from ada.config import AdaConfig
from ada.migrations import MigrationDriftError, MigrationVersionError
from ada.migrations.runner import run_migrations
from ada.migrations.types import Migration
from ada.migrations.v0001_phase0_foundation import MIGRATION as V0001
from ada.platform.db import get_connection, init_db


def test_migrations_record_checksums_and_are_idempotent(phase0_config: AdaConfig) -> None:
    init_db(phase0_config)
    init_db(phase0_config)

    connection = get_connection(phase0_config)
    try:
        rows = connection.execute(
            "SELECT version, name, checksum FROM ada_schema_migrations ORDER BY version"
        ).fetchall()
    finally:
        connection.close()

    assert [(row[0], row[1]) for row in rows] == [
        (1, "phase0_foundation"),
        (2, "canonical_domain"),
    ]
    assert all(len(row[2]) == 64 for row in rows)


def test_phase0_database_upgrades_without_losing_documents(phase0_config: AdaConfig) -> None:
    connection = get_connection(phase0_config)
    connection.executescript(
        """
        CREATE TABLE schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        INSERT INTO schema_version VALUES (1, '2026-01-01T00:00:00+00:00');
        CREATE TABLE documents (
            document_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            storage_location TEXT NOT NULL,
            hash TEXT NOT NULL UNIQUE,
            classification TEXT NOT NULL,
            pii_level TEXT NOT NULL,
            uploaded_by TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            status TEXT NOT NULL,
            review_request_id TEXT
        );
        INSERT INTO documents VALUES (
            'doc-1', 'memo.txt', 'local://memo', 'abc', 'internal', 'internal',
            'tester', '2026-01-01T00:00:00+00:00', 'REGISTERED', NULL
        );
        """
    )
    connection.commit()
    connection.close()

    init_db(phase0_config)

    connection = get_connection(phase0_config)
    try:
        row = connection.execute(
            "SELECT filename, title, version, source_system FROM documents"
        ).fetchone()
    finally:
        connection.close()
    assert tuple(row) == ("memo.txt", "memo.txt", 1, "phase0_intake")


def test_migration_checksum_drift_is_rejected(phase0_config: AdaConfig) -> None:
    init_db(phase0_config)
    connection = get_connection(phase0_config)
    connection.execute(
        "UPDATE ada_schema_migrations SET checksum = ? WHERE version = 1",
        ("0" * 64,),
    )
    connection.commit()
    connection.close()

    with pytest.raises(MigrationDriftError, match="drifted"):
        init_db(phase0_config)


def test_unknown_ahead_version_is_rejected(phase0_config: AdaConfig) -> None:
    init_db(phase0_config)
    connection = get_connection(phase0_config)
    connection.execute(
        """
        INSERT INTO ada_schema_migrations (version, name, checksum, applied_at)
        VALUES (99, 'future', ?, '2026-01-01T00:00:00+00:00')
        """,
        ("f" * 64,),
    )
    connection.commit()
    connection.close()

    with pytest.raises(MigrationVersionError, match="newer than or absent"):
        init_db(phase0_config)


def test_failed_migration_rolls_back_all_schema_changes() -> None:
    connection = sqlite3.connect(":memory:")
    broken = Migration(
        version=2,
        name="broken",
        statements=("CREATE TABLE transient_table (id TEXT PRIMARY KEY)", "NOT VALID SQL"),
    )

    with pytest.raises(sqlite3.OperationalError):
        run_migrations(connection, "sqlite", migrations=(V0001, broken))

    names = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    connection.close()
    assert "transient_table" not in names
    assert "ada_schema_migrations" not in names
