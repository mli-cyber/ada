# Agentic HR / Personnel & Training Portal Roadmap

> **Historical reference - superseded.** This is the original **v2** roadmap (pre-"Ada"). It
> has been superseded by [`../roadmap_v3.md`](../roadmap_v3.md), which carried everything here
> forward and added application profiles, multi-model budget tiers, the guardrail/untrusted-doc
> contracts, NFRs, an eval harness, KPIs, and diagrams. Kept only for historical context - do
> not use it for planning. For forward-looking enhancements, see the other files in this
> folder (e.g. [`policy_driven_rules.md`](policy_driven_rules.md)).

## 1. Project Purpose

The **Agentic HR / Personnel & Training Portal** is a parallel project to IWB that reuses applicable architectural patterns and framework components while focusing on personnel, training, organizational, and administrative data management.

The system will allow users to:

- Upload and ingest `XLSX`, `CSV`, `TXT`, `PDF`, `DOC`, and `DOCX` files.
- Extract, normalize, validate, and store information in structured databases.
- Manage personnel, training, organization, administrative actions, and due-outs through a natural-language chat interface.
- Use **Streamlit** as the initial application interface for chat, file upload, editable tables, dashboards, review screens, and report downloads.
- Add, retrieve, update, deactivate, and search records without requiring users to know SQL.
- Ask follow-up questions conversationally.
- Generate outputs as:
  - On-screen answers
  - On-screen tables
  - Excel
  - CSV
  - TXT
  - PDF
  - Secure/downloadable URLs
- Track provenance and supporting evidence for extracted or modified information.
- Support multiple HR domains/databases that can be added over time.

The system should reuse applicable IWB concepts such as:

- Agent orchestration
- Document ingestion
- Vector database / RAG
- Canonical structured state
- Provenance
- Validation
- Confidence handling
- Durable workflows/checkpoints
- Human review
- Report generation

---

# 2. Target Architecture

```text
                                USER
                                 │
                         Streamlit Interface
                                 │
          ┌──────────────┬───────┼───────────────┐
          │              │       │               │
        Chat          Uploads  Tables         Dashboards
          │              │    / Forms            │
          └──────────────┴───────┼───────────────┘
                                 │
                       Application / API Layer
                                 │
                         Agent Orchestrator
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
   Intent / Query          Ingestion / Mapping       Workflow / Report
      Agents                    Agents                    Agents
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                    Validation / Authorization
                                 │
                      Controlled Domain Tools
                                 │
      ┌──────────────┬───────────┼────────────┬──────────────┐
      │              │           │            │              │
 Personnel       Organization  Training   Due-Out/Admin   Documents
      │              │           │            │              │
      └──────────────┴───────────┼────────────┴──────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │                           │
             PostgreSQL / SQL              Vector DB
             Source of Truth          Semantic / Evidence
                   │                           │
                   └─────────────┬─────────────┘
                                 │
                           Report Service
                                 │
             ┌────────┬──────────┼─────────┬────────┐
             │        │          │         │        │
           Screen    XLSX       CSV       TXT      PDF
```

---


# 2.1 Streamlit Interface Strategy

Use **Streamlit as the initial user interface** for the MVP and early operational releases.

Streamlit is a strong fit because the application is primarily:

- Python-based.
- Data-centric.
- LLM/chat-centric.
- File-ingestion heavy.
- Table/report heavy.
- Internal/enterprise workflow oriented.

## Initial Streamlit Pages

```text
HR Portal
│
├── Home / Dashboard
├── AI Assistant
├── Personnel
├── Organization / Assignments
├── Training
├── Due-Outs / Suspenses
├── Administrative Actions
├── File Import / Review
├── Reports
├── Data Quality / Review Queue
└── Administration
```

## Streamlit UI Capabilities to Use

### Chat

Use the chat interface for commands such as:

```text
Add John Smith to J21.

Show all open due-outs for 185.

Who has training due within 30 days?

Generate the BA due-out report.
```

### File Upload

Support:

- XLSX
- XLS
- CSV
- TXT
- PDF
- DOC
- DOCX

Uploads should enter the staging/validation workflow before authoritative database changes.

### Editable Tables

Use editable tables for:

- Reviewing extracted records.
- Correcting schema mappings.
- Editing due-out responses.
- Resolving validation issues.
- Reviewing proposed bulk changes.

Edits must still flow through the same validation, authorization, audit, and change-set services used by chat.

### Dynamic Forms

Use forms when a structured interaction is safer or faster than chat.

Examples:

- Add person
- Create due-out
- Create reporting cycle
- Assign training
- Record completion
- Record leave
- Approve bulk import

### Dashboards

Provide role-aware dashboards for:

- My tasks / due-outs
- Unit due-outs
- Training readiness
- Upcoming arrivals/departures
- Open administrative actions
- Data-quality issues
- Reporting-cycle status

### Downloads

Allow verified datasets/reports to be downloaded as:

- XLSX
- CSV
- TXT
- PDF

For larger files, generate artifacts in backend/object storage and return a secure link rather than holding the entire file only in the UI process.

## Important Streamlit Architecture Rule

**Streamlit is the presentation layer, not the business-logic layer.**

Do not place core HR rules, LLM orchestration, database logic, or authorization directly inside page scripts.

Use:

```text
Streamlit UI
     │
     ▼
Application Services
     │
     ├── Agent Service
     ├── Query Service
     ├── Personnel Service
     ├── Training Service
     ├── Due-Out Service
     ├── Workflow Service
     ├── Report Service
     └── Authorization Service
             │
             ▼
         Databases
```

