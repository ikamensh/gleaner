"""In-memory mock of db.py for local development. No GCP dependencies needed.

Provides the same interface as db.py with realistic sample data pre-loaded.
Activate by setting GLEANER_MOCK=1 before starting the server.

Counter updates and stats assembly are shared with the cloud backend via
backend.stats, so the mock stays behavior-identical to production.
"""

import gzip
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone

from backend import stats

# --- In-memory stores ---
_tokens: dict[str, dict] = {}  # hash -> token data
_sessions: dict[str, dict] = {}  # session_id -> metadata
_transcripts: dict[str, bytes] = {}  # session_id -> gzipped bytes
_counters: dict[str, dict] = {}  # "global" / "user:{name}" -> counter doc
_users: dict[str, dict] = {}  # email -> user data

# --- Seed data ---

_USERS = ["ikamen", "alice", "bob"]
_HOSTS = ["MacBook-Pro", "dev-server-1", "alice-mbp", "bob-desktop"]
_PROJECTS = [
    "-Users-ikamen-ai-workspace-ilya-gleaner",
    "-Users-ikamen-ai-workspace-ilya-kodo",
    "-Users-ikamen-covenance-overseer",
    "-Users-alice-projects-frontend",
    "-Users-bob-projects-api",
]
_TOOLS = ["Read", "Edit", "Bash", "Grep", "Glob", "Write", "Agent", "Skill"]
_TOPICS = [
    "add personal home page to dashboard",
    "fix authentication bug in login flow",
    "refactor database queries for performance",
    "update CI pipeline configuration",
    "implement webhook retry logic",
    "add unit tests for scrubbing module",
    "deploy new version to production",
    "review PR #42 changes",
    "debug flaky test in e2e suite",
    "add CORS headers to API endpoints",
    "implement rate limiting middleware",
    "update README with deployment instructions",
    "fix CSS layout issue on mobile",
    "add dark mode support to dashboard",
    "optimize Docker image size",
    "set up monitoring alerts",
    "migrate database schema",
    "implement session search feature",
    "add export to CSV functionality",
    "fix timezone handling in timestamps",
]


def _seed():
    """Generate realistic mock sessions spanning the last 90 days."""
    import random

    random.seed(42)  # Reproducible
    now = datetime.now(timezone.utc)

    # Create mock users
    _users["ikamen@example.com"] = {
        "username": "ikamen",
        "email": "ikamen@example.com",
        "display_name": "Ilya Kamen",
        "picture": "",
        "onboarded": True,
        "created_at": now - timedelta(days=60),
    }
    _users["alice@example.com"] = {
        "username": "alice",
        "email": "alice@example.com",
        "display_name": "Alice",
        "picture": "",
        "onboarded": True,
        "created_at": now - timedelta(days=45),
    }

    # Create a token for local dev
    raw_token = "gl_mock_local_dev_token_1234567890abcdef"
    _tokens[_token_hash(raw_token)] = {
        "name": "ikamen",
        "issued_to": "ikamen@example.com",
        "owner_email": "ikamen@example.com",
        "notes": "Local dev token",
        "prefix": raw_token[:8],
        "active": True,
        "created_at": now - timedelta(days=30),
        "last_used_at": now,
        "usage_count": 100,
    }

    # Generate sessions
    for i in range(80):
        days_ago = random.randint(0, 89)
        hour = random.choice([9, 10, 11, 14, 15, 16, 17, 20, 21, 22])
        minute = random.randint(0, 59)
        start = now - timedelta(days=days_ago, hours=random.randint(0, 3))
        start = start.replace(hour=hour, minute=minute, second=0, microsecond=0)
        duration_min = random.randint(2, 120)
        end = start + timedelta(minutes=duration_min)

        user = random.choices(_USERS, weights=[0.5, 0.3, 0.2])[0]
        host = random.choice(_HOSTS)
        project = random.choice(_PROJECTS)
        topic = random.choice(_TOPICS)

        tool_counts = {}
        for tool in random.sample(_TOOLS, k=random.randint(2, 6)):
            tool_counts[tool] = random.randint(1, 50)

        msg_count = random.randint(4, 60)
        user_msgs = msg_count // 2
        assistant_msgs = msg_count - user_msgs
        tool_use_count = sum(tool_counts.values())
        transcript_size = random.randint(5000, 200000)

        sid = f"mock-session-{i:04d}"
        _sessions[sid] = {
            "session_id": sid,
            "topic": topic,
            "project": project,
            "cwd": f"/Users/{user}/projects/{project.split('-')[-1]}",
            "message_count": msg_count,
            "user_message_count": user_msgs,
            "assistant_message_count": assistant_msgs,
            "tool_use_count": tool_use_count,
            "tool_counts": tool_counts,
            "first_timestamp": start.isoformat(),
            "last_timestamp": end.isoformat(),
            "provenance": {
                "user": user,
                "host": host,
                "platform": "Darwin arm64",
            },
            "transcript_size": transcript_size,
            "transcript_gz_size": transcript_size // 4,
            "gcs_path": f"sessions/{sid}.jsonl.gz",
            "uploaded_at": end + timedelta(seconds=2),
        }

        # Minimal mock transcript
        transcript_lines = [
            json.dumps({"type": "user", "timestamp": start.isoformat(),
                         "message": {"content": topic}}),
            json.dumps({"type": "assistant", "timestamp": end.isoformat(),
                         "message": {"content": "Done."}}),
        ]
        _transcripts[sid] = gzip.compress("\n".join(transcript_lines).encode())

    # Replay the sessions through the same counter updates an upload would
    # trigger, oldest first so last_active/last_session_id land on the newest.
    for sid, data in sorted(_sessions.items(), key=lambda kv: kv[1]["first_timestamp"]):
        _update_mock_counters(sid, data, data["provenance"])


