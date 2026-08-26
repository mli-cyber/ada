from __future__ import annotations

import pytest

from ada.config import AdaConfig
from ada.platform.review import (
    ApprovalAction,
    ApprovalDecision,
    ReviewRequest,
    ReviewStatus,
    create_review_request,
    decide_review,
    get_review_request,
)


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        (ApprovalAction.APPROVE, ReviewStatus.APPROVED),
        (ApprovalAction.REJECT, ReviewStatus.REJECTED),
        (
            ApprovalAction.RETURN_FOR_CORRECTION,
            ReviewStatus.RETURNED_FOR_CORRECTION,
        ),
    ],
)
def test_review_lifecycle(
    phase0_config: AdaConfig,
    action: ApprovalAction,
    expected: ReviewStatus,
) -> None:
    request = create_review_request(
        phase0_config,
        ReviewRequest(
            subject_type="document",
            subject_id=f"doc-{action.value}",
            requested_by="editor@example.test",
            reason="Check classification",
        ),
    )
    assert get_review_request(phase0_config, request.request_id) == request
    resolved = decide_review(
        phase0_config,
        ApprovalDecision(
            request_id=request.request_id,
            action=action,
            decided_by="approver@example.test",
        ),
    )
    assert resolved.status is expected
    with pytest.raises(ValueError):
        decide_review(
            phase0_config,
            ApprovalDecision(
                request_id=request.request_id,
                action=ApprovalAction.APPROVE,
                decided_by="approver@example.test",
            ),
        )
