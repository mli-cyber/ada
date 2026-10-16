from __future__ import annotations

from ada.config import AdaConfig
from ada.domain import AdministrativeAction, Personnel, protect_national_identifier
from ada.platform.audit import read_events
from ada.platform.identity import Principal, Role
from ada.platform.review import ApprovalAction, ApprovalDecision, decide_review
from ada.provenance import entity_provenance_refs
from ada.services import CanonicalService


class TestCodec:
    key_id = "service-test-key"
    algorithm = "TEST-ONLY"

    def encrypt(self, plaintext: str) -> str:
        return f"cipher::{plaintext[::-1]}"


def test_secured_crud_creates_audit_provenance_and_state(
    phase0_config: AdaConfig,
) -> None:
    editor = Principal("editor@example.test", Role.EDITOR)
    service = CanonicalService(phase0_config, Personnel, principal=editor)
    result = service.create(
        Personnel(
            employee_number="ADA-101",
            first_name="Avery",
            last_name="Morgan",
            primary_email="avery@example.test",
            national_identifier=protect_national_identifier("123-45-6789", TestCodec()),
        )
    )

    entity_id = str(result.record["personnel_id"])
    assert result.record["primary_email"] == "avery@example.test"
    assert result.record["national_id_last4"] == "[REDACTED]"
    assert result.state.entity_refs[0].entity_id == entity_id
    assert result.state.entity_refs[0].version == 1
    assert result.state.provenance_refs == [result.provenance_ref_id]

    provenance = entity_provenance_refs(
        phase0_config,
        entity_type="personnel",
        entity_id=entity_id,
        entity_version=1,
    )
    assert provenance[0].method == "direct_entry"
    events = read_events(phase0_config)
    assert events[-1].action == "CREATE"
    assert events[-1].entity_version == 1
    assert events[-1].provenance_ref_ids == (result.provenance_ref_id,)

    viewer_service = CanonicalService(
        phase0_config,
        Personnel,
        principal=Principal("viewer@example.test", Role.VIEWER),
    )
    viewed = viewer_service.get(entity_id)
    assert viewed is not None
    assert viewed["first_name"] == "Avery"
    assert viewed["primary_email"] == "[REDACTED]"
    assert viewed["employee_number"] == "[REDACTED]"


def test_viewer_cannot_mutate(phase0_config: AdaConfig) -> None:
    viewer_service = CanonicalService(
        phase0_config,
        Personnel,
        principal=Principal("viewer@example.test", Role.VIEWER),
    )
    try:
        viewer_service.create(Personnel(first_name="Avery", last_name="Morgan"))
    except PermissionError as error:
        assert "create" in str(error)
    else:  # pragma: no cover - explicit authorization assertion
        raise AssertionError("viewer mutation unexpectedly succeeded")


def test_administrative_action_requires_matching_approved_review(
    phase0_config: AdaConfig,
) -> None:
    editor = Principal("editor@example.test", Role.EDITOR)
    personnel_result = CanonicalService(
        phase0_config,
        Personnel,
        principal=editor,
    ).create(Personnel(first_name="Avery", last_name="Morgan"))
    person_id = str(personnel_result.record["personnel_id"])

    service = CanonicalService(
        phase0_config,
        AdministrativeAction,
        principal=editor,
    )
    action = AdministrativeAction(
        personnel_id=person_id,
        action_type="COUNSELING",
        summary="Synthetic administrative action",
    )

    try:
        service.create(action)
    except PermissionError as error:
        assert "approved review" in str(error)
    else:  # pragma: no cover - explicit governance assertion
        raise AssertionError("high-impact mutation unexpectedly bypassed review")

    review = service.request_review(
        action.action_id,
        operation="CREATE",
        reason="High-impact administrative record",
    )
    decide_review(
        phase0_config,
        ApprovalDecision(
            request_id=review.request_id,
            action=ApprovalAction.APPROVE,
            decided_by="approver@example.test",
        ),
    )
    result = service.create(action, review_request_id=review.request_id)
    assert result.review_request_id == review.request_id
    assert result.record["review_request_id"] == review.request_id
