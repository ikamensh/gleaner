"""Unit tests for backend.db (cloud storage module).

Verifies idempotent store_session semantics without connecting to GCP:
- First upload of a session_id writes transcript + metadata and updates counters.
- Re-upload overwrites transcript + metadata (last-write-wins) but skips counters.
- Global and user-level caches are invalidated after every upload.

All GCP I/O is intercepted via unittest.mock — no network calls are made.
"""
from unittest.mock import MagicMock, call, patch

import pytest

from backend import db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _meta(session_id: str, topic: str = "test topic", msg_count: int = 4) -> dict:
    return {
        "session_id": session_id,
        "topic": topic,
        "message_count": msg_count,
        "user_message_count": 2,
        "assistant_message_count": 2,
        "tool_use_count": 2,
        "tool_counts": {"Read": 2},
        "first_timestamp": "2026-03-20T10:00:00Z",
        "last_timestamp": "2026-03-20T10:05:00Z",
        "project": "test-project",
        "cwd": "/tmp/test",
    }


def _prov(user: str = "testuser") -> dict:
    return {"user": user, "host": "ci", "platform": "Linux x86_64"}


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset the module-level cache between tests so they don't interfere."""
    db._cache.clear()
    yield
    db._cache.clear()


def _make_doc_ref(exists: bool) -> MagicMock:
    """Build a mock Firestore DocumentReference whose .get().exists == exists."""
    doc_ref = MagicMock()
    doc_ref.get.return_value.exists = exists
    return doc_ref


def _mock_db(doc_ref: MagicMock) -> MagicMock:
    """Return a mock Firestore client wired to return doc_ref for any collection/document."""
    mock = MagicMock()
    mock.collection.return_value.document.return_value = doc_ref
    return mock


def _mock_bucket() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# Counter gating
# ---------------------------------------------------------------------------


class TestCounterGating:
    """_update_counters is called only when the session_id is new."""

    def test_new_session_calls_update_counters(self):
        """First upload triggers counter updates exactly once."""
        doc_ref = _make_doc_ref(exists=False)
        with (
            patch("backend.db._db", return_value=_mock_db(doc_ref)),
            patch("backend.db._bucket", return_value=_mock_bucket()),
            patch("backend.db._update_counters") as mock_counters,
        ):
            db.store_session("new-sid", _meta("new-sid"), _prov(), b"gz_data", 50)

        mock_counters.assert_called_once_with("new-sid", _meta("new-sid"), _prov())

    def test_duplicate_session_skips_update_counters(self):
        """Re-upload of an existing session_id never calls _update_counters."""
        doc_ref = _make_doc_ref(exists=True)
        with (
            patch("backend.db._db", return_value=_mock_db(doc_ref)),
            patch("backend.db._bucket", return_value=_mock_bucket()),
            patch("backend.db._update_counters") as mock_counters,
        ):
            db.store_session("existing-sid", _meta("existing-sid"), _prov(), b"gz_data", 50)

        mock_counters.assert_not_called()

    def test_counter_update_exception_does_not_propagate(self):
        """A failing counter update is swallowed for new sessions (pre-existing contract)."""
        doc_ref = _make_doc_ref(exists=False)
        with (
            patch("backend.db._db", return_value=_mock_db(doc_ref)),
            patch("backend.db._bucket", return_value=_mock_bucket()),
            patch("backend.db._update_counters", side_effect=RuntimeError("boom")),
        ):
            # Should not raise
            db.store_session("fail-counter-sid", _meta("fail-counter-sid"), _prov(), b"gz", 10)


# ---------------------------------------------------------------------------
# Last-write-wins: transcript and metadata always overwritten
# ---------------------------------------------------------------------------


