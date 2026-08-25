"""Ada - Due-Outs / Suspenses page (scaffold).

Roadmap: Phase 9 (Due-Out / Suspense Management) - part of the MVP.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

st.set_page_config(page_title="Ada - Due-Outs", page_icon="A", layout="wide")
st.title("Due-Outs / Suspenses")
st.caption("Roadmap: Phase 9 (Due-Out / Suspense Management) - MVP")
st.info(
    "Scaffold placeholder. The due-out dashboard (reporting-cycle selector, summary "
    "metrics, filters, editable table, evidence, action history, export) is implemented "
    "in Phase 9. See doc/roadmap_v3.md Section 5.6."
)
