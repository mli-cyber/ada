"""Minimal application-profile bundles used by the Phase 0 shell."""

from __future__ import annotations

from typing import TypedDict

# Terminology mapping is defined per profile in Phase 2. Placeholder keys shown so the
# concept is visible in the scaffold.
KNOWN_PROFILES = ("military", "general")


class ProfileBundle(TypedDict):
    terminology: dict[str, str]
    enabled_domains: tuple[str, ...]
    report_templates: tuple[str, ...]
    defaults: dict[str, str]


_PROFILES: dict[str, ProfileBundle] = {
    "military": {
        "terminology": {
            "organization": "unit",
            "deadline": "suspense",
            "manager": "supervisor",
        },
        "enabled_domains": (
            "personnel",
            "organization",
            "training",
            "due_out",
            "administrative",
            "documents",
        ),
        "report_templates": ("roster", "training_compliance", "due_out_rollup"),
        "defaults": {"reporting_cycle": "monthly"},
    },
    "general": {
        "terminology": {
            "organization": "organization",
            "deadline": "deadline",
            "manager": "manager",
        },
        "enabled_domains": (
            "personnel",
            "organization",
            "training",
            "tasks",
            "administrative",
            "documents",
        ),
        "report_templates": ("roster", "training_compliance", "task_summary"),
        "defaults": {"reporting_cycle": "monthly"},
    },
}


def load_profile(name: str) -> dict[str, object]:
    """Return a copy of a known profile bundle."""

    normalized = name.strip().lower()
    if normalized not in _PROFILES:
        raise ValueError(f"Unknown profile {name!r}; expected one of {', '.join(KNOWN_PROFILES)}")
    profile = _PROFILES[normalized]
    return {
        "name": normalized,
        "terminology": dict(profile["terminology"]),
        "enabled_domains": tuple(profile["enabled_domains"]),
        "report_templates": tuple(profile["report_templates"]),
        "defaults": dict(profile["defaults"]),
    }
