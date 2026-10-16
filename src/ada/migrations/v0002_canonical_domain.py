"""Create the Phase 1 canonical domain and temporal-governance schema."""

from ada.migrations.types import Migration

MIGRATION = Migration(
    version=2,
    name="canonical_domain",
    statements=(
        """
        CREATE TABLE personnel (
            personnel_id TEXT PRIMARY KEY,
            employee_number TEXT,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            last_name TEXT NOT NULL,
            preferred_name TEXT,
            status TEXT NOT NULL,
            date_of_birth TEXT,
            national_id_ciphertext TEXT,
            national_id_last4 TEXT,
            national_id_key_id TEXT,
            national_id_algorithm TEXT,
            primary_email TEXT,
            phone TEXT,
            position_title TEXT,
            rank_grade TEXT,
            notes TEXT,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted')),
            CHECK (national_id_ciphertext IS NULL OR national_id_last4 IS NOT NULL)
        )
        """,
        """
        CREATE UNIQUE INDEX uq_personnel_employee_number_active
        ON personnel (employee_number)
        WHERE employee_number IS NOT NULL AND deleted_at IS NULL
        """,
        """
        CREATE INDEX ix_personnel_name
        ON personnel (last_name, first_name)
        """,
        """
        CREATE TABLE organizations (
            organization_id TEXT PRIMARY KEY,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            short_name TEXT,
            organization_type TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE UNIQUE INDEX uq_organizations_code_active
        ON organizations (code)
        WHERE deleted_at IS NULL
        """,
        """
        CREATE INDEX ix_organizations_name
        ON organizations (name)
        """,
        """
        CREATE TABLE organization_relationships (
            relationship_id TEXT PRIMARY KEY,
            parent_organization_id TEXT NOT NULL,
            child_organization_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            is_primary INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            FOREIGN KEY (parent_organization_id)
                REFERENCES organizations(organization_id),
            FOREIGN KEY (child_organization_id)
                REFERENCES organizations(organization_id),
            CHECK (parent_organization_id <> child_organization_id),
            CHECK (is_primary IN (0, 1)),
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE UNIQUE INDEX uq_org_primary_parent_active
        ON organization_relationships (child_organization_id)
        WHERE is_primary = 1 AND end_date IS NULL AND deleted_at IS NULL
        """,
        """
        CREATE INDEX ix_org_relationship_parent
        ON organization_relationships (parent_organization_id, start_date, end_date)
        """,
        """
        CREATE TABLE personnel_assignments (
            assignment_id TEXT PRIMARY KEY,
            personnel_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            assignment_type TEXT NOT NULL,
            position_title TEXT,
            is_primary INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id),
            FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
            CHECK (is_primary IN (0, 1)),
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE UNIQUE INDEX uq_personnel_primary_assignment_active
        ON personnel_assignments (personnel_id)
        WHERE is_primary = 1 AND end_date IS NULL AND deleted_at IS NULL
        """,
        """
        CREATE INDEX ix_personnel_assignment_org
        ON personnel_assignments (organization_id, start_date, end_date)
        """,
        """
        CREATE TABLE personnel_contacts (
            contact_id TEXT PRIMARY KEY,
            personnel_id TEXT NOT NULL,
            contact_type TEXT NOT NULL,
            value TEXT NOT NULL,
            label TEXT,
            is_primary INTEGER NOT NULL,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id),
            CHECK (is_primary IN (0, 1)),
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE INDEX ix_personnel_contacts_person
        ON personnel_contacts (personnel_id, contact_type)
        """,
        """
        CREATE TABLE training_courses (
            course_id TEXT PRIMARY KEY,
            code TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            provider TEXT,
            validity_days INTEGER,
            status TEXT NOT NULL,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            CHECK (validity_days IS NULL OR validity_days >= 0),
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE UNIQUE INDEX uq_training_course_code_active
        ON training_courses (code)
        WHERE deleted_at IS NULL
        """,
        """
        CREATE TABLE training_requirements (
            requirement_id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            organization_id TEXT,
            personnel_id TEXT,
            requirement_type TEXT NOT NULL,
            due_within_days INTEGER,
            is_mandatory INTEGER NOT NULL,
            inherits_to_descendants INTEGER NOT NULL,
            effective_from TEXT NOT NULL,
            effective_to TEXT,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES training_courses(course_id),
            FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
            FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id),
            CHECK (organization_id IS NOT NULL OR personnel_id IS NOT NULL),
            CHECK (due_within_days IS NULL OR due_within_days >= 0),
            CHECK (is_mandatory IN (0, 1)),
            CHECK (inherits_to_descendants IN (0, 1)),
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE INDEX ix_training_requirements_scope
        ON training_requirements (organization_id, personnel_id, effective_from, effective_to)
        """,
        """
        CREATE TABLE training_completions (
            completion_id TEXT PRIMARY KEY,
            personnel_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            completed_on TEXT NOT NULL,
            expires_on TEXT,
            status TEXT NOT NULL,
            certificate_document_id TEXT,
            score TEXT,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id),
            FOREIGN KEY (course_id) REFERENCES training_courses(course_id),
            FOREIGN KEY (certificate_document_id) REFERENCES documents(document_id),
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE INDEX ix_training_completions_person
        ON training_completions (personnel_id, course_id, completed_on)
        """,
        """
        CREATE TABLE due_outs (
            due_out_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            due_out_type TEXT NOT NULL,
            status TEXT NOT NULL,
            due_at TEXT,
            priority TEXT NOT NULL,
            owner_organization_id TEXT,
            created_by_principal TEXT NOT NULL,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            FOREIGN KEY (owner_organization_id)
                REFERENCES organizations(organization_id),
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE INDEX ix_due_outs_owner_status_due
        ON due_outs (owner_organization_id, status, due_at)
        """,
        """
        CREATE TABLE due_out_assignments (
            assignment_id TEXT PRIMARY KEY,
            due_out_id TEXT NOT NULL,
            assignee_personnel_id TEXT,
            assignee_organization_id TEXT,
            status TEXT NOT NULL,
            completed_at TEXT,
            response_text TEXT,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            FOREIGN KEY (due_out_id) REFERENCES due_outs(due_out_id),
            FOREIGN KEY (assignee_personnel_id) REFERENCES personnel(personnel_id),
            FOREIGN KEY (assignee_organization_id)
                REFERENCES organizations(organization_id),
            CHECK (
                assignee_personnel_id IS NOT NULL
                OR assignee_organization_id IS NOT NULL
            ),
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE INDEX ix_due_out_assignments_due_out
        ON due_out_assignments (due_out_id, status)
        """,
        """
        CREATE TABLE administrative_actions (
            action_id TEXT PRIMARY KEY,
            personnel_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            status TEXT NOT NULL,
            effective_from TEXT,
            effective_to TEXT,
            summary TEXT NOT NULL,
            review_request_id TEXT,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id),
            FOREIGN KEY (review_request_id) REFERENCES review_requests(request_id),
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE INDEX ix_administrative_actions_person
        ON administrative_actions (personnel_id, status, effective_from)
        """,
        """
        CREATE TABLE absences (
            absence_id TEXT PRIMARY KEY,
            personnel_id TEXT NOT NULL,
            absence_type TEXT NOT NULL,
            start_at TEXT NOT NULL,
            end_at TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            administrative_action_id TEXT,
            version INTEGER NOT NULL,
            classification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            FOREIGN KEY (personnel_id) REFERENCES personnel(personnel_id),
            FOREIGN KEY (administrative_action_id)
                REFERENCES administrative_actions(action_id),
            CHECK (end_at >= start_at),
            CHECK (version >= 1),
            CHECK (classification IN ('public', 'internal', 'restricted'))
        )
        """,
        """
        CREATE INDEX ix_absences_person_period
        ON absences (personnel_id, start_at, end_at)
        """,
        """
        ALTER TABLE documents ADD COLUMN title TEXT
        """,
        """
        ALTER TABLE documents ADD COLUMN document_type TEXT
        """,
        """
        ALTER TABLE documents ADD COLUMN source_system TEXT
        """,
        """
        ALTER TABLE documents ADD COLUMN version INTEGER NOT NULL DEFAULT 1
        """,
        """
        ALTER TABLE documents ADD COLUMN created_at TEXT
        """,
        """
        ALTER TABLE documents ADD COLUMN updated_at TEXT
        """,
        """
        ALTER TABLE documents ADD COLUMN valid_from TEXT
        """,
        """
        ALTER TABLE documents ADD COLUMN valid_to TEXT
        """,
        """
        ALTER TABLE documents ADD COLUMN deleted_at TEXT
        """,
        """
        ALTER TABLE documents ADD COLUMN metadata_json TEXT
        """,
        """
        ALTER TABLE documents ADD COLUMN created_by TEXT
        """,
        """
        ALTER TABLE documents ADD COLUMN updated_by TEXT
        """,
        """
        UPDATE documents
        SET title = filename,
            document_type = 'uploaded_file',
            source_system = 'phase0_intake',
            created_at = upload_date,
            updated_at = upload_date,
            valid_from = upload_date,
            metadata_json = '{}',
            created_by = uploaded_by,
            updated_by = uploaded_by
        WHERE created_at IS NULL
        """,
        """
        CREATE TABLE canonical_entity_history (
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_to TEXT,
            deleted_at TEXT,
            changed_by TEXT NOT NULL,
            change_reason TEXT,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (entity_type, entity_id, version),
            CHECK (version >= 1)
        )
        """,
        """
        CREATE UNIQUE INDEX uq_entity_history_current
        ON canonical_entity_history (entity_type, entity_id)
        WHERE valid_to IS NULL
        """,
        """
        CREATE INDEX ix_entity_history_as_of
        ON canonical_entity_history (entity_type, entity_id, valid_from, valid_to)
        """,
        """
        CREATE TABLE source_refs (
            source_ref_id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            location TEXT,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE evidence_refs (
            evidence_ref_id TEXT PRIMARY KEY,
            source_ref_id TEXT NOT NULL,
            locator TEXT NOT NULL,
            excerpt_hash TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (source_ref_id) REFERENCES source_refs(source_ref_id)
        )
        """,
        """
        CREATE TABLE provenance_refs (
            provenance_ref_id TEXT PRIMARY KEY,
            source_ref_id TEXT NOT NULL,
            method TEXT NOT NULL,
            confidence TEXT,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (source_ref_id) REFERENCES source_refs(source_ref_id)
        )
        """,
        """
        CREATE TABLE provenance_evidence (
            provenance_ref_id TEXT NOT NULL,
            evidence_ref_id TEXT NOT NULL,
            PRIMARY KEY (provenance_ref_id, evidence_ref_id),
            FOREIGN KEY (provenance_ref_id)
                REFERENCES provenance_refs(provenance_ref_id),
            FOREIGN KEY (evidence_ref_id) REFERENCES evidence_refs(evidence_ref_id)
        )
        """,
        """
        CREATE TABLE entity_provenance (
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            entity_version INTEGER NOT NULL,
            provenance_ref_id TEXT NOT NULL,
            linked_at TEXT NOT NULL,
            linked_by TEXT NOT NULL,
            PRIMARY KEY (
                entity_type,
                entity_id,
                entity_version,
                provenance_ref_id
            ),
            FOREIGN KEY (provenance_ref_id)
                REFERENCES provenance_refs(provenance_ref_id)
        )
        """,
        """
        CREATE INDEX ix_entity_provenance_lookup
        ON entity_provenance (entity_type, entity_id, entity_version)
        """,
    ),
)
