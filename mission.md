# Gleaner Mission

Gleaner is the durable system of record for coding-agent sessions.

Its mission is to capture coding-agent transcripts, scrub sensitive content before upload, store metadata plus the raw transcript safely, and make sessions retrievable for audit, search, and lightweight usage insight.

## Operating Principles

- Preserve session history as auditable records keyed by stable `session_id`.
- Scrub sensitive content before upload and keep raw transcript handling explicit.
- Treat upload idempotency as part of the core capture contract, not an implementation detail.
- Prefer deterministic local and CI acceptance tests that never touch production services by default.
- Keep mock/local storage and cloud database behavior aligned for externally visible semantics.
- Keep supported-source documentation accurate. Claude Code and Cursor capture are current same-tier scope here; kodo classification is in scope. Codex capture is part of the broader product spec but lands separately from this branch and must not be built here.
- `ikamensh/gleaner` is the main development repository (independent of the original covenance-ai fork parent); all PRs land here.

