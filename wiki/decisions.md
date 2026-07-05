# Decisions

## 2026-07-05 Intake Approval

Provenance: user approved the revised intake brief in the current transcript and confirmed the accepted answers from the earlier intake round.

Accepted decisions:

- Mission: Gleaner is the durable system of record for coding-agent sessions, capturing transcripts, scrubbing sensitive content before upload, storing metadata plus raw transcript safely, and making sessions retrievable for audit, search, and lightweight usage insight.
- Current supported sources in this repo: Claude Code and Cursor capture are in scope. Cursor is official same-tier support. kodo classification is in scope.
- Codex capture: in scope for the overall product spec, but implementation lands separately from the local `codex-capture` branch. Do not build the Codex adapter here.
- Duplicate `session_id` upload semantics: last-write-wins. The newer upload replaces transcript and metadata for that `session_id`.
- Counting semantics: counters, stats, and exports count unique `session_id`s only and must never inflate from duplicate uploads.
- Storage parity: mock/local storage and cloud database storage must agree on duplicate behavior.
- Acceptance testing: default CI and local acceptance tests must prove capture, duplicate replacement, unique-session counting, exports, and raw retrieval without touching production.
- Live-uploading end-to-end tests: keep behind explicit opt-in only. Default CI must not create deployed-service data.
- Documentation: reflect actual supported sources and current behavior. Claude Code and Cursor are supported here; Codex capture is pending/separate.
- Repository workflow: PR code changes against this fork, `ikamensh/gleaner`, as Hive's working repository for now.

Assumptions carried forward:

- No pre-existing durable spec files were present in this checkout at intake time, so the approved handoff brief is the source of truth for these files.
- Production care means not running default tests that upload to the deployed service.
- Code changes are not part of this spec-writing task.

