"""Administrative workflow engine (scaffold stub).

Durable, resumable, idempotent workflows with human approval and failure isolation
(escalation, in/out-processing, PCS/TDY, onboarding, remediation, access requests).
Roadmap: Phase 12 (engine) and Phase 13 (in/out-processing).
"""

from __future__ import annotations

from typing import Any


def start_workflow(name: str, inputs: dict[str, Any]) -> str:
    """Start a durable workflow and return its run id. Scaffold stub - Phase 12."""

    raise NotImplementedError("Workflow engine is implemented in roadmap Phase 12.")
