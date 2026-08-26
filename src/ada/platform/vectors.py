"""Chroma vector-store boundary."""

from __future__ import annotations

from typing import Any

from ada.config import AdaConfig


def get_client(config: AdaConfig) -> Any:
    import chromadb

    config.chroma_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(config.chroma_path))


def get_collection(config: AdaConfig) -> Any:
    return get_client(config).get_or_create_collection(config.chroma_collection)


def healthcheck(config: AdaConfig) -> bool:
    try:
        client = get_client(config)
        client.heartbeat()
        get_collection(config)
        return True
    except Exception:
        return False
