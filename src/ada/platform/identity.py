"""Identity and authorization boundary (scaffold stub).

Authentication may occur at the UI (OIDC); authorization is enforced here in the
service/tool layer via a role x permission matrix and field-level PII tiers.
Roadmap: Phase 0 (skeleton), Phase 19 (hardening).
"""

from __future__ import annotations


def authorize(user: str, action: str, resource: str) -> bool:
    """Return whether ``user`` may perform ``action`` on ``resource``. Scaffold stub."""

    raise NotImplementedError("Authorization is implemented in roadmap Phase 0/19.")
