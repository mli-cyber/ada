"""Append-only local audit logging."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ada.config import AdaConfig

_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class AuditEvent:
    user: str
    action: str
    entity_type: str
    entity_id: str
    source: str
    timestamp: str = field(default_factory=_now)
    previous_value: Any | None = None
    new_value: Any | None = None
    conversation_id: str | None = None
    agent: str | None = None
    confidence: float | None = None
    prompt_version: str | None = None
    change_set_id: str | None = None


def audit_path(config: AdaConfig) -> Path:
    return config.data_path / "audit" / "audit.jsonl"


def record_event(
    event: AuditEvent | dict[str, Any],
    config: AdaConfig | None = None,
) -> None:
    """Append and fsync one JSON event."""

    resolved_config = config or AdaConfig.from_env()
    path = audit_path(resolved_config)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(event) if isinstance(event, AuditEvent) else dict(event)
    with _LOCK, path.open("a", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, default=str, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_events(config: AdaConfig | None = None) -> list[AuditEvent]:
    resolved_config = config or AdaConfig.from_env()
    path = audit_path(resolved_config)
    if not path.exists():
        return []
    events: list[AuditEvent] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(AuditEvent(**json.loads(line)))
    return events
