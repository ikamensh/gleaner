# story: pull-export-sessions [cli]
As a developer I can sync sessions from the server into a local Parquet index so that I can analyze them offline.

## Rules
- `gleaner pull` creates or updates `~/.gleaner/index.parquet` with one row per session (at minimum: `session_id`, `topic`, `project`, `user`, `message_count`, `first_timestamp`, `last_timestamp`).
- Running pull twice is idempotent: already-synced sessions are not duplicated.
- Sessions added to the server between runs appear after the next pull.
- Raw JSONL files land at `~/.gleaner/sessions/{session_id}/raw.jsonl` (or `.jsonl.gz`).

## Examples
- Given at least one session is stored on the server
  When `gleaner pull` runs twice in a row
  Then the Parquet index has exactly one row per session both times.
