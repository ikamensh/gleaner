"""HTTP client for the Gleaner server API.

All network traffic between a developer machine and the Gleaner server goes
through GleanerClient. Credentials are passed in explicitly; this package
knows nothing about config files, local sessions, or scrubbing.
"""

import base64
import gzip
import json
import urllib.request
from urllib.parse import urlencode


class GleanerClient:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.token = token

    def _get(self, path: str, params: dict | None = None, timeout: int = 60) -> bytes:
        full_url = f"{self.url}{path}"
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                full_url += f"?{urlencode(clean)}"
        req = urllib.request.Request(full_url)
        req.add_header("Authorization", f"Bearer {self.token}")
        return urllib.request.urlopen(req, timeout=timeout).read()

    def whoami(self) -> str | None:
        """Verify the connection. Returns the username or None."""
        try:
            data = json.loads(self._get("/api/me", timeout=10))
            return data.get("user")
        except Exception:
            return None

    def upload_session(
        self, session_id: str, metadata: dict, transcript: bytes, provenance: dict
    ):
        """Upload session metadata + transcript (gzipped in transit)."""
        payload = {
            "session_id": session_id,
            "metadata": metadata,
            "provenance": provenance,
            "transcript_size": len(transcript),
            "transcript_gz_b64": base64.b64encode(gzip.compress(transcript)).decode(),
        }
        body = json.dumps(payload).encode()
        req = urllib.request.Request(f"{self.url}/api/session", data=body, method="POST")
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=30)

    def list_session_ids(self) -> set[str]:
        """All session IDs on the server (for backfill dedup).

        limit must be large: a small default would let backfill re-upload
        everything older, double-counting stats on each run.
        """
        data = json.loads(
            self._get("/api/sessions", {"ids_only": "true", "limit": "1000000"})
        )
        return set(data.get("session_ids", []))

    def fetch_sessions(self, since: str | None = None) -> list[dict]:
        """Full session metadata for export, optionally only newer than `since`."""
        params = {"limit": "100000", "export": "true"}
        if since:
            params["since"] = since
        data = json.loads(self._get("/api/sessions", params))
        return data.get("sessions", [])

    def download_transcript(self, session_id: str) -> bytes:
        """Raw gzipped JSONL transcript for one session."""
        return self._get(f"/api/session/{session_id}/raw")
