"""Object/document storage (scaffold stub).

Local filesystem by default; S3 adapter for production (``ADA__OBJECT_STORE_*``).
Roadmap: Phase 0 (Architecture and Security Foundation).
"""

from __future__ import annotations


class ObjectStore:
    """Abstract object store. Scaffold stub - concrete adapters land in Phase 0."""

    def put(self, key: str, data: bytes) -> str:
        raise NotImplementedError("Object storage is implemented in roadmap Phase 0.")

    def get(self, key: str) -> bytes:
        raise NotImplementedError("Object storage is implemented in roadmap Phase 0.")