This keeps the application replaceable later if a React/Angular/custom frontend becomes necessary.

## Session State Rule

Use Streamlit session state only for temporary UI state, such as:

- Current filters
- Current selected report
- Current chat display
- Current table selection

Persist important state in the backend/database:

- Conversation records that must survive refresh/restart
- Agent checkpoints
- Pending approvals
- Change sets
- Report jobs
- Due-out workflow state
- User preferences that must persist
- Import staging state

## Authentication vs Authorization

The UI may authenticate the user through enterprise identity/OIDC.

Authorization must remain application-controlled.

The backend/tool layer determines:

- Which domains the user may access.
- Which organizations the user may see.
- Which PII fields the user may retrieve.
- Which write operations the user may execute.
- Which reports the user may generate.
- Which bulk actions require approval.

---

# 3. Core Architectural Principles

## 3.1 Structured Database Is the Source of Truth

The vector database should not be the authoritative personnel or training database.

Use the structured database for:

- Personnel
- Organizations
- Positions
- Assignments
- Training courses
- Training requirements
- Training completions
- Administrative actions
- Leave/absence
- Qualifications
- Certifications
- Skills
- Tasks
- Readiness status

Use the vector database for:

- Policies
- SOPs
- Training guidance
- Uploaded PDFs
- Word documents
- Text files
- Source-document chunks
- Semantic retrieval
- Evidence retrieval
- Provenance context

---

## 3.2 LLMs Interpret; Deterministic Services Execute

LLMs should:

- Interpret user intent
- Extract information
- Route tasks
- Map schemas
- Explain results
- Ask for missing information
- Summarize reports
- Interpret policies

Deterministic application services should:

- Validate records
- Calculate dates
- Calculate compliance
- Determine readiness
- Authorize changes
- Execute database writes
- Generate authoritative query results
- Enforce permissions
- Generate exports

---

## 3.3 Do Not Give the LLM Unrestricted SQL Access

Instead of exposing:

```text
execute_sql(...)
```

provide controlled domain tools such as:

```text
create_person()
update_person()
search_people()

assign_person()
transfer_person()

create_course()
record_completion()
get_training_status()

record_leave()
create_action()

generate_report()
export_results()
```

---

# 4. Proposed Domain Databases

Initially these may be separate PostgreSQL schemas rather than separate physical database servers.

```text
hr_platform
│
├── identity
├── organization
├── training
├── due_out
├── administrative
├── documents
├── readiness
└── audit
```

Additional domains can be added later.

---

## 4.1 Personnel / Identity Domain

Potential entities:

```text
Person
Contact
SensitiveIdentity
EmergencyContact
```

Example fields:

```text
Person
├── person_id
├── first_name
├── middle_name
├── last_name
├── preferred_name
├── rank_grade
├── service_component
├── official_email
├── duty_phone
├── status
├── created_at
└── updated_at
```

Sensitive information should be isolated where practical:

```text
SensitiveIdentity
├── person_id
├── dod_id
├── ssn_encrypted
├── date_of_birth
└── access_classification
```

SSN should not be used as a primary key.

All other domains should reference an internal `person_id`.

---

## 4.2 Organization / Assignment Domain

```text
Organization
├── organization_id
├── name
├── abbreviation
├── parent_organization_id
├── organization_type
├── location
└── status
```

```text
Position
├── position_id
├── organization_id
├── position_name
├── duty_title
├── grade_requirement
├── skill_requirement
├── clearance_requirement
├── training_profile_id
└── status
```

```text
Assignment
├── assignment_id
├── person_id
├── organization_id
├── position_id
├── duty_title
├── arrival_date
├── assignment_start_date
├── estimated_departure_date
├── actual_departure_date
├── supervisor_id
└── assignment_status
```

---

## 4.3 Training Domain

```text
Course
├── course_id
├── course_name
├── course_code
├── provider
├── description
├── renewal_period
├── mandatory_optional
├── delivery_method
└── status
```

```text
TrainingRequirement
├── requirement_id
├── course_id
├── applicable_org
├── applicable_position
├── applicable_grade
├── applicable_role
├── effective_date
├── expiration_date
├── recurring_interval
├── authority
├── supersedes_requirement
└── status
```

```text
TrainingRecord
├── person_id
├── course_id
├── assigned_date
├── due_date
├── completion_date
├── expiration_date
├── completion_status
├── score
├── certificate
├── source
└── evidence_id
```

The model must support both:

- Required training
- Optional / unique individual training

---

## 4.4 Administrative Domain

```text
AdministrativeAction
├── action_id
├── person_id
├── action_type
├── start_date
├── due_date
├── completion_date
├── status
├── assigned_to
├── approving_authority
├── notes
└── source
```

Possible action types:

- Leave
- Award
- Evaluation
- Counseling
- In-processing
- Out-processing
- Promotion action
- PCS action
- TDY
- School application
- Personnel request
- Access request
- Account request
- Equipment issue/turn-in

---

## 4.5 Leave / Absence Domain

```text
Absence
├── absence_id
├── person_id
├── absence_type
├── start_date
├── end_date
├── approval_status
├── approving_authority
└── notes
```

Potential types:

- Leave
- Pass
- TDY
- Administrative absence
- Parental leave
- Convalescent leave
- Other absence

---


## 4.6 Due-Out / Suspense Management Domain

