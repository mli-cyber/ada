"""Phase 0 file intake: store and register, never parse."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ada.config import AdaConfig
from ada.platform.audit import AuditEvent, record_event
from ada.platform.db import execute, get_connection, init_db
from ada.platform.identity import Permission, Principal, authorize, current_principal
from ada.platform.storage import get_object_store

CLASSIFICATIONS = frozenset({"public", "internal", "restricted"})
PII_LEVELS = frozenset({"public", "internal", "sensitive"})


@dataclass(frozen=True)
class IntakeDocument:
    document_id: str
    filename: str
    storage_location: str
    hash: str
    classification: str
    pii_level: str
    uploaded_by: str
    upload_date: str
    status: str
    review_request_id: str | None = None


def _bytes(data: bytes | bytearray | Path | str) -> bytes:
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    return Path(data).read_bytes()


def ingest_file(
    data: bytes | bytearray | Path | str,
    *,
    filename: str,
    uploaded_by: str | None = None,
    classification: str = "internal",
    pii_level: str = "internal",
    review_request_id: str | None = None,
    config: AdaConfig | None = None,
    principal: Principal | None = None,
) -> str:
    """Store bytes, register metadata, and audit. Content is not parsed."""

    resolved_config = config or AdaConfig.from_env()
    resolved_principal = principal or current_principal(resolved_config)
    if not authorize(resolved_principal.role, Permission.CREATE):
        raise PermissionError("File intake requires the create permission")
    safe_filename = Path(filename).name.strip()
    if not safe_filename:
        raise ValueError("filename is required")
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"Unsupported classification: {classification}")
    if pii_level not in PII_LEVELS:
        raise ValueError(f"Unsupported PII level: {pii_level}")

    content = _bytes(data)
    digest = hashlib.sha256(content).hexdigest()
    init_db(resolved_config)
    duplicate_connection = get_connection(resolved_config)
    try:
        existing = execute(
            duplicate_connection,
            resolved_config,
            "SELECT document_id FROM documents WHERE hash = ?",
            (digest,),
        ).fetchone()
        if existing is not None:
            return str(existing[0])
    finally:
        duplicate_connection.close()

    document_id = str(uuid4())
    key = f"documents/{digest[:2]}/{digest}"
    storage_location = get_object_store(resolved_config).put(key, content)
    upload_date = datetime.now(UTC).isoformat()
    uploader = uploaded_by or resolved_principal.user

    connection = get_connection(resolved_config)
    try:
        execute(
            connection,
            resolved_config,
            """
            INSERT INTO documents (
                document_id, filename, storage_location, hash, classification,
                pii_level, uploaded_by, upload_date, status, review_request_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                safe_filename,
                storage_location,
                digest,
                classification,
                pii_level,
                uploader,
                upload_date,
                "REGISTERED",
                review_request_id,
            ),
        )
        connection.commit()
    except Exception:
        get_object_store(resolved_config).delete(key)
        raise
    finally:
        connection.close()

    record_event(
        AuditEvent(
            user=uploader,
            action="FILE_INTAKE",
            entity_type="document",
            entity_id=document_id,
            source="file_upload",
            new_value={
                "filename": safe_filename,
                "hash": digest,
                "classification": classification,
                "pii_level": pii_level,
            },
        ),
        resolved_config,
    )
    return document_id


def list_documents(config: AdaConfig | None = None) -> list[IntakeDocument]:
    resolved_config = config or AdaConfig.from_env()
    init_db(resolved_config)
    connection = get_connection(resolved_config)
    try:
        rows = execute(
            connection,
            resolved_config,
            """
            SELECT document_id, filename, storage_location, hash, classification,
                   pii_level, uploaded_by, upload_date, status, review_request_id
            FROM documents ORDER BY upload_date DESC
            """,
        ).fetchall()
        return [IntakeDocument(*tuple(row)) for row in rows]
    finally:
        connection.close()
