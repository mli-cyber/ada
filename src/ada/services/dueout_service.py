"""Due-out service (scaffold stub).

Recurring generation, typed responses, canonical status normalization, org/person
assignment, overdue calculation, escalation, and reporting-cycle rollups. Roadmap:
Phase 9 (Due-Out / Suspense Management).
"""

from __future__ import annotations

from typing import Any


def normalize_status(free_text: str) -> str:
    """Map a free-text status update to a canonical status. Scaffold stub - Phase 9."""

    raise NotImplementedError("Due-out service is implemented in roadmap Phase 9.")


def generate_recurring(cycle_id: str) -> list[dict[str, Any]]:
    """Instantiate recurring due-outs for a reporting cycle. Scaffold stub - Phase 9."""

    raise NotImplementedError("Due-out service is implemented in roadmap Phase 9.")
