"""Ada - AI Assistant page (scaffold).

Roadmap: Phase 3+ (Conversational CRUD / Query). The live chat product is intentionally
not wired in this scaffold; the Bedrock client methods are stubs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

st.set_page_config(page_title="Ada - AI Assistant", page_icon="A", layout="wide")
st.title("AI Assistant")
st.caption("Roadmap: Phase 3+ (Conversational CRUD and Natural-Language Query)")

st.warning(
    "Phase 3+ - not implemented. The conversational assistant is not wired in this "
    "scaffold build. The AWS Bedrock client boundary exists (src/ada/bedrock.py) but "
    "its chat/embed methods are stubs until the relevant roadmap phases."
)

st.chat_input("Assistant is disabled in the scaffold build", disabled=True)