Due-outs should be modeled as a first-class operational domain rather than stored only as spreadsheet columns or free-text notes.

The Due-Out domain provides the suspense, ownership, reporting-cycle, escalation, workflow, and response layer across Personnel, Training, Organization, and Administrative domains.

### Due-Out Template

Use templates for recurring requirements.

```text
DueOutTemplate
├── template_id
├── title
├── description
├── category
├── staff_section
├── due_out_type
├── recurrence
├── default_owner
├── required_organizations[]
├── default_due_rule
├── instructions
├── authority
├── active
└── version
```

Example:

```text
Update Alert Roster
Recurring: Monthly BA
Staff Section: S-1
Required Organizations: HHC, 185, 188, 189
Output Type: BOOLEAN
Due Rule: End of BA
```

### Due-Out Instance

A template creates an instance for a specific reporting cycle.

```text
DueOut
├── due_out_id
├── template_id
├── reporting_cycle_id
├── title
├── description
├── category
├── staff_section
├── due_out_type
├── priority
├── effective_date
├── due_date
├── status
├── owner
├── requesting_org
├── instructions
├── source
└── active
```

### Due-Out Response

Separate the overall requirement from each organization's response.

```text
DueOutResponse
├── response_id
├── due_out_id
├── organization_id
├── assigned_to
├── status
├── numerator
├── denominator
├── numeric_value
├── text_value
├── date_value
├── submitted_date
├── updated_date
├── notes
└── evidence_id
```

Example:

```text
GTCC Account Verification

HHC: 41 / 49
185: 52 / 55
188: 47 / 50
189: 39 / 42
```

Store ratios as structured values rather than only strings.

### Due-Out Types

Support typed outputs:

```text
BOOLEAN
COUNT
RATIO
PERCENTAGE
TEXT
DATE
DOCUMENT
PERSON_LIST
PERSON_ACTION
DATASET
CHECKLIST
```

### Individual Due-Out Actions

A due-out may generate individual actions.

```text
DueOutAction
├── action_id
├── due_out_id
├── person_id
├── organization_id
├── assigned_to
├── required_action
├── due_date
├── estimated_completion_date
├── canonical_status
├── status_detail
├── blocker
├── latest_update
├── completed_date
└── evidence_id
```

Example:

```text
Due-Out: ETS Processing
Person: John Smith
Required Action: Submit PAR
Due: 2026-09-15
Status: IN_PROGRESS
Latest Update: Checklist provided
```

### Canonical Due-Out Status

Normalize free-text operational updates into a controlled state while preserving the original note.

```text
NOT_STARTED
IN_PROGRESS
WAITING_ON_PERSON
WAITING_ON_EXTERNAL
SUBMITTED
RETURNED_FOR_CORRECTION
SCHEDULED
BLOCKED
COMPLETE
OVERDUE
CANCELLED
NOT_APPLICABLE
NEEDS_REVIEW
```

Example:

```text
Original:
"Called SM. No answer."

Canonical:
WAITING_ON_PERSON

Status Detail:
Called Soldier; no response.
```

### Blockers

```text
DueOutBlocker
├── blocker_id
├── due_out_action_id
├── blocker_type
├── description
├── responsible_party
├── opened_date
├── resolved_date
└── status
```

Potential blocker types:

```text
AWAITING_PERSON
AWAITING_SUPERVISOR
AWAITING_COMMAND
AWAITING_EXTERNAL_ORG
MISSING_DOCUMENT
SYSTEM_ISSUE
SCHEDULING_UNAVAILABLE
PENDING_TRANSFER
PENDING_RETIREMENT
OTHER
```

### Dependencies

```text
DueOutDependency
├── due_out_id
├── depends_on_due_out_id
└── dependency_type
```

Example:

```text
Departure Confirmed
      ↓
Closeout Evaluation
      ↓
Award
      ↓
Out-Processing
```

### Reporting Cycles

```text
ReportingCycle
├── cycle_id
├── name
├── start_date
├── end_date
├── reporting_date
├── cycle_type
└── status
```

Examples:

```text
AUG 2026 BA
SEP 2026 BA
OCT 2026 BA
```

Recurring due-out templates should instantiate automatically for each applicable reporting cycle.

### Due-Out Escalation

Support configurable escalation.

Example:

```text
30 days before due
→ notify action owner

14 days
→ notify owner + supervisor

7 days
→ elevate priority

Overdue
→ manager dashboard + escalation queue
```

### Due-Out Relationships

A due-out should reference authoritative records rather than duplicate them.

```text
                    Due-Out Engine
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
   Personnel          Training        Organization
       │                 │                 │
       └────────────┬────┴───────┬────────┘
                    │            │
              Administrative   Documents
                    │            │
                    └─────┬──────┘
                          │
                     Due-Out Status
```

Examples:

- ETS due-out → Personnel / Assignment record
- Training due-out → Training requirement / completion
- Evaluation due-out → Administrative action
- Alert roster due-out → Personnel/contact data
- Medical/admin due-out → Applicable external or administrative status record

---

## 4.7 Document / Evidence Domain


```text
Document
├── document_id
├── filename
├── document_type
├── uploaded_by
├── upload_date
├── storage_location
├── hash
├── version
├── classification
├── pii_level
└── status
```

```text
Evidence
├── evidence_id
├── document_id
├── entity_type
├── entity_id
├── page
├── row
├── section
├── extracted_text
├── confidence
└── extraction_agent
```

---

## 4.8 Future Domains

The platform should support later addition of:

