# Ada — Personnel, Training & Operations Assistant Roadmap (v3)

> **Ada** = *AI-Driven Assistant*. This document is **roadmap v3** and **supersedes v2**
> (`agentic_hr_personnel_training_portal_roadmap_v2.md`, now removed). v3 rebrands the
> product as Ada, fixes the technology stack on **AWS Bedrock + Streamlit**, generalizes
> the product beyond its initial military application, and completes every development
> phase with a fixed delivery template.

---

## 1. Project Purpose

**Ada** is a conversational, agentic assistant for **personnel, training, organizational,
and administrative data management**. It makes HR-style record keeping and task tracking
easy: users talk to Ada in natural language, upload messy files, and get back clean,
structured, auditable data and reports.

Ada allows users to:

- Upload and ingest `XLSX`, `CSV`, `TXT`, `PDF`, `DOC`, and `DOCX` files.
- Extract, normalize, validate, and store information in structured databases.
- Manage personnel, training, organization, administrative actions, and due-outs (tasks
  with suspenses) through a natural-language chat interface.
- Use **Streamlit** as the initial application interface for chat, file upload, editable
  tables, dashboards, review screens, and report downloads.
- Add, retrieve, update, deactivate, and search records without knowing SQL.
- Ask follow-up questions conversationally.
- Generate outputs as on-screen answers, on-screen tables, Excel, CSV, TXT, PDF, and
  secure/downloadable URLs.
- Track provenance and supporting evidence for extracted or modified information.
- Support multiple domains/databases that can be added over time.

### Relationship to IWB

Ada **reuses architectural patterns** proven in the AISI Intelligence Workbench (IWB) —
agent orchestration, document ingestion, vector/RAG retrieval, canonical structured state,
provenance, validation, confidence handling, durable workflows/checkpoints, human review,
and report generation. IWB is a **pattern source, not a parent product**. Ada is its own
product with its own brand, package (`ada`), and configuration namespace (`ADA__*`).

---

## 2. Product Positioning and Application Profiles

Ada's **core is general**: people, organizations, training/compliance, tasks with
deadlines, administrative actions, and documents exist in almost every workforce.

Ada's **first application profile is military-flavored** (staff sections, reporting/Battle
Assembly cycles, ETS/PCS, alert rosters). These are an **initial profile**, not the product
identity. A **profile** is a first-class configuration concept (see item in Section 4 and
Phase 2) that:

- Swaps terminology in prompts, labels, and reports.
- Toggles which domains and report templates are enabled.
- Provides profile-specific validation and defaults.

### Terminology map (military ↔ general)

| Military profile term | General profile term |
|---|---|
| Staff section (S-1, J21) | Department / team |
| Battle Assembly (BA) / reporting cycle | Reporting period / cycle |
| Due-out / suspense | Task / action item with deadline |
| ETS / out-processing | Offboarding |
| In-processing | Onboarding |
| Soldier / Service Member | Employee / member |
| Rank / grade | Level / grade |
| Alert roster | Contact roster |

The data model uses neutral internal names (`person`, `organization`, `assignment`,
`due_out`); profiles supply the display vocabulary.

---

## 3. Technology Stack

| Concern | Choice | Notes |
|---|---|---|
| UI | **Streamlit** | Presentation layer only (MVP + early releases) |
| LLM runtime | **AWS Bedrock** | Sole LLM runtime for v1 |
| Agent framework | **Strands** (`strands-agents`, `BedrockModel`) | Same pattern as IWB |
| AWS auth | `boto3.Session` via `AWS_PROFILE` + `AWS_REGION` | Reuses the operator's existing SSO/IAM profile |
| Chat models | Bedrock model IDs via `ADA__BEDROCK_CHAT_MODEL_ID` (+ optional switch list `ADA__BEDROCK_CHAT_MODELS`) | Model router with fallbacks (Phase 3+) |
| Embeddings | `amazon.titan-embed-text-v2:0` (fixed) | Switching invalidates the vector space |
| Source of truth | **PostgreSQL** (local SQLite/JSON default; Postgres adapter for prod) | Structured records |
| Semantic store | **Chroma / vector DB** | Policies, SOPs, uploaded docs, evidence |
| Object storage | Local filesystem (default) / **S3** (prod) | Documents and generated artifacts |
| Secrets | env (default) / AWS Secrets Manager / SSM | `ADA__SECRETS_BACKEND` |
| Packaging | `uv` + `pyproject.toml`, Python `>=3.13` | Mirrors IWB |
| Config namespace | `ADA__*` (+ standard `AWS_*`) | No `AISI` prefix |

### AWS Bedrock connection pattern

```text
AWS_PROFILE + AWS_REGION
        │
   boto3.Session(profile_name=..., region_name=...)
        │
   session.client("bedrock-runtime", region_name=...)
        │
   strands.models.BedrockModel(model_id=..., max_tokens=..., [temperature])
        │
   strands.Agent(model=BedrockModel(...))
```

Anthropic models on Bedrock reject a custom `temperature`; Ada follows IWB and omits it for
that provider. All AWS/Bedrock settings resolve from the environment through `AdaConfig`.

### Local-first defaults

Ada runs fully local by default (SQLite/JSON + local Chroma + local object store); the only
hard cloud dependency is **Bedrock** for embeddings and generation. Production adapters
(Postgres, S3, Secrets Manager) are opt-in via `ADA__*` variables.

---

