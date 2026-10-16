# Demo Superuser Mode

## Purpose and intended use

Demo Superuser Mode lets a presenter exercise every implemented Ada feature during a
demonstration without being limited by ordinary role-based access control or organization
scope. It is intended only for local, synthetic demonstrations. It is not a production
account and does not change the production authorization architecture.

When active, the current identity becomes a dedicated `Demo Superuser` principal
(`demo_superuser`) that holds every application permission and every PII tier. Writes still
flow through the controlled services, so validation, audit, provenance, and human-review
controls continue to apply.

## Prerequisites

Demo mode activates only when it is explicitly requested **and** the environment is verifiably
isolated. All of the following must hold:

- `ADA__DEMO_MODE` is enabled (truthy). This is necessary but never sufficient on its own.
- The relational backend is local SQLite. An operational PostgreSQL database is refused.
- The secrets backend is `env`. Production secret backends are refused.
- `ADA__DEMO_DATA_DIR` declares a dedicated, disposable directory, and the SQLite database
  plus every local store (data path, Chroma path, object-store path) resolve inside it. Paths
  are resolved through symlinks, so a symlink that escapes the demo directory is refused.

If demo mode is requested but any check fails, Ada fails closed: no demo principal is issued
and the affected pages stop with a clear message.

## Launch command

Use the dedicated launcher, which sets an isolated `.demo/` environment, verifies isolation
before starting, loads synthetic data, and binds to localhost:

```bash
./scripts/run_demo.sh
```

The launcher exports, for the demo session only:

- `ADA__DEMO_MODE=1`
- `ADA__DEMO_DATA_DIR=<repo>/.demo`
- `ADA__SECRETS_BACKEND=env`
- `ADA__DATA_PATH`, `ADA__DB_URL`, `ADA__CHROMA_PATH`, `ADA__OBJECT_STORE_PATH` under `.demo/`

## Demo identity and permissions

- Identity: `demo_superuser`
- Display name: `Demo Superuser`
- Role: dedicated `demo_superuser` role, distinct from the production `admin` role
- Permissions: all application permissions
- PII access: all tiers (public, internal, sensitive)
- Organization scope: the full synthetic hierarchy in the demo dataset

The demo role is gated. It cannot be selected through `ADA__DEV_ROLE`; attempting to do so
outside verified demo mode is rejected.

## Synthetic data requirements

- Demo data must be synthetic and safe to distribute. Never load real or operational records.
- The deterministic Phase 1 seed (`samples/phase1_seed/`) provides the demo dataset. The
  launcher loads it automatically; it can also be loaded manually:

  ```bash
  uv run python scripts/seed_phase1.py
  ```

- The seed is idempotent and insert-only; re-running it does not duplicate or overwrite data.
- National identifiers in the fixture are non-secret placeholders, never real values.

## Data reset procedure

The demo environment is disposable. To start clean:

```bash
rm -rf .demo
./scripts/run_demo.sh
```

The admin reset utility is also available within an isolated demo session (it only operates on
local SQLite):

```bash
./scripts/reset_local.sh --yes
```

## Known limitations

- Phase 1 does not enforce per-principal organization scoping, so "all organizations" is
  demonstrated through full-hierarchy scope and rollups rather than by relaxing a restriction
  that does not yet exist.
- The AI assistant, Training, Due-Outs, Reports, and Data Quality pages remain scaffold
  placeholders and are labeled as planned; demo mode does not fabricate these capabilities.
- The PostgreSQL path is intentionally impossible in demo mode, so it is not exercised there.
- Cross-page identity is derived from the verified configuration on each page rather than from
  a shared mutable session, so it stays consistent across navigation.

## Security restrictions

- Disabled by default; the opt-in flag alone never grants access.
- Fails closed when isolation cannot be verified.
- Never runs against an operational PostgreSQL database.
- Never uses a non-environment secrets backend.
- The database and local stores must resolve inside the declared demo directory, so an
  existing operational SQLite file, a database path override, or an escaping symlink cannot be
  selected.
- The demo role is never a production account and cannot be reached through role configuration.
- Demo activation performs no automatic external calls. The implemented Bedrock surface has no
  privileged mutating operations; the only external action is a manual, read-only health
  check. Use a non-production AWS profile during demonstrations.

## Troubleshooting

- "Demo mode requested but the environment is not isolated": one or more prerequisites failed.
  Read the listed findings. Common causes:
  - `ADA__DEMO_DATA_DIR` is unset.
  - `ADA__DB_URL` points to a SQLite file outside the demo directory, or to PostgreSQL.
  - A store path (data, Chroma, objects) is outside the demo directory.
  - `ADA__SECRETS_BACKEND` is not `env`.
- "Role 'demo_superuser' requires verified demo mode": the demo role was set through
  `ADA__DEV_ROLE`. Use `ADA__DEMO_MODE` and the launcher instead.
- Empty Personnel or Organization pages: load the synthetic seed with
  `uv run python scripts/seed_phase1.py` (the launcher does this automatically).