class TestLastWriteWins:
    """Transcript and metadata are always overwritten regardless of prior existence."""

    def test_gcs_blob_uploaded_for_new_session(self):
        """First upload writes the blob at the expected path."""
        doc_ref = _make_doc_ref(exists=False)
        mock_bucket = _mock_bucket()
        with (
            patch("backend.db._db", return_value=_mock_db(doc_ref)),
            patch("backend.db._bucket", return_value=mock_bucket),
            patch("backend.db._update_counters"),
        ):
            db.store_session("new-gcs", _meta("new-gcs"), _prov(), b"gz_bytes", 30)

        mock_bucket.blob.assert_called_once_with("sessions/new-gcs.jsonl.gz")
        mock_bucket.blob.return_value.upload_from_string.assert_called_once_with(
            b"gz_bytes", content_type="application/gzip"
        )

    def test_gcs_blob_overwritten_on_re_upload(self):
        """Re-upload writes updated bytes to the same blob path."""
        doc_ref = _make_doc_ref(exists=True)
        mock_bucket = _mock_bucket()
        new_bytes = b"updated_gz"
        with (
            patch("backend.db._db", return_value=_mock_db(doc_ref)),
            patch("backend.db._bucket", return_value=mock_bucket),
        ):
            db.store_session("dup-gcs", _meta("dup-gcs"), _prov(), new_bytes, 20)

        mock_bucket.blob.assert_called_once_with("sessions/dup-gcs.jsonl.gz")
        mock_bucket.blob.return_value.upload_from_string.assert_called_once_with(
            new_bytes, content_type="application/gzip"
        )

    def test_firestore_set_called_for_new_session(self):
        """First upload calls doc_ref.set() to create the document."""
        doc_ref = _make_doc_ref(exists=False)
        with (
            patch("backend.db._db", return_value=_mock_db(doc_ref)),
            patch("backend.db._bucket", return_value=_mock_bucket()),
            patch("backend.db._update_counters"),
        ):
            db.store_session("new-fs", _meta("new-fs", topic="hello"), _prov(), b"gz", 10)

        doc_ref.set.assert_called_once()
        stored = doc_ref.set.call_args[0][0]
        assert stored["topic"] == "hello"
        assert stored["provenance"] == _prov()

    def test_firestore_set_overwrites_on_re_upload(self):
        """Re-upload calls doc_ref.set() with updated metadata."""
        doc_ref = _make_doc_ref(exists=True)
        with (
            patch("backend.db._db", return_value=_mock_db(doc_ref)),
            patch("backend.db._bucket", return_value=_mock_bucket()),
        ):
            db.store_session("dup-fs", _meta("dup-fs", topic="updated topic"), _prov(), b"gz", 10)

        doc_ref.set.assert_called_once()
        stored = doc_ref.set.call_args[0][0]
        assert stored["topic"] == "updated topic"

    def test_stored_document_contains_gcs_path(self):
        """doc_data written to Firestore includes the correct gcs_path field."""
        doc_ref = _make_doc_ref(exists=False)
        with (
            patch("backend.db._db", return_value=_mock_db(doc_ref)),
            patch("backend.db._bucket", return_value=_mock_bucket()),
            patch("backend.db._update_counters"),
        ):
            db.store_session("path-check", _meta("path-check"), _prov(), b"gz", 10)

        stored = doc_ref.set.call_args[0][0]
        assert stored["gcs_path"] == "sessions/path-check.jsonl.gz"

    def test_stored_document_contains_size_fields(self):
        """doc_data includes transcript_size and transcript_gz_size from the call args."""
        doc_ref = _make_doc_ref(exists=False)
        gz_payload = b"x" * 77
        with (
            patch("backend.db._db", return_value=_mock_db(doc_ref)),
            patch("backend.db._bucket", return_value=_mock_bucket()),
            patch("backend.db._update_counters"),
        ):
            db.store_session("size-check", _meta("size-check"), _prov(), gz_payload, 200)

        stored = doc_ref.set.call_args[0][0]
        assert stored["transcript_size"] == 200
        assert stored["transcript_gz_size"] == 77


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------


class TestCacheInvalidation:
    """Global and per-user caches are evicted after every store_session call."""

    def _run_store(self, exists: bool, user: str = "testuser"):
        doc_ref = _make_doc_ref(exists=exists)
        with (
            patch("backend.db._db", return_value=_mock_db(doc_ref)),
            patch("backend.db._bucket", return_value=_mock_bucket()),
            patch("backend.db._update_counters"),
        ):
            db.store_session("cache-sid", _meta("cache-sid"), _prov(user=user), b"gz", 10)

    def test_global_cache_evicted_on_new_upload(self):
        db._cache["global_stats"] = (9_999_999_999.0, {"total_sessions": 3})
        self._run_store(exists=False)
        assert "global_stats" not in db._cache

    def test_user_cache_evicted_on_new_upload(self):
        db._cache["user_stats:testuser"] = (9_999_999_999.0, {"total_sessions": 3})
        self._run_store(exists=False)
        assert "user_stats:testuser" not in db._cache

    def test_global_cache_evicted_on_re_upload(self):
        db._cache["global_stats"] = (9_999_999_999.0, {"total_sessions": 3})
        self._run_store(exists=True)
        assert "global_stats" not in db._cache

    def test_user_cache_evicted_on_re_upload(self):
        db._cache["user_stats:testuser"] = (9_999_999_999.0, {"total_sessions": 3})
        self._run_store(exists=True)
        assert "user_stats:testuser" not in db._cache

    def test_unrelated_cache_entries_not_evicted(self):
        """Other cache keys (e.g. a different user) survive the upload."""
        db._cache["user_stats:otheruser"] = (9_999_999_999.0, {"total_sessions": 1})
        self._run_store(exists=False, user="testuser")
        assert "user_stats:otheruser" in db._cache