# --- Token functions ---


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _store_new_token(fields: dict) -> str:
    """Mint a token, store its record, and return the raw token (shown once)."""
    token = f"gl_{secrets.token_urlsafe(32)}"
    _tokens[_token_hash(token)] = {
        "prefix": token[:8],
        "active": True,
        "created_at": datetime.now(timezone.utc),
        "last_used_at": None,
        "usage_count": 0,
        **fields,
    }
    return token


def create_token(name: str, issued_to: str = "", notes: str = "") -> str:
    return _store_new_token({"name": name, "issued_to": issued_to, "notes": notes})


def validate_token(token: str) -> dict | None:
    h = _token_hash(token)
    data = _tokens.get(h)
    if not data or not data.get("active"):
        return None
    data["last_used_at"] = datetime.now(timezone.utc)
    data["usage_count"] = data.get("usage_count", 0) + 1
    return data


def list_tokens() -> list[dict]:
    return [{"id": k, **v} for k, v in _tokens.items()]


def revoke_token(id_or_prefix: str) -> bool:
    if id_or_prefix in _tokens:
        _tokens[id_or_prefix]["active"] = False
        return True
    for h, data in _tokens.items():
        if data.get("prefix", "").startswith(id_or_prefix):
            data["active"] = False
            return True
    return False


# --- Users ---


def get_user_by_email(email: str) -> dict | None:
    return _users.get(email)


def create_or_update_user(
    email: str, username: str, display_name: str = "", picture: str = ""
) -> dict:
    existing = _users.get(email, {})
    user_data = {
        "username": username,
        "email": email,
        "display_name": display_name,
        "picture": picture,
        "onboarded": True,
        "created_at": existing.get("created_at", datetime.now(timezone.utc)),
    }
    _users[email] = user_data
    return user_data


def is_username_taken(username: str, exclude_email: str = "") -> bool:
    return any(
        u["username"] == username for e, u in _users.items() if e != exclude_email
    )


def list_user_tokens(owner_email: str) -> list[dict]:
    return [
        {"id": k, **v}
        for k, v in _tokens.items()
        if v.get("owner_email") == owner_email
    ]


def create_user_token(username: str, owner_email: str, token_name: str = "") -> str:
    return _store_new_token({
        "name": username,
        "issued_to": owner_email,
        "owner_email": owner_email,
        "notes": token_name or "Dashboard",
    })


