"""Ada - Streamlit application shell (scaffold).

Presentation layer only. This entrypoint renders Ada's branding, a home/dashboard
landing view, and a sidebar summarizing the resolved (non-secret) configuration. The
individual pages under ``app/pages/`` are placeholders that state which roadmap phase
implements them.

Architecture rule (see doc/roadmap_v3.md Section 4.1): Streamlit is the presentation
layer, not the business-logic layer. Real logic will live in ``src/ada/services`` and
``src/ada/agents`` and be called from here.

Run with: ./scripts/run_app.sh
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Make ``src/`` importable when running via ``streamlit run`` without installation.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

try:  # dotenv is optional at runtime; ignore if unavailable in a bare environment.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - convenience only
    pass

from ada import __version__
from ada.config import AdaConfig


def _sidebar(config: AdaConfig) -> None:
    st.sidebar.title("Ada")
    st.sidebar.caption("AI-Driven Assistant")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Configuration")
    for key, value in config.describe().items():
        st.sidebar.write(f"**{key}:** `{value}`")
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Scaffold build. Feature pages are placeholders mapped to roadmap phases "
        "(see doc/roadmap_v3.md)."
    )
    st.sidebar.caption(f"v{__version__}")


def main() -> None:
    st.set_page_config(page_title="Ada", page_icon="A", layout="wide")

    config = AdaConfig.from_env()
    _sidebar(config)

    st.title("Ada")
    st.subheader("AI-Driven Assistant for personnel, training & operations")

    st.markdown(
        """
        Ada makes personnel, training, and operational record-keeping easy: talk in
        natural language, upload messy files, and get back clean, structured, auditable
        data and reports.

        **This is a foundation build.** Phase 0 platform/security boundaries are available;
        domain features will be implemented in later roadmap phases.
        """
    )

    st.markdown("### Pages")
    cols = st.columns(3)
    pages = [
        ("Home / Dashboard", "Live"),
        ("AI Assistant", "Phase 3+"),
        ("Personnel", "Phase 1/3"),
        ("Organization / Assignments", "Phase 1/3"),
        ("Training", "Phase 10"),
        ("Due-Outs / Suspenses", "Phase 9"),
        ("Administrative Actions", "Phase 12"),
        ("File Import / Review", "Phase 5/6"),
        ("Reports", "Phase 11"),
        ("Data Quality / Review Queue", "Phase 8/18"),
        ("Administration", "Phase 0/2"),
    ]
    for i, (name, phase) in enumerate(pages):
        with cols[i % 3]:
            st.markdown(f"**{name}**")
            st.caption(phase)

    st.markdown("---")
    st.caption(
        "Use the sidebar page navigation to open a section. See doc/roadmap_v3.md for the "
        "full plan (Phases 0-19)."
    )


if __name__ == "__main__":
    main()
