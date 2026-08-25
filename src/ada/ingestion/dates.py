"""Date normalization service (scaffold stub).

Normalizes Excel serials, YYYYMMDD, MM/DD/YYYY, free-text, and TBD/N/A into typed
fields while always preserving the original source value for provenance. Timezone
handling is explicit. Roadmap: Phase 5, Section 7.7.
"""

from __future__ import annotations

from typing import Any


def normalize_date(raw: Any) -> dict[str, Any]:
    """Return ``{"value": <iso|None>, "original": raw}``. Scaffold stub - Phase 5."""

    raise NotImplementedError("Date normalization is implemented in roadmap Phase 5.")
