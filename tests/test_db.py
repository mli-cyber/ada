from __future__ import annotations

from ada.config import AdaConfig
from ada.platform.db import get_connection, healthcheck, init_db


def test_sqlite_init_is_idempotent(phase0_config: AdaConfig) -> None:
    init_db(phase0_config)
    init_db(phase0_config)
    assert healthcheck(phase0_config)

    connection = get_connection(phase0_config)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        connection.close()
    assert {"schema_version", "documents", "review_requests", "approval_decisions"} <= tables


def test_unknown_database_scheme_is_unhealthy(phase0_config: AdaConfig) -> None:
    bad = AdaConfig.from_env({"ADA__DB_URL": "mysql://localhost/ada"})
    assert not healthcheck(bad)
