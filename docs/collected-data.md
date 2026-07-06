# What Data Gleaner Collects

Gleaner currently supports two IDE sources: **Claude Code** and **Cursor**. Both are fully supported, same-tier official sources. Codex capture is in-scope for the overall project but is currently pending (landing separately in another branch); it is not implemented or supported in this repository yet.

## Transcript content

Each session produces a JSONL file. Gleaner uploads the **entire file** after scrubbing PII/secrets.

### Claude Code

| Content type | Present? | Example |
|---|---|---|
| User messages | Full text | Every prompt typed by the user |
| Assistant replies | Full text | All of Claude's responses |
| Tool inputs | Full | Tool name + parameters (file path, bash command, search pattern, …) |
| Tool results | Full | File contents from Read, command stdout/stderr from Bash, Grep matches, etc. |
| Timestamps | Yes | ISO 8601 per message |
| Thinking traces | No | Claude Code does not write extended-thinking tokens to JSONL |
| Images / binary | No | Only text representations appear |

### Cursor

| Content type | Present? | Notes |
|---|---|---|
| User messages | Full text | Every prompt typed by the user |
| Assistant replies | Full text | All of the agent's responses |
| Tool inputs | Full | Tool name + parameters |
| Tool results | Full | Command output, file contents, etc. |
| Timestamps | No | Cursor does not include per-message timestamps |
| Images / binary | No | Only text representations appear |

**Source code exposure**: when the IDE reads a file, the full file content appears as a tool result in the transcript and is uploaded.

## Scrubbing (before upload)

Runs client-side (`scrub_text()`), so raw data never leaves the machine.

**Engine**: Presidio (default) or legacy regex fallback.

Detected and replaced with `[secret-redacted]` / `[pii-redacted]`:

- API keys, tokens, passwords (pattern: `api_key`, `secret`, `token`, `password`, …)
- PEM private keys
- Bearer tokens (20+ char)
- Connection strings (postgres/mysql/mongodb/redis/amqp URIs)
- AWS access keys (`AKIA…`)
- GitHub tokens (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`)
- Credit cards, SSNs, IBANs, passports, phone numbers, emails, IP addresses

## Extracted metadata

Stored in Firestore as a document per session (`sessions/{session_id}`):

```
session_id          string     UUID
ide                 string     "claude_code" or "cursor"
topic               string     First user message, truncated to 200 chars
project             string     Project directory name (Claude Code) or Cursor project name
cwd                 string     Working directory at session start (empty for Cursor)
message_count       int        Total JSONL lines
user_message_count  int        Lines with role/type=user
assistant_message_count int    Lines with role/type=assistant
tool_use_count      int        Total tool invocations
tool_counts         map        Per-tool breakdown, e.g. {"Bash": 3, "Read": 5}
first_timestamp     timestamp  Earliest message timestamp (null for Cursor sessions)
last_timestamp      timestamp  Latest message timestamp (null for Cursor sessions)
transcript_size     int        Uncompressed transcript bytes
transcript_gz_size  int        Gzipped transcript bytes
redactions          int        Number of PII/secret replacements made
source              string     "human", "kodo", or "test" (auto-classified by tags.py)
task_type           string     "development", "swe_bench", "merge_conflict", "verification",
                               "commit", "analysis", "kodo_harness", "kodo_other", or "test"
provenance.user     string     OS username (overridden by token identity)
provenance.host     string     Hostname
provenance.platform string     e.g. "Darwin arm64"
uploaded_at         timestamp  Server-side upload time
```

### Source classification (`source` and `task_type`)

`tags.py` classifies every session at upload time:

- **`source: "kodo"`** — session originated from the kodo coding agent. Detected by: project name contains "kodo", known temporary paths, specific topic patterns ("Fix the following", "Resolve the merge conflicts", etc.), host is "openclaw-1" with empty cwd, project contains "instance_", or Cursor project contains "kodo-benchmark".
- **`source: "test"`** — project name is "gleaner-e2e" (integration test sessions).
- **`source: "human"`** — everything else (a developer's interactive session).

`task_type` further subdivides kodo sessions (`swe_bench`, `merge_conflict`, `verification`, `commit`, `analysis`, `kodo_harness`, `kodo_other`) and labels human sessions as `development`.

## Storage

Firestore is a NoSQL document database — each session is a nested dict
keyed by `session_id`, no schema enforced, no joins.

- **Metadata** → Firestore document (`sessions/{session_id}`)
- **Full transcript** → GCS blob (`sessions/{session_id}.jsonl.gz`)
- **Aggregates** → Firestore `counters` collection (pre-computed stats)

See `DATA_STORAGE.md` in project root for the full storage architecture diagram.

## Filtering

Sessions are skipped (not uploaded) when:
- No user messages
- No assistant messages
- All assistant messages are rate-limit errors ("hit your limit")
