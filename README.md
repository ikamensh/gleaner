# Gleaner

Harvest and centralize coding-agent session transcripts across your team.

Gleaner automatically uploads complete session transcripts to central storage when a session ends. It gives your team visibility into how Claude Code and Cursor are being used: which tools, which projects, how often, and the full conversation history.

Supported sources: **Claude Code** and **Cursor** are currently supported as same-tier official sources. Support for Codex capture is in-scope for the overall project but is pending (landing separately in another branch).

https://gleaner-430011644943.europe-west1.run.app/gleaner/

## Quick start

```bash
# Install the CLI (requires uv: https://docs.astral.sh/uv)
uv tool install git+https://github.com/covenance-ai/gleaner

# Configure and install the session hooks (Claude Code + Cursor)
gleaner setup https://gleaner-430011644943.europe-west1.run.app gl_your_token

# Check everything is working
gleaner status
```

That's it. New Claude Code and Cursor sessions auto-upload from now on.

Get a token by signing in with Google at your Gleaner dashboard.

## CLI commands

```bash
gleaner setup URL TOKEN              # Save config + install Claude Code and Cursor hooks
gleaner status                       # Show config, hook, and connection status
gleaner on                           # Enable all session upload hooks
gleaner off                          # Disable all session upload hooks
gleaner auth TOKEN                   # Update the API token
gleaner backfill                     # Upload existing Claude Code sessions from ~/.claude/projects/
gleaner backfill --source cursor     # Upload existing Cursor sessions from ~/.cursor/projects/
gleaner backfill --dry-run           # Preview what would be uploaded
gleaner collect                      # Collect local IDE sessions into the local vault
gleaner pull                         # Download sessions for local analysis (Parquet)
gleaner pull --transcripts           # Also download raw transcripts
gleaner serve                        # Start local dashboard (http://127.0.0.1:8765)
```

Config is stored in `~/.config/gleaner.json`. Claude Code hooks are managed in `~/.claude/settings.json`; Cursor hooks in `~/.cursor/hooks.json`.

## How it works

### Claude Code

```
Claude Code session ends
        |
        v
SessionEnd hook fires (gleaner-upload)
        |
        v
  - finds the session JSONL in ~/.claude/projects/
  - parses metadata (message counts, tools used, duration, timestamps)
  - optionally scrubs PII/secrets
  - classifies source (human/kodo/test) and task_type
  - uploads metadata to Firestore + raw transcript to GCS
```

### Cursor

```
Cursor agent session ends
        |
        v
stop hook fires (gleaner-cursor-upload)
        |
        v
  - finds the session JSONL in ~/.cursor/projects/*/agent-transcripts/
  - parses metadata (message counts, tools used)
  - optionally scrubs PII/secrets
  - classifies source (human/kodo/test) and task_type
  - uploads metadata to Firestore + raw transcript to GCS
```

A periodic launchd agent (every 5 min) runs `gleaner backfill --source cursor` to catch any sessions missed by the stop hook.

Both IDEs record full session transcripts locally as JSONL files. Gleaner collects these centrally so you can browse, search, and analyze them across your whole team.

## Dashboard

The web dashboard is available at your Gleaner URL. Sign in with Google to onboard, or use a `gl_` token.

Features:
- **Home**: personal stats, activity heatmap, recent sessions
- **Team**: aggregate stats, member activity, project breakdown
- **Sessions**: filterable list with full transcript viewer and search
- **Settings**: token management, setup instructions

## Deploy the server

The server deploys to Cloud Run automatically on push to `main` via GitHub Actions.

For manual initial setup:

```bash
# Set required env vars on Cloud Run
gcloud run services update gleaner --region europe-west1 \
    --update-env-vars "GLEANER_ADMIN_TOKEN=$(openssl rand -hex 32)" \
    --update-env-vars "GLEANER_GOOGLE_CLIENT_ID=your-oauth-client-id"
```

The admin token is for the `/admin/*` API (bulk token management). The Google client ID enables the "Sign in with Google" button for user onboarding.

## API

