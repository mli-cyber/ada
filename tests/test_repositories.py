from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from ada.config import AdaConfig
from ada.domain import DocumentRecord, Personnel, protect_national_identifier
from ada.domain.documents import DocumentPIILevel
from ada.persistence import ConcurrencyConflictError, TemporalRepository


class TestCodec:
    key_id = "repository-test-key"
    algorithm = "TEST-ONLY"

    def encrypt(self, plaintext: str) -> str:
        return f"cipher::{plaintext[::-1]}"


def test_personnel_round_trip_preserves_encrypted_identifier(
    phase0_config: AdaConfig,
) -> None:
    repository = TemporalRepository(phase0_config, Personnel)
    person = repository.create(
        Personnel(
            employee_number="ADA-001",
            first_name="Avery",
            last_name="Morgan",
            national_identifier=protect_national_identifier("123-45-6789", TestCodec()),
            primary_email="avery@example.test",
            created_by="seed",
            updated_by="seed",
        )
    )

    loaded = repository.get(person.personnel_id)
    assert loaded == person
    assert loaded is not None
    assert loaded.national_identifier is not None
    assert loaded.national_identifier.last4 == "6789"


def test_temporal_update_as_of_concurrency_and_soft_delete(
    phase0_config: AdaConfig,
) -> None:
    repository = TemporalRepository(phase0_config, Personnel)
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    person = repository.create(
        Personnel(
            first_name="Avery",
            last_name="Morgan",
            created_at=created_at,
            updated_at=created_at,
            valid_from=created_at,
            created_by="seed",
            updated_by="seed",
        )
    )
    update_at = created_at + timedelta(days=1)
    updated = repository.update(
        replace(person, last_name="Quinn"),
        expected_version=1,
        changed_by="editor@example.test",
        reason="Corrected legal name",
        changed_at=update_at,
    )

    assert updated.version == 2
    assert repository.get(person.personnel_id, as_of=created_at).last_name == "Morgan"  # type: ignore[union-attr]
    assert repository.get(person.personnel_id, as_of=update_at).last_name == "Quinn"  # type: ignore[union-attr]
    history = repository.history(person.personnel_id)
    assert [item.version for item in history] == [1, 2]
    assert history[0].valid_to == update_at

    with pytest.raises(ConcurrencyConflictError) as conflict:
        repository.update(
            replace(person, first_name="Stale"),
            expected_version=1,
            changed_by="editor@example.test",
            changed_at=update_at + timedelta(hours=1),
        )
    assert conflict.value.actual == 2
    assert repository.get(person.personnel_id).first_name == "Avery"  # type: ignore[union-attr]

    delete_at = update_at + timedelta(days=1)
    tombstone = repository.delete(
        person.personnel_id,
        expected_version=2,
        changed_by="editor@example.test",
        reason="Synthetic separation",
        changed_at=delete_at,
    )
    assert tombstone.version == 3
    assert tombstone.deleted_at == delete_at
    assert repository.get(person.personnel_id) is None
    assert repository.get(person.personnel_id, include_deleted=True) == tombstone
    assert repository.get(person.personnel_id, as_of=update_at).version == 2  # type: ignore[union-attr]
    assert repository.list() == []
    assert repository.list(include_deleted=True) == [tombstone]


def test_document_extension_round_trip(phase0_config: AdaConfig) -> None:
    repository = TemporalRepository(phase0_config, DocumentRecord)
    now = datetime.now(UTC)
    document = repository.create(
        DocumentRecord(
            filename="policy.txt",
            storage_location="local://policy",
            hash="sha256-policy",
            pii_level=DocumentPIILevel.INTERNAL,
            uploaded_by="tester@example.test",
            upload_date=now,
            title="Synthetic Policy",
            document_type="policy",
            source_system="phase1_seed",
            metadata={"fixture": True, "format_version": 1},
            created_by="tester@example.test",
            updated_by="tester@example.test",
        )
    )
    assert repository.get(document.document_id) == document
