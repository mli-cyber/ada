# Ada Architecture & Roadmap Sector Assessment

> **Status: historical input to roadmap v3.** Most "Partial" items below — Policy
> Foundation, Source Authority, My Work, Case Management, Domain Events, Connector Framework,
> and AdaState scaling — have since been incorporated into
> [`../roadmap_v3.md`](../roadmap_v3.md) / [`../phase_0.md`](../phase_0.md). Kept for the
> sector-by-sector rationale, not as an open TODO list.

> **Purpose:** A concise assessment snapshot of the then-current Ada `roadmap_v3.md` and
> `diagrams.md`, organized by architectural sector.
>
> Ratings:
>
> - **Strong** — well designed and should largely be kept as-is.
> - **Good** — solid foundation, but needs targeted refinement.
> - **Partial** — concept exists or is implied, but needs a more explicit architecture, service, data model, or earlier roadmap placement.

---

## Executive Scorecard

| Sector | Rating | Current Assessment | Main Recommendation |
|---|---|---|---|
| Core Data Architecture | **Strong** | Clear separation between structured source-of-truth data and semantic/document retrieval | Keep; refine document/object/vector boundaries |
| Streamlit / Service Separation | **Strong** | UI is presentation-only and business logic remains behind services | Keep as a core architecture rule |
| Structured DB vs. Vector DB | **Strong** | Correct principle: SQL is authoritative, vector DB supports RAG/evidence | Clarify in diagrams that vector data never supplies authoritative report values |
| Due-Out / Suspense Domain | **Strong** | Mature first-class data model with templates, responses, actions, blockers, cycles, and typed values | Keep; connect due-outs directly to policy/rule lineage |
| Messy Spreadsheet Ingestion | **Strong** | Structure detection, mapping, validation, entity resolution, preview, and approval are well defined | Keep; expand reconciliation/source-authority handling |
| Agent Architecture | **Good** | Appropriate specialist agents and controlled tool layer | Clarify Strands vs. LangGraph responsibilities; avoid agentizing deterministic decisions |
| Model Router / Cost Governance | **Good** | Strong tiering, fallback, task-class routing, ceilings, and evaluation concepts | Route by capability rather than hard-coding model names into architecture |
| Security / Guardrails | **Good** | Strong RBAC, PII tiers, prompt-injection handling, authz, and restricted tools | Add an explicit outbound **LLM Data Guard** |
| Provenance / Evidence | **Good** | Strong data provenance and source attribution design | Extend provenance to policy/rules and fix Phase 6 ↔ Phase 7 dependency cycle |
| Temporal / Historical Model | **Good** | Effective dates, soft delete, history, and reporting cycles are present | Add explicit `as_of` / point-in-time reporting and snapshots |
| Human Review / Approval | **Good** | HITL is clearly part of the architecture and high-impact actions require approval | Add a minimal review primitive earlier; keep Phase 18 for advanced review workflows |
| Organization Hierarchy | **Good** | Parent-child organization model exists and supports hierarchy | Add hierarchy scope, inheritance, and roll-up services as first-class capabilities |
| Policy / Requirement Management | **Partial** | Policy intelligence exists, but too late and too retrieval-focused | Add **Phase 2A Policy Foundation**, Policy Registry, rules, defaults, source authority, and policy gaps |
| Policy-to-Task Resolution | **Partial** | Current design can retrieve policy, but does not yet explicitly resolve which policy/rule applies to each task | Add Policy Router Agent + deterministic Policy Resolution Service |
| No-SOP / Local Default Handling | **Partial** | Current roadmap does not fully define how Ada operates when local SOPs are missing | Add `AUTHORITATIVE`, `DERIVED_APPROVED`, `LOCAL_DEFAULT`, `UNKNOWN`, and PolicyGap |
| Source Authority / Reconciliation | **Partial** | Conflict detection exists, but source precedence is not fully modeled | Add Source Registry, field-level authority rules, and Reconciliation Center |
| HR Operational Work Queue | **Partial** | Due-outs/admin/review pages exist separately | Add a unified **My Work** queue |
| Case Management | **Partial** | Multi-step workflows exist, but related tasks are not grouped into a business case | Add `Case`, participants, tasks, documents, events, blockers, timeline |
| Event-Driven Automation | **Partial** | Arrival/departure-triggered automation is implied | Add explicit domain events and transactional outbox pattern |
| Connector / External-System Framework | **Partial** | MVP is file-driven and production adapters are mainly infrastructure adapters | Define a future `SourceConnector` interface for HR/training/SharePoint/API systems |
| AdaState / Workflow State | **Partial** | Canonical state concept is strong conceptually but too large for target scale | Redefine AdaState as a lightweight workflow/reference envelope |
| Reporting Architecture | **Good** | Verified dataset/report principle is strong | Separate evidence/citation retrieval from authoritative report-value generation |
| Readiness / Analytics | **Good** | Deterministic readiness and analytics are appropriately positioned | Add explainable roll-ups and historical/as-of analysis |
| Evaluation / Testing | **Strong** | Golden datasets, adversarial testing, query-plan tests, ingestion tests, and phase acceptance are well defined | Keep and extend to policy-resolution, reconciliation, and hierarchy roll-ups |
| Product Generalization / Profiles | **Strong** | Military-first profile with neutral core terminology is well designed | Keep; apply profiles to policy/default bundles and workflows too |
| Production Hardening | **Good** | Strong coverage of security, reliability, LLM controls, and testing | Add records lifecycle, connector security, and policy-version governance |