All data endpoints require a `Bearer` token (user token or Google JWT).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/session` | Bearer | Upload a session transcript |
| `GET` | `/api/sessions` | Bearer | List sessions (filter: `?user=`, `?project=`, `?limit=`) |
| `GET` | `/api/session/{id}` | Bearer | Session metadata |
| `GET` | `/api/session/{id}/raw` | Bearer | Download raw JSONL.gz |
| `GET` | `/api/me` | Bearer/Google | Personal stats or onboarding status |
| `GET` | `/api/stats` | Bearer | Aggregate usage stats |
| `POST` | `/api/onboard` | Google | Complete user onboarding |
| `POST` | `/api/tokens` | Bearer | Create own API token |
| `GET` | `/api/tokens` | Bearer | List own tokens |
| `DELETE` | `/api/tokens/{id}` | Bearer | Revoke own token |
| `POST` | `/admin/tokens` | Admin | Create token for any user |
| `GET` | `/admin/tokens` | Admin | List all tokens |

## Project structure

```
gleaner/
  gleaner/              # Installable client package
    cli.py                  # gleaner command: setup, status, on/off, auth, backfill, collect, serve, pull
    upload.py               # gleaner-upload: Claude Code SessionEnd hook handler
    cursor.py               # Cursor session discovery (~/.cursor/projects/)
    cursor_upload.py        # gleaner-cursor-upload: Cursor stop hook handler
    backfill.py             # gleaner backfill: upload existing sessions (Claude Code + Cursor)
    config.py               # Config file + Claude Code and Cursor hook management
    tags.py                 # Session classification: source (human/kodo/test) and task_type
    schema.py               # Vault data schema (SessionMeta, NormalizedEntry)
    vault.py                # Local session vault (~/.gleaner/)
    scrub.py                # PII/secret scrubbing (optional deps)
    cc_format.py            # Claude Code JSONL format helpers
    pull.py                 # gleaner pull: download sessions to Parquet
  server/                   # FastAPI server (deployed to Cloud Run)
    server.py               # API routes and auth
    db.py                   # Firestore + GCS operations
    db_mock.py              # In-memory mock for dev/testing
    dashboard.html          # Single-file SPA dashboard
    Dockerfile
    requirements.txt
  ops/                      # Operational scripts (run manually)
    backfill_counters.py    # Rebuild counter docs from sessions
    backfill_topics.py      # Extract topics from transcripts
    scrub_cloud.py          # Scrub all transcripts in GCS
  tests/
    test_e2e.py             # Upload-and-retrieve integration tests
    test_scrub.py           # PII scrubbing unit tests
  .github/workflows/
    deploy.yml              # CI: test + deploy to Cloud Run on push
  pyproject.toml
```

## Architecture

```
Developer machine                        GCP (covenance-469421)
+------------------+                     +----------------------------+
| Claude Code      |                     | Cloud Run (gleaner)        |
|  SessionEnd hook |--POST /api/session->| FastAPI server             |
|  gleaner-upload  |                     |   |           |            |
+------------------+                     |   v           v            |
                                         | Firestore   GCS            |
+------------------+                     | (metadata)  (transcripts)  |
| Cursor           |                     |   |           |            |
|  stop hook       |--POST /api/session->|   v           v            |
|  gleaner-cursor- |                     | sessions/   sessions/      |
|  upload          |                     | users/      {id}.jsonl.gz  |
+------------------+                     | tokens/                    |
                                         +----------------------------+
+------------------+
| Web browser      |--GET /api/sessions->Cloud Run-->JSON/HTML
| Dashboard        |
+------------------+
```

## Environment variables

**Server-side** (Cloud Run):

| Variable | Default | Description |
|----------|---------|-------------|
| `GLEANER_GCP_PROJECT` | `covenance-469421` | GCP project ID |
| `GLEANER_GCS_BUCKET` | `gleaner-sessions` | GCS bucket for transcripts |
| `GLEANER_ADMIN_TOKEN` | (none) | Admin token for `/admin/*` endpoints |
| `GLEANER_GOOGLE_CLIENT_ID` | (none) | Google OAuth client ID for sign-in |
| `BASE_PATH` | `/gleaner` | URL prefix |
| `PORT` | `8080` | HTTP listen port |