def revoke_user_token(id_or_prefix: str, owner_email: str) -> bool:
    for h, data in _tokens.items():
        if data.get("owner_email") != owner_email:
            continue
        if h == id_or_prefix or data.get("prefix", "").startswith(id_or_prefix):
            data["active"] = False
            return True
    return False


# --- Backup ---


def export_firestore() -> dict:
    return {"status": "mock_export", "output_uri": "gs://mock/backups/mock", "operation": "mock-op"}


# --- Session functions ---


def _update_mock_counters(session_id: str, metadata: dict, provenance: dict):
    """Apply the shared counter deltas to the in-memory counter docs."""
    stats.apply_deltas(_counters, stats.counter_deltas(session_id, metadata, provenance))


def _recent_sessions(user: str | None = None, limit: int = 10) -> list[dict]:
    results = sorted(
        _sessions.values(),
        key=lambda s: s.get("uploaded_at", ""),
        reverse=True,
    )
    if user:
        results = [s for s in results if s.get("provenance", {}).get("user") == user]
    return [stats.session_summary(s) for s in results[:limit]]


def store_session(
    session_id: str,
    metadata: dict,
    provenance: dict,
    transcript_gz: bytes,
    transcript_size: int,
):
    is_new = session_id not in _sessions
    doc = {
        **metadata,
        "session_id": session_id,
        "provenance": provenance,
        "transcript_size": transcript_size,
        "transcript_gz_size": len(transcript_gz),
        "gcs_path": f"sessions/{session_id}.jsonl.gz",
        "uploaded_at": datetime.now(timezone.utc),
    }
    _sessions[session_id] = doc
    _transcripts[session_id] = transcript_gz
    if is_new:  # idempotent: re-upload overwrites but never double-counts
        _update_mock_counters(session_id, metadata, provenance)


def get_session(session_id: str) -> dict | None:
    data = _sessions.get(session_id)
    if data is None:
        return None
    return {**data, "session_id": session_id}


def get_session_transcript(session_id: str) -> bytes | None:
    return _transcripts.get(session_id)


def list_sessions(
    user: str | None = None,
    project: str | None = None,
    limit: int = 100,
    ids_only: bool = False,
    uploaded_after: datetime | None = None,
    keep_tool_counts: bool = False,
    session_date: str | None = None,
) -> list:
    results = sorted(
        _sessions.values(),
        key=lambda s: s.get("uploaded_at", ""),
        reverse=True,
    )
    if user:
        results = [s for s in results if s.get("provenance", {}).get("user") == user]
    if project:
        results = [s for s in results if s.get("project") == project]
    if uploaded_after:
        results = [s for s in results if s.get("uploaded_at", "") > uploaded_after]
    if session_date:
        results = [s for s in results if (s.get("first_timestamp") or "")[:10] == session_date]
    if limit:
        results = results[:limit]
    if ids_only:
        return [s.get("session_id", "") for s in results]
    out = []
    for s in results:
        row = {**s, "session_id": s.get("session_id", "")}
        if not keep_tool_counts:
            row.pop("tool_counts", None)
        out.append(row)
    return out


def get_user_stats(username: str) -> dict:
    """Personal stats from counter doc — mirrors db.get_user_stats."""
    u = _counters.get(f"user:{username}")
    if not u:
        return stats.build_user_stats(username, None, [], None)
    recent = _recent_sessions(user=username, limit=20)
    last_sid = u.get("last_session_id", "")
    last_session = get_session(last_sid) if last_sid else None
    return stats.build_user_stats(username, u, recent, last_session)


def get_stats() -> dict:
    """Aggregate stats from counter docs — mirrors db.get_stats."""
    user_counters = {
        key.split(":", 1)[1]: counter
        for key, counter in _counters.items()
        if key.startswith("user:")
    }
    return stats.build_global_stats(
        _counters.get("global"),
        _counters.get("global:users", {}),
        _counters.get("global:projects", {}),
        _counters.get("global:daily", {}),
        user_counters,
        _recent_sessions(limit=10),
    )


# Seed on import
_seed()
