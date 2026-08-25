"""Unstructured document ingestion (scaffold stub).

TXT/PDF/DOC/DOCX pipeline: classify -> extract -> chunk -> vector index -> extraction
agent -> canonical records -> validation. Untrusted-content rules strictly enforced;
ingestion never triggers writes without human confirmation. Roadmap: Phase 6.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def ingest_document(path: Path) -> dict[str, Any]:
    """Extract candidate records + evidence from a document. Scaffold stub - Phase 6."""

    raise NotImplementedError("Unstructured ingestion is implemented in roadmap Phase 6.")
