"""Secrets backend boundary."""

from __future__ import annotations

import os

from ada.config import AdaConfig


def get_secret(
    name: str,
    config: AdaConfig | None = None,
    *,
    environ: dict[str, str] | None = None,
) -> str:
    """Resolve a secret without logging or returning backend metadata."""

    resolved_config = config or AdaConfig.from_env(environ)
    backend = resolved_config.secrets_backend
    if backend == "env":
        values = environ if environ is not None else os.environ
        if name not in values:
            raise KeyError(name)
        return values[name]
    if backend == "aws-secrets-manager":
        raise NotImplementedError("AWS Secrets Manager adapter is implemented in Phase 19")
    if backend == "ssm":
        raise NotImplementedError("AWS SSM adapter is implemented in Phase 19")
    raise ValueError(f"Unsupported secrets backend: {backend}")
