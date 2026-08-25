"""Application profiles (scaffold stub).

A profile swaps terminology, toggles enabled domains/report templates, and supplies
defaults/validation overrides. Ships ``military`` (first) and ``general`` profiles.
Roadmap: Phase 2, Section 4.3.
"""

from __future__ import annotations

# Terminology mapping is defined per profile in Phase 2. Placeholder keys shown so the
# concept is visible in the scaffold.
KNOWN_PROFILES = ("military", "general")


def load_profile(name: str) -> dict[str, object]:
    """Load a profile config bundle by name. Scaffold stub - see roadmap Phase 2."""

    raise NotImplementedError("Profiles are implemented in roadmap Phase 2.")
