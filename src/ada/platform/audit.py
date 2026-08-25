"""Audit logging (scaffold stub).

Every important write must create an ``AuditEvent`` (timestamp, user, action, entity,
previous/new value, source, conversation_id, agent, confidence, prompt_version,
change_set_id). Roadmap: Phase 0 (skeleton), Phase 3+ (write auditing), Phase 19.
"""

from __future__ import annotations

from typing import Any


def record_event(event: dict[str, Any]) -> None:
    """Persist an audit event. Scaffold stub - see roadmap Phase 3 / Section 15."""

    raise NotImplementedError("Audit logging is implemented in roadmap Phase 3+.")
