"""Ada - Organization / Assignments page (scaffold).

Roadmap: Phase 1 (Canonical Domain Model) + Phase 3 (Conversational CRUD).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

st.set_page_config(page_title="Ada - Organization", page_icon="A", layout="wide")
st.title("Organization / Assignments")
st.caption("Roadmap: Phase 1 (schema) + Phase 3 (conversational CRUD)")
st.info(
    "Scaffold placeholder. Organizations, positions, and assignments are implemented "
    "per the roadmap. See doc/roadmap_v3.md Section 5.2."
)
