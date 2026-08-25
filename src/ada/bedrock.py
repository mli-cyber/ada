"""Ada Bedrock client boundary (scaffold stub).

This module defines the *shape* of Ada's AWS Bedrock integration, mirroring the
connection pattern proven in the AISI IWB project:

    AWS_PROFILE + AWS_REGION
        -> boto3.Session(profile_name=..., region_name=...)
        -> session.client("bedrock-runtime", region_name=...)
        -> strands.models.BedrockModel(...)  ->  strands.Agent(...)

The session/client construction is real so import-time wiring can be validated, but the
product methods (:meth:`AdaBedrockClient.chat`, :meth:`AdaBedrockClient.embed`) are
intentional stubs. They raise ``NotImplementedError`` until the relevant roadmap phase.

Roadmap: Phase 0 (client boundary), Phase 3+ (chat), Phase 6 (embeddings/RAG).

NOTE: Not for production use in this scaffold. No live assistant flow is wired yet.
"""

from __future__ import annotations

from typing import Any

from ada.config import AdaConfig


class AdaBedrockClient:
    """Thin boundary around AWS Bedrock runtime for Ada.

    Construction resolves an AWS session lazily so that unit tests and the Streamlit
    shell can import this module without valid AWS credentials. Call :meth:`connect`
    (or any product method, once implemented) to establish the runtime client.
    """

    def __init__(self, config: AdaConfig) -> None:
        self._config = config
        self._session: Any | None = None
        self._runtime: Any | None = None

    def connect(self) -> None:
        """Construct the boto3 session and bedrock-runtime client.

        Uses ``AWS_PROFILE``/``AWS_REGION`` exactly like IWB. Kept import-safe: boto3 is
        imported here rather than at module load so the scaffold imports cleanly even in
        environments without boto3 configured.
        """

        import boto3  # local import keeps module import cheap and side-effect free

        session_kwargs: dict[str, Any] = {"region_name": self._config.aws_region}
        if self._config.aws_profile:
            session_kwargs["profile_name"] = self._config.aws_profile
        self._session = boto3.Session(**session_kwargs)
        self._runtime = self._session.client(
            "bedrock-runtime", region_name=self._config.aws_region
        )

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Send a chat turn to a Bedrock model and return the reply.

        Roadmap: Phase 3 (Conversational CRUD) wires this into the orchestrator agent
        via Strands ``BedrockModel``/``Agent`` with guardrails and cost/token ceilings.
        """

        raise NotImplementedError(
            "AdaBedrockClient.chat is a scaffold stub; implemented in roadmap Phase 3+."
        )

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Return embeddings for ``texts`` using the fixed Titan embedding model.

        Roadmap: Phase 6 (Unstructured Document Ingestion / RAG).
        """

        raise NotImplementedError(
            "AdaBedrockClient.embed is a scaffold stub; implemented in roadmap Phase 6."
        )
