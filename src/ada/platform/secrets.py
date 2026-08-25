"""Secrets backend (scaffold stub).

Supports env (default), AWS Secrets Manager, or SSM via ``ADA__SECRETS_BACKEND``.
Roadmap: Phase 0 (Architecture and Security Foundation).
"""

from __future__ import annotations


def get_secret(name: str) -> str:
    """Resolve a secret by name. Scaffold stub - see roadmap Phase 0."""

    raise NotImplementedError("Secrets resolution is implemented in roadmap Phase 0.")
