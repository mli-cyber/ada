from __future__ import annotations

from pathlib import Path

import pytest

from ada.config import AdaConfig


@pytest.fixture
def phase0_config(tmp_path: Path) -> AdaConfig:
    return AdaConfig.from_env(
        {
            "ADA__DATA_PATH": str(tmp_path / "data"),
            "ADA__DB_URL": f"sqlite:///{tmp_path / 'data' / 'ada.db'}",
            "ADA__CHROMA_PATH": str(tmp_path / "chroma"),
            "ADA__CHROMA_COLLECTION": "test-collection",
            "ADA__OBJECT_STORE_PATH": str(tmp_path / "objects"),
            "ADA__DEV_USER": "tester@example.test",
            "ADA__DEV_ROLE": "admin",
        }
    )
