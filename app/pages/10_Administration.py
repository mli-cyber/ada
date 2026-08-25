"""Ada - Administration page (scaffold).

Roadmap: Phase 0 (Architecture and Security) + Phase 2 (Domain Registry and Profiles).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ada.config import AdaConfig

st.set_page_config(page_title="Ada - Administration", page_icon="A", layout="wide")
st.title("Administration")
st.caption("Roadmap: Phase 0 (Security) + Phase 2 (Domain Registry and Profiles)")

config = AdaConfig.from_env()
st.subheader("Resolved configuration (non-secret)")
st.table({"Setting": list(config.describe().keys()), "Value": list(config.describe().values())})

st.info(
    "Scaffold placeholder. Users, roles/permissions, PII tiers, domain registry, and "
    "application-profile management are implemented per the roadmap. See "
    "doc/roadmap_v3.md Phases 0 and 2."
)
