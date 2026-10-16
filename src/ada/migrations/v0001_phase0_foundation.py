"""Adopt the Phase 0 platform schema into the migration ledger."""

from ada.migrations.types import Migration

MIGRATION = Migration(
    version=1,
    name="phase0_foundation",
    statements=(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS review_requests (
            request_id TEXT PRIMARY KEY,
            subject_type TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS approval_decisions (
            decision_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            action TEXT NOT NULL,
            decided_by TEXT NOT NULL,
            comment TEXT,
            decided_at TEXT NOT NULL,
            FOREIGN KEY (request_id) REFERENCES review_requests(request_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            storage_location TEXT NOT NULL,
            hash TEXT NOT NULL UNIQUE,
            classification TEXT NOT NULL,
            pii_level TEXT NOT NULL,
            uploaded_by TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            status TEXT NOT NULL,
            review_request_id TEXT,
            FOREIGN KEY (review_request_id) REFERENCES review_requests(request_id)
        )
        """,
    ),
)
