# Temporary Security Exceptions

Security exceptions are explicit, narrow, and reviewed when dependencies change. They do not
waive new advisories.

## Chroma 1.5.9 server-path advisories

**Status:** Temporarily accepted for the Phase 0 local-only adapter; remove as soon as a
patched Chroma release is available.

**Advisories:** `PYSEC-2026-311`, `CVE-2026-45830`, `CVE-2026-45831`,
`CVE-2026-45833`.

**Why no upgrade is available:** As of 2026-08-26, PyPI reports 1.5.9 as the latest Chroma
release and `pip-audit` lists no fixed version.

**Affected surfaces:** The advisories concern Chroma's remotely reachable Python FastAPI
server, dynamic remote embedding-function configuration, and multi-tenant authorization.

**Ada compensating controls:**

- Ada instantiates only local `chromadb.PersistentClient`; it does not start or expose the
  Chroma FastAPI server.
- Phase 0 supplies no remote Chroma URL, tenant API, authentication provider, or inbound
  network listener.
- Ada creates a fixed local collection without an external embedding function or
  `trust_remote_code`.
- The vector-store adapter is reachable only through controlled application services.
- Dependabot checks weekly; all non-listed advisories remain blocking in CI.

**Removal condition:** Upgrade to the first patched stable Chroma release, remove the audit
ignore flags, rerun the full unit/integration suite, and delete this exception.
