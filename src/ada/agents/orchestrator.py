"""Orchestrator / intent agent (scaffold stub).

Determines user intent (CREATE, READ, UPDATE, DEACTIVATE, SEARCH, UPLOAD, REPORT,
SCHEMA_CHANGE) and routes to controlled tools/workflows. Runs on AWS Bedrock via
Strands, subject to guardrails and the untrusted-document contract. Roadmap: Phase 3.
"""

from __future__ import annotations

from typing import Any


def route_intent(message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify intent and return a routing decision. Scaffold stub - roadmap Phase 3."""

    raise NotImplementedError("Orchestrator agent is implemented in roadmap Phase 3.")