---

# Sector Details

## 1. Core Data Architecture — Strong

### What is strong

The design correctly separates:

```text
Structured SQL / PostgreSQL
→ authoritative personnel, training, organization, due-out, and admin records

Vector DB
→ semantic search, policy retrieval, document chunks, supporting evidence

Object Storage
→ original uploaded/generated files
```

The source-of-truth principle is one of the strongest parts of the roadmap.

### Improvement

Make the storage boundaries explicit in the main architecture diagram:

```text
Document Service
├── SQL metadata
├── Object storage
└── Vector chunks
```

Do not let the vector DB become an implicit document repository or operational database.

---

## 2. Streamlit / Service Separation — Strong

### What is strong

The roadmap explicitly prevents business logic from being embedded in Streamlit pages.

```text
Streamlit
    ↓
Application Services
    ↓
Agents / Domain Services / Databases
```

This preserves the ability to replace Streamlit later without rewriting the core platform.

### Improvement

Keep this rule strict.

Streamlit session state should remain transient only.

---

## 3. Structured DB vs. Vector DB — Strong

### What is strong

Ada already establishes:

> LLMs interpret; deterministic services execute.

and:

> Structured DB is the source of truth.

This is correct for HR/personnel operations.

### Improvement

For reports, explicitly use:

```text
SQL
 ↓
Verified Result Dataset
 ↓
Report Service
```

The vector DB may supply evidence/citations but not authoritative report values.

---

## 4. Due-Out / Suspense Management — Strong

### What is strong

The Due-Out domain is one of the most complete pieces of the roadmap.

It includes:

```text
DueOutTemplate
DueOut
DueOutResponse
DueOutAction
DueOutBlocker
DueOutDependency
ReportingCycle
```

It also correctly separates organization-level responses from person-level actions.

### Improvement

Add policy lineage:

```text
Policy
 ↓
Approved Rule
 ↓
DueOutTemplate
 ↓
DueOut
 ↓
Response / Action
 ↓
Evidence
```

---

## 5. Messy Spreadsheet Ingestion — Strong

### What is strong

The roadmap recognizes that:

```text
one workbook != one table
one sheet != one table
first row != always header
```

The structure/mapping pipeline is appropriate:

```text
Upload
 ↓
Parser
 ↓
Structure / Header Detection
 ↓
Schema Mapping
 ↓
Validation
 ↓
Entity Resolution
 ↓
Preview
 ↓
Commit
```

### Improvement

Add source-authority reconciliation after validation.

---

## 6. Agent Architecture — Good

### What is strong

Agents are mainly being used for ambiguity-heavy tasks:

```text
intent
schema mapping
spreadsheet structure
unstructured extraction
entity resolution assistance
due-out text interpretation
report narrative
```

This is appropriate.

### Improvement

Clarify the architecture rule:

> **Use agents where language or structure is ambiguous. Use deterministic code where the rule is known.**

Do not create agents for:

```text
authorization
overdue calculation
readiness calculation
policy resolution
database writes
workflow transitions
organization roll-ups
```

---

## 7. Model Router / Cost Governance — Good

### What is strong

The current design includes:

- budget tiers,
- fallback chains,
- task-class routing,
- request ceilings,
- model evaluation,
- fixed embeddings.

### Improvement

Define architecture-facing model requirements as capabilities:

```text
FAST_ROUTING
STRUCTURED_EXTRACTION
COMPLEX_REASONING
MULTIMODAL
HIGH_STAKES_REVIEW
```

Then configuration maps those capabilities to current Bedrock model IDs.

This reduces architecture dependence on rapidly changing model names.

---

## 8. Security / Guardrails — Good

### What is strong

The roadmap already includes:

