# Ada Evaluation Harness

Golden datasets and per-phase acceptance evals so each roadmap phase's exit criteria are
**measurable** (mirrors the AISI IWB `evals/` approach). See `doc/roadmap_v3.md` Section 10.

## Layout

```text
evals/
├── datasets/       # golden inputs (workbooks, documents, query sets)
├── expected/       # expected outputs
├── query_plans/    # natural-language -> structured query plan goldens
├── adversarial/    # prompt-injection documents that must NOT cause tool calls/writes
└── runners/        # per-phase acceptance runners
```

## Metrics (as phases land)

- Extraction accuracy (Phase 6)
- Schema-mapping accuracy (Phase 5)
- Query-plan correctness (Phase 4)
- Due-out normalization accuracy (Phase 9)
- Report fidelity (Phase 11)
- Adversarial safety: 0 tool calls/writes triggered by injected document content (Phase 19)

This directory is a scaffold placeholder; runners are added starting in Phase 4.
