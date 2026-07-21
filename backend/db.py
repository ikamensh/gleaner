"""Gleaner database operations: Firestore for metadata, GCS for raw transcripts."""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timezone

import google.auth
import google.auth.transport.requests
from google.api_core.exceptions import NotFound
from google.cloud import firestore, storage

from backend import stats

GCP_PROJECT = os.environ.get("GLEANER_GCP_PROJECT", "covenance-469421")
GCS_BUCKET = os.environ.get("GLEANER_GCS_BUCKET", "gleaner-sessions")
CACHE_TTL_SECONDS = int(os.environ.get("GLEANER_CACHE_TTL", "300"))  # 5 minutes

_db_client = None
_gcs_client = None
_gcs_bucket_obj = None
_cache: dict[str, tuple[float, dict]] = {}  # key -> (expiry_timestamp, data)


def _cache_get(key: str) -> dict | None:
    entry = _cache.get(key)
    if entry and entry[0] > datetime.now(timezone.utc).timestamp():
        return entry[1]
    return None


def _cache_set(key: str, data: dict) -> dict:
    _cache[key] = (datetime.now(timezone.utc).timestamp() + CACHE_TTL_SECONDS, data)
    return data


def _db():
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(project=GCP_PROJECT)
    return _db_client


def _bucket():
    global _gcs_client, _gcs_bucket_obj
    if _gcs_bucket_obj is None:
        _gcs_client = storage.Client(project=GCP_PROJECT)
        _gcs_bucket_obj = _gcs_client.bucket(GCS_BUCKET)
    return _gcs_bucket_obj


# --- Tokens ---


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _store_new_token(fields: dict) -> str:
    """Mint a token, store its record, and return the raw token (shown once)."""
    token = f"gl_{secrets.token_urlsafe(32)}"
    _db().collection("tokens").document(_token_hash(token)).set(
        {
            "prefix": token[:8],
            "active": True,
            "created_at": firestore.SERVER_TIMESTAMP,
            "last_used_at": None,
            "usage_count": 0,
            **fields,
        }
    )
    return token


def create_token(name: str, issued_to: str = "", notes: str = "") -> str:
    """Create a new API token. Returns the raw token (shown only once)."""
    return _store_new_token({"name": name, "issued_to": issued_to, "notes": notes})


def validate_token(token: str) -> dict | None:
    """Validate a bearer token. Returns metadata or None."""
    doc_ref = _db().collection("tokens").document(_token_hash(token))
    doc = doc_ref.get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    if not data.get("active"):
        return None
    try:
        doc_ref.update(
            {
                "last_used_at": firestore.SERVER_TIMESTAMP,
                "usage_count": firestore.Increment(1),
            }
        )
    except Exception:
        pass
    return data


def list_tokens() -> list[dict]:
    """List all tokens (without hashes)."""
    tokens = []
    for doc in _db().collection("tokens").stream():
        data = doc.to_dict() or {}
        data["id"] = doc.id
        tokens.append(data)
    return tokens


def revoke_token(id_or_prefix: str) -> bool:
    """Revoke a token by hash ID or prefix."""
    doc_ref = _db().collection("tokens").document(id_or_prefix)
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.update({"active": False})
        return True
    for doc in _db().collection("tokens").stream():
        data = doc.to_dict() or {}
        if data.get("prefix", "").startswith(id_or_prefix):
            doc.reference.update({"active": False})
            return True
    return False


# --- Users ---


def get_user_by_email(email: str) -> dict | None:
    """Get user document by email."""
    doc = _db().collection("users").document(email).get()
    if not doc.exists:
        return None
    return doc.to_dict()


def create_or_update_user(
    email: str, username: str, display_name: str = "", picture: str = ""
) -> dict:
    """Create or update a user. Marks them as onboarded."""
    user_data = {
        "username": username,
        "email": email,
        "display_name": display_name,
        "picture": picture,
        "onboarded": True,
    }
    doc_ref = _db().collection("users").document(email)
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.update(user_data)
    else:
        user_data["created_at"] = firestore.SERVER_TIMESTAMP
        doc_ref.set(user_data)
    return user_data


def is_username_taken(username: str, exclude_email: str = "") -> bool:
    """Check if a username is already in use."""
    for doc in _db().collection("users").stream():
        data = doc.to_dict() or {}
        if data.get("username") == username and doc.id != exclude_email:
            return True
    return False


