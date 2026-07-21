"""Local vault for coding sessions.

Copies sessions from every local source into a unified format. Each
session keeps the raw original alongside a normalized transcript.

Layout:
    ~/.gleaner/
    ├── index.parquet
    └── sessions/
        └── {session_id}/
            ├── raw.jsonl           # exact copy from IDE
            └── transcript.jsonl    # normalized format

Normalized JSONL (one object per line):
    {"role": "user|assistant", "ts": "ISO8601|null", "content": [{type, ...}, ...]}
"""

import datetime
import json
import shutil
import sys
from pathlib import Path

from gleaner.enrich import collect_provenance, tag_session
from gleaner.sources import SOURCES, codex, parser_for_ide
from gleaner.vault.schema import NormalizedEntry, SessionMeta

VAULT_DIR = Path.home() / ".gleaner"


def _role(raw: str | None) -> str:
    """Coerce an arbitrary role/type to the NormalizedEntry vocabulary."""
    return raw if raw in ("user", "assistant") else "unknown"


def _normalize_codex_entry(entry: dict) -> dict:
    """Normalize one Codex rollout line (payload-wrapped) to vault format."""
    ts = entry.get("timestamp")
    payload = entry.get("payload", {})
    ptype = payload.get("type")
    if entry.get("type") == "response_item" and ptype == "message":
        content = codex.content_to_canonical(payload.get("content", []))
        return NormalizedEntry(role=_role(payload.get("role")), ts=ts, content=content).model_dump()
    if entry.get("type") == "response_item" and (name := codex.tool_name(payload)):
        return NormalizedEntry(
            role="unknown", ts=ts, content=[{"type": "tool_use", "name": name}]
        ).model_dump()
    # reasoning / tool output / event_msg / session_meta -> opaque marker
    return NormalizedEntry(role="unknown", ts=ts, content=[]).model_dump()


def normalize_entry(entry: dict) -> dict:
    """Normalize a JSONL entry from any IDE format to vault format.

    Claude Code: {"type": "user", "timestamp": "...", "message": {"content": ...}}
    Cursor:      {"role": "user", "message": {"content": [...]}}
    Codex:       {"type": "response_item", "payload": {"role": ..., "content": [...]}}
    Output:      {"role": "user|assistant|unknown", "ts": "...|null", "content": [...]}
    """
    if "payload" in entry and entry.get("type") in codex.CODEX_LINE_TYPES:
        return _normalize_codex_entry(entry)
    role = _role(entry.get("type") or entry.get("role"))
    ts = entry.get("timestamp")
    content = entry.get("message", {}).get("content", [])
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    return NormalizedEntry(role=role, ts=ts, content=content).model_dump()


def ingest_session(
    session_id: str,
    raw_path: Path,
    ide: str,
    project: str,
    cwd: str = "",
    vault_dir: Path = VAULT_DIR,
) -> dict | None:
    """Ingest a session into the vault.

    Copies the raw file and creates a normalized transcript.
    Returns metadata dict for the index, or None if already exists or worthless.
    """
    session_dir = vault_dir / "sessions" / session_id
    if session_dir.exists():
        return None

    meta = parser_for_ide(ide)(raw_path)
    if meta.pop("worthless", False):
        return None

    session_dir.mkdir(parents=True)
    shutil.copy2(raw_path, session_dir / "raw.jsonl")

    with open(raw_path) as f_in, open(session_dir / "transcript.jsonl", "w") as f_out:
        for line in f_in:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
                f_out.write(json.dumps(normalize_entry(entry)) + "\n")
            except json.JSONDecodeError:
                continue

    provenance = collect_provenance()
    tags = tag_session(project, meta.get("topic", ""), provenance["host"], cwd, ide=ide)

    return SessionMeta(
        session_id=session_id,
        ide=ide,
        project=project,
        topic=meta.get("topic", ""),
        cwd=cwd,
        source=tags["source"],
        task_type=tags["task_type"],
        user=provenance["user"],
        host=provenance["host"],
        platform=provenance["platform"],
        message_count=meta["message_count"],
        user_message_count=meta["user_message_count"],
        assistant_message_count=meta["assistant_message_count"],
        tool_use_count=meta["tool_use_count"],
        tool_counts_json=json.dumps(meta["tool_counts"]),
        first_timestamp=meta["first_timestamp"],
        last_timestamp=meta["last_timestamp"],
        transcript_size=raw_path.stat().st_size,
        ingested_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        origin="local",
    ).model_dump()


def update_index(new_rows: list[dict], vault_dir: Path = VAULT_DIR) -> int:
    """Merge new session rows into the parquet index. Returns count added."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not new_rows:
        return 0

    index_path = vault_dir / "index.parquet"

    if index_path.exists():
        existing = pq.read_table(index_path)
        existing_ids = set(existing.column("session_id").to_pylist())
        truly_new = [r for r in new_rows if r["session_id"] not in existing_ids]
        if not truly_new:
            return 0
        new_table = pa.Table.from_pylist(truly_new)
        merged = pa.concat_tables([existing, new_table], promote_options="default")
        pq.write_table(merged, index_path, compression="zstd")
        return len(truly_new)
    else:
        new_table = pa.Table.from_pylist(new_rows)
        pq.write_table(new_table, index_path, compression="zstd")
        return len(new_rows)


def collect(vault_dir: Path = VAULT_DIR) -> int:
    """Scan every local source and ingest new sessions into the vault.

    Returns number of sessions added.
    """
    vault_dir.mkdir(parents=True, exist_ok=True)
    sessions_dir = vault_dir / "sessions"
    existing = (
        {d.name for d in sessions_dir.iterdir() if d.is_dir()}
        if sessions_dir.exists()
        else set()
    )
    new_rows = []

    for source in SOURCES.values():
        for session_id, project_name, path in source.find(None):
            if session_id in existing:
                continue
            try:
                row = ingest_session(
                    session_id, path, source.ide, project_name, vault_dir=vault_dir
                )
                if row:
                    new_rows.append(row)
            except Exception as e:
                print(f"  {session_id[:12]}... skipped: {e}", file=sys.stderr)

    added = update_index(new_rows, vault_dir=vault_dir)
    return added