- Qualifications
- Certifications
- Skills
- Education
- Experience
- Awards
- Travel
- Equipment
- Access/accounts
- In-processing
- Out-processing
- Readiness
- Recruiting
- Performance

---

# 5. Canonical HR State

Use a common, serializable, provenance-carrying state shared across agents.

```text
HRState
│
├── people[]
├── organizations[]
├── positions[]
├── assignments[]
├── courses[]
├── training_requirements[]
├── training_records[]
├── due_out_templates[]
├── due_outs[]
├── due_out_responses[]
├── due_out_actions[]
├── due_out_blockers[]
├── reporting_cycles[]
├── administrative_actions[]
├── absences[]
├── documents[]
├── evidence[]
├── validation_issues[]
├── unresolved_questions[]
└── provenance[]
```

---

# 6. Field Handling Policy

Each field should declare how missing values are handled.

```text
REQUIRED
RECOMMENDED
OPTIONAL
DEFAULTABLE
```

Example:

```text
Person

name             REQUIRED
employee_id      RECOMMENDED
organization     OPTIONAL
position         OPTIONAL
email            OPTIONAL
supervisor       OPTIONAL
status           DEFAULT = ACTIVE
created_at       DEFAULT = current timestamp
```

Example interaction:

```text
User:
Add John Smith to Division A.

System:
I have John Smith and Division A.
Employee ID, position, email, and supervisor were not provided.
Would you like to add any of those, or should I leave them blank?

User:
Leave them blank.

System:
John Smith was added successfully.
```

The user should also be able to provide instructions such as:

```text
Add John Smith. Use defaults or leave missing optional information blank.
```

---

# 7. Domain Registry

Create an extensible domain registry.

```text
Domain Registry
│
├── personnel
├── organization
├── training
├── due_out
├── administrative
├── documents
└── future domains
```

Each domain registers:

- Schema
- Entities
- Relationships
- Validation rules
- Permissions
- CRUD tools
- Report templates
- PII classification
- Vector collections
- Agent-access rules

This allows new databases/domains to be introduced without redesigning the core orchestrator.

---

# 8. Development Roadmap

# Phase 0 — Architecture and Security Foundation

## Goal

Establish architecture and security boundaries before processing real personnel data.

## Tasks

- Define frontend/chat architecture.
- Define agent orchestration layer.
- Define database access layer.
- Deploy PostgreSQL development environment.
- Deploy vector database.
- Establish object/document storage.
- Implement authentication.
- Implement role-based access control.
- Define field-level PII restrictions.
- Define encryption requirements.
- Implement secrets management.
- Implement audit logging.
- Define retention/deletion policy.
- Define document classification/PII tagging.
- Prevent unrestricted SQL access by agents.

## Exit Criteria

- Base architecture documented.
- Authentication/authorization model established.
- PII handling model established.
- Structured database available.
- Vector database available.
- Object storage available.

---

# Phase 1 — Canonical HR Domain Model

## Goal

Implement the initial structured data model.

## Initial Domains

1. Personnel
2. Organization
3. Training
4. Due-Out / Suspense Management
5. Administrative
6. Documents

## Tasks

- Define database entities.
- Define relationships.
- Define IDs and keys.
- Define field policies.
- Define validation rules.
- Define PII classification.
- Implement database migrations.
- Create sample/test data.
- Create canonical HR state.

## Exit Criteria

- Schemas implemented.
- Relationships validated.
- Test data available.
- CRUD service layer available.

---

# Phase 2 — Domain Registry and Extensibility Framework

## Goal

Allow future databases/domains to be added without changing the core architecture.

## Tasks

- Implement domain registry.
- Define domain registration interface.
- Register initial domains.
- Add domain-specific tool definitions.
- Add validation-policy registration.
- Add permission-policy registration.
- Add report-template registration.

## Exit Criteria

A developer can add a new domain without changing the main orchestrator.

---

# Phase 3 — Conversational CRUD

## Goal

Manage structured databases using natural language.

## Supported Intents

```text
CREATE
READ
UPDATE
DEACTIVATE
SEARCH
REPORT
UPLOAD
```

## Example Commands

```text
Add Jane Doe as a Data Scientist in J21.

Show me Jane Doe.

Change Jane Doe's supervisor to John Smith.

Mark Jane's annual training complete.

Deactivate John Doe.

Show everyone in J21.
```

## Tasks

- Implement intent/orchestrator agent.
- Implement controlled personnel tools.
- Implement organization tools.
- Implement training tools.
- Implement administrative tools.
- Implement missing-field handling.
- Implement default values.
- Implement confirmation policies.
- Implement write auditing.

## Exit Criteria

Users can create, retrieve, update, search, and deactivate records without SQL.

---

# Phase 4 — Natural-Language Query Engine

## Goal

Allow conversational queries across one or more domains.

## Example Queries

```text
Show everyone in J21.

Who has overdue training?

Show people departing in the next 90 days.

Who is on leave next week?

Which personnel have both incomplete training and open administrative actions?

Show all open S-1 due-outs.

Which due-outs are overdue?

Show 185's incomplete due-outs.

What is due before the next BA?

Show all due-outs blocked by an external organization.
```

## Approach

Convert natural language into a structured query plan rather than unrestricted raw SQL.

Example:

```json
{
  "entity": "person",
  "filters": [
    {"organization": "J21"},
    {"training_status": "OVERDUE"}
  ]
}
```

Application code converts the query plan into approved SQL.

## Conversational Context