def list_user_tokens(owner_email: str) -> list[dict]:
    """List tokens owned by a specific user."""
    tokens = []
    for doc in (
        _db().collection("tokens").where("owner_email", "==", owner_email).stream()
    ):
        data = doc.to_dict() or {}
        data["id"] = doc.id
        tokens.append(data)
    return tokens


def create_user_token(username: str, owner_email: str, token_name: str = "") -> str:
    """Create a token for a user. Returns the raw token (shown once)."""
    return _store_new_token(
        {
            "name": username,
            "issued_to": owner_email,
            "owner_email": owner_email,
            "notes": token_name or "Dashboard",
        }
    )


def revoke_user_token(id_or_prefix: str, owner_email: str) -> bool:
    """Revoke a token, verifying ownership."""
    doc_ref = _db().collection("tokens").document(id_or_prefix)
    doc = doc_ref.get()
    if doc.exists and (doc.to_dict() or {}).get("owner_email") == owner_email:
        doc_ref.update({"active": False})
        return True
    for doc in (
        _db().collection("tokens").where("owner_email", "==", owner_email).stream()
    ):
        data = doc.to_dict() or {}
        if data.get("prefix", "").startswith(id_or_prefix):
            doc.reference.update({"active": False})
            return True
    return False


# --- Backup ---


