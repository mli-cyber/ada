"""Ada configuration loaded from the environment.

This is one of the few modules with real (non-stub) logic in the initial scaffold:
it loads AWS/Bedrock settings and local paths from ``ADA__*`` and standard ``AWS_*``
environment variables, mirroring the connection pattern used by the AISI IWB project.

Roadmap: Phase 0 (Architecture and Security Foundation).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# Fixed embedding model. Switching embedding models invalidates the existing vector
# space and requires a full reset + re-ingest, so this is intentionally not exposed
# as a user-selectable option (same rationale as IWB).
DEFAULT_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"

# Conservative default chat model. Override with ADA__BEDROCK_CHAT_MODEL_ID.
DEFAULT_CHAT_MODEL = "us.anthropic.claude-sonnet-5"

# Default application profile (see roadmap section 4.3 / Phase 2).
DEFAULT_PROFILE = "military"


def _parse_model_list(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


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

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "AdaConfig":
        values = environ if environ is not None else os.environ

        chat_options = _parse_model_list(values.get("ADA__BEDROCK_CHAT_MODELS"))
        chat_model_id = values.get("ADA__BEDROCK_CHAT_MODEL_ID", DEFAULT_CHAT_MODEL)
        if not chat_options:
            chat_options = (chat_model_id,)

        data_path = Path(values.get("ADA__DATA_PATH", "src/ada/tmp/data"))

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
        )

    def describe(self) -> dict[str, str]:
        """Return a non-secret summary suitable for display in the Streamlit sidebar."""

        return {
            "AWS Region": self.aws_region,
            "AWS Profile": self.aws_profile or "(default credential chain)",
            "Chat Model": self.chat_model_id,
            "Embedding Model": self.embedding_model_id,
            "Profile": self.profile,
        }