Support:

```text
User:
Show overdue training.

User:
Only J21.

User:
Only people departing this year.

User:
Export that.
```

The system should preserve the current result/query context.

## Exit Criteria

- Multi-domain queries work.
- Follow-up filtering works.
- Query provenance is recorded.
- Unsafe SQL is not executed.

---

# Phase 5 — Structured File Ingestion

## Goal

Import structured/semi-structured files.

## Supported Formats

- XLSX
- XLS
- CSV

## Pipeline

```text
Upload
  ↓
Parser
  ↓
Header Detection
  ↓
Schema Mapping Agent
  ↓
Validation
  ↓
Entity Resolution
  ↓
Import Preview
  ↓
Database Commit
```


## Spreadsheet Structure Agent

Do not assume:

```text
one workbook = one table
one sheet = one table
first row = header
```

Operational HR workbooks may contain:

- Multiple unrelated tables on one sheet.
- Section headers that change the meaning of rows below them.
- Merged cells.
- Blank spacer rows.
- Repeated headers.
- Unit response columns.
- Counts and ratios.
- Dates stored in multiple formats.
- Free-text action/status notes.
- Person names embedded inside multi-line cells.

Use:

```text
Workbook
   ↓
Sheet Classification
   ↓
Region / Section Detection
   ↓
Table Detection
   ↓
Header Detection
   ↓
Semantic Section Identification
   ↓
Schema Mapping
   ↓
Record Extraction
```

The agent should be able to recognize structures such as:

```text
Medical
  ↓
MRC 3
  ↓
Individual personnel rows
```

and assign those records to the correct canonical category.

## Date Normalization Service

Normalize:

```text
Excel serial dates
YYYYMMDD values
MM/DD/YYYY
Free-text dates
"Appointment scheduled 8/31"
"TBD"
"N/A"
blank values
```

into typed fields where possible:

```text
actual_date
estimated_date
due_date
completion_date
status_update_date
```

Always preserve the original source value for provenance.


## Schema Mapping Example

Incoming:

```text
Full Name
Emp #
Unit
Training Name
Completion
```

Mapped to:

```text
Full Name      → person.name
Emp #          → person.employee_id
Unit           → assignment.organization
Training Name  → course.name
Completion     → training_record.completion_date
```

## Import Preview

```text
Records detected:        1,027
New personnel:              84
Existing personnel:        923
Potential duplicates:       11
Missing required fields:     9
Unmapped columns:             2
```

Require confirmation for significant bulk writes.

## Exit Criteria

Excel and CSV files can populate multiple domain schemas reliably.

---

# Phase 6 — Unstructured Document Ingestion

## Goal

Extract structured records from unstructured documents.

## Supported Formats

- TXT
- PDF
- DOC
- DOCX

## Pipeline

```text
Document
   ↓
Classification
   ↓
Text/Table Extraction
   ↓
Chunking
   ↓
Vector DB
   ↓
Extraction Agent
   ↓
Canonical HR Records
   ↓
Validation
   ↓
Structured Database
```

## Example: Training Certificate

Extract:

```text
person
course
completion_date
certificate_number
expiration_date
```

## Example: Personnel Memorandum

Extract:

```text
person
organization
position
arrival_date
departure_date
```

## Example: Policy Document

Extract:

```text
requirement
applicable_population
course
frequency
effective_date
authority
```

## Exit Criteria

Unstructured files produce structured, reviewed records with source attribution.

---

# Phase 7 — Provenance and Evidence Engine

## Goal

Make important records traceable to their source.

Example:

```text
John Smith
Cyber Awareness
Completed: 2026-08-15

Source:
Annual_Training_Roster.xlsx
Sheet: J21
Row: 72
Uploaded: 2026-08-20
```

Or:

```text
Source:
Training_Certificate_JohnSmith.pdf
Page: 1
Confidence: 0.97
```

Track:

- Source document
- Page/row/section
- Extraction method
- Confidence
- Timestamp
- User
- Agent
- Original value
- Modified value

## Exit Criteria

Important answers and database changes can be traced to source evidence.

---

# Phase 8 — Entity Resolution and Data Quality

## Goal

Resolve duplicate or conflicting records.

Example:

```text
John Smith
John A Smith
Smith, John A.
J. Smith
```

Potential signals:

- Internal person ID
- DOD ID
- Employee ID
- Email
- Organization
- Position
- Date range
- Name similarity

## Data Quality Agent

Detect:

- Duplicate personnel
- Conflicting completion dates
- Unknown organizations
- Unknown training
- Invalid dates
- Duplicate training records
- Missing identifiers
- Expired requirements
- Inconsistent positions
- Orphaned records

## Exit Criteria

The system flags ambiguous or conflicting data rather than silently changing authoritative records.

---


# Phase 8A — Due-Out / Suspense Management

## Goal

Convert spreadsheet-based due-outs into structured, queryable, assignable, auditable operational workflows.

This phase is part of the MVP.

## Tasks

- Implement `DueOutTemplate`.
- Implement `DueOut`.
- Implement `DueOutResponse`.
- Implement `DueOutAction`.
- Implement `DueOutBlocker`.
- Implement `DueOutDependency`.
- Implement `ReportingCycle`.
- Implement recurring due-out generation.
- Implement typed due-out responses.
- Implement canonical due-out statuses.
- Implement organization-level responses.
- Implement person-level actions.
- Implement due dates and overdue calculation.
- Implement ownership/assignment.
- Implement escalation policies.
- Connect due-outs to Personnel, Training, Organization, Administrative, and Document domains.
- Add due-out evidence/provenance.
- Add Streamlit due-out dashboard.
- Add editable due-out review table.
- Add due-out chat tools.
- Add BA/reporting-cycle rollup.

