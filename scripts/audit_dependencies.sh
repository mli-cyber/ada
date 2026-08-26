#!/usr/bin/env bash
set -euo pipefail

# Chroma has no patched PyPI release as of 2026-08-26. Ada does not expose the affected
# network/multi-tenant server paths. See doc/security_exceptions.md.
exec uv run --no-sync pip-audit \
  --ignore-vuln PYSEC-2026-311 \
  --ignore-vuln CVE-2026-45830 \
  --ignore-vuln CVE-2026-45831 \
  --ignore-vuln CVE-2026-45833
