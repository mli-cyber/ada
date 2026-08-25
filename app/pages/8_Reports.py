"""Ada - Reports page (scaffold).

Roadmap: Phase 11 (Reporting and Export Framework).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

st.set_page_config(page_title="Ada - Reports", page_icon="A", layout="wide")
st.title("Reports")
st.caption("Roadmap: Phase 11 (Reporting and Export Framework)")
st.info(
    "Scaffold placeholder. Verified datasets export to Screen/XLSX/CSV/TXT/PDF and "
    "secure URLs. See doc/roadmap_v3.md Phase 11."
)
