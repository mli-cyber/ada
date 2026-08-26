"""Object/document storage adapters."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Protocol, runtime_checkable

from ada.config import AdaConfig


@runtime_checkable
class ObjectStore(Protocol):
    def put(self, key: str, data: bytes) -> str: ...
    def get(self, key: str) -> bytes:
        ...

    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...
    def url(self, key: str) -> str: ...


class LocalObjectStore:
    """Atomic, path-traversal-safe filesystem object store."""

    def __init__(self, base_path: Path | str) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        normalized = PurePosixPath(key.replace("\\", "/"))
        if (
            not key
            or not normalized.parts
            or normalized.is_absolute()
            or ".." in normalized.parts
        ):
            raise ValueError(f"Unsafe object key: {key!r}")
        path = (self.base_path / Path(*normalized.parts)).resolve()
        base = self.base_path.resolve()
        if path != base and base not in path.parents:
            raise ValueError(f"Unsafe object key: {key!r}")
        return path

    def put(self, key: str, data: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".ada-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, path)
        except Exception:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise
        return self.url(key)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def url(self, key: str) -> str:
        return self._path(key).as_uri()


class S3ObjectStore:
    """Production adapter contract; implementation is deferred to Phase 19."""

    def _deferred(self) -> None:
        raise NotImplementedError("S3ObjectStore is implemented during Phase 19 hardening")

    def put(self, key: str, data: bytes) -> str:
        self._deferred()
        return ""  # pragma: no cover

    def get(self, key: str) -> bytes:
        self._deferred()
        return b""  # pragma: no cover

    def delete(self, key: str) -> None:
        self._deferred()

    def exists(self, key: str) -> bool:
        self._deferred()
        return False  # pragma: no cover

    def url(self, key: str) -> str:
        self._deferred()
        return ""  # pragma: no cover


def get_object_store(config: AdaConfig) -> ObjectStore:
    return LocalObjectStore(config.object_store_path)


def healthcheck(config: AdaConfig) -> bool:
    try:
        store = get_object_store(config)
        key = ".healthcheck"
        store.put(key, b"ok")
        healthy = store.get(key) == b"ok"
        store.delete(key)
        return healthy
    except Exception:
        return False
