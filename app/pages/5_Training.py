"""Ada - Training page (scaffold).

Roadmap: Phase 10 (Training Requirement Engine).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

st.set_page_config(page_title="Ada - Training", page_icon="A", layout="wide")
st.title("Training")
st.caption("Roadmap: Phase 10 (Training Requirement Engine)")
st.info(
    "Scaffold placeholder. Courses, requirements, records, and compliance status "
    "(COMPLETE/DUE_SOON/OVERDUE/...) are implemented per the roadmap. See "
    "doc/roadmap_v3.md Section 5.3 and Phase 10."
)
