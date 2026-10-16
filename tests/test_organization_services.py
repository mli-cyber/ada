from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from ada.config import AdaConfig
from ada.domain import (
    Organization,
    OrganizationRelationship,
    Personnel,
    PersonnelAssignment,
    TrainingCourse,
    TrainingRequirement,
)
from ada.domain.personnel import AssignmentType
from ada.platform.identity import Principal, Role
from ada.services import (
    CanonicalService,
    OrganizationHierarchyService,
    OrganizationScopeService,
    RollupService,
)


@pytest.fixture
def organization_graph(
    phase0_config: AdaConfig,
) -> tuple[Principal, Organization, Organization, Organization]:
    editor = Principal("editor@example.test", Role.EDITOR)
    organizations = CanonicalService(
        phase0_config,
        Organization,
        principal=editor,
    )
    root = Organization(code="ADA", name="Ada Command", organization_type="COMMAND")
    child = Organization(code="OPS", name="Operations", organization_type="DIRECTORATE")
    team = Organization(code="OPS-A", name="Operations Team A", organization_type="TEAM")
    for organization in (root, child, team):
        organizations.create(organization)

    hierarchy = OrganizationHierarchyService(phase0_config, principal=editor)
    hierarchy.add_relationship(
        OrganizationRelationship(
            parent_organization_id=root.organization_id,
            child_organization_id=child.organization_id,
            start_date=date(2020, 1, 1),
        )
    )
    hierarchy.add_relationship(
        OrganizationRelationship(
            parent_organization_id=child.organization_id,
            child_organization_id=team.organization_id,
            start_date=date(2020, 1, 1),
        )
    )
    return editor, root, child, team


def test_hierarchy_scope_tree_and_cycle_prevention(
    phase0_config: AdaConfig,
    organization_graph: tuple[Principal, Organization, Organization, Organization],
) -> None:
    editor, root, child, team = organization_graph
    hierarchy = OrganizationHierarchyService(phase0_config, principal=editor)

    assert hierarchy.parent(team.organization_id).organization_id == child.organization_id  # type: ignore[union-attr]
    assert hierarchy.ancestor_ids(team.organization_id) == (
        child.organization_id,
        root.organization_id,
    )
    assert set(hierarchy.descendant_ids(root.organization_id)) == {
        child.organization_id,
        team.organization_id,
    }
    tree = hierarchy.tree(root.organization_id)
    assert tree.children[0].organization.organization_id == child.organization_id
    assert tree.children[0].children[0].organization.organization_id == team.organization_id

    scope = OrganizationScopeService(phase0_config, principal=editor)
    assert set(scope.organization_ids(root.organization_id)) == {
        root.organization_id,
        child.organization_id,
        team.organization_id,
    }
    assert scope.contains(root.organization_id, team.organization_id)

    with pytest.raises(ValueError, match="cycle"):
        hierarchy.add_relationship(
            OrganizationRelationship(
                parent_organization_id=team.organization_id,
                child_organization_id=root.organization_id,
                start_date=date(2020, 1, 1),
            )
        )


def test_personnel_rollup_deduplicates_and_uses_primary_assignments(
    phase0_config: AdaConfig,
    organization_graph: tuple[Principal, Organization, Organization, Organization],
) -> None:
    editor, root, child, team = organization_graph
    people = CanonicalService(phase0_config, Personnel, principal=editor)
    assignments = CanonicalService(
        phase0_config,
        PersonnelAssignment,
        principal=editor,
    )
    first = Personnel(first_name="Avery", last_name="Morgan")
    second = Personnel(first_name="Jordan", last_name="Quinn")
    people.create(first)
    people.create(second)
    assignments.create(
        PersonnelAssignment(
            personnel_id=first.personnel_id,
            organization_id=child.organization_id,
            start_date=date(2020, 1, 1),
        )
    )
    assignments.create(
        PersonnelAssignment(
            personnel_id=first.personnel_id,
            organization_id=team.organization_id,
            assignment_type=AssignmentType.ADDITIONAL_DUTY,
            is_primary=False,
            start_date=date(2020, 1, 1),
        )
    )
    assignments.create(
        PersonnelAssignment(
            personnel_id=second.personnel_id,
            organization_id=team.organization_id,
            start_date=date(2020, 1, 1),
        )
    )

    rollup = RollupService(phase0_config, principal=editor).personnel(
        root.organization_id,
        as_of=datetime.now(UTC),
    )
    assert rollup.total_personnel == 2
    assert rollup.direct_counts[child.organization_id] == 1
    assert rollup.direct_counts[team.organization_id] == 1
    assert set(rollup.personnel_ids) == {first.personnel_id, second.personnel_id}


def test_closest_training_requirement_wins(
    phase0_config: AdaConfig,
    organization_graph: tuple[Principal, Organization, Organization, Organization],
) -> None:
    editor, root, _, team = organization_graph
    courses = CanonicalService(phase0_config, TrainingCourse, principal=editor)
    requirements = CanonicalService(
        phase0_config,
        TrainingRequirement,
        principal=editor,
    )
    course = TrainingCourse(code="ADA-101", title="Ada Safety")
    courses.create(course)
    root_requirement = TrainingRequirement(
        course_id=course.course_id,
        organization_id=root.organization_id,
        due_within_days=30,
        effective_from=date(2020, 1, 1),
    )
    team_requirement = TrainingRequirement(
        course_id=course.course_id,
        organization_id=team.organization_id,
        due_within_days=7,
        effective_from=date(2020, 1, 1),
    )
    requirements.create(root_requirement)
    requirements.create(team_requirement)

    effective = OrganizationScopeService(
        phase0_config,
        principal=editor,
    ).effective_training_requirements(team.organization_id)
    assert len(effective) == 1
    assert effective[0].requirement_id == team_requirement.requirement_id
    assert effective[0].due_within_days == 7
