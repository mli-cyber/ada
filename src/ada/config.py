"""Environment-driven, side-effect-free Ada configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
DEFAULT_CHAT_MODEL = "us.anthropic.claude-sonnet-5"
DEFAULT_PROFILE = "military"
DEFAULT_MODELS_HIGH = (
    "us.anthropic.claude-opus-5",
    "us.anthropic.claude-sonnet-5",
)
DEFAULT_MODELS_BALANCED = (
    "us.anthropic.claude-sonnet-5",
    "us.amazon.nova-pro-v1:0",
    "openai.gpt-oss-120b-1:0",
)
DEFAULT_MODELS_ECONOMY = (
    "us.amazon.nova-pro-v1:0",
    "openai.gpt-oss-120b-1:0",
    "us.meta.llama3-1-70b-instruct-v1:0",
    "mistral.mistral-large-3",
    "google.gemma-3-27b-it",
)
MODEL_TIERS = ("high", "balanced", "economy")


def _parse_model_list(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _int(values: Mapping[str, str], name: str, default: int) -> int:
    value = int(values.get(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True)
class AdaConfig:
    """Resolved Ada configuration.

    All fields resolve from the environment via :meth:`from_env`. Nothing here reaches
    out to AWS; constructing an :class:`AdaConfig` is cheap and side-effect free.
    """

    aws_region: str
    aws_profile: str | None
    chat_model_id: str
    embedding_model_id: str
    chat_model_options: tuple[str, ...]
    profile: str
    chat_temperature: float
    chat_max_tokens: int
    data_path: Path
    chroma_path: Path
    chroma_collection: str
    object_store_path: Path
    db_url: str
    secrets_backend: str
    dev_user: str
    dev_role: str
    max_agent_loops: int
    request_timeout_seconds: int
    model_tier: str
    models_high: tuple[str, ...]
    models_balanced: tuple[str, ...]
    models_economy: tuple[str, ...]
    high_max_tokens: int
    balanced_max_tokens: int
    economy_max_tokens: int
    high_max_agent_loops: int
    balanced_max_agent_loops: int
    economy_max_agent_loops: int

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> AdaConfig:
        values = environ if environ is not None else os.environ

        chat_options = _parse_model_list(values.get("ADA__BEDROCK_CHAT_MODELS"))
        chat_model_id = values.get("ADA__BEDROCK_CHAT_MODEL_ID", DEFAULT_CHAT_MODEL)
        if not chat_options:
            chat_options = (chat_model_id,)

        data_path = Path(values.get("ADA__DATA_PATH", "src/ada/tmp/data"))
        model_tier = values.get("ADA__MODEL_TIER", "balanced").strip().lower()
        if model_tier not in MODEL_TIERS:
            raise ValueError(
                f"ADA__MODEL_TIER must be one of {', '.join(MODEL_TIERS)}; got {model_tier!r}"
            )

        models_high = _parse_model_list(values.get("ADA__MODELS_HIGH")) or DEFAULT_MODELS_HIGH
        models_balanced = (
            _parse_model_list(values.get("ADA__MODELS_BALANCED")) or DEFAULT_MODELS_BALANCED
        )
        models_economy = (
            _parse_model_list(values.get("ADA__MODELS_ECONOMY")) or DEFAULT_MODELS_ECONOMY
        )
        db_url = values.get("ADA__DB_URL") or f"sqlite:///{data_path / 'ada.db'}"

        return cls(
            aws_region=values.get("AWS_REGION", values.get("ADA__AWS_REGION", "us-east-1")),
            aws_profile=values.get("AWS_PROFILE") or None,
            chat_model_id=chat_model_id,
            embedding_model_id=values.get(
                "ADA__BEDROCK_EMBEDDING_MODEL_ID", DEFAULT_EMBEDDING_MODEL
            ),
            chat_model_options=chat_options,
            profile=values.get("ADA__PROFILE", DEFAULT_PROFILE),
            chat_temperature=float(values.get("ADA__CHAT_TEMPERATURE", "0.2")),
            chat_max_tokens=int(values.get("ADA__CHAT_MAX_TOKENS", "8192")),
            data_path=data_path,
            chroma_path=Path(values.get("ADA__CHROMA_PATH", "src/ada/tmp/chroma")),
            chroma_collection=values.get("ADA__CHROMA_COLLECTION", "ada-rag"),
            object_store_path=Path(
                values.get("ADA__OBJECT_STORE_PATH", "src/ada/tmp/objects")
            ),
            db_url=db_url,
            secrets_backend=values.get("ADA__SECRETS_BACKEND", "env").strip().lower(),
            dev_user=values.get("ADA__DEV_USER", "dev@ada.local"),
            dev_role=values.get("ADA__DEV_ROLE", "admin").strip().lower(),
            max_agent_loops=_int(values, "ADA__MAX_AGENT_LOOPS", 8),
            request_timeout_seconds=_int(values, "ADA__REQUEST_TIMEOUT_SECONDS", 30),
            model_tier=model_tier,
            models_high=models_high,
            models_balanced=models_balanced,
            models_economy=models_economy,
            high_max_tokens=_int(values, "ADA__HIGH_MAX_TOKENS", 16384),
            balanced_max_tokens=_int(values, "ADA__BALANCED_MAX_TOKENS", 8192),
            economy_max_tokens=_int(values, "ADA__ECONOMY_MAX_TOKENS", 4096),
            high_max_agent_loops=_int(values, "ADA__HIGH_MAX_AGENT_LOOPS", 12),
            balanced_max_agent_loops=_int(values, "ADA__BALANCED_MAX_AGENT_LOOPS", 8),
            economy_max_agent_loops=_int(values, "ADA__ECONOMY_MAX_AGENT_LOOPS", 5),
        )

    @property
    def active_tier(self) -> str:
        """Return the validated active budget tier."""

        return self.model_tier

    def models_for_tier(self, tier: str | None = None) -> tuple[str, ...]:
        """Return the primary/fallback chain for a tier."""

        resolved = (tier or self.model_tier).lower()
        if resolved not in MODEL_TIERS:
            raise ValueError(f"Unknown model tier: {resolved}")
        return getattr(self, f"models_{resolved}")

    @property
    def active_chat_model(self) -> str:
        """Return the primary model for the active tier."""

        return self.models_for_tier()[0]

    @property
    def db_backend(self) -> str:
        """Return the configured relational database backend."""

        if self.db_url.startswith("sqlite:///"):
            return "sqlite"
        if self.db_url.startswith(("postgresql://", "postgres://")):
            return "postgresql"
        return "unknown"

    def describe(self) -> dict[str, str]:
        """Return a demo-safe summary suitable for general application surfaces."""

        return {
            "Database": self.db_backend,
            "Role": self.dev_role,
            "Model Tier": self.active_tier,
            "Chat Model": self.active_chat_model,
            "Embedding Model": self.embedding_model_id,
            "Profile": self.profile,
        }

    def describe_aws(self) -> dict[str, str]:
        """Return non-secret AWS session identifiers for the dedicated local-only tab."""

        return {
            "AWS Region": self.aws_region,
            "AWS Profile": self.aws_profile or "(default credential chain)",
        }
