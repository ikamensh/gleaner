# story: claude-code-capture [cli]
As a developer using Claude Code I can have my sessions captured automatically when they end so that my team has a durable record without me doing anything.

## Rules
- `gleaner setup` installs the `gleaner-upload` SessionEnd hook into `~/.claude/settings.json`.
- Ending a Claude Code session fires the hook and uploads the session within seconds.
- The uploaded record carries correct `topic`, `project`, `message_count`, and `provenance.user`.

## Examples
- Given `gleaner setup` has been run and `GLEANER_TOKEN` is configured
  When a Claude Code session ends (Ctrl-D or `/exit`)
  Then `GET /api/sessions?limit=5` returns the new session with correct topic, project, message_count, and provenance.user.
