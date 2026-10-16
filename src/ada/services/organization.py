"""Organization hierarchy, scope, inherited requirements, and rollup services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time

from ada.config import AdaConfig
from ada.domain.organization import Organization, OrganizationRelationship
from ada.domain.personnel import Personnel, PersonnelAssignment
from ada.domain.training import TrainingRequirement
from ada.persistence import TemporalRepository
from ada.platform.identity import (
    Permission,
    Principal,
    authorize,
    current_principal,
)
from ada.provenance import ProvenanceBundle
from ada.services.canonical import CanonicalService, MutationResult


def _at(value: datetime | None) -> datetime:
    resolved = value or datetime.now(UTC)
    if resolved.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    return resolved


def _date_in_range(value: date, start: date, end: date | None) -> bool:
    return start <= value and (end is None or value <= end)


@dataclass(frozen=True)
class OrganizationNode:
    organization: Organization
    children: tuple[OrganizationNode, ...] = ()


@dataclass(frozen=True)
class PersonnelRollup:
    root_organization_id: str
    as_of: datetime
    organization_ids: tuple[str, ...]
    direct_counts: dict[str, int]
    total_personnel: int
    personnel_ids: tuple[str, ...]


class OrganizationHierarchyService:
    def __init__(
        self,
        config: AdaConfig,
        *,
        principal: Principal | None = None,
    ):
        self.config = config
        self.principal = principal or current_principal(config)
        self.organizations = TemporalRepository(config, Organization)
        self.relationships = TemporalRepository(config, OrganizationRelationship)

    def add_relationship(
        self,
        relationship: OrganizationRelationship,
        *,
        provenance: ProvenanceBundle | None = None,
        reason: str | None = None,
    ) -> MutationResult:
        self._require(Permission.CREATE)
        parent = self.organizations.get(relationship.parent_organization_id)
        child = self.organizations.get(relationship.child_organization_id)
        if parent is None or child is None:
            raise ValueError("parent and child organizations must exist")
        effective_at = max(
            datetime.combine(relationship.start_date, time.min, tzinfo=UTC),
            datetime.now(UTC),
        )
        if relationship.parent_organization_id in self.descendant_ids(
            relationship.child_organization_id,
            as_of=effective_at,
        ):
            raise ValueError("organization relationship would create a cycle")
        if relationship.is_primary:
            existing_parent = self.parent(
                relationship.child_organization_id,
                as_of=effective_at,
            )
            if existing_parent is not None:
                raise ValueError(
                    f"organization already has active primary parent "
                    f"{existing_parent.organization_id}"
                )
        return CanonicalService(
            self.config,
            OrganizationRelationship,
            principal=self.principal,
        ).create(relationship, provenance=provenance, reason=reason)

    def parent(
        self,
        organization_id: str,
        *,
        as_of: datetime | None = None,
    ) -> Organization | None:
        self._require(Permission.READ)
        instant = _at(as_of)
        relationship = next(
            (
                item
                for item in self._active_relationships(instant)
                if item.child_organization_id == organization_id and item.is_primary
            ),
            None,
        )
        if relationship is None:
            return None
        return self.organizations.get(
            relationship.parent_organization_id,
            as_of=instant,
        )

    def children(
        self,
        organization_id: str,
        *,
        as_of: datetime | None = None,
    ) -> tuple[Organization, ...]:
        self._require(Permission.READ)
        instant = _at(as_of)
        child_ids = {
            item.child_organization_id
            for item in self._active_relationships(instant)
            if item.parent_organization_id == organization_id and item.is_primary
        }
        organizations = [
            organization
            for child_id in child_ids
            if (organization := self.organizations.get(child_id, as_of=instant)) is not None
        ]
        return tuple(sorted(organizations, key=lambda item: (item.name, item.organization_id)))

    def ancestor_ids(
        self,
        organization_id: str,
        *,
        as_of: datetime | None = None,
    ) -> tuple[str, ...]:
        self._require(Permission.READ)
        instant = _at(as_of)
        parents = {
            item.child_organization_id: item.parent_organization_id
            for item in self._active_relationships(instant)
            if item.is_primary
        }
        result: list[str] = []
        seen = {organization_id}
        current = organization_id
        while current in parents:
            current = parents[current]
            if current in seen:
                raise RuntimeError("cycle detected in persisted organization hierarchy")
            seen.add(current)
            result.append(current)
        return tuple(result)

    def descendant_ids(
        self,
        organization_id: str,
        *,
        as_of: datetime | None = None,
    ) -> tuple[str, ...]:
        self._require(Permission.READ)
        instant = _at(as_of)
        children: dict[str, set[str]] = {}
        for relationship in self._active_relationships(instant):
            if relationship.is_primary:
                children.setdefault(relationship.parent_organization_id, set()).add(
                    relationship.child_organization_id
                )
        result: list[str] = []
        visited = {organization_id}
        queue = sorted(children.get(organization_id, ()))
        while queue:
            child_id = queue.pop(0)
            if child_id in visited:
                raise RuntimeError("cycle detected in persisted organization hierarchy")
            visited.add(child_id)
            result.append(child_id)
            queue.extend(sorted(children.get(child_id, ())))
        return tuple(result)

    def tree(
        self,
        root_organization_id: str,
        *,
        as_of: datetime | None = None,
    ) -> OrganizationNode:
        self._require(Permission.READ)
        instant = _at(as_of)
        root = self.organizations.get(root_organization_id, as_of=instant)
        if root is None:
            raise ValueError(f"organization {root_organization_id} was not found")

        def build(organization: Organization, ancestors: frozenset[str]) -> OrganizationNode:
            if organization.organization_id in ancestors:
                raise RuntimeError("cycle detected in persisted organization hierarchy")
            next_ancestors = ancestors | {organization.organization_id}
            return OrganizationNode(
                organization=organization,
                children=tuple(
                    build(child, next_ancestors)
                    for child in self.children(
                        organization.organization_id,
                        as_of=instant,
                    )
                ),
            )

        return build(root, frozenset())

    def _active_relationships(
        self,
        as_of: datetime,
    ) -> tuple[OrganizationRelationship, ...]:
        value = as_of.date()
        return tuple(
            relationship
            for relationship in self.relationships.list(as_of=as_of)
            if _date_in_range(value, relationship.start_date, relationship.end_date)
        )

    def _require(self, permission: Permission) -> None:
        if not authorize(self.principal.role, permission):
            raise PermissionError(
                f"{self.principal.role.value} lacks {permission.value} permission"
            )


class OrganizationScopeService:
    def __init__(
        self,
        config: AdaConfig,
        *,
        principal: Principal | None = None,
    ):
        self.config = config
        self.principal = principal or current_principal(config)
        self.hierarchy = OrganizationHierarchyService(config, principal=self.principal)
        self.requirements = TemporalRepository(config, TrainingRequirement)

    def organization_ids(
        self,
        root_organization_id: str,
        *,
        as_of: datetime | None = None,
        include_root: bool = True,
    ) -> tuple[str, ...]:
        instant = _at(as_of)
        descendants = self.hierarchy.descendant_ids(root_organization_id, as_of=instant)
        return (root_organization_id, *descendants) if include_root else descendants

    def contains(
        self,
        root_organization_id: str,
        candidate_organization_id: str,
        *,
        as_of: datetime | None = None,
    ) -> bool:
        return candidate_organization_id in self.organization_ids(
            root_organization_id,
            as_of=as_of,
        )

    def effective_training_requirements(
        self,
        organization_id: str,
        *,
        as_of: datetime | None = None,
    ) -> tuple[TrainingRequirement, ...]:
        instant = _at(as_of)
        ordered_scope = (
            organization_id,
            *self.hierarchy.ancestor_ids(organization_id, as_of=instant),
        )
        distance = {organization: index for index, organization in enumerate(ordered_scope)}
        selected: dict[str, TrainingRequirement] = {}
        for requirement in self.requirements.list(as_of=instant):
            scope_id = requirement.organization_id
            if scope_id is None or scope_id not in distance:
                continue
            if (
                scope_id != organization_id
                and not requirement.inherits_to_descendants
            ):
                continue
            if not _date_in_range(
                instant.date(),
                requirement.effective_from,
                requirement.effective_to,
            ):
                continue
            existing = selected.get(requirement.course_id)
            existing_scope = existing.organization_id if existing is not None else None
            if (
                existing is None
                or existing_scope is None
                or distance[scope_id] < distance[existing_scope]
            ):
                selected[requirement.course_id] = requirement
        return tuple(sorted(selected.values(), key=lambda item: item.course_id))


class RollupService:
    def __init__(
        self,
        config: AdaConfig,
        *,
        principal: Principal | None = None,
    ):
        self.principal = principal or current_principal(config)
        self.scope = OrganizationScopeService(config, principal=self.principal)
        self.assignments = TemporalRepository(config, PersonnelAssignment)
        self.people = TemporalRepository(config, Personnel)

    def personnel(
        self,
        root_organization_id: str,
        *,
        as_of: datetime | None = None,
    ) -> PersonnelRollup:
        if not authorize(self.principal.role, Permission.READ):
            raise PermissionError(f"{self.principal.role.value} lacks read permission")
        instant = _at(as_of)
        organization_ids = self.scope.organization_ids(
            root_organization_id,
            as_of=instant,
        )
        scoped = set(organization_ids)
        active_people = {person.personnel_id for person in self.people.list(as_of=instant)}
        direct: dict[str, set[str]] = {
            organization_id: set() for organization_id in organization_ids
        }
        for assignment in self.assignments.list(as_of=instant):
            if (
                assignment.organization_id in scoped
                and assignment.personnel_id in active_people
                and assignment.is_primary
                and _date_in_range(
                    instant.date(),
                    assignment.start_date,
                    assignment.end_date,
                )
            ):
                direct[assignment.organization_id].add(assignment.personnel_id)
        personnel_ids = tuple(sorted(set().union(*direct.values())))
        return PersonnelRollup(
            root_organization_id=root_organization_id,
            as_of=instant,
            organization_ids=organization_ids,
            direct_counts={
                organization_id: len(personnel)
                for organization_id, personnel in direct.items()
            },
            total_personnel=len(personnel_ids),
            personnel_ids=personnel_ids,
        )