## Example User Commands

```text
Show all of my open due-outs.

Show only S-1 due-outs.

What is due before the next BA?

Show 185's incomplete due-outs.

Which due-outs are overdue?

Show all Soldiers waiting on an evaluation.

Who has an ETS action within 90 days?

What medical actions remain incomplete?

Which units have not completed GTCC verification?

Show everything blocked by an external organization.

What changed since last BA?

Give me the five most urgent due-outs.

Export the current due-out report to Excel.
```

## Streamlit Due-Out Page

Recommended layout:

```text
Due-Out Dashboard
│
├── Reporting Cycle Selector
├── Summary Metrics
│   ├── Open
│   ├── Due Soon
│   ├── Overdue
│   ├── Blocked
│   └── Complete
│
├── Filters
│   ├── Staff Section
│   ├── Organization
│   ├── Owner
│   ├── Status
│   ├── Priority
│   └── Due Date
│
├── Editable Due-Out Table
├── Selected Due-Out Detail
├── Evidence / Source
├── Action History
└── Export / Report
```

## Exit Criteria

- Recurring due-outs can be created from templates.
- Due-outs can be assigned at organization and individual levels.
- Users can update due-outs through chat or editable tables.
- Free-text statuses are normalized.
- Blockers and dependencies are tracked.
- Due-outs can be filtered by organization, staff section, owner, status, and reporting cycle.
- Overdue and due-soon status is calculated automatically.
- Due-out reports can be exported.
- All important changes are auditable.

---

# Phase 9 — Training Requirement Engine

## Goal

Determine which training applies to each person.

Example:

```text
IF
organization = J21
AND
position = Analyst

THEN
Cyber Awareness = Required
OPSEC = Required
Course X = Required
```

Support requirements based on:

- Organization
- Position
- Role
- Grade
- Individual assignment
- Optional individual courses
- Recurring intervals
- Expiration dates
- Waivers
- Exceptions

## Training Status Values

```text
COMPLETE
DUE_SOON
OVERDUE
NOT_STARTED
EXPIRED
WAIVED
NOT_APPLICABLE
UNKNOWN
```

The LLM may interpret policy language, but deterministic code should calculate final status.

## Exit Criteria

The system automatically determines training compliance from stored requirements and records.

---

# Phase 10 — Reporting and Export Framework

## Goal

Generate multiple outputs from the same verified dataset.

## Default Output

On-screen answer or table.

## Export Formats

- XLSX
- CSV
- TXT
- PDF

Potential link outputs:

- Secure temporary download URL
- Dashboard URL
- Stored report URL

## Architecture

```text
Database Query
     ↓
Result Dataset
     │
     ├── Screen
     ├── XLSX
     ├── CSV
     ├── TXT
     └── PDF
```

The report generator must use the verified result dataset rather than asking the LLM to regenerate values.

## Initial Reports

1. Organization roster
2. Training compliance
3. Overdue training
4. Training expiration
5. Arrival/departure report
6. Leave/absence report
7. Open administrative actions
8. Individual personnel summary
9. Manager summary
10. Data-quality report
11. Due-out / suspense rollup
12. Reporting-cycle / BA due-out report
13. Blocked due-outs report
14. Due-outs by organization
15. Due-outs by staff section

## Exit Criteria

Any supported query result can be exported consistently.

---

# Phase 11 — Administrative Workflow Engine

## Goal

Turn administrative records into durable workflows.

Example:

```text
New Arrival
    ↓
Generate Onboarding Actions
    ↓
Assign Required Training
    ↓
Request Accounts
    ↓
Assign Supervisor
    ↓
Track Completion
```

Potential workflows:

- Due-out / suspense escalation
- Recurring reporting-cycle due-outs
- In-processing
- Out-processing
- PCS
- TDY
- Leave
- New employee onboarding
- Training remediation
- Account/access requests
- Position changes

## Required Workflow Capabilities

- Durable checkpoints
- Pause/resume
- Idempotent actions
- Human approval
- Failure isolation
- Auditability

## Exit Criteria

Multi-step personnel workflows retain state and can resume safely.

---

# Phase 12 — In-Processing and Out-Processing Automation

## Goal

Automatically generate tasks using arrival and departure data.

Example:

```text
Arrival Date = September 15
        ↓
Create:
- onboarding checklist
- mandatory training
- supervisor task
- account requests
```

Departure:

```text
Estimated departure ≤ 60 days
        ↓
Generate:
- out-processing checklist
- account termination tasks
- equipment return tasks
- knowledge transfer tasks
```

## Exit Criteria

Arrival/departure events can automatically trigger approved workflows.

---

# Phase 13 — Qualifications, Certifications, Skills, and Education

## Goal

Expand into talent and workforce management.

Add domains:

```text
Qualification
PersonQualification

Certification
PersonCertification

Skill
PersonSkill

Education
Experience
```

Example queries:

```text
Find people with Python, AWS, and machine-learning experience.

Who has a CISSP expiring this year?

Who is qualified for Position X?
```

## Exit Criteria

New talent domains are added through the domain registry without changing the core architecture.

---

# Phase 14 — Personnel Readiness Engine

## Goal

Calculate derived readiness across domains.

Example:

