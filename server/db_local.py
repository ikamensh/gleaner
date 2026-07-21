"""Local vault storage backend: reads sessions from ~/.gleaner/.

Implements the same interface as db.py / db_mock.py but reads from
the local parquet index and JSONL transcript files. No cloud dependencies.

Stats are produced by replaying the shared counter deltas (backend.stats)
over the vault rows, so local mode returns exactly the shapes the cloud
backend does.
"""

import getpass
import gzip
import json
from datetime import datetime
from pathlib import Path

import pyarrow.parquet as pq

from backend import stats

VAULT_DIR = Path.home() / ".gleaner"
LOCAL_USER = getpass.getuser()

_index_cache: list[dict] | None = None
_index_mtime: float = 0


def _load_index() -> list[dict]:
    """Load parquet index, re-reading only when the file changes."""
    global _index_cache, _index_mtime
    path = VAULT_DIR / "index.parquet"
    if not path.exists():
        _index_cache = []
        return []
    mtime = path.stat().st_mtime
    if _index_cache is not None and mtime == _index_mtime:
        return _index_cache
    _index_cache = pq.read_table(path).to_pylist()
    _index_mtime = mtime
    return _index_cache


def _tool_counts(row: dict) -> dict:
    try:
        return json.loads(row.get("tool_counts_json", "{}"))
    except (json.JSONDecodeError, TypeError):
        return {}


def _replay_counters(rows: list[dict]) -> dict:
    """Build counter docs by replaying the shared per-session deltas.

    Oldest first, so last_active/last_session_id land on the newest session.
    """
    counters: dict = {}
    for r in sorted(rows, key=lambda r: r.get("first_timestamp") or ""):
        metadata = {
            "project": r.get("project", ""),
            "message_count": r.get("message_count", 0),
            "tool_use_count": r.get("tool_use_count", 0),
            "tool_counts": _tool_counts(r),
            "first_timestamp": r.get("first_timestamp", ""),
            "last_timestamp": r.get("last_timestamp", ""),
        }
        deltas = stats.counter_deltas(
            r["session_id"], metadata, {"user": r.get("user", "")}
        )
        stats.apply_deltas(counters, deltas)
    return counters


def _row_to_session(row: dict, include_tool_counts: bool = False) -> dict:
    """Convert a parquet row to the API session shape."""
    result = {
        "session_id": row["session_id"],
        "topic": row.get("topic", ""),
        "project": row.get("project", ""),
        "cwd": row.get("cwd", ""),
        "message_count": row.get("message_count", 0),
        "user_message_count": row.get("user_message_count", 0),
        "assistant_message_count": row.get("assistant_message_count", 0),
        "tool_use_count": row.get("tool_use_count", 0),
        "first_timestamp": row.get("first_timestamp"),
        "last_timestamp": row.get("last_timestamp"),
        "provenance": {
            "user": row.get("user", ""),
            "host": row.get("host", ""),
            "platform": row.get("platform", ""),
        },
        "transcript_size": row.get("transcript_size", 0),
        "uploaded_at": row.get("ingested_at", ""),
    }
    if include_tool_counts:
        try:
            result["tool_counts"] = json.loads(row.get("tool_counts_json", "{}"))
        except (json.JSONDecodeError, TypeError):
            result["tool_counts"] = {}
    return result


# --- Tokens (stubs) ---


def validate_token(token: str) -> dict | None:
    return {"name": LOCAL_USER, "active": True}


def create_token(name: str, issued_to: str = "", notes: str = "") -> str:
    raise NotImplementedError("Tokens not available in local mode")


def list_tokens() -> list[dict]:
    return []


def revoke_token(id_or_prefix: str) -> bool:
    return False


# --- Users (stubs) ---


def get_user_by_email(email: str) -> dict | None:
    return None


def create_or_update_user(
    email: str, username: str, display_name: str = "", picture: str = ""
) -> dict:
    raise NotImplementedError("User management not available in local mode")


def is_username_taken(username: str, exclude_email: str = "") -> bool:
    return False


def list_user_tokens(owner_email: str) -> list[dict]:
    return []


def create_user_token(username: str, owner_email: str, token_name: str = "") -> str:
    raise NotImplementedError("Tokens not available in local mode")


def revoke_user_token(id_or_prefix: str, owner_email: str) -> bool:
    return False


# --- Backup (stub) ---


def export_firestore() -> dict:
    return {"status": "not_available"}


# --- Sessions ---


def store_session(
    session_id: str,
    metadata: dict,
    provenance: dict,
    transcript_gz: bytes,
    transcript_size: int,
):
    raise NotImplementedError("Upload not supported in local mode. Use 'gleaner collect'.")


def get_session(session_id: str) -> dict | None:
    for row in _load_index():
        if row["session_id"] == session_id:
            return _row_to_session(row, include_tool_counts=True)
    return None


def get_session_transcript(session_id: str) -> bytes | None:
    raw_path = VAULT_DIR / "sessions" / session_id / "raw.jsonl"
    if not raw_path.exists():
        return None
    return gzip.compress(raw_path.read_bytes())


def list_sessions(
    user: str | None = None,
    project: str | None = None,
    limit: int = 100,
    ids_only: bool = False,
    uploaded_after: datetime | None = None,
    keep_tool_counts: bool = False,
    session_date: str | None = None,
) -> list:
    rows = _load_index()

    if user:
        rows = [r for r in rows if r.get("user") == user]
    if project:
        rows = [r for r in rows if r.get("project") == project]
    if uploaded_after:
        after_str = uploaded_after.isoformat()
        rows = [r for r in rows if (r.get("ingested_at") or "") > after_str]
    if session_date:
        rows = [r for r in rows if (r.get("first_timestamp") or "")[:10] == session_date]

    rows.sort(key=lambda r: r.get("first_timestamp") or "", reverse=True)

    if limit:
        rows = rows[:limit]

    if ids_only:
        return [r["session_id"] for r in rows]

    return [_row_to_session(r, include_tool_counts=keep_tool_counts) for r in rows]


def get_user_stats(username: str) -> dict:
    rows = [r for r in _load_index() if r.get("user") == username]
    counter = _replay_counters(rows).get(f"user:{username}")
    if not counter:
        return stats.build_user_stats(username, None, [], None)

    sorted_rows = sorted(rows, key=lambda r: r.get("first_timestamp") or "", reverse=True)
    recent = [_row_to_session(r) for r in sorted_rows[:20]]
    last_session = get_session(counter.get("last_session_id", ""))
    return stats.build_user_stats(username, counter, recent, last_session)


def get_stats() -> dict:
    rows = _load_index()
    counters = _replay_counters(rows)
    user_counters = {
        key.split(":", 1)[1]: counter
        for key, counter in counters.items()
        if key.startswith("user:")
    }
    sorted_rows = sorted(rows, key=lambda r: r.get("first_timestamp") or "", reverse=True)
    recent = [_row_to_session(r) for r in sorted_rows[:10]]
    return stats.build_global_stats(
        counters.get("global"),
        counters.get("global:users", {}),
        counters.get("global:projects", {}),
        counters.get("global:daily", {}),
        user_counters,
        recent,
    )
