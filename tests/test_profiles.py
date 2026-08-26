from __future__ import annotations

import pytest

from ada.registry.profiles import load_profile


def test_known_profiles_have_distinct_terminology() -> None:
    military = load_profile("military")
    general = load_profile("general")
    assert military["terminology"] != general["terminology"]
    assert military["name"] == "military"
    assert general["name"] == "general"


def test_unknown_profile_rejected() -> None:
    with pytest.raises(ValueError):
        load_profile("unknown")
