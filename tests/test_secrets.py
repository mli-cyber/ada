from __future__ import annotations

import pytest

from ada.platform.secrets import get_secret


def test_env_secret_resolution() -> None:
    assert get_secret("TOKEN", environ={"TOKEN": "value"}) == "value"


def test_missing_env_secret_raises() -> None:
    with pytest.raises(KeyError):
        get_secret("MISSING", environ={})


def test_unknown_backend_raises() -> None:
    with pytest.raises(ValueError):
        get_secret(
            "TOKEN",
            environ={"TOKEN": "value", "ADA__SECRETS_BACKEND": "unknown"},
        )
