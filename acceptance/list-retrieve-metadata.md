# story: list-retrieve-metadata [api]
As a developer or dashboard user I can browse my session list and inspect individual session metadata so that I can find and understand past sessions.

## Rules
- `GET /api/sessions` supports `user=`, `project=`, `limit=`, and `since=` filters, each returning only matching sessions.
- List entries carry `session_id`, `topic`, `project`, `message_count`, `first_timestamp`, `last_timestamp`, and `provenance`.
- `tool_counts` is omitted from the list by default and present with `export=true`.
- `GET /api/session/{id}` returns the complete record including `tool_counts`.

## Examples
- Given sessions from users alice and bob exist
  When `GET /api/sessions?user=alice` is called
  Then only sessions with `provenance.user == "alice"` are returned.
