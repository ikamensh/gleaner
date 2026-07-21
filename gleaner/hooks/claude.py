"""Claude Code SessionEnd hook handler (the `gleaner-upload` command).

Reads session info from stdin (Claude Code hook JSON), finds the JSONL
transcript on disk, parses metadata, and uploads via the shared pipeline.

Best-effort: never fails loudly, never blocks Claude Code. Writes the
upload outcome to /tmp/gleaner_upload_{session_id} (read by the arcade
overlay).
"""

import json
import os
import sys
from pathlib import Path

from gleaner.pipeline import finalize_metadata, upload_transcript
from gleaner.setup.config import get_credentials
from gleaner.sources.claude import find_session_file, parse_transcript


def main():
    """Entry point for gleaner-upload CLI and SessionEnd hook."""
    url, token = get_credentials()
    if not url or not token:
        return

    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return

    session_id = hook_input.get("session_id", "")
    cwd = hook_input.get("cwd", "")
    if not session_id:
        return

    transcript_path = find_session_file(session_id)
    if not transcript_path:
        return

    metadata = parse_transcript(transcript_path)
    if metadata.pop("worthless", False):
        return

    finalize_metadata(
        metadata,
        session_id=session_id,
        project=transcript_path.parent.name,
        cwd=cwd,
        ide="claude_code",
        # Explicit env var (set by orchestrators like kodo) beats heuristics
        source_override=os.environ.get("CLAUDE_SESSION_SOURCE", ""),
    )

    status_file = Path(f"/tmp/gleaner_upload_{session_id}")
    try:
        upload_transcript(session_id, metadata, transcript_path)
        status_file.write_text("ok")
    except Exception as exc:
        status_file.write_text(str(exc))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
