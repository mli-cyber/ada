"""Ada - Data Quality / Review Queue page (scaffold).

Roadmap: Phase 8 (Entity Resolution and Data Quality) + Phase 18 (Human Review).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

st.set_page_config(page_title="Ada - Data Quality", page_icon="A", layout="wide")
st.title("Data Quality / Review Queue")
st.caption("Roadmap: Phase 8 (Data Quality) + Phase 18 (Human Review)")
st.info(
    "Scaffold placeholder. Duplicate/conflict detection and the human review/approval "
    "queue for ambiguous or high-impact actions are implemented per the roadmap. See "
    "doc/roadmap_v3.md Phases 8 and 18."
)
