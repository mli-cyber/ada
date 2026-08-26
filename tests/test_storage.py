from __future__ import annotations

from pathlib import Path

import pytest

from ada.platform.storage import LocalObjectStore


def test_local_object_store_round_trip(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path / "objects")
    location = store.put("nested/example.txt", b"hello")
    assert location.startswith("file://")
    assert store.exists("nested/example.txt")
    assert store.get("nested/example.txt") == b"hello"
    store.delete("nested/example.txt")
    assert not store.exists("nested/example.txt")


@pytest.mark.parametrize("key", ["", ".", "../escape", "/absolute", r"..\escape"])
def test_local_object_store_rejects_path_traversal(tmp_path: Path, key: str) -> None:
    store = LocalObjectStore(tmp_path / "objects")
    with pytest.raises(ValueError):
        store.put(key, b"unsafe")


def test_seed_document_round_trip(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path / "objects")
    seed = Path("samples/phase0_seed/sample_policy.txt").read_bytes()
    store.put("seed/sample_policy.txt", seed)
    assert store.get("seed/sample_policy.txt") == seed
