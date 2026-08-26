#!/usr/bin/env bash
set -euo pipefail

# Do not source this script; sourcing can terminate the shell on errors.
if (return 0 2>/dev/null); then
  echo "Do not source this script."
  echo "Run it directly: ./scripts/run_app.sh"
  return 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Starting Ada (AI-Driven Assistant)..."
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

# The temporary AWS SSO helper displays a short-lived device code, so the development
# launcher is intentionally localhost-only. Production authentication replaces this helper.
echo "Local development URL: http://localhost:8501"
STREAMLIT_ARGS=(streamlit run app/streamlit_app.py --server.address=localhost)

if command -v uv >/dev/null 2>&1; then
  # `uv run` resolves this project's own virtualenv (syncing from pyproject.toml if
  # needed) regardless of what is activated in the caller's shell.
  exec uv run "${STREAMLIT_ARGS[@]}"
fi

# No uv on PATH: fall back to the current Python environment (must have deps installed).
if ! python -c "import streamlit" >/dev/null 2>&1; then
  echo "Missing runtime packages in the current Python environment."
  echo "Install once with:"
  echo "  uv sync"
  echo "or:"
  echo "  python -m pip install -e ."
  exit 1
fi

exec python -m "${STREAMLIT_ARGS[@]}"
