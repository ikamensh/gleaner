# Iteration 1

**Outcome**: Hardened the core capture contract around idempotent uploads, enforced mock/cloud parity for replacement logic, added local acceptance tests, guarded live production tests behind opt-in, and reconciled supported-source documentation.

## Goal

Harden the core capture contract around idempotent uploads and safe local acceptance testing.

## Acceptance Signal

- A duplicate `session_id` upload uses last-write-wins semantics.
- The newer upload replaces transcript and metadata for that `session_id`.
- Counters, stats, and exports count unique `session_id`s only and never inflate from duplicate uploads.
- Mock/local storage and cloud database storage agree on duplicate behavior.
- Default CI and local acceptance tests prove capture, duplicate replacement, unique-session counting, exports, and raw retrieval without touching production.
- Live-uploading end-to-end tests are behind explicit opt-in only; default CI must not create deployed-service data.
- Docs reflect actual supported sources and current behavior: Claude Code and Cursor capture here, with Codex capture pending in a separate branch.
- Code changes are PR'd against `ikamensh/gleaner`, Hive's working repository for now.

## Likely Next Steps

1. Write acceptance stories for capture, duplicate replacement, unique stats/counting, exports, and raw retrieval.
2. Add or adjust tests for mock/local duplicate behavior.
3. Fix storage behavior so duplicate `session_id` replacement is consistent across mock and cloud paths.
4. Gate live production end-to-end tests behind explicit opt-in.
5. Reconcile README, storage docs, and collected-data docs with the supported-source reality.

## Out of Scope for This Branch

Do not build the Codex capture adapter here. Codex capture remains in scope for the overall spec, but implementation lands separately from the local `codex-capture` branch.
