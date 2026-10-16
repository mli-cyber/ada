"""Persistent Phase 1 bridge for Phase 0 provenance reference contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from ada.config import AdaConfig
from ada.platform.db import execute, get_connection, init_db
from ada.provenance.refs import EvidenceRef, ProvenanceRef, SourceRef


@dataclass(frozen=True)
class ProvenanceBundle:
    source: SourceRef
    evidence: tuple[EvidenceRef, ...]
    provenance: ProvenanceRef

    def __post_init__(self) -> None:
        if self.provenance.source_ref_id != self.source.source_ref_id:
            raise ValueError("provenance and source references do not match")
        evidence_ids = {item.evidence_ref_id for item in self.evidence}
        if set(self.provenance.evidence_ref_ids) != evidence_ids:
            raise ValueError("provenance evidence IDs do not match the bundle")
        if any(item.source_ref_id != self.source.source_ref_id for item in self.evidence):
            raise ValueError("all evidence must refer to the bundle source")


def save_entity_provenance(
    config: AdaConfig,
    bundle: ProvenanceBundle,
    *,
    entity_type: str,
    entity_id: str,
    entity_version: int,
    linked_by: str,
) -> str:
    """Persist one provenance graph and link it to an entity version."""

    if entity_version < 1:
        raise ValueError("entity_version must be at least 1")
    init_db(config)
    connection = get_connection(config)
    now = datetime.now(UTC).isoformat()
    try:
        execute(
            connection,
            config,
            """
            INSERT INTO source_refs (
                source_ref_id, source_type, source_id, location, created_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (source_ref_id) DO NOTHING
            """,
            (
                bundle.source.source_ref_id,
                bundle.source.source_type,
                bundle.source.source_id,
                bundle.source.location,
                now,
            ),
        )
        for evidence in bundle.evidence:
            execute(
                connection,
                config,
                """
                INSERT INTO evidence_refs (
                    evidence_ref_id, source_ref_id, locator, excerpt_hash, created_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (evidence_ref_id) DO NOTHING
                """,
                (
                    evidence.evidence_ref_id,
                    evidence.source_ref_id,
                    evidence.locator,
                    evidence.excerpt_hash,
                    now,
                ),
            )
        execute(
            connection,
            config,
            """
            INSERT INTO provenance_refs (
                provenance_ref_id, source_ref_id, method, confidence,
                metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (provenance_ref_id) DO NOTHING
            """,
            (
                bundle.provenance.provenance_ref_id,
                bundle.provenance.source_ref_id,
                bundle.provenance.method,
                (
                    str(bundle.provenance.confidence)
                    if bundle.provenance.confidence is not None
                    else None
                ),
                json.dumps(bundle.provenance.metadata, sort_keys=True),
                bundle.provenance.created_at,
            ),
        )
        for evidence_id in bundle.provenance.evidence_ref_ids:
            execute(
                connection,
                config,
                """
                INSERT INTO provenance_evidence (provenance_ref_id, evidence_ref_id)
                VALUES (?, ?)
                ON CONFLICT (provenance_ref_id, evidence_ref_id) DO NOTHING
                """,
                (bundle.provenance.provenance_ref_id, evidence_id),
            )
        execute(
            connection,
            config,
            """
            INSERT INTO entity_provenance (
                entity_type, entity_id, entity_version, provenance_ref_id,
                linked_at, linked_by
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (
                entity_type, entity_id, entity_version, provenance_ref_id
            ) DO NOTHING
            """,
            (
                entity_type,
                entity_id,
                entity_version,
                bundle.provenance.provenance_ref_id,
                now,
                linked_by,
            ),
        )
        connection.commit()
        return bundle.provenance.provenance_ref_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def entity_provenance_refs(
    config: AdaConfig,
    *,
    entity_type: str,
    entity_id: str,
    entity_version: int | None = None,
) -> tuple[ProvenanceRef, ...]:
    init_db(config)
    connection = get_connection(config)
    try:
        version_clause = " AND ep.entity_version = ?" if entity_version is not None else ""
        parameters: tuple[object, ...] = (
            (entity_type, entity_id, entity_version)
            if entity_version is not None
            else (entity_type, entity_id)
        )
        cursor = execute(
            connection,
            config,
            f"""
            SELECT pr.provenance_ref_id, pr.source_ref_id, pr.method,
                   pr.confidence, pr.metadata_json, pr.created_at
            FROM entity_provenance ep
            JOIN provenance_refs pr
              ON pr.provenance_ref_id = ep.provenance_ref_id
            WHERE ep.entity_type = ? AND ep.entity_id = ?{version_clause}
            ORDER BY ep.entity_version, pr.provenance_ref_id
            """,
            parameters,
        )
        results: list[ProvenanceRef] = []
        for row in cursor.fetchall():
            evidence_rows = execute(
                connection,
                config,
                """
                SELECT evidence_ref_id
                FROM provenance_evidence
                WHERE provenance_ref_id = ?
                ORDER BY evidence_ref_id
                """,
                (row[0],),
            ).fetchall()
            results.append(
                ProvenanceRef(
                    provenance_ref_id=str(row[0]),
                    source_ref_id=str(row[1]),
                    method=str(row[2]),
                    confidence=float(row[3]) if row[3] is not None else None,
                    metadata=json.loads(str(row[4])),
                    created_at=str(row[5]),
                    evidence_ref_ids=tuple(str(item[0]) for item in evidence_rows),
                )
            )
        return tuple(results)
    finally:
        connection.close()
