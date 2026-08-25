"""Structured file ingestion (scaffold stub).

XLSX/XLS/CSV pipeline: parse -> header/section/table detection -> schema mapping ->
validation -> entity resolution -> import preview -> commit. Ingested content is
untrusted data, never instructions. Roadmap: Phase 5.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def preview_import(path: Path) -> dict[str, Any]:
    """Return a non-committing import preview (counts, mappings). Scaffold stub - Phase 5."""

    raise NotImplementedError("Structured ingestion is implemented in roadmap Phase 5.")
