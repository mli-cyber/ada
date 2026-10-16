#!/usr/bin/env bash
set -euo pipefail

# Do not source this script; sourcing can terminate the shell on errors.
if (return 0 2>/dev/null); then
  echo "Do not source this script."
  echo "Run it directly: ./scripts/run_demo.sh"
  return 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

# Dedicated, disposable, synthetic demo environment. These are deliberately NOT the
# default dev/production paths and never a PostgreSQL (operational) database.
DEMO_DIR="${ROOT_DIR}/.demo"
export ADA__DEMO_MODE=1
export ADA__DEMO_DATA_DIR="${DEMO_DIR}"
export ADA__SECRETS_BACKEND=env
export ADA__DATA_PATH="${DEMO_DIR}/data"
export ADA__DB_URL="sqlite:///${DEMO_DIR}/data/ada.db"
export ADA__CHROMA_PATH="${DEMO_DIR}/chroma"
export ADA__OBJECT_STORE_PATH="${DEMO_DIR}/objects"

echo "Starting Ada Demo Superuser Mode (synthetic, isolated data only)..."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to launch demo mode. Install it or run: python -m pip install -e ."
  exit 1
fi

# Fail closed: refuse to launch unless the environment verifies as isolated.
uv run --no-sync python - <<'PY'
import sys

from ada.config import AdaConfig
from ada.platform.demo import DemoModeError, verify_demo_isolation

config = AdaConfig.from_env()
try:
    verify_demo_isolation(config)
except DemoModeError as exc:
    print(f"Refusing to start demo mode: {exc}", file=sys.stderr)
    sys.exit(2)
print("Demo environment verified isolated (local SQLite, environment secrets).")
PY

# Load deterministic synthetic demo data (idempotent).
uv run --no-sync python scripts/seed_phase1.py

echo "Local demo URL: http://localhost:8501"
exec uv run --no-sync streamlit run app/streamlit_app.py --server.address=localhost
