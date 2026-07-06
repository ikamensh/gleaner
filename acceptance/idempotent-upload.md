# story: idempotent-upload [api]
As an operator or developer retrying a failed upload I can upload the same session twice safely so that retries never corrupt stats or duplicate data.

## Rules
- POST `/api/session` with a duplicate `session_id` returns ok (not a conflict).
- Re-upload replaces stored transcript and metadata (last-write-wins).
- Counters, stats, and exports count unique `session_id`s: re-upload never inflates them.
- The sessions list contains exactly one entry per `session_id`.
- Mock and cloud storage agree on all of the above.

## Examples
- Given a session with `session_id = "S"` was already uploaded
  When the same session is uploaded again with updated metadata/transcript (V2)
  Then `GET /api/session/S` returns V2 metadata, `GET /api/session/S/raw` returns V2 bytes,
  and `GET /api/stats` `total_sessions` increased by exactly 1 relative to before either upload.
- Given the same session is uploaded a third time
  When `GET /api/stats` is read
  Then `total_sessions` still reflects exactly one session for "S".
