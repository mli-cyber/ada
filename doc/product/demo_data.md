# Phase 1 Demo Data

Phase 1 demo data is synthetic, deterministic, and safe to distribute with the repository.
It exists to exercise canonical schemas, temporal history, hierarchy operations, security
filtering, and the read-only Streamlit demonstrations.

Load it with:

```bash
uv run python scripts/seed_phase1.py
```

The loader creates 30 records on its first run and skips the same 30 stable IDs on later runs.
It never overwrites an existing canonical record.

## Rules

- Never copy production or operational personnel records into this dataset.
- Use the fixed Ada UUID namespace and semantic keys so IDs remain stable.
- Use clearly fictional names, organizations, documents, and identifiers.
- Do not include plaintext national identifiers. The encrypted field uses a non-secret test
  codec marker and the suffix is synthetic.
- Keep source fixtures normalized and reviewable under `samples/phase1_seed/`.
- The seed operation must be idempotent.

## Expected coverage

- Three organization levels with at least two sibling organizations.
- Current and historical personnel assignments.
- Personnel with public, internal, and sensitive fields.
- Training courses, inherited requirements, and completion history.
- Open and completed due-outs.
- One administrative action and one absence.
- Document and evidence references used by entity provenance.

The seed manifest records the fixture format version and UUID namespace. Tests verify that a
second seed run does not create duplicates and that all generated IDs match expected values.
Each seeded entity version also receives deterministic evidence and provenance references back
to `samples/phase1_seed/seed.json`.
