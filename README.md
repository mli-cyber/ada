# Ada - AI-Driven Assistant

**Ada** is a conversational, agentic assistant for **personnel, training, and operations**
data management. Users talk to Ada in natural language, upload messy files
(`XLSX/CSV/TXT/PDF/DOC/DOCX`; `PPTX` planned), and get back clean, structured, auditable
data and reports.

> **Status:** Phase 0 foundation. Local storage, security, review/provenance, model-routing,
> intake, audit, health, and CI boundaries are implemented; domain features will be built in
> later roadmap phases. Later-phase domain modules remain intentional placeholders.

**Stack:** Streamlit UI + AWS Bedrock (via Strands) + a relational source of truth (SQLite
local default; PostgreSQL opt-in/production path) + Chroma (semantic/evidence). Local-first
by default; the only hard cloud dependency is Bedrock.

## Positioning

Ada's core is general (people, organizations, training/compliance, tasks with deadlines,
administrative actions, documents). Its **first application profile is military-flavored**
(staff sections, reporting cycles, due-outs, ETS/PCS) - an *initial profile*, not the product
identity. A neutral `general` profile adapts the same core to civilian HR.

## Quickstart

```bash
cp example.env .env    # then edit .env with your AWS profile/region/model settings
uv sync
./scripts/run_app.sh
```

The development launcher binds to `localhost` because the Administration page includes a
separate `AWS Session (Local Only)` tab with a temporary SSO device-login helper. General
demo surfaces omit the AWS profile and region; `.env` and AWS credential caches are never
committed.

Ada connects to AWS Bedrock using your existing AWS profile:

```dotenv
AWS_PROFILE=<your-sso-or-iam-profile>
AWS_REGION=us-east-1
ADA__BEDROCK_CHAT_MODEL_ID=us.anthropic.claude-sonnet-5
ADA__MODEL_TIER=balanced
```

Run local quality checks:

```bash
uv run ruff check .
uv run mypy src/ada
uv run pytest
./scripts/audit_dependencies.sh
```

## Layout

```text
app/streamlit_app.py      # Streamlit UI entrypoint (presentation only)
app/pages/                # multipage nav (Home, Assistant, Personnel, ... , Administration)
src/ada/config.py         # AdaConfig: ADA__* + AWS_* env loader (real)
src/ada/bedrock.py        # AWS Bedrock client + live healthcheck boundary
src/ada/                  # platform, domain, registry, agents, tools, services,
                          #   ingestion, provenance, quality, reports, workflows
evals/                    # golden datasets + per-phase acceptance evals (placeholder)
tests/                    # platform unit tests + manual Bedrock integration test
doc/roadmap_v3.md         # the active roadmap (Phases 0-19); supersedes v2
doc/product.md            # product overview and naming
```

## Configuration

All settings resolve from the environment through `AdaConfig` (`src/ada/config.py`) using the
`ADA__*` namespace plus standard `AWS_*` variables. See [`example.env`](example.env) for the
full list. `.env` is gitignored.

## Documentation

- [`doc/roadmap_v3.md`](doc/roadmap_v3.md) - active roadmap, Phases 0-19
  (MVP = Phases 0-11, including Phase 2A)
- [`doc/product.md`](doc/product.md) - product overview and naming
- [`doc/diagrams.md`](doc/diagrams.md) - architecture and flow diagrams
- [`doc/phase_0.md`](doc/phase_0.md) - executable Phase 0 foundation specification
- [`doc/architecture.md`](doc/architecture.md) - implemented Phase 0 boundaries and controls
- [`doc/security_exceptions.md`](doc/security_exceptions.md) - temporary, reviewed dependency exceptions

## Relationship to IWB

Ada reuses architectural patterns from the AISI Intelligence Workbench (agent orchestration,
ingestion, RAG, provenance, validation, human review, reporting) and the same AWS Bedrock
connection pattern. IWB is a pattern source, not a parent product.