## 4. Target Architecture

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
                       Application / Service Layer
                                 │
                         Agent Orchestrator (Bedrock)
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
    Intent / Query          Ingestion / Mapping       Workflow / Report
      Agents                    Agents                    Agents
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                  Validation / Authorization / Guardrails
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

### 4.1 Streamlit interface strategy

Use **Streamlit as the presentation layer only** for the MVP and early operational
releases. It is a strong fit because Ada is Python-based, data-centric, LLM/chat-centric,
file-ingestion heavy, table/report heavy, and internal/enterprise-workflow oriented.

**Initial pages**

```text
Ada
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

**Architecture rule:** Do not place core rules, LLM orchestration, database logic, or
authorization inside page scripts. Streamlit calls stable **application services**:

```text
Streamlit UI
     │
     ▼
Application Services
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

**Session-state rule:** Use Streamlit session state only for transient UI state (filters,
current selection, chat display). Persist durable state (conversations, checkpoints, pending
approvals, change sets, report jobs, due-out state, import staging) in the backend.

**Auth vs. authz:** The UI may authenticate via enterprise identity/OIDC. **Authorization
remains application-controlled** (which domains, organizations, PII fields, write
operations, reports, and bulk actions a user may access).

### 4.2 Core architectural principles

- **Structured DB is the source of truth.** The vector DB is for policies, SOPs, uploaded
  documents, evidence, and semantic retrieval — never the authoritative personnel/training
  record.
- **LLMs interpret; deterministic services execute.** LLMs interpret intent, extract, map
  schemas, explain, and summarize. Deterministic code validates, calculates dates/compliance/
  readiness, authorizes, writes, and generates exports.
- **No unrestricted SQL for the LLM.** Provide controlled domain tools (`create_person()`,
  `update_person()`, `search_people()`, `assign_person()`, …), never `execute_sql(...)`.

### 4.3 Application-profile mechanism

A **profile** is a registered config bundle: `{ terminology, enabled_domains,
report_templates, defaults, validation_overrides }`. The `military` profile ships first; a
neutral `general` profile is the fallback. Profiles are resolved at startup
(`ADA__PROFILE=military|general`) and injected into prompts, labels, and the domain registry
so the same core serves multiple markets.

---

## 5. Proposed Domain Databases

Initially separate PostgreSQL **schemas**, not separate servers.

```text
ada_platform
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

### 5.1 Personnel / Identity domain

```text
Person
├── person_id
├── first_name
├── middle_name
├── last_name
├── preferred_name
├── rank_grade          # profile-labeled (rank | level)
├── service_component   # profile-labeled
├── official_email
├── duty_phone
├── status
├── created_at
└── updated_at
```

Sensitive data is isolated:

```text
SensitiveIdentity
├── person_id
├── national_id_encrypted   # e.g. SSN/DoD ID, encrypted
├── date_of_birth
└── access_classification
```

Rules: national IDs are never primary keys; all domains reference internal `person_id`;
`Contact` and `EmergencyContact` are separate entities.

### 5.2 Organization / Assignment domain

```text
Organization
├── organization_id
├── name
├── abbreviation
├── parent_organization_id
├── organization_type
├── location
└── status

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

### 5.3 Training domain

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

Supports both required and optional/individual training.

### 5.4 Administrative domain

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

Action types: Leave, Award, Evaluation, Counseling, In-processing, Out-processing,
Promotion, PCS, TDY, School application, Personnel request, Access request, Account request,
Equipment issue/turn-in.

### 5.5 Leave / Absence domain

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

Types: Leave, Pass, TDY, Administrative absence, Parental leave, Convalescent leave, Other.

### 5.6 Due-Out / Suspense domain

Due-outs are a **first-class operational domain** (suspense, ownership, reporting cycle,
escalation, workflow, and response) across Personnel, Training, Organization, and
Administrative domains — not spreadsheet columns or free text.

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

DueOut                      # instance for a reporting cycle
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

DueOutResponse              # per-organization response
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

DueOutAction               # per-person action
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

DueOutBlocker
├── blocker_id
├── due_out_action_id
├── blocker_type
├── description
├── responsible_party
├── opened_date
├── resolved_date
└── status

DueOutDependency
├── due_out_id
├── depends_on_due_out_id
└── dependency_type

