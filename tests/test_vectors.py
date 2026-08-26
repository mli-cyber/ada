from __future__ import annotations

from ada.config import AdaConfig
from ada.platform.vectors import get_collection, healthcheck


def test_chroma_collection_and_healthcheck(phase0_config: AdaConfig) -> None:
    collection = get_collection(phase0_config)
    assert collection.name == phase0_config.chroma_collection
    assert healthcheck(phase0_config)
