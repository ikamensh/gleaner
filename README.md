# Gleaner

Harvest and centralize coding-agent session transcripts across your team.

Gleaner automatically uploads complete session transcripts to central storage when a session ends. It gives your team visibility into how Claude Code and Cursor are being used: which tools, which projects, how often, and the full conversation history.

Supported sources: **Claude Code** and **Cursor** are currently supported as same-tier official sources. Support for Codex capture is in-scope for the overall project but is pending (landing separately in another branch).

https://gleaner-430011644943.europe-west1.run.app/gleaner/

## Quick start

Works on macOS, Linux, and Windows; the same commands everywhere.

```bash
# Install the CLI (requires uv: https://docs.astral.sh/uv)
uv tool install git+https://github.com/ikamensh/gleaner

# Configure and install the session hooks (Claude Code + Cursor)
# and the periodic sync agent
gleaner setup https://gleaner-430011644943.europe-west1.run.app gl_your_token

# Check everything is working
gleaner status

# Optional: menu bar / system tray icon with an on/off switch
gleaner tray install   # start at login
gleaner tray           # or run it right now
```

That's it. New Claude Code and Cursor sessions auto-upload from now on.

Get a token by signing in with Google at your Gleaner dashboard.

## CLI commands

```bash
gleaner setup URL TOKEN [--name N]   # Save a remote + install Claude Code and Cursor hooks
gleaner status                       # Show active remote, hooks, and connection status
gleaner on                           # Enable all session upload hooks
gleaner off                          # Disable all session upload hooks
gleaner auth TOKEN                   # Update the active remote's API token
gleaner remote list                  # List configured remotes (* marks the active one)
gleaner remote add NAME URL TOKEN    # Add/replace a remote (--no-activate to not switch)
gleaner remote use NAME              # Switch the active remote (instance)
gleaner remote remove NAME           # Delete a remote
gleaner remote show [NAME]           # Show a remote's URL + live connection status
gleaner backfill                     # Upload existing Claude Code sessions from ~/.claude/projects/
gleaner backfill --source cursor     # Upload existing Cursor sessions from ~/.cursor/projects/
gleaner backfill --dry-run           # Preview what would be uploaded
gleaner collect                      # Collect local IDE sessions into the local vault
gleaner pull                         # Download sessions for local analysis (Parquet)
gleaner pull --transcripts           # Also download raw transcripts
gleaner serve                        # Start local dashboard (http://127.0.0.1:8765)
gleaner tray                         # Menu bar / tray icon: quick status + on/off switch
gleaner tray install                 # Start the tray at login (uninstall to remove)
```

Config is stored in `~/.config/gleaner.json` as one or more **named remotes** (Gleaner server instances) with one active; the active remote is what hooks and the CLI upload to. Switch instances with `gleaner remote use NAME`, or override per-invocation with `GLEANER_REMOTE=NAME` (or `GLEANER_URL`/`GLEANER_TOKEN`). Claude Code hooks are managed in `~/.claude/settings.json`; Cursor hooks in `~/.cursor/hooks.json`.

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

### Periodic sync agent

`gleaner setup` also registers a sync agent with the OS-native scheduler that
runs `gleaner-backfill --source all` every 5 minutes. It is the primary
capture path for Codex (which has no session hooks) and a safety net behind
the Claude Code and Cursor hooks. Re-uploads are idempotent server-side.

| OS | Scheduler | Registration |
|----|-----------|--------------|
| macOS | launchd | `~/Library/LaunchAgents/com.gleaner.sync.plist` |
| Linux | systemd user timer | `~/.config/systemd/user/gleaner-backfill.{service,timer}` |
| Windows | Task Scheduler | task `GleanerBackfill` (windowed, no console flash) |

The agent logs to `~/.gleaner/backfill.log`. `gleaner on` / `gleaner off`
toggle the hooks and the agent together; `gleaner status` reports what is
actually registered.

### Tray app

`gleaner tray` puts Gleaner in the macOS menu bar or the Linux/Windows
system tray: a green dot while capturing, gray when paused, with a menu for
toggling capture, running a backfill immediately, and opening the dashboard.
`gleaner tray install` registers it as a login item (launchd agent on macOS,
XDG autostart on Linux, `HKCU\...\Run` on Windows).

Both IDEs record full session transcripts locally as JSONL files. Gleaner collects these centrally so you can browse, search, and analyze them across your whole team.

## Dashboard

The web dashboard is available at your Gleaner URL. Sign in with Google to onboard, or use a `gl_` token.

Features:
- **Home**: personal stats, activity heatmap, recent sessions
- **Team**: aggregate stats, member activity, project breakdown
- **Sessions**: filterable list with full transcript viewer and search
- **Settings**: token management, setup instructions

## Deploy the server

The server can be deployed to Cloud Run manually via GitHub Actions (using `workflow_dispatch`).

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
  gleaner/                  # Installable client package
    sources/                # Finding & parsing local IDE sessions (self-contained)
      claude.py                 # Claude Code discovery + flat JSONL parser (shared with Cursor)
      cursor.py                 # Cursor session discovery (~/.cursor/projects/)
      codex.py                  # Codex rollout discovery + parser (~/.codex/sessions/)
      summary.py                # Shared session-metadata computation
      cc_format.py              # Claude Code JSONL format models
    remote/                 # HTTP client for the Gleaner server (self-contained)
      client.py                 # GleanerClient: upload, list, fetch, download
    scrub/                  # PII/secret scrubbing (self-contained)
      legacy.py                 # piicleaner + detect-secrets backend
      presidio.py               # Presidio backend (optional deps)
    vault/                  # Local session store (~/.gleaner/)
      schema.py                 # SessionMeta, NormalizedEntry
      store.py                  # Ingest, normalize, parquet index, collect
    setup/                  # Configuring a machine (self-contained)
      config.py                 # Config file + credential resolution
      installers.py             # Claude/Cursor hooks (absolute-path commands)
      sync_agent.py             # Periodic backfill: launchd / systemd timer / schtasks
      autostart.py              # Tray login item: launchd / XDG autostart / HKCU Run
    hooks/                  # Session-end hook handlers
      claude.py                 # gleaner-upload: Claude Code SessionEnd hook
      cursor.py                 # gleaner-cursor-upload: Cursor stop hook
    enrich.py               # Classification (source/task_type) + provenance
    pipeline.py             # Shared upload flow: enrich -> scrub -> remote
    backfill.py             # gleaner backfill: upload existing sessions (all sources)
    pull.py                 # gleaner pull: download sessions to Parquet
    tray.py                 # gleaner tray: menu bar / system tray status + on/off
    cli.py                  # gleaner command: setup, status, on/off, auth, backfill, collect, serve, pull, tray
  server/                   # FastAPI server (deployed to Cloud Run)
    server.py               # API routes and auth
    db_local.py             # Local-vault storage backend (gleaner serve)
    db_mock.py              # In-memory mock for dev/testing
    dashboard.html          # Single-file SPA dashboard
  backend/                  # Cloud storage backend
    db.py                   # Firestore + GCS operations
    ops/                    # Operational scripts (run manually)
  tests/
    test_architecture.py    # Package dependency contract
    test_e2e.py             # Upload-and-retrieve integration tests
    test_scrub.py           # PII scrubbing unit tests
  .github/workflows/
    deploy.yml              # CI: test + manual deploy to Cloud Run
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
