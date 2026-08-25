"""Entity resolution and data-quality detection (scaffold stub).

Clusters likely-same entities (ID/email/org/position/name similarity) and detects
duplicates, conflicts, unknown references, invalid dates, and orphaned records. Flags
rather than silently overwriting. Roadmap: Phase 8.
"""

from __future__ import annotations

from typing import Any


def detect_issues(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a list of data-quality issues. Scaffold stub - see roadmap Phase 8."""

    raise NotImplementedError("Data-quality engine is implemented in roadmap Phase 8.")