```text
RBAC
PII tiers
authorization in service layer
prompt-injection protection
tool allowlists
high-impact confirmation
audit logs
```

### Improvement

Add a dedicated **LLM Data Guard**:

```text
Database
 ↓
Authorization
 ↓
LLM Data Guard
 ↓
Minimum-Necessary Fields
 ↓
Agent
```

This prevents unnecessary sensitive data from entering model context.

---

## 9. Provenance / Evidence — Good

### What is strong

Ada captures:

```text
document
page / row / section
agent
confidence
timestamp
original value
modified value
```

### Improvement

Extend provenance to rules:

```text
Rule
├── source_policy
├── source_section
├── authority
├── extraction_version
├── reviewed_by
├── approved_at
└── rule_version
```

Also resolve the Phase 6 ↔ Phase 7 dependency cycle by creating a minimal provenance contract early.

---

## 10. Temporal / Historical Model — Good

### What is strong

The roadmap includes:

- effective dating,
- mutable-record history,
- soft delete,
- reporting cycles,
- arrival/departure history.

### Improvement

Add explicit:

```text
as_of
```

query/report behavior.

Example:

```text
What was 2 DSB readiness at the August reporting cycle?
```

should use historical state, not today's records.

---

## 11. Human Review / Approval — Good

### What is strong

The architecture correctly shows human review before high-impact commits.

### Improvement

The primitive should exist early:

```text
ReviewRequest
ApprovalDecision
Reviewer
Reason
Status
```

Phase 18 can then provide advanced review routing and delegation rather than introducing review for the first time.

---

## 12. Organization Hierarchy — Good

### What is strong

`Organization.parent_organization_id` gives the model the correct hierarchical foundation.

### Improvement

Create explicit services:

```text
OrganizationHierarchyService
OrganizationScopeService
RollupService
```

Example:

```text
2 DSB
├── HHC
├── A CO
├── B CO
└── C CO
```

A query against 2 DSB should automatically understand descendant scope when appropriate.

Also support:

```text
BDE default
 ↓
BN override
 ↓
Company override
```

for policy, training, escalation, and reporting configuration.

---

## 13. Policy / Requirement Management — Partial

### Current gap

The roadmap currently places advanced policy intelligence too late relative to training, due-outs, and workflows.

### Recommendation

Add:

```text
Phase 2A — Policy Foundation
```

with:

```text
PolicyDocument
PolicyRule
CandidateRule
PolicyGap
SourceAuthority
TaskPolicyLink
ApplicablePolicySet
```

Keep the later Policy Intelligence phase for advanced comparison/change-impact capabilities.

---

## 14. Policy-to-Task Resolution — Partial

### Current gap

Retrieving relevant policy is not the same as determining which approved rule governs a task.

### Recommendation

Use:

```text
Task Classification
 ↓
Policy Router Agent
 ↓
Policy Resolution Service
 ↓
Applicable Approved Rule Set
 ↓
Rule / Workflow Engine
```

The final resolution should be deterministic and versioned.

---

## 15. No-SOP / Local Default Handling — Partial

### Current gap

Ada needs a clear operating mode when the unit has no local SOP.

### Recommendation

Use:

```text
AUTHORITATIVE
DERIVED_APPROVED
LOCAL_DEFAULT
UNKNOWN
```

and a `PolicyGap` registry.

Ada can continue operating, but must visibly distinguish system defaults from official policy.

---

## 16. Source Authority / Reconciliation — Partial

### Current gap

Entity resolution/data-quality can identify a conflict, but the current architecture needs a clearer answer to:

```text
Which source should win?
```

### Recommendation

Add:

```text
Source
SourceAuthorityPolicy
```

with field-level source precedence.

Also add a Reconciliation Center in Streamlit for unresolved conflicts.

---

## 17. HR Operational Work Queue — Partial

### Current gap

Operational work is currently distributed across:

```text
Due-Outs
Administrative Actions
Review Queue
Training
```

### Recommendation

Add:

```text
My Work
```

that combines:

```text
tasks
due-outs
approvals
blocked actions
policy reviews
data-quality issues
upcoming deadlines
escalations
```

This should become one of the primary user experiences.

---

## 18. Case Management — Partial

### Current gap

A real HR process may span multiple tables and workflows.

### Recommendation

Add:

```text
Case
CaseParticipant
CaseTask
CaseDocument
CaseEvent
```

Example:

```text
Out-Processing Case
├── Evaluation
├── Award
├── Equipment
├── Account Closure
├── Due-Outs
├── Documents
├── Blockers
└── Timeline
```

---

