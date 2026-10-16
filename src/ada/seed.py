"""Deterministic, idempotent Phase 1 canonical demo-data loader."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from ada.config import AdaConfig
from ada.domain import (
    Absence,
    AdministrativeAction,
    CanonicalEntity,
    DocumentRecord,
    DueOut,
    DueOutAssignment,
    EncryptedNationalIdentifier,
    Organization,
    OrganizationRelationship,
    Personnel,
    PersonnelAssignment,
    TrainingCompletion,
    TrainingCourse,
    TrainingRequirement,
    deterministic_id,
)
from ada.domain.administrative import AbsenceStatus, AdministrativeStatus
from ada.domain.documents import DocumentPIILevel
from ada.domain.dueouts import DueOutPriority, DueOutStatus, DueOutType
from ada.domain.personnel import AssignmentType
from ada.persistence import TemporalRepository
from ada.provenance import (
    EvidenceRef,
    ProvenanceBundle,
    ProvenanceRef,
    SourceRef,
    save_entity_provenance,
)

DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "samples" / "phase1_seed" / "seed.json"
SEED_ACTOR = "phase1-seed@ada.local"
SEED_EFFECTIVE_AT = datetime.fromisoformat("2026-01-01T00:00:00+00:00")


@dataclass(frozen=True)
class SeedResult:
    created: dict[str, int]
    skipped: dict[str, int]

    @property
    def total_created(self) -> int:
        return sum(self.created.values())

    @property
    def total_skipped(self) -> int:
        return sum(self.skipped.values())


def _id(entity_type: str, key: str) -> str:
    return deterministic_id(entity_type, key)


def _common() -> dict[str, Any]:
    return {
        "created_at": SEED_EFFECTIVE_AT,
        "updated_at": SEED_EFFECTIVE_AT,
        "valid_from": SEED_EFFECTIVE_AT,
        "created_by": SEED_ACTOR,
        "updated_by": SEED_ACTOR,
    }


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class _Seeder:
    def __init__(self, config: AdaConfig, fixture: Path):
        self.config = config
        self.fixture = fixture
        self.created: Counter[str] = Counter()
        self.skipped: Counter[str] = Counter()
        self.source = SourceRef(
            source_type="fixture_manifest",
            source_id="ada-phase1-canonical-demo-v1",
            location=str(fixture.relative_to(fixture.parents[2])),
            source_ref_id=_id("source_ref", "phase1-seed-v1"),
        )

    def add[EntityT: CanonicalEntity](
        self,
        entity: EntityT,
        model: type[EntityT],
        *,
        locator: str,
    ) -> None:
        repository = TemporalRepository(self.config, model)
        existing = repository.get(entity.entity_id, include_deleted=True)
        if existing is None:
            persisted = repository.create(
                entity,
                changed_by=SEED_ACTOR,
                reason="deterministic_phase1_seed",
            )
            self.created[model.ENTITY_TYPE] += 1
        else:
            self.skipped[model.ENTITY_TYPE] += 1
            return
        evidence = EvidenceRef(
            source_ref_id=self.source.source_ref_id,
            locator=locator,
            evidence_ref_id=_id("evidence_ref", f"{model.ENTITY_TYPE}:{entity.entity_id}"),
        )
        provenance = ProvenanceRef(
            source_ref_id=self.source.source_ref_id,
            evidence_ref_ids=(evidence.evidence_ref_id,),
            method="deterministic_fixture",
            confidence=1.0,
            created_at=SEED_EFFECTIVE_AT.isoformat(),
            provenance_ref_id=_id(
                "provenance_ref",
                f"{model.ENTITY_TYPE}:{entity.entity_id}",
            ),
            metadata={"fixture_version": 1},
        )
        save_entity_provenance(
            self.config,
            ProvenanceBundle(
                source=self.source,
                evidence=(evidence,),
                provenance=provenance,
            ),
            entity_type=model.ENTITY_TYPE,
            entity_id=persisted.entity_id,
            entity_version=persisted.version,
            linked_by=SEED_ACTOR,
        )


def seed_phase1(
    config: AdaConfig | None = None,
    *,
    fixture_path: Path | None = None,
) -> SeedResult:
    """Load the normalized synthetic fixture without changing existing records."""

    resolved_config = config or AdaConfig.from_env()
    fixture = fixture_path or DEFAULT_FIXTURE
    payload: dict[str, list[dict[str, Any]]] = json.loads(fixture.read_text(encoding="utf-8"))
    seeder = _Seeder(resolved_config, fixture)

    for row in payload["organizations"]:
        seeder.add(
            Organization(
                organization_id=_id("organization", row["key"]),
                code=row["code"],
                name=row["name"],
                short_name=row.get("short_name"),
                organization_type=row["organization_type"],
                **_common(),
            ),
            Organization,
            locator=f"organizations/{row['key']}",
        )

    for row in payload["organization_relationships"]:
        seeder.add(
            OrganizationRelationship(
                relationship_id=_id("organization_relationship", row["key"]),
                parent_organization_id=_id("organization", row["parent_key"]),
                child_organization_id=_id("organization", row["child_key"]),
                start_date=date.fromisoformat(row["start_date"]),
                **_common(),
            ),
            OrganizationRelationship,
            locator=f"organization_relationships/{row['key']}",
        )

    for row in payload["personnel"]:
        encrypted = (
            EncryptedNationalIdentifier(
                ciphertext=row["national_id_ciphertext"],
                last4=row["national_id_last4"],
                key_id="phase1-fixture-key",
                algorithm="TEST-FIXTURE-ONLY",
            )
            if row.get("national_id_ciphertext")
            else None
        )
        seeder.add(
            Personnel(
                personnel_id=_id("personnel", row["key"]),
                employee_number=row["employee_number"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                primary_email=row.get("primary_email"),
                position_title=row.get("position_title"),
                rank_grade=row.get("rank_grade"),
                national_identifier=encrypted,
                **_common(),
            ),
            Personnel,
            locator=f"personnel/{row['key']}",
        )

    for row in payload["personnel_assignments"]:
        seeder.add(
            PersonnelAssignment(
                assignment_id=_id("personnel_assignment", row["key"]),
                personnel_id=_id("personnel", row["personnel_key"]),
                organization_id=_id("organization", row["organization_key"]),
                assignment_type=(
                    AssignmentType.PRIMARY
                    if row["is_primary"]
                    else AssignmentType.ADDITIONAL_DUTY
                ),
                position_title=row.get("position_title"),
                is_primary=bool(row["is_primary"]),
                start_date=date.fromisoformat(row["start_date"]),
                end_date=_date(row.get("end_date")),
                **_common(),
            ),
            PersonnelAssignment,
            locator=f"personnel_assignments/{row['key']}",
        )

    for row in payload["training_courses"]:
        seeder.add(
            TrainingCourse(
                course_id=_id("training_course", row["key"]),
                code=row["code"],
                title=row["title"],
                provider=row.get("provider"),
                validity_days=row.get("validity_days"),
                **_common(),
            ),
            TrainingCourse,
            locator=f"training_courses/{row['key']}",
        )

    for row in payload["training_requirements"]:
        seeder.add(
            TrainingRequirement(
                requirement_id=_id("training_requirement", row["key"]),
                course_id=_id("training_course", row["course_key"]),
                organization_id=(
                    _id("organization", row["organization_key"])
                    if row.get("organization_key")
                    else None
                ),
                personnel_id=(
                    _id("personnel", row["personnel_key"])
                    if row.get("personnel_key")
                    else None
                ),
                due_within_days=row.get("due_within_days"),
                inherits_to_descendants=bool(row["inherits_to_descendants"]),
                effective_from=date.fromisoformat(row["effective_from"]),
                **_common(),
            ),
            TrainingRequirement,
            locator=f"training_requirements/{row['key']}",
        )

    for row in payload["documents"]:
        seeder.add(
            DocumentRecord(
                document_id=_id("document", row["key"]),
                filename=row["filename"],
                title=row["title"],
                storage_location=row["storage_location"],
                hash=row["hash"],
                pii_level=DocumentPIILevel.INTERNAL,
                uploaded_by=SEED_ACTOR,
                upload_date=SEED_EFFECTIVE_AT,
                document_type=row["document_type"],
                source_system="phase1_seed",
                metadata={"synthetic": True, "fixture_version": 1},
                **_common(),
            ),
            DocumentRecord,
            locator=f"documents/{row['key']}",
        )

    for row in payload["training_completions"]:
        seeder.add(
            TrainingCompletion(
                completion_id=_id("training_completion", row["key"]),
                personnel_id=_id("personnel", row["personnel_key"]),
                course_id=_id("training_course", row["course_key"]),
                completed_on=date.fromisoformat(row["completed_on"]),
                expires_on=_date(row.get("expires_on")),
                score=row.get("score"),
                **_common(),
            ),
            TrainingCompletion,
            locator=f"training_completions/{row['key']}",
        )

    for row in payload["due_outs"]:
        seeder.add(
            DueOut(
                due_out_id=_id("due_out", row["key"]),
                title=row["title"],
                description=row.get("description"),
                due_out_type=DueOutType(row["due_out_type"]),
                status=DueOutStatus(row["status"]),
                due_at=_datetime(row.get("due_at")),
                priority=DueOutPriority(row["priority"]),
                owner_organization_id=_id(
                    "organization",
                    row["owner_organization_key"],
                ),
                created_by_principal=SEED_ACTOR,
                **_common(),
            ),
            DueOut,
            locator=f"due_outs/{row['key']}",
        )

    for row in payload["due_out_assignments"]:
        seeder.add(
            DueOutAssignment(
                assignment_id=_id("due_out_assignment", row["key"]),
                due_out_id=_id("due_out", row["due_out_key"]),
                assignee_personnel_id=(
                    _id("personnel", row["personnel_key"])
                    if row.get("personnel_key")
                    else None
                ),
                assignee_organization_id=(
                    _id("organization", row["organization_key"])
                    if row.get("organization_key")
                    else None
                ),
                status=DueOutStatus(row["status"]),
                completed_at=_datetime(row.get("completed_at")),
                **_common(),
            ),
            DueOutAssignment,
            locator=f"due_out_assignments/{row['key']}",
        )

    for row in payload["administrative_actions"]:
        seeder.add(
            AdministrativeAction(
                action_id=_id("administrative_action", row["key"]),
                personnel_id=_id("personnel", row["personnel_key"]),
                action_type=row["action_type"],
                status=AdministrativeStatus(row["status"]),
                summary=row["summary"],
                effective_from=_datetime(row.get("effective_from")),
                **_common(),
            ),
            AdministrativeAction,
            locator=f"administrative_actions/{row['key']}",
        )

    for row in payload["absences"]:
        seeder.add(
            Absence(
                absence_id=_id("absence", row["key"]),
                personnel_id=_id("personnel", row["personnel_key"]),
                absence_type=row["absence_type"],
                status=AbsenceStatus(row["status"]),
                start_at=datetime.fromisoformat(row["start_at"]),
                end_at=datetime.fromisoformat(row["end_at"]),
                notes=row.get("notes"),
                **_common(),
            ),
            Absence,
            locator=f"absences/{row['key']}",
        )

    return SeedResult(created=dict(seeder.created), skipped=dict(seeder.skipped))
