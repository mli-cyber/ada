from __future__ import annotations

import pytest

from ada.config import AdaConfig
from ada.platform.audit import read_events
from ada.platform.identity import Principal, Role
from ada.platform.intake import ingest_file, list_documents


def test_file_intake_stores_registers_and_audits(phase0_config: AdaConfig) -> None:
    document_id = ingest_file(
        b"synthetic document",
        filename="../../sample.txt",
        classification="internal",
        pii_level="internal",
        config=phase0_config,
    )
    documents = list_documents(phase0_config)
    assert len(documents) == 1
    assert documents[0].document_id == document_id
    assert documents[0].filename == "sample.txt"
    assert documents[0].storage_location.startswith("file://")
    assert read_events(phase0_config)[0].action == "FILE_INTAKE"

    duplicate_id = ingest_file(
        b"synthetic document",
        filename="duplicate.txt",
        config=phase0_config,
    )
    assert duplicate_id == document_id


def test_file_intake_requires_create_permission(phase0_config: AdaConfig) -> None:
    with pytest.raises(PermissionError):
        ingest_file(
            b"content",
            filename="sample.txt",
            config=phase0_config,
            principal=Principal("viewer@example.test", Role.VIEWER),
        )


@pytest.mark.parametrize(
    ("filename", "classification", "pii_level"),
    [
        ("", "internal", "internal"),
        ("sample.txt", "secret", "internal"),
        ("sample.txt", "internal", "top-secret"),
    ],
)
def test_file_intake_validates_metadata(
    phase0_config: AdaConfig,
    filename: str,
    classification: str,
    pii_level: str,
) -> None:
    with pytest.raises(ValueError):
        ingest_file(
            b"content",
            filename=filename,
            classification=classification,
            pii_level=pii_level,
            config=phase0_config,
        )