## 19. Event-Driven Automation — Partial

### Current gap

Arrival/departure automation exists conceptually but events are not yet first-class architecture objects.

### Recommendation

Define domain events:

```text
PersonArrived
PersonTransferred
DepartureApproaching
TrainingExpired
DueOutOverdue
PolicyUpdated
DocumentIngested
```

Flow:

```text
Domain Event
 ↓
Rule Engine
 ↓
Workflow
 ↓
Case / Task / Due-Out
 ↓
My Work
```

Use a transactional outbox pattern for reliability.

---

## 20. Connector / External-System Framework — Partial

### Current gap

The MVP correctly focuses on uploaded files, but later integrations should not require a new architecture.

### Recommendation

Define:

```text
SourceConnector
├── source_system
├── domain
├── authority
├── mapping
├── sync_strategy
├── scope
├── last_sync
└── status
```

Potential future sources:

```text
HR system
Training system
SharePoint
S3
Database
REST API
```

---

## 21. AdaState / Workflow State — Partial

### Current gap

The canonical state is conceptually useful but too large if interpreted as holding large domain datasets during agent execution.

### Recommendation

Use references instead:

```text
AdaState
├── request_id
├── user_context
├── task_type
├── organization_scope[]
├── selected_entity_refs[]
├── result_ref
├── evidence_refs[]
├── policy_rule_refs[]
├── change_set_id
├── approval_id
└── workflow_status
```

Keep domain records in SQL.

---

## 22. Reporting Architecture — Good

### What is strong

The roadmap correctly states that reports should come from verified datasets.

### Improvement

Explicitly separate:

```text
Verified operational values
```

from:

```text
policy/evidence narrative
```

The report service can combine them for presentation, but only the structured dataset supplies authoritative values.

---

## 23. Readiness / Analytics — Good

### What is strong

Readiness calculations are deterministic, and LLMs are limited to explanation/summarization.

### Improvement

Add:

```text
explainable roll-ups
historical/as-of analysis
driver analysis
```

Example:

```text
2 DSB = RED

Drivers:
- 8 overdue training items
- 3 overdue evaluations
- 1 incomplete alert roster
- 2 incomplete departure actions
```

---

## 24. Evaluation / Testing — Strong

### What is strong

The current roadmap already includes:

```text
golden datasets
query-plan tests
mapping accuracy
due-out normalization tests
report fidelity tests
adversarial prompt-injection tests
per-phase acceptance criteria
```

### Improvement

Add tests for:

```text
policy resolution
policy precedence
no-SOP behavior
source reconciliation
organization roll-ups
as-of reporting
LLM Data Guard
```

---

## 25. Product Generalization / Profiles — Strong

### What is strong

The military profile is separated from the neutral product identity.

This supports future workforce use cases without rewriting the core data model.

### Improvement

Profiles should also configure:

```text
policy bundles
system defaults
workflow templates
report templates
terminology
validation overrides
```

---

## 26. Production Hardening — Good

### What is strong

The roadmap covers:

```text
RBAC / ABAC
encryption
transactions
rollback
backups
versioning
durable workflows
prompt security
restricted tools
testing
```

### Improvement

Also include:

```text
records lifecycle enforcement
policy-version governance
connector security
source-system credential isolation
event replay / idempotency
```

---

# Recommended Priority Summary

## Strong — Keep

```text
Core Data Architecture
Streamlit / Service Separation
Structured DB vs. Vector DB
Due-Out Domain
Messy Spreadsheet Ingestion
Evaluation / Testing
Product Profiles
```

## Good — Refine

```text
Agent Architecture
Model Router
Security / Guardrails
Provenance
Temporal Model
Human Review
Organization Hierarchy
Reporting
Readiness / Analytics
Production Hardening
```

## Partial — Address Explicitly

```text
Policy Foundation
Policy Resolution
No-SOP Handling
Source Authority / Reconciliation
My Work Queue
Case Management
Domain Events
Connector Framework
AdaState Scaling
```

---

# Recommended Architectural Direction

The most important evolution is to make Ada:

```text
Policy-aware
Source-aware
Hierarchy-aware
Historically reproducible
Operationally task-centered
```

Target operating model:

```text
People / Organizations / Training / Admin
                  │
                  ▼
          Cases / Tasks / Due-Outs
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
     Policies  Workflows  Evidence
        │         │         │
        └─────────┼─────────┘
                  ▼
          Deterministic Rules
                  │
                  ▼
              My Work
                  │
                  ▼
         Streamlit + AI Assistant
```

This keeps HR work at the center of the product while agents, policy RAG, data services, workflows, and automation support that work.
