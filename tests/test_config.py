"""Smoke tests for AdaConfig env loading (scaffold).

These validate the one piece of real logic in the initial scaffold: environment-driven
configuration. They do not touch AWS.
"""

from __future__ import annotations

from pathlib import Path

from ada.config import DEFAULT_EMBEDDING_MODEL, AdaConfig


def test_defaults_without_env() -> None:
    cfg = AdaConfig.from_env({})
    assert cfg.aws_region == "us-east-1"
    assert cfg.aws_profile is None
    assert cfg.embedding_model_id == DEFAULT_EMBEDDING_MODEL
    assert cfg.profile == "military"
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
        }
    )
    assert cfg.aws_region == "us-west-2"
    assert cfg.aws_profile == "ada-dev"
    assert cfg.chat_model_id == "us.anthropic.claude-opus-5"
    assert cfg.chat_model_options == ("a", "b", "c")
    assert cfg.profile == "general"
    assert cfg.data_path == Path("/tmp/ada")


def test_describe_is_non_secret() -> None:
    cfg = AdaConfig.from_env({"AWS_PROFILE": "ada-dev"})
    described = cfg.describe()
    assert described["AWS Profile"] == "ada-dev"
    assert "Chat Model" in described
