# Iteration plan

Goal: Iteration 2: Add a read-only `gleaner sessions` CLI command that lists locally-captured sessions from the local vault.
Proposed by: agent · approved 2026-07-22

## 1. Implement `gleaner sessions` CLI command

**Story:** As a developer, I can run `gleaner sessions` to see a local, read-only list of my recently captured coding-agent sessions (newest-first, showing source, project, timestamp, and message count) without querying the production server.

**Constraints:** - Add `gleaner sessions` CLI command.
- Read strictly from the local vault; no network requests, never touches production.
- Display one row per unique `session_id`, ordered newest-first.
- Required fields: source (claude/cursor), project, last-updated time, message count.
- Include optional `--source` and `--limit` (default 20) flags.
- Write a deterministic test using a temporary vault to assert the command lists mock sessions correctly (fields, newest-first ordering, `--source` filtering).
- Add the command to the README CLI section.
