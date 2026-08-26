"""Smoke tests for AdaConfig env loading (scaffold).

These validate the one piece of real logic in the initial scaffold: environment-driven
configuration. They do not touch AWS.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ada.config import DEFAULT_EMBEDDING_MODEL, AdaConfig


def test_defaults_without_env() -> None:
    cfg = AdaConfig.from_env({})
    assert cfg.aws_region == "us-east-1"
    assert cfg.aws_profile is None
    assert cfg.embedding_model_id == DEFAULT_EMBEDDING_MODEL
    assert cfg.profile == "military"
    assert cfg.db_backend == "sqlite"
    assert cfg.active_tier == "balanced"
    assert cfg.active_chat_model == cfg.models_balanced[0]
    assert cfg.dev_role == "admin"
    # A single configured chat model becomes the sole switch option.
    assert cfg.chat_model_options == (cfg.chat_model_id,)


def test_env_overrides() -> None:
    cfg = AdaConfig.from_env(
        {
            "AWS_REGION": "us-west-2",
            "AWS_PROFILE": "ada-dev",
            "ADA__BEDROCK_CHAT_MODEL_ID": "us.anthropic.claude-opus-5",
            "ADA__BEDROCK_CHAT_MODELS": "a, b ,c",
            "ADA__PROFILE": "general",
            "ADA__DATA_PATH": "/tmp/ada",
            "ADA__DB_URL": "postgresql://localhost/ada",
            "ADA__MODEL_TIER": "economy",
            "ADA__MODELS_ECONOMY": "economy-primary,economy-fallback",
            "ADA__DEV_ROLE": "viewer",
        }
    )
    assert cfg.aws_region == "us-west-2"
    assert cfg.aws_profile == "ada-dev"
    assert cfg.chat_model_id == "us.anthropic.claude-opus-5"
    assert cfg.chat_model_options == ("a", "b", "c")
    assert cfg.profile == "general"
    assert cfg.data_path == Path("/tmp/ada")
    assert cfg.db_backend == "postgresql"
    assert cfg.active_chat_model == "economy-primary"
    assert cfg.dev_role == "viewer"


def test_describe_is_non_secret() -> None:
    cfg = AdaConfig.from_env({"AWS_PROFILE": "ada-dev"})
    described = cfg.describe()
    aws_described = cfg.describe_aws()
    assert "AWS Profile" not in described
    assert "AWS Region" not in described
    assert aws_described["AWS Profile"] == "ada-dev"
    assert "Chat Model" in described
    assert "Model Tier" in described
    assert "Database" in described
    assert not any("secret" in key.lower() for key in described)
    assert not any("secret" in key.lower() for key in aws_described)


def test_invalid_model_tier_rejected() -> None:
    with pytest.raises(ValueError):
        AdaConfig.from_env({"ADA__MODEL_TIER": "free"})
