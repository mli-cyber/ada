#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

if [[ "${1:-}" != "--yes" ]]; then
  echo "Refusing to reset without explicit confirmation."
  echo "Run: ./scripts/reset_local.sh --yes"
  exit 2
fi

exec uv run python -m ada.platform.maintenance reset --yes