def export_firestore() -> dict:
    """Trigger a Firestore export to GCS. Returns operation info."""
    import urllib.request
    import json

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_uri = f"gs://{GCS_BUCKET}/backups/{stamp}"

    credentials, _ = google.auth.default()
    credentials.refresh(google.auth.transport.requests.Request())

    url = f"https://firestore.googleapis.com/v1/projects/{GCP_PROJECT}/databases/(default):exportDocuments"
    body = json.dumps({
        "outputUriPrefix": output_uri,
        "collectionIds": ["sessions", "tokens"],
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {credentials.token}")
    req.add_header("Content-Type", "application/json")
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    return {"status": "export_started", "output_uri": output_uri, "operation": result.get("name", "")}


# --- Counters (pre-computed aggregates) ---


def _counter_update(doc_ref, updates: dict):
    """Apply atomic field updates to a counter doc, creating it if needed."""
    try:
        doc_ref.update(updates)
    except NotFound:
        doc_ref.set({})
        doc_ref.update(updates)


# Map neutral counter-delta ops (backend.stats) to Firestore field transforms.
_FIRESTORE_OPS = {
    "inc": firestore.Increment,
    "set": lambda v: v,
    "union": firestore.ArrayUnion,
}


def _update_counters(session_id: str, metadata: dict, provenance: dict):
    """Incrementally update counter docs after a session upload."""
    counters = _db().collection("counters")
    for doc_name, fields in stats.counter_deltas(session_id, metadata, provenance).items():
        updates = {path: _FIRESTORE_OPS[op](value) for path, (op, value) in fields.items()}
        _counter_update(counters.document(doc_name), updates)


def _recent_sessions(user: str | None = None, limit: int = 10) -> list[dict]:
    """Fetch recent sessions with a simple limit query (no full scan)."""
    query = _db().collection("sessions")
    if user:
        query = query.where("provenance.user", "==", user)
    query = query.order_by("uploaded_at", direction=firestore.Query.DESCENDING).limit(limit)
    return [
        stats.session_summary({**(doc.to_dict() or {}), "session_id": doc.id})
        for doc in query.stream()
    ]


# --- Sessions ---


def store_session(
    session_id: str,
    metadata: dict,
    provenance: dict,
    transcript_gz: bytes,
    transcript_size: int,
):
    """Store session metadata in Firestore and raw transcript in GCS.

    Upsert semantics: re-uploading an existing session_id overwrites the
    transcript and metadata (last-write-wins) but does not re-increment
    any counter — each session_id is counted exactly once.
    """
    doc_ref = _db().collection("sessions").document(session_id)
    is_new = not doc_ref.get().exists

    blob = _bucket().blob(f"sessions/{session_id}.jsonl.gz")
    blob.upload_from_string(transcript_gz, content_type="application/gzip")
    doc_data = {
        **metadata,
        "provenance": provenance,
        "transcript_size": transcript_size,
        "transcript_gz_size": len(transcript_gz),
        "gcs_path": f"sessions/{session_id}.jsonl.gz",
        "uploaded_at": firestore.SERVER_TIMESTAMP,
    }
    doc_ref.set(doc_data)

    if is_new:
        try:
            _update_counters(session_id, metadata, provenance)
        except Exception as e:
            logging.warning("Counter update failed for session %s: %s", session_id, e)

    # Invalidate caches so next read reflects the new/updated session
    _cache.pop("global_stats", None)
    if provenance.get("user"):
        _cache.pop(f"user_stats:{provenance['user']}", None)


def get_session(session_id: str) -> dict | None:
    """Get session metadata from Firestore."""
    doc = _db().collection("sessions").document(session_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["session_id"] = doc.id
    return data


def get_session_transcript(session_id: str) -> bytes | None:
    """Download raw gzipped transcript from GCS."""
    blob = _bucket().blob(f"sessions/{session_id}.jsonl.gz")
    if not blob.exists():
        return None
    return blob.download_as_bytes()


def delete_session(session_id: str) -> bool:
    """Delete a session from Firestore and GCS. Returns True if it existed."""
    doc_ref = _db().collection("sessions").document(session_id)
    doc = doc_ref.get()
    if not doc.exists:
        return False
    doc_ref.delete()
    blob = _bucket().blob(f"sessions/{session_id}.jsonl.gz")
    if blob.exists():
        blob.delete()
    return True


def list_sessions(
    user: str | None = None,
    project: str | None = None,
    limit: int = 100,
    ids_only: bool = False,
    uploaded_after: datetime | None = None,
    keep_tool_counts: bool = False,
    session_date: str | None = None,
) -> list:
    """List sessions, optionally filtered."""
    query = _db().collection("sessions")

    if user:
        query = query.where("provenance.user", "==", user)
    if project:
        query = query.where("project", "==", project)
    if uploaded_after:
        query = query.where("uploaded_at", ">", uploaded_after)

    query = query.order_by("uploaded_at", direction=firestore.Query.DESCENDING)
    if limit:
        query = query.limit(limit)

    if ids_only:
        return [doc.id for doc in query.stream()]

    results = []
    for doc in query.stream():
        data = doc.to_dict() or {}
        data["session_id"] = doc.id
        if not keep_tool_counts:
            data.pop("tool_counts", None)
        results.append(data)

    if session_date:
        results = [s for s in results if (s.get("first_timestamp") or "")[:10] == session_date]

    return results


def get_user_stats(username: str) -> dict:
    """Personal stats for a single user: last session, weekly stats, heatmap, rhythm."""
    cached = _cache_get(f"user_stats:{username}")
    if cached:
        return cached
    return _cache_set(f"user_stats:{username}", _compute_user_stats(username))


def _compute_user_stats(username: str) -> dict:
    """Read from user counter doc + limited queries. No full scan."""
    doc = _db().collection("counters").document(f"user:{username}").get()
    if not doc.exists:
        return stats.build_user_stats(username, None, [], None)

    u = doc.to_dict()
    recent = _recent_sessions(user=username, limit=20)
    last_session_id = u.get("last_session_id", "")
    last_session = get_session(last_session_id) if last_session_id else None
    return stats.build_user_stats(username, u, recent, last_session)


def get_stats() -> dict:
    """Aggregate stats across all sessions."""
    cached = _cache_get("global_stats")
    if cached:
        return cached
    return _cache_set("global_stats", _compute_stats())


def _compute_stats() -> dict:
    """Read from global counter + user counters + limited query. No full scan."""
    counters = _db().collection("counters")

    # Read 4 split counter docs
    refs = [counters.document(n) for n in ("global", "global:daily", "global:users", "global:projects")]
    docs = {doc.id: doc.to_dict() for doc in _db().get_all(refs) if doc.exists}
    g = docs.get("global")
    if not g:
        return stats.build_global_stats(None, {}, {}, {}, {}, [])

    users_map = docs.get("global:users", {})

    # Batch-read user counters for enrichment (top_project, active_days_this_week)
    user_refs = [counters.document(f"user:{u}") for u in users_map]
    user_counters = {}
    if user_refs:
        for udoc in _db().get_all(user_refs):
            if udoc.exists:
                # doc id is "user:username"
                uname = udoc.id.split(":", 1)[1] if ":" in udoc.id else udoc.id
                user_counters[uname] = udoc.to_dict()

    return stats.build_global_stats(
        g,
        users_map,
        docs.get("global:projects", {}),
        docs.get("global:daily", {}),
        user_counters,
        _recent_sessions(limit=10),
    )
