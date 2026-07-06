# story: cursor-capture [cli]
As a developer using Cursor I can have my AI-assisted sessions captured the same way Claude Code sessions are so that coverage does not depend on which IDE I used.

## Rules
- The `gleaner-cursor-upload` stop hook posts the session when a Cursor agent session completes.
- The uploaded session is tagged with its source IDE (`provenance.ide == "cursor"` or equivalent).

## Examples
- Given the Cursor hook is configured and `GLEANER_TOKEN` is set
  When a Cursor AI session completes
  Then the session appears in `GET /api/sessions?limit=5` with the cursor source tag.
