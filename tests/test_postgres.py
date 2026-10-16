from __future__ import annotations

import os
from dataclasses import replace
from urllib.parse import urlparse

import pytest

from ada.config import AdaConfig
from ada.domain import Personnel, deterministic_id
from ada.persistence import ConcurrencyConflictError, TemporalRepository
from ada.platform.db import get_connection, init_db
from ada.seed import seed_phase1
from ada.services import RollupService

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def postgres_config() -> AdaConfig:
    url = os.environ.get("ADA_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("ADA_TEST_POSTGRES_URL is not configured")
    if urlparse(url).path.strip("/") != "ada_test":
        raise RuntimeError(
            "PostgreSQL compatibility tests require the disposable ada_test database"
        )
    config = AdaConfig.from_env(
        {
            "ADA__DB_URL": url,
            "ADA__DATA_PATH": "/tmp/ada-postgres-test",
            "ADA__DEV_USER": "postgres-test@ada.local",
            "ADA__DEV_ROLE": "admin",
        }
    )
    connection = get_connection(config)
    connection.execute("DROP SCHEMA public CASCADE")
    connection.execute("CREATE SCHEMA public")
    connection.commit()
    connection.close()
    yield config
    connection = get_connection(config)
    connection.execute("DROP SCHEMA public CASCADE")
    connection.execute("CREATE SCHEMA public")
    connection.commit()
    connection.close()


def test_postgres_migrations_seed_temporal_crud_and_rollup(
    postgres_config: AdaConfig,
) -> None:
    init_db(postgres_config)
    init_db(postgres_config)
    first = seed_phase1(postgres_config)
    second = seed_phase1(postgres_config)
    assert first.total_created == 30
    assert second.total_skipped == 30

    repository = TemporalRepository(postgres_config, Personnel)
    person_id = deterministic_id("personnel", "avery-morgan")
    person = repository.get(person_id)
    assert person is not None
    updated = repository.update(
        replace(person, preferred_name="Ave"),
        expected_version=1,
        changed_by="postgres-test@ada.local",
    )
    assert updated.version == 2
    with pytest.raises(ConcurrencyConflictError):
        repository.update(
            replace(person, preferred_name="Stale"),
            expected_version=1,
            changed_by="postgres-test@ada.local",
        )

    root_id = deterministic_id("organization", "ada-command")
    assert RollupService(postgres_config).personnel(root_id).total_personnel == 4