```text
John Smith

Training        GREEN
Administrative  AMBER
Qualification   GREEN
Assignment      GREEN
Access          RED

Overall         RED
```

Blocking condition:

```text
System X access is incomplete.
```

The readiness engine calculates the result deterministically.

The LLM explains the result conversationally.

## Exit Criteria

Users can see overall readiness and the conditions preventing readiness.

---

# Phase 15 — Advanced Reporting and Management Analytics

## Goal

Provide management-level analytics.

Potential analytics:

- Organization readiness
- Training trends
- Overdue trends
- Upcoming departures
- Staffing gaps
- Position vacancy analysis
- Completion percentages
- Requirement-change impact
- Administrative workload
- Data-quality trends

Example:

```text
J21 Training Readiness

Current:     91.3%
Last Month:  88.5%
Change:      +2.8%

Primary Gap:
Course ABC — 14 personnel incomplete
```

The application calculates analytics.

The LLM summarizes and explains.

---

# Phase 16 — Policy / Requirement Intelligence

## Goal

Combine structured database truth with vector-based policy retrieval.

Example user question:

```text
What policy requires this training?
```

System:

```text
Structured DB:
Course X is required for Position Y.

Vector DB:
Retrieve supporting policy and section.

Response:
Course X is required for personnel in Position Y under Policy Z,
Section 4.2.
```

## Exit Criteria

The system can connect structured requirements to supporting policy evidence.

---

# Phase 17 — Human Review and Approval

## Goal

Provide explicit review for ambiguous or high-impact actions.

Examples requiring review:

- Potential duplicate person
- Unknown course
- New database field
- Policy interpretation
- Bulk updates
- Requirement replacement
- Identity conflict
- Large imports
- Significant deletions/deactivations

Example:

```text
I found two records that may represent the same person.

Match confidence: 82%

Review before merging.
```

## Exit Criteria

High-risk or ambiguous agent actions can be paused for authorized human review.

---

# Phase 18 — Production Hardening

## Security

- RBAC / ABAC
- Field-level PII controls
- Encryption at rest
- Encryption in transit
- Secrets management
- Session security
- Audit trails
- Document access control
- Secure logging
- Data retention controls

## Reliability

- Idempotent writes
- Database transactions
- Rollback
- Backups
- Restore
- Record versioning
- Durable agent checkpoints
- Failure isolation

## LLM Controls

- Prompt injection protection
- Restricted tools
- Authorization before write operations
- Schema validation
- Output validation
- Confidence thresholds
- Bounded agent loops
- Cost/token controls
- Tool allowlists

## Testing

- Unit tests
- Database tests
- Schema tests
- Ingestion tests
- Agent evaluation suite
- Permission tests
- Report-validation tests
- Adversarial prompt tests
- Bulk-import tests
- Recovery tests

## Exit Criteria

The platform is hardened for broader operational deployment.

---

# 9. MVP Scope

Do not build all phases before demonstrating value.

A strong MVP consists of:

```text
Phase 0    Architecture and Security
Phase 1    Canonical HR Model
Phase 2    Domain Registry
Phase 3    Conversational CRUD
Phase 4    Natural-Language Query
Phase 5    Excel/CSV Ingestion
Phase 6    PDF/DOC/TXT Ingestion
Phase 7    Provenance
Phase 8    Data Quality
Phase 8A   Due-Out / Suspense Management
Phase 9    Training Requirements
Phase 10   Reporting and Export
```

The MVP should demonstrate:

1. Upload a personnel roster.
2. Upload training records.
3. Upload a complex due-out workbook.
4. Detect multiple tables/sections within a workbook.
5. Normalize due-outs into structured records.
6. Upload policy or supporting documents.
7. Add personnel conversationally.
8. Update personnel conversationally.
9. Create and assign due-outs conversationally.
10. Ask who belongs to a unit.
11. Ask who has incomplete or overdue training.
12. Ask who is arriving or departing.
13. Ask what due-outs are open, overdue, blocked, or due soon.
14. Filter due-outs by staff section, organization, reporting cycle, or owner.
15. Retrieve evidence supporting a record or due-out.
16. Edit reviewed records in Streamlit tables.
17. Generate a manager-ready Excel or PDF report.
18. Generate a BA/reporting-cycle due-out rollup.

The first compelling demonstration should be:

```text
Upload messy operational workbook
          ↓
Agent detects sections/tables
          ↓
Preview normalized records
          ↓
User approves import
          ↓
Structured HR + Due-Out databases
          ↓
User asks questions in chat
          ↓
On-screen table / dashboard
          ↓
Excel / PDF report
```
# 10. Recommended Development Sequence

```text
FOUNDATION
   │
   ├─ Phase 0   Architecture / Security
   ├─ Phase 1   Canonical HR Model
   └─ Phase 2   Domain Registry
           │
           ▼
STREAMLIT CORE APPLICATION
   │
   ├─ Streamlit navigation / authentication
   ├─ Phase 3   Conversational CRUD
   ├─ Phase 4   Natural-Language Query
   └─ Phase 5   Structured Ingestion
           │
           ▼
AGENTIC DOCUMENT + SPREADSHEET PROCESSING
   │
   ├─ Spreadsheet Structure Agent
   ├─ Phase 6   Unstructured Ingestion
   ├─ Phase 7   Provenance
   └─ Phase 8   Data Quality
           │
           ▼
OPERATIONAL TRACKING
   │
   ├─ Phase 8A  Due-Out / Suspense Management
   ├─ Phase 9   Training Requirements
   └─ Phase 10  Reporting / Export
           │
           ▼
WORKFLOW AUTOMATION
   │
   ├─ Phase 11  Administrative Workflows
   └─ Phase 12  In/Out Processing
           │
           ▼
EXPANSION
   │
   ├─ Phase 13  Skills / Qualifications
   ├─ Phase 14  Readiness
   ├─ Phase 15  Analytics
   └─ Phase 16  Policy Intelligence
           │
           ▼
ENTERPRISE
   │
   ├─ Phase 17  Human Review
   └─ Phase 18  Production Hardening
```
# 11. Initial Agent Architecture

