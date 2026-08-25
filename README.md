# Ada - AI-Driven Assistant

**Ada** is a conversational, agentic assistant for **personnel, training, and operations**
data management. Users talk to Ada in natural language, upload messy files (XLSX/CSV/PDF/DOC/
TXT), and get back clean, structured, auditable data and reports.

> **Status:** Scaffold / early foundation. The application skeleton, AWS Bedrock connection
> boundary, configuration, and Streamlit shell are in place; domain features are implemented
> per the roadmap. Most `src/ada/*` modules are intentional placeholders that raise
> `NotImplementedError` and reference their roadmap phase.

**Stack:** Streamlit UI + AWS Bedrock (via Strands) + PostgreSQL (source of truth) + Chroma
(semantic/evidence). Local-first by default; the only hard cloud dependency is Bedrock.

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

Ada connects to AWS Bedrock using your existing AWS profile:

```dotenv
AWS_PROFILE=<your-sso-or-iam-profile>
AWS_REGION=us-east-1
ADA__BEDROCK_CHAT_MODEL_ID=us.anthropic.claude-sonnet-5
```

Run the tests:

```bash
uv run pytest
```

## Layout

```text
app/streamlit_app.py      # Streamlit UI entrypoint (presentation only)
app/pages/                # multipage nav (Home, Assistant, Personnel, ... , Administration)
src/ada/config.py         # AdaConfig: ADA__* + AWS_* env loader (real)
src/ada/bedrock.py        # AWS Bedrock client boundary (stub methods)
src/ada/                  # platform, domain, registry, agents, tools, services,
                          #   ingestion, provenance, quality, reports, workflows (stubs)
evals/                    # golden datasets + per-phase acceptance evals (placeholder)
tests/                    # scaffold smoke tests
doc/roadmap_v3.md         # the active roadmap (Phases 0-19); supersedes v2
doc/product.md            # product overview and naming
```

## Configuration

All settings resolve from the environment through `AdaConfig` (`src/ada/config.py`) using the
`ADA__*` namespace plus standard `AWS_*` variables. See [`example.env`](example.env) for the
full list. `.env` is gitignored.

## Documentation

- [`doc/roadmap_v3.md`](doc/roadmap_v3.md) - active roadmap, Phases 0-19 (MVP = Phases 0-11)
- [`doc/product.md`](doc/product.md) - product overview and naming

## Relationship to IWB

Ada reuses architectural patterns from the AISI Intelligence Workbench (agent orchestration,
ingestion, RAG, provenance, validation, human review, reporting) and the same AWS Bedrock
connection pattern. IWB is a pattern source, not a parent product.
