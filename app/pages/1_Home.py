"""Ada - Home / Dashboard page (scaffold).

Roadmap: live shell landing; role-aware dashboards arrive with Phases 9-16.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

st.set_page_config(page_title="Ada - Home", page_icon="A", layout="wide")
st.title("Home / Dashboard")
st.caption("Roadmap: shell landing (live); dashboards in Phases 9-16")
st.info(
    "Scaffold placeholder. Role-aware dashboards (my tasks/due-outs, unit due-outs, "
    "training readiness, arrivals/departures, data-quality) are implemented per the "
    "roadmap. See doc/roadmap_v3.md."
)
