"""Report exporters (scaffold stub).

Exports verified result datasets to Screen/XLSX/CSV/TXT/PDF and secure URLs. The
generator uses verified datasets, never LLM-regenerated values. Roadmap: Phase 11.
"""

from __future__ import annotations

from typing import Any

EXPORT_FORMATS = ("screen", "xlsx", "csv", "txt", "pdf")


def export(dataset: list[dict[str, Any]], fmt: str) -> bytes:
    """Export a verified dataset to ``fmt``. Scaffold stub - see roadmap Phase 11."""

    raise NotImplementedError("Report exporters are implemented in roadmap Phase 11.")
