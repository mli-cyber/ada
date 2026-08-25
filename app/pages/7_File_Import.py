"""Ada - File Import / Review page (scaffold).

Roadmap: Phase 5 (Structured Ingestion) + Phase 6 (Unstructured Ingestion).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

st.set_page_config(page_title="Ada - File Import", page_icon="A", layout="wide")
st.title("File Import / Review")
st.caption("Roadmap: Phase 5 (XLSX/CSV) + Phase 6 (PDF/DOC/TXT)")
st.info(
    "Scaffold placeholder. Upload -> section/table detection -> schema mapping -> "
    "validation -> import preview -> approve. All ingested content is treated as "
    "untrusted data. See doc/roadmap_v3.md Phases 5-6 and Section 7.1."
)
st.file_uploader(
    "Upload (disabled in scaffold)",
    type=["xlsx", "xls", "csv", "txt", "pdf", "doc", "docx"],
    disabled=True,
)
