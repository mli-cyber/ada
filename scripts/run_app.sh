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

# Bind on all interfaces so other devices on the LAN can reach the app, but pass the
# server address explicitly so Streamlit never opens a raw UDP socket to auto-detect the
# LAN IP (that syscall fails in sandboxed/restricted environments).
LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"

if [[ -n "${LAN_IP}" ]]; then
  STREAMLIT_ARGS=(streamlit run app/streamlit_app.py --server.address=0.0.0.0 --browser.serverAddress="${LAN_IP}")
else
  echo "Could not determine a LAN IP; app will only be reachable at localhost:8501."
  STREAMLIT_ARGS=(streamlit run app/streamlit_app.py --server.address=localhost)
fi

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
