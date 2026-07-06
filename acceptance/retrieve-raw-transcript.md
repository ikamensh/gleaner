# story: retrieve-raw-transcript [api]
As an operator or analyst I can download the original JSONL transcript of a session so that I can inspect the full conversation offline.

## Rules
- `GET /api/session/{id}/raw` with a valid Bearer token returns `200 OK` with `Content-Type: application/gzip`.
- The body decompresses to valid JSONL where each line has a `type` field (`user`, `assistant`, `tool_result`, or `summary`).
- The content matches what was uploaded: same number of lines, same message payloads.

## Examples
- Given session "S" was uploaded with a non-empty transcript
  When `GET /api/session/S/raw` is called with a valid token
  Then the gunzipped body equals the uploaded transcript line for line.
