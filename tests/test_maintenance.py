from __future__ import annotations

from pathlib import Path

import pytest

from ada.config import AdaConfig
from ada.platform.db import healthcheck, init_db
from ada.platform.identity import Principal, Role
from ada.platform.maintenance import reset_local
from ada.platform.storage import LocalObjectStore


def test_reset_requires_confirmation_and_admin(phase0_config: AdaConfig) -> None:
    with pytest.raises(ValueError):
        reset_local(phase0_config)
    with pytest.raises(PermissionError):
        reset_local(
            phase0_config,
            confirm=True,
            principal=Principal("viewer@example.test", Role.VIEWER),
        )


def test_reset_clears_and_reinitializes_local_stores(phase0_config: AdaConfig) -> None:
    init_db(phase0_config)
    phase0_config.chroma_path.mkdir(parents=True)
    (phase0_config.chroma_path / "chroma-data").write_text("value")
    LocalObjectStore(phase0_config.object_store_path).put("test.txt", b"value")

    summary = reset_local(phase0_config, confirm=True)
    assert summary["reinitialized"]
    assert healthcheck(phase0_config)
    assert not (phase0_config.chroma_path / "chroma-data").exists()
    assert not (phase0_config.object_store_path / "test.txt").exists()
    assert Path(phase0_config.data_path / "audit" / "audit.jsonl").exists()
