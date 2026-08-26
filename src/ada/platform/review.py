"""Minimal persistent review and approval primitive."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from ada.config import AdaConfig
from ada.platform.db import execute, get_connection, init_db


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ReviewStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION"


class ApprovalAction(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN_FOR_CORRECTION = "RETURN_FOR_CORRECTION"


@dataclass(frozen=True)
class ReviewRequest:
    subject_type: str
    subject_id: str
    requested_by: str
    reason: str
    request_id: str = field(default_factory=lambda: str(uuid4()))
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ApprovalDecision:
    request_id: str
    action: ApprovalAction
    decided_by: str
    comment: str | None = None
    decision_id: str = field(default_factory=lambda: str(uuid4()))
    decided_at: str = field(default_factory=_now)


def create_review_request(config: AdaConfig, request: ReviewRequest) -> ReviewRequest:
    init_db(config)
    connection = get_connection(config)
    try:
        execute(
            connection,
            config,
            """
            INSERT INTO review_requests (
                request_id, subject_type, subject_id, requested_by, reason,
                status, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.request_id,
                request.subject_type,
                request.subject_id,
                request.requested_by,
                request.reason,
                request.status.value,
                request.created_at,
                request.updated_at,
                json.dumps(request.metadata, sort_keys=True),
            ),
        )
        connection.commit()
        return request
    finally:
        connection.close()


def get_review_request(config: AdaConfig, request_id: str) -> ReviewRequest | None:
    init_db(config)
    connection = get_connection(config)
    try:
        row = execute(
            connection,
            config,
            """
            SELECT request_id, subject_type, subject_id, requested_by, reason,
                   status, created_at, updated_at, metadata_json
            FROM review_requests WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()
        if row is None:
            return None
        return ReviewRequest(
            request_id=row[0],
            subject_type=row[1],
            subject_id=row[2],
            requested_by=row[3],
            reason=row[4],
            status=ReviewStatus(row[5]),
            created_at=row[6],
            updated_at=row[7],
            metadata=json.loads(row[8]),
        )
    finally:
        connection.close()


def decide_review(config: AdaConfig, decision: ApprovalDecision) -> ReviewRequest:
    request = get_review_request(config, decision.request_id)
    if request is None:
        raise KeyError(decision.request_id)
    if request.status is not ReviewStatus.PENDING:
        raise ValueError(f"Review request is already {request.status}")

    status = {
        ApprovalAction.APPROVE: ReviewStatus.APPROVED,
        ApprovalAction.REJECT: ReviewStatus.REJECTED,
        ApprovalAction.RETURN_FOR_CORRECTION: ReviewStatus.RETURNED_FOR_CORRECTION,
    }[decision.action]
    updated_at = _now()
    connection = get_connection(config)
    try:
        execute(
            connection,
            config,
            """
            INSERT INTO approval_decisions (
                decision_id, request_id, action, decided_by, comment, decided_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                decision.decision_id,
                decision.request_id,
                decision.action.value,
                decision.decided_by,
                decision.comment,
                decision.decided_at,
            ),
        )
        execute(
            connection,
            config,
            "UPDATE review_requests SET status = ?, updated_at = ? WHERE request_id = ?",
            (status.value, updated_at, request.request_id),
        )
        connection.commit()
    finally:
        connection.close()
    resolved = get_review_request(config, request.request_id)
    if resolved is None:  # pragma: no cover - database invariant
        raise RuntimeError("Review request disappeared after decision")
    return resolved
