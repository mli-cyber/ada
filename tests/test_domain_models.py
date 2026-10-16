from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from ada.domain import (
    Absence,
    AdministrativeAction,
    DocumentRecord,
    DueOut,
    DueOutAssignment,
    Organization,
    OrganizationRelationship,
    Personnel,
    PersonnelAssignment,
    PersonnelContact,
    TrainingCompletion,
    TrainingCourse,
    TrainingRequirement,
    deterministic_id,
    protect_national_identifier,
    validate_field_policy,
)
from ada.domain.documents import DocumentPIILevel
from ada.domain.personnel import ContactType


class TestCodec:
    key_id = "test-key"
    algorithm = "TEST-ONLY"

    def encrypt(self, plaintext: str) -> str:
        return f"cipher::{plaintext[::-1]}"


def test_deterministic_ids_are_stable_and_namespaced() -> None:
    first = deterministic_id("personnel", "ADA-001")
    assert first == deterministic_id("PERSONNEL", "ada-001")
    assert first != deterministic_id("organization", "ada-001")


def test_national_identifier_crosses_encryption_boundary() -> None:
    protected = protect_national_identifier("123-45-6789", TestCodec())
    person = Personnel(
        first_name="Avery",
        last_name="Morgan",
        national_identifier=protected,
    )
    assert protected.last4 == "6789"
    assert "123456789" not in protected.ciphertext
    assert person.national_identifier is protected

    with pytest.raises(TypeError, match="encrypted"):
        Personnel(  # type: ignore[arg-type]
            first_name="Avery",
            last_name="Morgan",
            national_identifier="123-45-6789",
        )


def test_field_policy_returns_structured_recommendations() -> None:
    person = Personnel(first_name="Avery", last_name="Morgan")
    issues = validate_field_policy(person)
    assert {(issue.field, issue.code) for issue in issues} == {
        ("employee_number", "recommended"),
        ("primary_email", "recommended"),
    }


def test_all_phase1_entities_construct_with_canonical_metadata() -> None:
    now = datetime.now(UTC)
    person = Personnel(first_name="Avery", last_name="Morgan")
    organization = Organization(code="HQ", name="Headquarters", organization_type="HQ")
    relationship = OrganizationRelationship(
        parent_organization_id=organization.organization_id,
        child_organization_id="child",
        start_date=date(2026, 1, 1),
    )
    assignment = PersonnelAssignment(
        personnel_id=person.personnel_id,
        organization_id=organization.organization_id,
        start_date=date(2026, 1, 1),
    )
    contact = PersonnelContact(
        personnel_id=person.personnel_id,
        contact_type=ContactType.EMAIL,
        value="avery@example.test",
    )
    course = TrainingCourse(code="ADA-101", title="Ada Basics")
    requirement = TrainingRequirement(
        course_id=course.course_id,
        organization_id=organization.organization_id,
        effective_from=date(2026, 1, 1),
    )
    completion = TrainingCompletion(
        personnel_id=person.personnel_id,
        course_id=course.course_id,
        completed_on=date(2026, 2, 1),
    )
    due_out = DueOut(title="Submit roster", created_by_principal="tester@example.test")
    due_assignment = DueOutAssignment(
        due_out_id=due_out.due_out_id,
        assignee_organization_id=organization.organization_id,
    )
    action = AdministrativeAction(
        personnel_id=person.personnel_id,
        action_type="COUNSELING",
        summary="Synthetic action",
    )
    absence = Absence(
        personnel_id=person.personnel_id,
        absence_type="LEAVE",
        start_at=now,
        end_at=now,
        administrative_action_id=action.action_id,
    )
    document = DocumentRecord(
        filename="memo.txt",
        storage_location="local://memo",
        hash="abc",
        pii_level=DocumentPIILevel.INTERNAL,
        uploaded_by="tester@example.test",
        upload_date=now,
    )

    entities = (
        person,
        organization,
        relationship,
        assignment,
        contact,
        course,
        requirement,
        completion,
        due_out,
        due_assignment,
        action,
        absence,
        document,
    )
    assert all(entity.version == 1 for entity in entities)
    assert len({entity.entity_id for entity in entities}) == len(entities)


def test_invalid_temporal_ranges_are_rejected() -> None:
    with pytest.raises(ValueError, match="end_date"):
        PersonnelAssignment(
            personnel_id="person",
            organization_id="org",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 1, 1),
        )
    with pytest.raises(ValueError, match="exactly one"):
        DueOutAssignment(due_out_id="due")
