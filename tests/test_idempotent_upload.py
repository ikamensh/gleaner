"""Regression tests for idempotent session uploads.

Contract: POST /api/session with a duplicate session_id must
  - Replace the stored transcript and metadata (last-write-wins)
  - NOT increment any counter or stat (unique session_id counted once)
  - NOT create a second entry in the sessions list

All tests run against the in-memory mock server (GLEANER_MOCK=1, set in
conftest.py) and make no network calls.
"""

import base64
import gzip
import json

import pytest
from fastapi.testclient import TestClient

from server.server import app

client = TestClient(app, root_path="/gleaner")
AUTH = {"Authorization": "Bearer mock"}


def _build_payload(
    session_id: str,
    topic: str,
    message_count: int,
    tool_counts: dict | None = None,
    transcript_lines: list[str] | None = None,
) -> dict:
    """Build a minimal valid POST /api/session payload."""
    if tool_counts is None:
        tool_counts = {}
    tool_use_count = sum(tool_counts.values())
    user_msgs = max(1, message_count // 2)
    asst_msgs = message_count - user_msgs

    if transcript_lines is None:
        transcript_lines = [
            json.dumps({"type": "user", "timestamp": "2026-03-20T10:00:00Z",
                        "message": {"content": topic}}),
            json.dumps({"type": "assistant", "timestamp": "2026-03-20T10:05:00Z",
                        "message": {"content": "Done."}}),
        ]
    raw = "\n".join(transcript_lines).encode()
    gz = gzip.compress(raw)

    return {
        "session_id": session_id,
        "metadata": {
            "session_id": session_id,
            "message_count": message_count,
            "user_message_count": user_msgs,
            "assistant_message_count": asst_msgs,
            "tool_use_count": tool_use_count,
            "tool_counts": tool_counts,
            "first_timestamp": "2026-03-20T10:00:00Z",
            "last_timestamp": "2026-03-20T10:05:00Z",
            "topic": topic,
            "project": "idempotent-test-project",
            "cwd": "/tmp/idempotent",
        },
        "provenance": {"user": "ikamen", "host": "ci", "platform": "Linux x86_64"},
        "transcript_size": len(raw),
        "transcript_gz_b64": base64.b64encode(gz).decode(),
    }


def _post(payload: dict) -> dict:
    r = client.post("/api/session", json=payload, headers=AUTH)
    assert r.status_code == 200, r.text
    return r.json()


class TestIdempotentUpload:
    """POST /api/session with a duplicate session_id: last-write-wins, no counter inflation.

    Each test uses a unique session_id so tests are independent of each other
    and of the seeded mock data.
    """

    def test_first_upload_returns_ok(self):
        """Normal first upload returns status ok and echoes the session_id."""
        sid = "idem-first-upload"
        result = _post(_build_payload(sid, "initial topic", 4))
        assert result["status"] == "ok"
        assert result["session_id"] == sid

    def test_duplicate_upload_returns_ok(self):
        """Duplicate upload is accepted (not rejected as conflict)."""
        sid = "idem-dup-returns-ok"
        _post(_build_payload(sid, "v1", 3))
        result = _post(_build_payload(sid, "v2", 3))
        assert result["status"] == "ok"

    def test_duplicate_replaces_metadata(self):
        """Second upload overwrites topic, message_count, and tool_counts."""
        sid = "idem-replace-meta"

        _post(_build_payload(sid, "original topic", 3, {"Read": 1}))
        _post(_build_payload(sid, "updated topic", 9, {"Read": 3, "Edit": 2}))

        r = client.get(f"/api/session/{sid}", headers=AUTH)
        assert r.status_code == 200
        data = r.json()
        assert data["topic"] == "updated topic", "metadata was not replaced"
        assert data["message_count"] == 9
        assert data["tool_counts"] == {"Read": 3, "Edit": 2}

    def test_duplicate_replaces_transcript(self):
        """Second upload overwrites the stored raw transcript bytes."""
        sid = "idem-replace-transcript"

        lines_v1 = [json.dumps({"type": "user", "message": {"content": "version one"}})]
        lines_v2 = [json.dumps({"type": "user", "message": {"content": "version two"}})]

        _post(_build_payload(sid, "v1", 2, transcript_lines=lines_v1))
        _post(_build_payload(sid, "v2", 2, transcript_lines=lines_v2))

        r = client.get(f"/api/session/{sid}/raw", headers=AUTH)
        assert r.status_code == 200
        raw_text = gzip.decompress(r.content).decode()

        assert "version two" in raw_text, "transcript was not replaced"
        assert "version one" not in raw_text, "old transcript content still present"

    def test_duplicate_does_not_inflate_global_session_count(self):
        """Re-uploading the same session_id does not increment total_sessions."""
        sid = "idem-global-count"
        payload = _build_payload(sid, "counter test", 5)

        count_before = client.get("/api/stats", headers=AUTH).json()["total_sessions"]

        _post(payload)
        count_after_first = client.get("/api/stats", headers=AUTH).json()["total_sessions"]
        assert count_after_first == count_before + 1, "first upload should increment by 1"

        _post(payload)
        count_after_dup = client.get("/api/stats", headers=AUTH).json()["total_sessions"]
        assert count_after_dup == count_after_first, (
            f"duplicate upload inflated total_sessions: {count_after_first} → {count_after_dup}"
        )

    def test_duplicate_does_not_inflate_global_message_count(self):
        """Re-uploading the same session_id does not increment total_messages."""
        sid = "idem-global-messages"
        payload = _build_payload(sid, "message counter test", 6)

        msgs_before = client.get("/api/stats", headers=AUTH).json()["total_messages"]

        _post(payload)
        msgs_after_first = client.get("/api/stats", headers=AUTH).json()["total_messages"]
        assert msgs_after_first == msgs_before + 6

        _post(payload)
        msgs_after_dup = client.get("/api/stats", headers=AUTH).json()["total_messages"]
        assert msgs_after_dup == msgs_after_first, (
            f"duplicate upload inflated total_messages: {msgs_after_first} → {msgs_after_dup}"
        )

    def test_duplicate_does_not_inflate_user_session_count(self):
        """Re-uploading does not inflate the per-user session counter."""
        sid = "idem-user-sessions"
        payload = _build_payload(sid, "user counter test", 4)

        user_before = client.get("/api/user/ikamen/stats", headers=AUTH).json()["total_sessions"]

        _post(payload)
        user_after_first = client.get("/api/user/ikamen/stats", headers=AUTH).json()["total_sessions"]
        assert user_after_first == user_before + 1

        _post(payload)
        user_after_dup = client.get("/api/user/ikamen/stats", headers=AUTH).json()["total_sessions"]
        assert user_after_dup == user_after_first, (
            f"duplicate upload inflated user total_sessions: {user_after_first} → {user_after_dup}"
        )

    def test_session_appears_exactly_once_in_list(self):
        """Uploading the same session_id twice yields a single entry in the sessions list."""
        sid = "idem-list-dedup"
        payload = _build_payload(sid, "list dedup test", 3)

        _post(payload)
        _post(payload)

        r = client.get("/api/sessions?limit=0", headers=AUTH)
        assert r.status_code == 200
        ids = [s["session_id"] for s in r.json()["sessions"]]
        assert ids.count(sid) == 1, (
            f"session_id appears {ids.count(sid)} times in list, expected 1"
        )

    def test_triple_upload_no_counter_inflation(self):
        """Three uploads of the same session_id count as exactly one session."""
        sid = "idem-triple"
        payload = _build_payload(sid, "triple upload test", 5)

        count_before = client.get("/api/stats", headers=AUTH).json()["total_sessions"]

        _post(payload)
        _post(payload)
        _post(payload)

        count_after = client.get("/api/stats", headers=AUTH).json()["total_sessions"]
        assert count_after == count_before + 1, (
            f"three uploads should count as one: before={count_before}, after={count_after}"
        )

    def test_retrieve_metadata_after_duplicate_upload(self):
        """GET /api/session/{id} returns the most-recent metadata after re-upload."""
        sid = "idem-retrieve-meta"

        _post(_build_payload(sid, "first version", 2))
        _post(_build_payload(sid, "second version", 8, {"Bash": 4}))

        r = client.get(f"/api/session/{sid}", headers=AUTH)
        assert r.status_code == 200
        meta = r.json()
        assert meta["topic"] == "second version"
        assert meta["message_count"] == 8
        assert meta["tool_counts"]["Bash"] == 4