ReportingCycle
├── cycle_id
├── name
├── start_date
├── end_date
├── reporting_date
├── cycle_type
└── status
```

**Typed outputs:** `BOOLEAN, COUNT, RATIO, PERCENTAGE, TEXT, DATE, DOCUMENT, PERSON_LIST,
PERSON_ACTION, DATASET, CHECKLIST`. Store ratios as structured values, not strings.

**Canonical status** (normalize free text, preserve original): `NOT_STARTED, IN_PROGRESS,
WAITING_ON_PERSON, WAITING_ON_EXTERNAL, SUBMITTED, RETURNED_FOR_CORRECTION, SCHEDULED,
BLOCKED, COMPLETE, OVERDUE, CANCELLED, NOT_APPLICABLE, NEEDS_REVIEW`.

**Blocker types:** `AWAITING_PERSON, AWAITING_SUPERVISOR, AWAITING_COMMAND,
AWAITING_EXTERNAL_ORG, MISSING_DOCUMENT, SYSTEM_ISSUE, SCHEDULING_UNAVAILABLE,
PENDING_TRANSFER, PENDING_RETIREMENT, OTHER`.

Recurring templates instantiate automatically per applicable reporting cycle. Escalation is
configurable (e.g., 30/14/7 days → owner → owner+supervisor → priority → escalation queue).
Due-outs reference authoritative records rather than duplicating them.

### 5.7 Document / Evidence domain

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

### 5.8 Future domains

Qualifications, Certifications, Skills, Education, Experience, Awards, Travel, Equipment,
Access/accounts, In-processing, Out-processing, Readiness, Recruiting, Performance.

---

## 6. Canonical State, Field Policy, and Domain Registry

### 6.1 Canonical state

A common, serializable, provenance-carrying state shared across agents:

```text
AdaState
├── people[]                  ├── due_out_actions[]
├── organizations[]          ├── due_out_blockers[]
├── positions[]              ├── reporting_cycles[]
├── assignments[]            ├── administrative_actions[]
├── courses[]                ├── absences[]
├── training_requirements[]  ├── documents[]
├── training_records[]       ├── evidence[]
├── due_out_templates[]      ├── validation_issues[]
├── due_outs[]               ├── unresolved_questions[]
├── due_out_responses[]      └── provenance[]
```

### 6.2 Field handling policy

Each field declares missing-value handling: `REQUIRED, RECOMMENDED, OPTIONAL, DEFAULTABLE`.
Example (`Person`): `name REQUIRED`, `employee_id RECOMMENDED`, others `OPTIONAL`,
`status DEFAULT=ACTIVE`, `created_at DEFAULT=now`. Ada asks about missing recommended fields
and honors instructions like "use defaults or leave optional fields blank."

### 6.3 Domain registry

Each domain registers: schema, entities, relationships, validation rules, permissions, CRUD
tools, report templates, PII classification, vector collections, agent-access rules, and
**profile bindings**. New domains are added without redesigning the orchestrator.

---

## 7. Cross-Cutting Concerns (apply to every phase)

These concerns are designed once and enforced across all phases. Full hardening is Phase 19,
but the contracts below are non-negotiable from Phase 0.

### 7.1 Untrusted-document & prompt-injection handling

- Treat **all ingested file content** (PDF/DOCX/XLSX/CSV/TXT) as **untrusted data, never
  instructions**. Document text is placed in clearly delimited data context, separate from
  agent system/tool instructions.
- Ingestion and extraction agents **may never trigger writes or tool calls that mutate
  state** without an explicit human confirmation step.
- Strip/escape control sequences; ignore embedded "instructions" in documents.
- Adversarial-prompt tests are part of the eval suite (Section 8, item 3).

### 7.2 Bedrock guardrails & cost/token governance

- **Model routing + fallbacks** (reuse the IWB router pattern): a default chat model with an
  allowlisted switch list and graceful fallback.
- **Per-request ceilings:** max tokens, bounded agent loops, max agent calls per document/
  task, and time budgets.
- **PII redaction** via Bedrock Guardrails on inputs/outputs where configured.
- **Prompt versioning:** every agent prompt has a version recorded in provenance/audit.
- Cross-references the confirmation/risk model (Section 12).

### 7.3 Temporal & audit data model

- History/versioning for mutable records (e.g., `Assignment` history), **soft-delete**
  (`status`/`deactivated_at`) preferred over hard delete; hard delete is an explicit,
  audited, high-impact action.
- Effective-dating beyond training requirements where records have validity windows.

### 7.4 Change-set & undo model

- Chat-driven and bulk writes are grouped into **change sets** that are previewable,
  approvable, and **reversible**, paired with the audit trail (Section 13) and confirmation
  model (Section 12).

### 7.5 RBAC & PII tiers

- Explicit **role × permission matrix** (e.g., `viewer, editor, approver, admin`) and
  **field-level PII tiers** (public / internal / sensitive) built on `SensitiveIdentity`.
- Authorization is enforced in the service/tool layer, not the UI.

### 7.6 Deployment / infrastructure target

- Local-first now; production path on AWS: **RDS Postgres**, **S3**, **Bedrock**, **KMS**
  for encryption, container runtime (**ECS/EKS**). Reuse IWB's `Dockerfile` pattern.

### 7.7 Time & date normalization

- A shared date/time service normalizes Excel serials, `YYYYMMDD`, `MM/DD/YYYY`, free-text
  and `TBD`/`N/A` into typed fields (`actual_date`, `estimated_date`, `due_date`,
  `completion_date`, `status_update_date`); the **original value is always preserved** for
  provenance. Timezone handling is explicit for due dates and reporting cycles.

---

## 8. Non-Functional Requirements (initial targets)

| Dimension | Initial target (MVP) | Notes |
|---|---|---|
| Scale | 50k persons, 500k training records, 100k due-out actions | Postgres-backed; paginate UI |
| Concurrency | 25 concurrent internal users | Streamlit + service layer |
| Bedrock latency budget | Chat < 8s p50 / < 20s p95; extraction batched | Router picks model; timeouts bounded |
| Ingestion | 10k-row workbook processed with preview < 5 min | Bounded agent loops |
| Availability | Business-hours internal use; graceful degradation if Bedrock unavailable | Local stores stay readable |
| Data retention | Configurable; audit retained ≥ 1 year by default | `ADA__*` retention knobs |
| Cost | Per-request token ceilings; per-day soft budget alerting | Governance (7.2) |

These are starting targets, refined during Phase 19.

---

## 9. Development Roadmap

Every phase uses the same template: **Goal · Scope / non-goals · Deliverables · Repo targets
· Depends on · Exit criteria · Test / demo notes**.

Repo targets reference the scaffold created in this repo:
`src/ada/{config.py, bedrock.py, platform/, domain/, registry/, agents/, tools/, services/,
ingestion/, provenance/, quality/, reports/, workflows/}`, plus `app/`, `evals/`, `tests/`.

> **Phase numbering:** v3 renumbers into a clean linear sequence. The former "Phase 8A"
> (Due-Out Management) is now **Phase 9**; every subsequent phase shifts by one, giving
> Phases 0–19.

| v3 phase | Topic | Was (v2) |
|---|---|---|
| 0 | Architecture & Security Foundation | 0 |
| 1 | Canonical Domain Model | 1 |
| 2 | Domain Registry & Profiles | 2 |
| 3 | Conversational CRUD | 3 |
| 4 | Natural-Language Query Engine | 4 |
| 5 | Structured File Ingestion | 5 |
| 6 | Unstructured Document Ingestion | 6 |
| 7 | Provenance & Evidence Engine | 7 |
| 8 | Entity Resolution & Data Quality | 8 |
| 9 | Due-Out / Suspense Management | 8A |
| 10 | Training Requirement Engine | 9 |
| 11 | Reporting & Export Framework | 10 |
| 12 | Administrative Workflow Engine | 11 |
| 13 | In/Out-Processing Automation | 12 |
| 14 | Qualifications, Certs, Skills, Education | 13 |
| 15 | Personnel Readiness Engine | 14 |
| 16 | Advanced Reporting & Analytics | 15 |
| 17 | Policy / Requirement Intelligence | 16 |
| 18 | Human Review & Approval | 17 |
| 19 | Production Hardening | 18 |

---

### Phase 0 — Architecture and Security Foundation

- **Goal:** Establish architecture and security boundaries before processing real data.
- **Scope / non-goals:** Foundations, config, and boundaries only. No domain CRUD, no
  ingestion, no live assistant product.
- **Deliverables:** Frontend/chat architecture; agent-orchestration boundary; DB access
  layer; PostgreSQL dev environment; vector DB; object/document storage; authentication;
  RBAC skeleton; field-level PII restrictions; encryption requirements; secrets management;
  audit logging; retention/deletion policy; document classification/PII tagging;
  no-unrestricted-SQL guarantee; Bedrock client boundary; profile mechanism stub;
  untrusted-document contract (7.1); guardrail/cost contract (7.2).
- **Repo targets:** `src/ada/config.py`, `src/ada/bedrock.py`, `src/ada/platform/*`
  (identity, audit, secrets, storage), `app/`, `example.env`.
- **Depends on:** —
- **Exit criteria:** Base architecture documented; auth/authz model established; PII model
  established; structured DB, vector DB, and object storage available; Bedrock reachable via
  `AWS_PROFILE`/`AWS_REGION`.
- **Test / demo notes:** Config loads from env; Bedrock session constructs; Streamlit shell
  launches with placeholder pages.

### Phase 1 — Canonical Domain Model

- **Goal:** Implement the initial structured data model.
- **Scope / non-goals:** Schema + CRUD service layer. No chat, no ingestion.
- **Initial domains:** Personnel, Organization, Training, Due-Out, Administrative,
  Documents.
- **Deliverables:** Entities, relationships, IDs/keys, field policies, validation rules, PII
  classification, DB migrations, sample/test data, canonical `AdaState`; temporal/soft-delete
  policy (7.3).
- **Repo targets:** `src/ada/domain/*`, migrations, `src/ada/services/*` (CRUD).
- **Depends on:** Phase 0.
- **Exit criteria:** Schemas implemented; relationships validated; test data available; CRUD
  service layer available.
- **Test / demo notes:** DB + schema tests green; seed data loads.

### Phase 2 — Domain Registry and Profiles

- **Goal:** Add domains/profiles without changing the core architecture.
- **Scope / non-goals:** Registry + profile config. No new business domains yet.
- **Deliverables:** Domain registry; registration interface; register initial domains;
  domain-specific tool/validation/permission/report-template registration; **application-
  profile mechanism** (4.3) with `military` and `general` profiles.
- **Repo targets:** `src/ada/registry/*`, profile config under `src/ada/config.py`/registry.
- **Depends on:** Phase 1.
- **Exit criteria:** A developer can add a domain without changing the orchestrator; switching
  `ADA__PROFILE` swaps terminology and enabled domains.
- **Test / demo notes:** Registry unit tests; profile-swap snapshot test.

### Phase 3 — Conversational CRUD

- **Goal:** Manage structured databases using natural language.
- **Scope / non-goals:** Controlled tools only. **No unrestricted SQL.**
- **Supported intents:** `CREATE, READ, UPDATE, DEACTIVATE, SEARCH, REPORT, UPLOAD`.
- **Deliverables:** Intent/orchestrator agent; controlled personnel/org/training/admin tools;
  missing-field handling; defaults; confirmation policies (Section 12); write auditing
  (Section 13); change-set grouping (7.4); prompt versioning (7.2).
- **Repo targets:** `src/ada/agents/*` (intent/orchestrator), `src/ada/tools/*`,
  `src/ada/services/*`.
- **Depends on:** Phases 1–2.
- **Exit criteria:** Users create, retrieve, update, search, and deactivate records without
  SQL; writes are audited and reversible.
- **Test / demo notes:** "Add Jane Doe as a Data Scientist in J21", "Change Jane's
  supervisor", "Deactivate John Doe" — each audited; permission tests pass.

### Phase 4 — Natural-Language Query Engine

- **Goal:** Conversational queries across one or more domains.
- **Scope / non-goals:** Read-side. NL → **structured query plan** → approved SQL (never raw
  LLM SQL).
- **Deliverables:** Query agent; query-plan schema; plan→SQL compiler; conversational context/
  follow-up filtering; query provenance.
- **Repo targets:** `src/ada/agents/*` (query), `src/ada/services/*` (query).
- **Depends on:** Phases 1–3.
- **Exit criteria:** Multi-domain queries work; follow-up filtering works; query provenance
  recorded; unsafe SQL never executed.
- **Test / demo notes:** "Who has overdue training?" → "Only J21" → "Export that." Query-plan
  golden tests in `evals/`.

### Phase 5 — Structured File Ingestion

- **Goal:** Import structured/semi-structured files (`XLSX, XLS, CSV`).
- **Scope / non-goals:** Structured formats. Untrusted-content rules (7.1) apply.
- **Pipeline:** Upload → Parser → Header Detection → Schema Mapping Agent → Validation →
  Entity Resolution → Import Preview → Commit.
- **Deliverables:** Spreadsheet Structure Agent (multi-table/section/merged/repeated headers,
  unit response columns, counts/ratios); **date normalization service** (7.7); schema mapping;
  import preview with counts; bulk-write confirmation.
- **Repo targets:** `src/ada/ingestion/*`, `src/ada/agents/*` (schema mapping),
  `src/ada/services/*`.
- **Depends on:** Phases 1–4.
- **Exit criteria:** Excel/CSV populate multiple domain schemas reliably; preview precedes
  commit; provenance captured.
- **Test / demo notes:** Messy operational workbook → sections detected → preview →
  approve → structured records. Ingestion tests in `evals/`.

### Phase 6 — Unstructured Document Ingestion

- **Goal:** Extract structured records from `TXT, PDF, DOC, DOCX`.
- **Scope / non-goals:** Extraction + RAG indexing; untrusted-content rules (7.1) strictly
  enforced.
- **Pipeline:** Document → Classification → Text/Table Extraction → Chunking → Vector DB →
  Extraction Agent → Canonical records → Validation → Structured DB.
- **Deliverables:** Classifier; extractor(s) for certificates/memoranda/policy; chunker;
  Chroma indexing; evidence capture stubs.
- **Repo targets:** `src/ada/ingestion/*`, `src/ada/provenance/*` (evidence hooks).
- **Depends on:** Phases 1–5, 7 (evidence).
- **Exit criteria:** Unstructured files produce structured, **reviewed** records with source
  attribution.
- **Test / demo notes:** Training certificate → person/course/dates extracted with evidence;
  adversarial-document test passes (no injected tool calls).

### Phase 7 — Provenance and Evidence Engine

- **Goal:** Make important records traceable to their source.
- **Scope / non-goals:** Provenance/evidence services and rendering.
- **Deliverables:** Track source document, page/row/section, extraction method, confidence,
  timestamp, user, agent, original vs. modified value; evidence linkage to records.
- **Repo targets:** `src/ada/provenance/*`.
- **Depends on:** Phases 1, 5–6.
- **Exit criteria:** Important answers and changes trace to source evidence.
- **Test / demo notes:** "Where did this completion date come from?" → file/sheet/row +
  confidence.

### Phase 8 — Entity Resolution and Data Quality

- **Goal:** Resolve duplicate/conflicting records; flag quality issues.
- **Scope / non-goals:** Detection + human-in-the-loop flagging; no silent overwrite.
- **Deliverables:** Entity resolution (ID/DoD ID/employee ID/email/org/position/date/name
  similarity); Data Quality Agent (duplicates, conflicts, unknown orgs/courses, invalid
  dates, orphaned/expired records).
- **Repo targets:** `src/ada/quality/*`.
- **Depends on:** Phases 1, 5–7.
- **Exit criteria:** System flags ambiguous/conflicting data rather than silently changing
  authoritative records.
- **Test / demo notes:** "John Smith / J. Smith / Smith, John A." clustered with confidence;
  review queue populated.

### Phase 9 — Due-Out / Suspense Management  *(MVP; was 8A)*

- **Goal:** Convert spreadsheet-based due-outs into structured, queryable, assignable,
  auditable operational workflows.
- **Scope / non-goals:** Full due-out domain + dashboard; escalation policies configurable.
- **Deliverables:** `DueOutTemplate/DueOut/DueOutResponse/DueOutAction/DueOutBlocker/
  DueOutDependency/ReportingCycle`; recurring generation; typed responses; canonical statuses;
  org-level responses; person-level actions; overdue calculation; ownership/assignment;
  escalation; cross-domain links; evidence/provenance; Streamlit due-out dashboard; editable
  review table; chat tools; reporting-cycle rollup.
- **Repo targets:** `src/ada/services/*` (due-out engine), `src/ada/domain/*` (due-out
  entities), `app/pages/6_Due_Outs.py`.
- **Depends on:** Phases 1–8.
- **Exit criteria:** Recurring due-outs from templates; org + individual assignment; chat/table
  updates; free-text normalized; blockers/dependencies tracked; filter by org/section/owner/
  status/cycle; auto overdue/due-soon; exportable; fully auditable.
- **Test / demo notes:** "Show all open S-1 due-outs", "What is due before the next cycle?",
  "Export the current due-out report to Excel."

### Phase 10 — Training Requirement Engine  *(MVP; was 9)*

- **Goal:** Determine which training applies to each person and compute status.
- **Scope / non-goals:** LLM may interpret policy language; **deterministic code computes
  final status**.
- **Deliverables:** Requirement rules by org/position/role/grade/assignment/optional/recurring/
  expiration/waivers/exceptions; status values `COMPLETE, DUE_SOON, OVERDUE, NOT_STARTED,
  EXPIRED, WAIVED, NOT_APPLICABLE, UNKNOWN`.
- **Repo targets:** `src/ada/services/*` (training), `src/ada/domain/*` (training).
- **Depends on:** Phases 1–4.
- **Exit criteria:** Compliance computed automatically from stored requirements and records.
- **Test / demo notes:** "Who has overdue training in J21?" matches deterministic fixture.

### Phase 11 — Reporting and Export Framework  *(MVP; was 10)*

- **Goal:** Generate multiple outputs from the same verified dataset.
- **Scope / non-goals:** Report generator uses **verified result datasets**, never LLM-
  regenerated values.
- **Deliverables:** Screen/XLSX/CSV/TXT/PDF exporters; secure/temporary download URLs; initial
  report set (roster, training compliance, overdue, expiration, arrival/departure, leave, open
  admin actions, individual summary, manager summary, data-quality, due-out rollups by cycle/
  org/section, blocked due-outs).
- **Repo targets:** `src/ada/reports/*`, `app/pages/8_Reports.py`.
- **Depends on:** Phases 4, 9–10.
- **Exit criteria:** Any supported query result exports consistently across formats.
- **Test / demo notes:** Report-validation tests compare exports to source dataset.

### Phase 12 — Administrative Workflow Engine  *(was 11)*

- **Goal:** Turn administrative records into durable workflows.
- **Scope / non-goals:** Durable, resumable, idempotent workflows with human approval.
- **Deliverables:** Workflows (due-out escalation, recurring cycles, in/out-processing, PCS,
  TDY, leave, onboarding, training remediation, account/access, position changes); durable
  checkpoints; pause/resume; idempotency; failure isolation; auditability.
- **Repo targets:** `src/ada/workflows/*`.
- **Depends on:** Phases 1, 9.
- **Exit criteria:** Multi-step workflows retain state and resume safely.
- **Test / demo notes:** Recovery tests (kill mid-workflow → resume).

### Phase 13 — In-Processing and Out-Processing Automation  *(was 12)*

- **Goal:** Auto-generate tasks from arrival/departure data.
- **Scope / non-goals:** Event-triggered, approved workflows.
- **Deliverables:** Arrival → onboarding checklist + mandatory training + supervisor task +
  account requests; departure (≤ threshold) → out-processing checklist + account termination
  + equipment return + knowledge transfer.
- **Repo targets:** `src/ada/workflows/*`.
- **Depends on:** Phases 9, 12.
- **Exit criteria:** Arrival/departure events trigger approved workflows.
- **Test / demo notes:** Arrival date set → onboarding tasks generated for review.

### Phase 14 — Qualifications, Certifications, Skills, Education  *(was 13)*

- **Goal:** Expand into talent/workforce management via the registry.
- **Deliverables:** `Qualification/PersonQualification`, `Certification/PersonCertification`,
  `Skill/PersonSkill`, `Education`, `Experience`; talent queries.
- **Repo targets:** `src/ada/domain/*`, `src/ada/registry/*`.
- **Depends on:** Phase 2.
- **Exit criteria:** Talent domains added through the registry without core changes.
- **Test / demo notes:** "Find people with Python, AWS, and ML experience"; "Who has a CISSP
  expiring this year?"

### Phase 15 — Personnel Readiness Engine  *(was 14)*

- **Goal:** Compute derived readiness across domains.
- **Scope / non-goals:** Deterministic calculation; LLM explains.
- **Deliverables:** Per-domain status (Training/Administrative/Qualification/Assignment/
  Access) → overall readiness; blocking-condition surfacing.
- **Repo targets:** `src/ada/services/*` (readiness), `src/ada/reports/*`.
- **Depends on:** Phases 10, 14.
- **Exit criteria:** Users see overall readiness and blocking conditions.
- **Test / demo notes:** RED overall with "System X access incomplete" explanation.

### Phase 16 — Advanced Reporting and Management Analytics  *(was 15)*

- **Goal:** Management-level analytics.
- **Scope / non-goals:** App calculates; LLM summarizes.
- **Deliverables:** Org readiness, training/overdue trends, upcoming departures, staffing gaps,
  vacancy analysis, completion %, requirement-change impact, admin workload, data-quality
  trends.
- **Repo targets:** `src/ada/reports/*` (analytics).
- **Depends on:** Phases 11, 15.
- **Exit criteria:** Analytics reproducible and explainable.
- **Test / demo notes:** "J21 training readiness 91.3% (+2.8%); gap: Course ABC, 14
  incomplete."

### Phase 17 — Policy / Requirement Intelligence  *(was 16)*

- **Goal:** Combine structured truth with vector-based policy retrieval.
- **Deliverables:** Structured requirement + retrieved policy section → grounded answer with
  citation.
- **Repo targets:** `src/ada/agents/*`, `src/ada/ingestion/*` (retrieval), `src/ada/reports/*`.
- **Depends on:** Phases 6, 10.
- **Exit criteria:** System connects structured requirements to supporting policy evidence.
- **Test / demo notes:** "What policy requires this training?" → "Policy Z, Section 4.2."

### Phase 18 — Human Review and Approval  *(was 17)*

- **Goal:** Explicit review for ambiguous/high-impact actions.
- **Deliverables:** Review queue for potential duplicates, unknown courses, new fields, policy
  interpretation, bulk updates, requirement replacement, identity conflicts, large imports,
  significant deletions/deactivations; pause/resume with authorized approval.
- **Repo targets:** `src/ada/services/*` (review), `app/pages/9_Data_Quality.py`.
- **Depends on:** Phases 8, 12.
- **Exit criteria:** High-risk/ambiguous agent actions can be paused for authorized human
  review.
- **Test / demo notes:** "Two records may be the same person (82%). Review before merging."

### Phase 19 — Production Hardening  *(was 18)*

- **Goal:** Harden Ada for broader operational deployment.
- **Security:** RBAC/ABAC; field-level PII controls; encryption at rest/in transit (KMS);
  secrets management; session security; audit trails; document access control; secure logging;
  retention controls.
- **Reliability:** Idempotent writes; DB transactions; rollback; backups/restore; record
  versioning; durable checkpoints; failure isolation.
- **LLM controls:** Prompt-injection protection; restricted tools; authorization before
  writes; schema/output validation; confidence thresholds; bounded loops; cost/token controls;
  tool allowlists.
- **Testing:** Unit/DB/schema/ingestion tests; **agent evaluation suite**; permission tests;
  report validation; **adversarial-prompt tests**; bulk-import tests; recovery tests.
- **Repo targets:** cross-cutting across `src/ada/*`, `evals/`, `tests/`, deployment configs.
- **Depends on:** all prior phases.
- **Exit criteria:** Platform hardened; NFR targets (Section 8) met or re-baselined.

---

## 10. Agent Evaluation Harness

Ada ships an `evals/` suite so each phase's exit criteria are **measurable** (mirrors IWB's
`evals/`):

- **Golden datasets:** representative workbooks, documents, and query sets with expected
  outputs.
- **Metrics:** extraction accuracy, schema-mapping accuracy, query-plan correctness, due-out
  normalization accuracy, report fidelity.
- **Adversarial suite:** prompt-injection documents that must **not** cause tool calls/writes.
- **Per-phase acceptance:** each phase adds evals gating its "done."

```text
evals/
├── datasets/           # golden inputs
├── expected/           # expected outputs
├── query_plans/        # NL → plan goldens
├── adversarial/        # injection documents
└── runners/            # per-phase acceptance runners
```

---

## 11. MVP Scope

Do not build all phases before demonstrating value. The MVP is **Phases 0–11**:

```text
Phase 0    Architecture and Security
Phase 1    Canonical Domain Model
Phase 2    Domain Registry & Profiles
Phase 3    Conversational CRUD
Phase 4    Natural-Language Query
Phase 5    Structured (Excel/CSV) Ingestion
Phase 6    Unstructured (PDF/DOC/TXT) Ingestion
Phase 7    Provenance
Phase 8    Entity Resolution & Data Quality
Phase 9    Due-Out / Suspense Management
Phase 10   Training Requirement Engine
Phase 11   Reporting and Export
```

The MVP should demonstrate: upload a roster; upload training records; upload a complex
due-out workbook; detect multiple tables/sections; normalize due-outs; upload policy/support
docs; add/update personnel conversationally; create/assign due-outs conversationally; ask who
belongs to a unit; ask who has overdue training; ask who is arriving/departing; ask what
due-outs are open/overdue/blocked/due-soon; filter due-outs; retrieve supporting evidence;
edit reviewed records in Streamlit tables; generate a manager-ready Excel/PDF report; generate
a reporting-cycle due-out rollup.

**First compelling demo:**

```text
Upload messy operational workbook
          ↓
Agent detects sections/tables
          ↓
Preview normalized records
          ↓
User approves import
          ↓
Structured records + Due-Out data
          ↓
User asks questions in chat
          ↓
On-screen table / dashboard
          ↓
Excel / PDF report
```

---

## 12. Recommended Development Sequence

```text
FOUNDATION
   ├─ Phase 0   Architecture / Security
   ├─ Phase 1   Canonical Model
   └─ Phase 2   Domain Registry & Profiles
           ▼
STREAMLIT CORE APPLICATION
   ├─ Streamlit navigation / authentication
   ├─ Phase 3   Conversational CRUD
   ├─ Phase 4   Natural-Language Query
   └─ Phase 5   Structured Ingestion
           ▼
AGENTIC DOCUMENT + SPREADSHEET PROCESSING
   ├─ Phase 6   Unstructured Ingestion
   ├─ Phase 7   Provenance
   └─ Phase 8   Entity Resolution / Data Quality
           ▼
OPERATIONS
   ├─ Phase 9   Due-Outs / Suspenses
   ├─ Phase 10  Training Requirements
   └─ Phase 11  Reporting / Export
           ▼
WORKFLOW + TALENT + ANALYTICS
   ├─ Phase 12  Administrative Workflows
   ├─ Phase 13  In/Out Processing
   ├─ Phase 14  Skills / Qualifications
   ├─ Phase 15  Readiness
   ├─ Phase 16  Analytics
   └─ Phase 17  Policy Intelligence
           ▼
GOVERNANCE + HARDENING
   ├─ Phase 18  Human Review
   └─ Phase 19  Production Hardening
```

---

## 13. Initial Agent Architecture

All agents run on **AWS Bedrock** via Strands and are subject to guardrails (7.2) and the
untrusted-document contract (7.1).

- **Orchestrator / Intent Agent** — determines intent (`CREATE, READ, UPDATE, DEACTIVATE,
  SEARCH, UPLOAD, REPORT, SCHEMA_CHANGE`) and selects tools/workflow.
- **Ingestion Agent** — file type, document type, parser, target domain, extraction workflow.
- **Schema Mapping Agent** — maps incoming columns to canonical schema (`"Emp #" →
  employee_id`, `"Unit" → organization`, `"Training Name" → course_name`, `"Completed" →
  completion_date`).
- **Spreadsheet Structure Agent** — detects sections/tables/repeated headers/merged labels/
  response columns; extracts counts/ratios/dates/free-text.
- **Extraction Agent** — extracts entities/relationships from unstructured documents.
- **Due-Out / Suspense Agent** — identifies requirements, cycle, owner; interprets free-text
  status; identifies blockers and person-level child actions; routes updates through
  controlled Due-Out tools; summarizes without changing authoritative calculations.
- **Entity Resolution Agent** — same-person/org/course/requirement determination.
- **Validation / Data Quality Agent** — missing/invalid/duplicate/conflict/impossible-date/
  broken-relationship checks.
- **Database Agent / Tool Layer** — executes approved actions through controlled functions
  (no unrestricted SQL).
- **Query Agent** — NL → approved structured query specification.
- **Report Agent** — formats verified datasets to Screen/Table/XLSX/CSV/TXT/PDF/secure URL.

---

## 14. Confirmation and Risk Model

- **Reads:** no confirmation (e.g., "Show all overdue personnel").
- **Normal writes:** validate first; ask about missing recommended info (e.g., "Add Jane Doe
  to J21").
- **High-impact writes:** require confirmation (deactivate 400 people, mark everyone complete,
  replace an org-wide requirement, import 10,000 records, delete a domain). Example: *"This
  operation will update 417 personnel records. Proceed?"*
- **Change sets (7.4):** high-impact operations are grouped, previewed, approved, and
  reversible.

---

## 15. Audit Requirements

Every important write creates an audit event:

```text
AuditEvent
timestamp · user · action · entity_type · entity_id ·
previous_value · new_value · source · conversation_id ·
agent · confidence · prompt_version · change_set_id
```

Example:

```text
2026-08-25 10:32 · User: manager@example · Action: UPDATE
Person: Jane Doe · Field: supervisor · Old: Bob Smith · New: Kevin Jones
Source: Chat · change_set: cs_00123 · prompt_version: intent@v3
```

---

## 16. Long-Term Product Direction

Ada starts as a personnel/training/operations tracker, but the architecture supports a broader
**agentic workforce operations platform**:

```text
Training / Task Tracker
      ↓
Personnel Administration Assistant
      ↓
Personnel Readiness Platform
      ↓
Talent / Workforce Management
      ↓
Agentic Workforce Operations Platform
```

The reusable platform shares agent orchestration, ingestion, retrieval, provenance,
validation, database management, reporting, human review, workflow execution, and security
controls — across multiple **application profiles** (military first, general thereafter).

---

## 17. Streamlit Decision Summary

Use Streamlit for the MVP and initial operational release: fast Python-native development;
natural fit with the Bedrock/agent stack; strong dataframe/editable-table support; file-heavy
and chat-driven workflows; internal dashboards/review queues; multipage support; downloadable
reports; UI-layer enterprise identity.

**Constraints to design around:** Streamlit reruns scripts during interaction; session state
is not durable workflow storage; authentication ≠ authorization; core services must not depend
on Streamlit APIs; large report files use backend/object storage.

```text
NOW                          LATER, IF REQUIRED
Streamlit                    React / Other Frontend
   │                                │
   ▼                                ▼
Stable Application Services  ← same services →
   │
   ▼
Agents / Databases / Workflows
```

This keeps the core platform replaceable without rework, and lets Ada grow from a Streamlit
MVP into a broader product without locking the platform to Streamlit.

---

## 18. Glossary

- **Ada** — the product; *AI-Driven Assistant*.
- **Due-out / suspense** — a task/requirement with an owner and deadline, often per reporting
  cycle (general term: *action item / task*).
- **Reporting cycle / BA** — a recurring period against which due-outs are tracked (general:
  *reporting period*).
- **Profile** — a config bundle that adapts terminology and enabled features to a market.
- **Provenance** — the traceable source (document/page/row) and method behind a value.
- **Change set** — a grouped, previewable, reversible batch of writes.
- **IWB** — AISI Intelligence Workbench; a pattern source for Ada, not a parent product.

---

## 19. Product KPIs / Success Metrics

| KPI | Target signal |
|---|---|
| Ingestion accuracy | ≥ 95% correct field mapping on golden workbooks |
| Query correctness | ≥ 95% query-plan match on golden query set |
| Due-out normalization | ≥ 90% free-text → correct canonical status |
| Time-to-report | Messy workbook → manager report in minutes, not hours |
| Human-review rate | High-impact actions reviewed 100% of the time |
| Auditability | 100% of important writes produce an audit event |
| Adversarial safety | 0 tool calls/writes triggered by injected document content |
