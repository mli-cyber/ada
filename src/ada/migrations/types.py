"""Immutable migration contracts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Migration:
    """One ordered, forward-only database migration."""

    version: int
    name: str
    statements: tuple[str, ...]

    @property
    def checksum(self) -> str:
        payload = "\n-- statement --\n".join(
            (str(self.version), self.name, *(statement.strip() for statement in self.statements))
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("Migration versions start at 1")
        if not self.name or not self.name.replace("_", "").isalnum():
            raise ValueError("Migration names use letters, digits, and underscores")
        if not self.statements:
            raise ValueError("A migration must contain at least one statement")
