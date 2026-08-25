"""Domain registry (scaffold stub).

Each domain registers schema, entities, relationships, validation rules, permissions,
CRUD tools, report templates, PII classification, vector collections, agent-access
rules, and profile bindings. Roadmap: Phase 2 (Domain Registry and Profiles).
"""

from __future__ import annotations

from typing import Any


class DomainRegistry:
    """Registry allowing new domains without changing the orchestrator. Scaffold stub."""

    def register(self, name: str, spec: dict[str, Any]) -> None:
        raise NotImplementedError("Domain registry is implemented in roadmap Phase 2.")
