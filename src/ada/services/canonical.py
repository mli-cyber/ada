"""Secured canonical CRUD service with audit, review, provenance, and PII controls."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, date, datetime
from enum import Enum
from typing import Any, cast
from uuid import uuid4

from ada.config import AdaConfig
from ada.domain.common import CanonicalEntity, EncryptedNationalIdentifier
from ada.domain.state import AdaState
from ada.persistence import TemporalRepository
from ada.platform.audit import AuditEvent, record_event
from ada.platform.identity import (
    Permission,
    PIITier,
    Principal,
    Role,
    authorize,
    current_principal,
    filter_record,
)
from ada.platform.review import (
    ReviewRequest,
    ReviewStatus,
    create_review_request,
    get_review_request,
)
from ada.provenance import (
    ProvenanceBundle,
    ProvenanceRef,
    SourceRef,
    save_entity_provenance,
)

_REVIEW_REQUIRED_TYPES = frozenset({"administrative_action"})

_BASE_TIERS: dict[str, PIITier | str] = {
    "version": PIITier.INTERNAL,
    "classification": PIITier.PUBLIC,
    "created_at": PIITier.INTERNAL,
    "updated_at": PIITier.INTERNAL,
    "valid_from": PIITier.INTERNAL,
    "valid_to": PIITier.INTERNAL,
    "deleted_at": PIITier.INTERNAL,
    "created_by": PIITier.INTERNAL,
    "updated_by": PIITier.INTERNAL,
}

_ENTITY_FIELD_TIERS: dict[str, dict[str, PIITier | str]] = {
    "personnel": {
        "personnel_id": PIITier.PUBLIC,
        "employee_number": PIITier.INTERNAL,
        "first_name": PIITier.PUBLIC,
        "middle_name": PIITier.INTERNAL,
        "last_name": PIITier.PUBLIC,
        "preferred_name": PIITier.PUBLIC,
        "status": PIITier.PUBLIC,
        "date_of_birth": PIITier.SENSITIVE,
        "national_id_last4": PIITier.SENSITIVE,
        "primary_email": PIITier.INTERNAL,
        "phone": PIITier.INTERNAL,
        "position_title": PIITier.PUBLIC,
        "rank_grade": PIITier.PUBLIC,
        "notes": PIITier.SENSITIVE,
    },
    "personnel_contact": {
        "contact_id": PIITier.INTERNAL,
        "personnel_id": PIITier.INTERNAL,
        "contact_type": PIITier.INTERNAL,
        "value": PIITier.SENSITIVE,
        "label": PIITier.INTERNAL,
        "is_primary": PIITier.INTERNAL,
    },
    "organization": {
        "organization_id": PIITier.PUBLIC,
        "code": PIITier.PUBLIC,
        "name": PIITier.PUBLIC,
        "short_name": PIITier.PUBLIC,
        "organization_type": PIITier.PUBLIC,
        "status": PIITier.PUBLIC,
        "description": PIITier.PUBLIC,
    },
    "organization_relationship": {
        "relationship_id": PIITier.PUBLIC,
        "parent_organization_id": PIITier.PUBLIC,
        "child_organization_id": PIITier.PUBLIC,
        "relationship_type": PIITier.PUBLIC,
        "is_primary": PIITier.PUBLIC,
        "start_date": PIITier.PUBLIC,
        "end_date": PIITier.PUBLIC,
    },
    "document": {
        "document_id": PIITier.PUBLIC,
        "filename": PIITier.PUBLIC,
        "storage_location": PIITier.INTERNAL,
        "hash": PIITier.INTERNAL,
        "pii_level": PIITier.PUBLIC,
        "uploaded_by": PIITier.INTERNAL,
        "upload_date": PIITier.INTERNAL,
        "status": PIITier.PUBLIC,
        "review_request_id": PIITier.INTERNAL,
        "title": PIITier.PUBLIC,
        "document_type": PIITier.PUBLIC,
        "source_system": PIITier.INTERNAL,
        "metadata": PIITier.SENSITIVE,
    },
    "administrative_action": {
        "action_id": PIITier.INTERNAL,
        "personnel_id": PIITier.INTERNAL,
        "action_type": PIITier.INTERNAL,
        "status": PIITier.INTERNAL,
        "effective_from": PIITier.INTERNAL,
        "effective_to": PIITier.INTERNAL,
        "summary": PIITier.SENSITIVE,
        "review_request_id": PIITier.INTERNAL,
    },
}


@dataclass(frozen=True)
class MutationResult:
    record: dict[str, Any]
    state: AdaState
    audit_correlation_id: str
    provenance_ref_id: str
    review_request_id: str | None = None


def _value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, EncryptedNationalIdentifier):
        return value.last4
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _value(item) for key, item in value.items()}
    return value


def _record(entity: CanonicalEntity) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in fields(entity):
        value = getattr(entity, item.name)
        if item.name == "national_identifier":
            result["national_id_last4"] = value.last4 if value is not None else None
        else:
            result[item.name] = _value(value)
    return result


def _attach_review[EntityT: CanonicalEntity](
    entity: EntityT,
    review_request_id: str | None,
) -> EntityT:
    if review_request_id is None or not hasattr(entity, "review_request_id"):
        return entity
    return cast(EntityT, replace(cast(Any, entity), review_request_id=review_request_id))


class CanonicalService[EntityT: CanonicalEntity]:
    """Only application-facing CRUD path for one canonical entity type."""

    def __init__(
        self,
        config: AdaConfig,
        model: type[EntityT],
        *,
        principal: Principal | None = None,
    ):
        self.config = config
        self.model = model
        self.principal = principal or current_principal(config)
        self.repository = TemporalRepository(config, model)

    def get(
        self,
        entity_id: str,
        *,
        as_of: datetime | None = None,
        include_deleted: bool = False,
    ) -> dict[str, Any] | None:
        self._require(Permission.READ)
        entity = self.repository.get(
            entity_id,
            as_of=as_of,
            include_deleted=include_deleted,
        )
        return self._secured_record(entity) if entity is not None else None

    def list(
        self,
        *,
        as_of: datetime | None = None,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        self._require(Permission.READ)
        return [
            self._secured_record(entity)
            for entity in self.repository.list(as_of=as_of, include_deleted=include_deleted)
        ]

    def create(
        self,
        entity: EntityT,
        *,
        provenance: ProvenanceBundle | None = None,
        review_request_id: str | None = None,
        reason: str | None = None,
    ) -> MutationResult:
        self._require(Permission.CREATE)
        self._ensure_review(entity.entity_id, "CREATE", review_request_id)
        now = datetime.now(UTC)
        candidate = replace(
            entity,
            version=1,
            created_at=now,
            updated_at=now,
            valid_from=now,
            valid_to=None,
            deleted_at=None,
            created_by=self.principal.user,
            updated_by=self.principal.user,
        )
        candidate = _attach_review(candidate, review_request_id)
        created = self.repository.create(
            candidate,
            changed_by=self.principal.user,
            reason=reason,
        )
        return self._complete_mutation(
            "CREATE",
            created,
            previous=None,
            expected_version=None,
            provenance=provenance,
            review_request_id=review_request_id,
        )

    def update(
        self,
        entity: EntityT,
        *,
        expected_version: int,
        provenance: ProvenanceBundle | None = None,
        review_request_id: str | None = None,
        reason: str | None = None,
    ) -> MutationResult:
        self._require(Permission.UPDATE)
        self._ensure_review(entity.entity_id, "UPDATE", review_request_id)
        entity = _attach_review(entity, review_request_id)
        previous = self.repository.get(entity.entity_id, include_deleted=True)
        updated = self.repository.update(
            entity,
            expected_version=expected_version,
            changed_by=self.principal.user,
            reason=reason,
        )
        return self._complete_mutation(
            "UPDATE",
            updated,
            previous=previous,
            expected_version=expected_version,
            provenance=provenance,
            review_request_id=review_request_id,
        )

    def delete(
        self,
        entity_id: str,
        *,
        expected_version: int,
        provenance: ProvenanceBundle | None = None,
        review_request_id: str | None = None,
        reason: str | None = None,
    ) -> MutationResult:
        self._require(Permission.DEACTIVATE)
        self._ensure_review(entity_id, "DELETE", review_request_id)
        previous = self.repository.get(entity_id, include_deleted=True)
        deleted = self.repository.delete(
            entity_id,
            expected_version=expected_version,
            changed_by=self.principal.user,
            reason=reason,
        )
        return self._complete_mutation(
            "DELETE",
            deleted,
            previous=previous,
            expected_version=expected_version,
            provenance=provenance,
            review_request_id=review_request_id,
        )

    def request_review(
        self,
        entity_id: str,
        *,
        operation: str,
        reason: str,
        expected_version: int | None = None,
    ) -> ReviewRequest:
        self._require(Permission.CREATE)
        normalized_operation = operation.upper()
        if normalized_operation not in {"CREATE", "UPDATE", "DELETE"}:
            raise ValueError("review operation must be CREATE, UPDATE, or DELETE")
        request = ReviewRequest(
            subject_type=self.model.ENTITY_TYPE,
            subject_id=entity_id,
            requested_by=self.principal.user,
            reason=reason,
            metadata={
                "operation": normalized_operation,
                "expected_version": expected_version,
            },
        )
        created = create_review_request(self.config, request)
        record_event(
            AuditEvent(
                user=self.principal.user,
                action="REQUEST_REVIEW",
                entity_type=self.model.ENTITY_TYPE,
                entity_id=entity_id,
                source="canonical_service",
                review_request_id=created.request_id,
                expected_version=expected_version,
            ),
            self.config,
        )
        return created

    def _complete_mutation(
        self,
        action: str,
        entity: EntityT,
        *,
        previous: EntityT | None,
        expected_version: int | None,
        provenance: ProvenanceBundle | None,
        review_request_id: str | None,
    ) -> MutationResult:
        correlation_id = str(uuid4())
        bundle = provenance or self._direct_entry_provenance(correlation_id)
        provenance_ref_id = save_entity_provenance(
            self.config,
            bundle,
            entity_type=self.model.ENTITY_TYPE,
            entity_id=entity.entity_id,
            entity_version=entity.version,
            linked_by=self.principal.user,
        )
        record_event(
            AuditEvent(
                user=self.principal.user,
                action=action,
                entity_type=self.model.ENTITY_TYPE,
                entity_id=entity.entity_id,
                source="canonical_service",
                previous_value=(
                    {"version": previous.version, "deleted": previous.deleted_at is not None}
                    if previous is not None
                    else None
                ),
                new_value={
                    "version": entity.version,
                    "deleted": entity.deleted_at is not None,
                },
                outcome="SUCCESS",
                entity_version=entity.version,
                expected_version=expected_version,
                correlation_id=correlation_id,
                review_request_id=review_request_id,
                provenance_ref_ids=(provenance_ref_id,),
            ),
            self.config,
        )
        state = AdaState(principal_id=self.principal.user)
        state.add_entity_ref(self.model.ENTITY_TYPE, entity.entity_id, entity.version)
        state.provenance_refs.append(provenance_ref_id)
        return MutationResult(
            record=self._secured_record(entity),
            state=state,
            audit_correlation_id=correlation_id,
            provenance_ref_id=provenance_ref_id,
            review_request_id=review_request_id,
        )

    def _ensure_review(
        self,
        entity_id: str,
        operation: str,
        review_request_id: str | None,
    ) -> None:
        required = (
            self.model.ENTITY_TYPE in _REVIEW_REQUIRED_TYPES
            and self.principal.role is not Role.ADMIN
        )
        if review_request_id is None:
            if required:
                raise PermissionError(
                    f"{self.model.ENTITY_TYPE} {operation.lower()} requires approved review"
                )
            return
        request = get_review_request(self.config, review_request_id)
        if request is None:
            raise ValueError(f"Unknown review request: {review_request_id}")
        if request.status is not ReviewStatus.APPROVED:
            raise PermissionError(f"Review request {review_request_id} is not approved")
        if request.subject_type != self.model.ENTITY_TYPE or request.subject_id != entity_id:
            raise ValueError("review request subject does not match the mutation")
        if str(request.metadata.get("operation", "")).upper() != operation:
            raise ValueError("review request operation does not match the mutation")

    def _secured_record(self, entity: EntityT) -> dict[str, Any]:
        tiers = {**_BASE_TIERS, **_ENTITY_FIELD_TIERS.get(self.model.ENTITY_TYPE, {})}
        return filter_record(_record(entity), self.principal.role, tiers)

    def _direct_entry_provenance(self, correlation_id: str) -> ProvenanceBundle:
        source = SourceRef(
            source_type="user_action",
            source_id=self.principal.user,
            location=f"canonical_service:{correlation_id}",
        )
        provenance = ProvenanceRef(
            source_ref_id=source.source_ref_id,
            method="direct_entry",
            metadata={"correlation_id": correlation_id},
        )
        return ProvenanceBundle(source=source, evidence=(), provenance=provenance)

    def _require(self, permission: Permission) -> None:
        if not authorize(self.principal.role, permission):
            raise PermissionError(
                f"{self.principal.role.value} lacks {permission.value} permission"
            )
