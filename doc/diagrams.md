# Ada - Architecture & Flow Diagrams

This is the single place that collects Ada's flowcharts with a short explanation of each.
Diagrams 1–8 also appear in [`roadmap_v3.md`](roadmap_v3.md) in context; diagrams 9–16 live
here and in any directly relevant phase document. The headline diagrams (1–2, simplified)
also appear in [`product.md`](product.md).

> **Living diagrams (subject to change).** These flowcharts reflect the *current* design
> intent and will be **updated/replaced** as the architecture is refined or as phases are
> implemented. If a diagram ever diverges from the code, treat the implementation and the
> per-phase docs (e.g. [`phase_0.md`](phase_0.md)) as the source of truth.

## Contents

1. [Target architecture](#1-target-architecture)
2. [Agentic / multi-agent architecture](#2-agentic--multi-agent-architecture)
3. [Model Router + budget tiers](#3-model-router--budget-tiers)
4. [AWS Bedrock connection](#4-aws-bedrock-connection)
5. [Streamlit UI -> Services -> DB](#5-streamlit-ui---services---db)
6. [Structured ingestion pipeline](#6-structured-ingestion-pipeline)
7. [MVP first-demo flow](#7-mvp-first-demo-flow)
8. [Development sequence](#8-development-sequence)
9. [Document storage & provenance](#9-document-storage--provenance)
10. [Policy resolution](#10-policy-resolution)
11. [Read / write safety (LLM Data Guard)](#11-read--write-safety-llm-data-guard)
12. [Organization hierarchy & roll-up](#12-organization-hierarchy--roll-up)
13. [Event-driven workflow](#13-event-driven-workflow)
14. [Policy lineage](#14-policy-lineage)
15. [Phase 0 component boundaries](#15-phase-0-component-boundaries)
16. [CI/CD delivery flow](#16-cicd-delivery-flow)

---

## 1. Target architecture

The end-to-end system. Streamlit is presentation-only; all logic lives behind the
**application/service layer**, which is the *only* layer allowed to touch the databases.
Agents interpret; **controlled domain tools**, the **LLM Data Guard**, and deterministic
services execute. The structured DB is the source of truth; the object store holds original
files; the vector DB holds policy/document chunks, embeddings, and evidence.

```mermaid
flowchart TD
    User[User] --> UI[Streamlit Interface]
    UI --> Chat[Chat]
    UI --> Uploads[Uploads]
    UI --> Tables[Tables / Forms]
    UI --> Dash[Dashboards]
    Chat --> Svc[Application / Service Layer]
    Uploads --> Svc
    Tables --> Svc
    Dash --> Svc
    Svc --> Orch["Agent Orchestrator (Bedrock)"]
    Orch --> IntentQ[Intent / Query Agents]
    Orch --> Ingest[Ingestion / Mapping Agents]
    Orch --> WFR[Workflow / Report Agents]
    IntentQ --> Gate[Validation / Authorization / Data Guard / Guardrails]
    Ingest --> Gate
    WFR --> Gate
    Gate --> Tools[Controlled Domain Tools]
    Tools --> Personnel[Personnel]
    Tools --> Org[Organization]
    Tools --> Training[Training]
    Tools --> DueAdmin[Due-Out / Admin]
    Tools --> Docs[Documents]
    Personnel --> SQL[("SQLite / PostgreSQL - source of truth")]
    Org --> SQL
    Training --> SQL
    DueAdmin --> SQL
    Docs --> SQL
    Docs --> Obj[("Object Store - originals / artifacts")]
    Docs --> Vec[("Vector DB - chunks / embeddings / evidence")]
    SQL --> Reports[Report Service]
    Vec --> Reports
    Reports --> Out["Screen / XLSX / CSV / TXT / PDF"]
```

See roadmap Section 4.

---

## 2. Agentic / multi-agent architecture

How requests flow through agents. A **supervisor/orchestrator** routes to specialist
subgraphs (query, ingestion, due-out, report). The ingestion subgraph shows the
orchestrator-worker + evaluator-optimizer pattern. Every path passes through **guardrails**
and the **model router**, and **high-impact** actions pause at a **human-in-the-loop**
interrupt (LangGraph) before deterministic services commit + audit.

```mermaid
flowchart TD
    UI[Streamlit UI] --> Sup[Orchestrator / Supervisor Agent]
    Sup -->|query| QG[Query subgraph]
    Sup -->|ingest| ING[Ingestion subgraph]
    Sup -->|due-out| DO[Due-Out subgraph]
    Sup -->|report| RPT[Report subgraph]

    subgraph ingestGraph [Ingestion subgraph]
        Struct[Spreadsheet Structure] --> MapW["Schema Mapping workers (fan-out)"]
        MapW --> Val[Validation / Data Quality]
        Val --> EvalLoop[Evaluator-Optimizer loop]
        EvalLoop --> Prev[Import Preview]
    end
    ING --> ingestGraph

    Sup --- State[("AdaState reference envelope + structured handoffs")]
    Sup --- Guard["Guardrails: untrusted-doc + injection + tool allowlist"]
    Sup --- Router["Model Router: tier + capability, fallbacks"]

    Prev --> HITL{High-impact?}
    HITL -->|yes| Review["Human review - LangGraph interrupt"]
    HITL -->|no| Commit["Deterministic services: validate / calc / authorize / write"]
    Review --> Commit
    Commit --> DB[(Structured DB)]
    Commit --> Prov[Provenance + Audit]
    Obs["Observability: traces + routing log + evals"] --- Sup
```

See roadmap Section 13. Framework: **Strands** (agents/tools) + **LangGraph** (durable,
checkpointed workflows).

---

## 3. Model Router + budget tiers

Ada is **multi-model**. A task class maps to a requested **capability**, and two orthogonal
levers pick the model for each call: that capability and the **budget tier** (High / Balanced
/ Economy). Each tier has a primary model and a fallback chain. Lower tiers are a cost/quality
lever, **not** a kill switch - the required pipeline always runs.

```mermaid
flowchart TD
    Tier["Budget tier: High / Balanced (default) / Economy"] --> Router[Model Router]
    Task["Task class: routing / extraction / high-stakes"] --> Capability["Requested capability"]
    Capability --> Router
    Router -->|primary| M1[Tier primary model]
    Router -->|on failure| M2[Fallback chain]
    Router --- Ceil["Ceilings + optional-pass policy (for_tier)"]
    subgraph tiers [Tier profiles]
        High["High: claude-opus-5 -> claude-sonnet-5"]
        Bal["Balanced: claude-sonnet-5 -> nova-pro, gpt-oss-120b"]
        Eco["Economy: nova-pro -> gpt-oss-120b, llama3-1-70b, mistral-large-3, gemma-3-27b"]
    end
    M1 --- tiers
    M2 --- tiers
```

See roadmap Section 7.2. Embeddings stay fixed (`amazon.titan-embed-text-v2:0`).

---

## 4. AWS Bedrock connection

How Ada reaches Bedrock - the same `boto3` session pattern as IWB, driven entirely by
`AWS_PROFILE` / `AWS_REGION` through `AdaConfig`.

```mermaid
flowchart TD
    Env["AWS_PROFILE + AWS_REGION"] --> Session["boto3.Session(profile_name, region_name)"]
    Session --> Client["session.client('bedrock-runtime', region_name)"]
    Client --> Model["strands.models.BedrockModel(model_id, max_tokens, [temperature])"]
    Model --> AgentNode["strands.Agent(model=BedrockModel(...))"]
```

See roadmap Section 3.

---

## 5. Streamlit UI -> Services -> DB

The separation-of-concerns rule: the UI never holds business logic. It calls stable
**application services**, which own all database access. This keeps the platform replaceable
(e.g., swap Streamlit for React later) without touching the core.

```mermaid
flowchart TD
    UI[Streamlit UI] --> Svc[Application Services]
    Svc --> A[Agent Service]
    Svc --> Q[Query Service]
    Svc --> P[Personnel Service]
    Svc --> T[Training Service]
    Svc --> D[Due-Out Service]
    Svc --> W[Workflow Service]
    Svc --> R[Report Service]
    Svc --> Z[Authorization Service]
    A --> DB[(Databases)]
    Q --> DB
    P --> DB
    T --> DB
    D --> DB
    W --> DB
    R --> DB
    Z --> DB
```

See roadmap Section 4.1.

---

## 6. Structured ingestion pipeline

The Phase 5 path for spreadsheets/CSV: parse, detect headers, map heterogeneous columns to
the canonical schema, validate, resolve entities, **preview**, then commit. Nothing is
written until the preview is approved.

```mermaid
flowchart LR
    Upload[Upload] --> Parser[Parser]
    Parser --> Header[Header Detection]
    Header --> Mapping[Schema Mapping Agent]
    Mapping --> Validation[Validation]
    Validation --> Entity[Entity Resolution]
    Entity --> Preview[Import Preview]
    Preview --> Commit[Commit]
```

See roadmap Phase 5.

---

## 7. MVP first-demo flow

The headline demo: a messy operational workbook becomes structured records + due-outs, then
answers and a manager-ready report - in minutes.

```mermaid
flowchart TD
    Upload[Upload messy operational workbook] --> Detect[Agent detects sections / tables]
    Detect --> Preview[Preview normalized records]
    Preview --> Approve[User approves import]
    Approve --> Stored[Structured records + Due-Out data]
    Stored --> Ask[User asks questions in chat]
    Ask --> View[On-screen table / dashboard]
    View --> Report[Excel / PDF report]
```

See roadmap Section 11.

---

## 8. Development sequence

The phase delivery order, grouped by stage. The MVP is Phases 0-11, including Phase 2A.

```mermaid
flowchart TD
    subgraph f [FOUNDATION]
        P0[Phase 0 Architecture / Security] --> P1[Phase 1 Canonical Model] --> P2["Phase 2 Domain Registry & Profiles"] --> P2A["Phase 2A Policy Foundation / Source Authority / Data Guard"]
    end
    subgraph core [STREAMLIT CORE APPLICATION]
        Nav[Streamlit navigation / authentication] --> P3[Phase 3 Conversational CRUD] --> P4[Phase 4 Natural-Language Query] --> P5[Phase 5 Structured Ingestion]
    end
    subgraph docs [AGENTIC DOCUMENT + SPREADSHEET PROCESSING]
        P6[Phase 6 Unstructured Ingestion] --> P7[Phase 7 Provenance] --> P8[Phase 8 Entity Resolution / Data Quality]
    end
    subgraph ops [OPERATIONS]
        P9[Phase 9 Due-Outs / Suspenses] --> P10[Phase 10 Training Requirements] --> P11[Phase 11 Reporting / Export]
    end
    subgraph adv [WORKFLOW + TALENT + ANALYTICS]
        P12[Phase 12 Workflows / Cases / Events] --> P13[Phase 13 In/Out Processing] --> P14[Phase 14 Skills / Qualifications] --> P15[Phase 15 Readiness] --> P16[Phase 16 Analytics] --> P17[Phase 17 Advanced Policy Intelligence]
    end
    subgraph gov [GOVERNANCE + HARDENING]
        P18[Phase 18 Human Review] --> P19[Phase 19 Production Hardening]
    end
    f --> core --> docs --> ops --> adv --> gov
```

See roadmap Section 12.

---

## 9. Document storage & provenance

Documents are **not** stored "in the vector DB." The Document Service splits responsibilities:
SQL holds metadata/ACL/version, object storage holds the original file, and the vector DB holds
chunks/embeddings - all linked by `document_id`, with provenance spanning the three.

```mermaid
flowchart TD
    Upload[Uploaded File] --> DocSvc[Document Service]
    DocSvc --> Obj[Object Store - Original File]
    DocSvc --> Meta[SQL - Metadata / ACL / Version]
    DocSvc --> Chunk[Chunking / Embedding]
    Chunk --> Vec[Vector DB]
    Meta --> Prov[Provenance]
    Vec --> Prov
    Obj --> Prov
```

See roadmap Section 3 ("Local-first defaults") and Phases 0/7.

---

## 10. Policy resolution

Retrieving relevant policy is not the same as deciding which **approved rule** governs a task.
A request/event is classified, an agent narrows the policy family, and a **deterministic,
versioned** Policy Resolution Service returns the applicable approved rule set.

```mermaid
flowchart TD
    Req[User Request / Event] --> Task[Task Classification]
    Task --> Router[Policy Router Agent]
    Router --> Resolver[Policy Resolution Service]
    Resolver --> Rules[Applicable Approved Rule Set]
    Rules --> Engine[Deterministic Rule / Workflow Engine]
    Engine --> Action[Task / Due-Out / Requirement]
```

See roadmap Phase 2A.

---

## 11. Read / write safety (LLM Data Guard)

Writes flow through authorization, validation, and change-sets, pausing for human approval when
high-impact. Reads pass through the **LLM Data Guard** so only minimum-necessary fields ever
reach the model.

Write path:

```mermaid
flowchart TD
    Agent[Agent] --> Tool[Controlled Tool Request]
    Tool --> Auth[Authorization]
    Auth --> Valid[Validation]
    Valid --> Change[Change Set]
    Change --> Impact{High Impact?}
    Impact -->|Yes| Review[Human Approval]
    Impact -->|No| Tx[Transaction]
    Review --> Tx
    Tx --> Audit[Audit Event]
```

Read path:

```mermaid
flowchart TD
    DB[(Structured DB)] --> AuthR[Authorization]
    AuthR --> Guard[LLM Data Guard]
    Guard --> AgentR[Agent / LLM]
```

See roadmap 7.5 / 7.8 and Section 14.

---

## 12. Organization hierarchy & roll-up

A query against a parent org resolves descendant scope; roll-up services aggregate metrics up
the hierarchy, and configuration inherits BDE → BN → CO.

```mermaid
flowchart TD
    BDE[Brigade] --> BN[Battalion]
    BN --> HHC[HHC]
    BN --> A[Alpha]
    BN --> B[Bravo]
    BN --> C[Charlie]
    HHC --> Roll[Roll-Up Service]
    A --> Roll
    B --> Roll
    C --> Roll
    Roll --> Output[Readiness / Due-Out / Personnel Metrics]
```

See roadmap Phase 1 (hierarchy/roll-up services).

---

## 13. Event-driven workflow

Domain changes emit events (via a transactional outbox) that a rule engine turns into
workflows, cases, tasks, and due-outs - surfacing in My Work, with no agent polling.

```mermaid
flowchart TD
    Change[Domain Change] --> Event[Domain Event]
    Event --> Rules[Rule Engine]
    Rules --> WF[Workflow]
    WF --> Case[Case]
    WF --> Task[Task]
    WF --> Due[Due-Out]
    Case --> Queue[My Work]
    Task --> Queue
    Due --> Queue
```

See roadmap Phase 12.

---

## 14. Policy lineage

Every operational item traces back to an approved rule and its governing policy - and forward
to the evidence that supports its status.

```mermaid
flowchart LR
    Policy[Policy] --> Rule[Approved Rule]
    Rule --> Template[Due-Out / Workflow Template]
    Template --> Instance[Task / Due-Out Instance]
    Instance --> Response[Response / Action]
    Response --> Evidence[Evidence]
```

See roadmap Phase 2A / Phase 7.

---

## 15. Phase 0 component boundaries

The concrete foundation boundary delivered in Phase 0. The service/tool layer is the only
layer allowed to touch the database; platform controls and storage adapters remain separate,
testable modules.

```mermaid
flowchart TD
    UI[Streamlit UI + Administration health page]
    UI --> Svc[Service/Tool layer - only place allowed to touch DB]
    Svc --> Auth[identity: RBAC matrix + PII tiers + dev principal]
    Svc --> DataGuard[dataguard: minimum-necessary model context]
    Svc --> DB[db: sqlite default / postgres opt-in + healthcheck]
    Svc --> Vec[vectors: Chroma client + healthcheck]
    Svc --> Obj[storage: LocalObjectStore + S3 stub]
    Svc --> Aud[audit: AuditEvent JSONL sink]
    Svc --> Sec[secrets: env backend + AWS stubs]
    Svc --> Guard[guardrails: untrusted-doc wrap + cost/token contract]
    Svc --> Models[models: tier + capability registry]
    Svc --> Review[review: minimal approval primitive]
    Svc --> Prov[provenance: early reference contract]
    Svc --> Bed[bedrock: connect + healthcheck - chat/embed stubbed]
```

See [`phase_0.md`](phase_0.md), Section 4.

---

## 16. CI/CD delivery flow

Phase 0 establishes credential-free PR CI plus a manually authorized Bedrock integration
test. Phase 19 adds immutable, signed artifact promotion and production rollback.

```mermaid
flowchart LR
    PR[Change / Pull Request] --> CI[Phase 0 PR CI]
    CI --> Quality["Frozen sync / Ruff / mypy / pytest"]
    CI --> Docs["Links / Mermaid / tracked-data guard"]
    CI --> Security["Secrets / dependency scan"]
    Quality --> Merge[Protected main]
    Docs --> Merge
    Security --> Merge
    Merge --> Bedrock["Manual Bedrock integration via OIDC"]
    Merge --> CD[Phase 19 CD]
    CD --> Build["Build immutable image"]
    Build --> Supply["SBOM / scan / sign / attest"]
    Supply --> Dev[Deploy dev]
    Dev --> Stage[Promote same digest to staging]
    Stage --> Approval{"Production approved?"}
    Approval -->|yes| Prod[Promote same digest to production]
    Approval -->|no| Hold[Hold]
    Prod --> Health{"Healthy?"}
    Health -->|yes| Complete[Complete]
    Health -->|no| Rollback[Automatic rollback]
```

See roadmap Section 7.10 and [`phase_0.md`](phase_0.md), item 18.