## Orchestrator / Intent Agent

Determines user intent and selects the appropriate tools/workflow.

Examples:

```text
CREATE
READ
UPDATE
DEACTIVATE
SEARCH
UPLOAD
REPORT
SCHEMA_CHANGE
```

---

## Ingestion Agent

Determines:

- File type
- Document type
- Required parser
- Target domain
- Required extraction workflow

---

## Schema Mapping Agent

Maps incoming columns/fields to the canonical schema.

Example:

```text
"Emp #"            → employee_id
"Unit"             → organization
"Training Name"    → course_name
"Completed"        → completion_date
```

---

## Spreadsheet Structure Agent

Interprets irregular workbook layouts before schema mapping.

Responsibilities:

- Detect logical sections within sheets.
- Detect multiple tables within a sheet.
- Identify repeated/shifted headers.
- Interpret merged labels and section boundaries.
- Detect organization response columns.
- Extract counts, ratios, dates, and free-text statuses.
- Normalize irregular operational spreadsheets into candidate records.

---

## Extraction Agent

Extracts structured entities and relationships from unstructured documents.

---

## Due-Out / Suspense Agent

Handles due-out-specific interpretation and workflow routing.

Responsibilities:

- Identify due-out requirements.
- Determine reporting cycle.
- Identify responsible organization/owner.
- Interpret free-text status updates.
- Identify blockers.
- Identify person-level child actions.
- Route updates through controlled Due-Out tools.
- Generate summaries and rollups without changing authoritative calculations.

---

## Entity Resolution Agent

Determines whether records refer to the same person, organization, course, or requirement.

---

## Validation / Data Quality Agent

Checks:

- Missing required information
- Invalid types
- Duplicates
- Conflicts
- Unknown values
- Impossible dates
- Broken relationships

---

## Database Agent / Tool Layer

Executes approved database actions through controlled functions.

The LLM should not receive unrestricted SQL access.

---

## Query Agent

Converts user language into approved structured query specifications.

---

## Report Agent

Formats verified result datasets into:

- Screen
- Table
- XLSX
- CSV
- TXT
- PDF
- Secure URL

---

# 12. Confirmation and Risk Model

## Read Operations

No confirmation required.

Example:

```text
Show all overdue personnel.
```

---

## Normal Record Writes

Validate first.

Example:

```text
Add Jane Doe to J21.
```

If recommended information is missing, ask whether the user wants to provide it or leave it blank/defaulted.

---

## High-Impact Writes

Require confirmation.

Examples:

```text
Deactivate 400 personnel.

Mark everyone complete.

Replace an organization-wide training requirement.

Import 10,000 records.

Delete a domain.
```

Example response:

```text
This operation will update 417 personnel records.

Proceed?
```

---

# 13. Audit Requirements

Every important write should create an audit event.

```text
AuditEvent

timestamp
user
action
entity_type
entity_id
previous_value
new_value
source
conversation_id
agent
confidence
```

Example:

```text
2026-08-25 10:32
User: manager@example
Action: UPDATE
Person: Jane Doe
Field: supervisor
Old: Bob Smith
New: Kevin Jones
Source: Chat
```

---

# 14. Long-Term Product Direction

The initial system is a personnel/training tracker, but the architecture should support expansion into a broader **agentic workforce and HR operations platform**.

Potential evolution:

```text
Training Tracker
      ↓
Personnel Administration Portal
      ↓
Personnel Readiness Platform
      ↓
Talent / Workforce Management
      ↓
Agentic HR Operations Platform
```

The reusable platform architecture can support multiple business domains while sharing:

- Agent orchestration
- Ingestion
- Retrieval
- Provenance
- Validation
- Database management
- Reporting
- Human review
- Workflow execution
- Security controls


---

# 15. Streamlit Decision Summary

Use Streamlit for the MVP and initial operational release.

## Why It Fits

- Fast Python-native development.
- Natural fit with the existing LLM/agent stack.
- Strong support for dataframes and editable tables.
- Suitable for file-heavy workflows.
- Suitable for chat-driven workflows.
- Easy construction of internal dashboards and review queues.
- Multipage application support.
- Downloadable report workflows.
- Enterprise identity can be integrated at the UI layer.

## Constraints to Design Around

- Streamlit reruns application scripts during interaction.
- Session state should not be treated as durable workflow storage.
- Authentication does not replace application-level authorization.
- Core services should not depend on Streamlit APIs.
- Very complex enterprise UX may eventually justify a separate frontend.
- Large report files should be stored/generated through backend/object storage when practical.

## Architectural Decision

```text
NOW
Streamlit
   │
   ▼
Stable Application Services
   │
   ▼
Agents / Databases / Workflows

LATER, IF REQUIRED
React / Other Frontend
   │
   ▼
Same Application Services
```

This allows rapid delivery without locking the core platform to Streamlit.
