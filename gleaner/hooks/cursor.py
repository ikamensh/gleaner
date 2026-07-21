"""Cursor `stop` hook handler (the `gleaner-cursor-upload` command).

Registered in ~/.cursor/hooks.json under the `stop` hook. Cursor passes a
JSON payload on stdin with conversation_id, status, and workspace_roots.

Best-effort: never fails loudly, never blocks Cursor.
"""

import json
import os
import sys

from gleaner.pipeline import finalize_metadata, upload_transcript
from gleaner.setup.config import get_credentials
from gleaner.sources.claude import parse_transcript
from gleaner.sources.cursor import find_cursor_session_file


def main():
    url, token = get_credentials()
    if not url or not token:
        return

    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return

    conversation_id = hook_input.get("conversation_id", "")
    if not conversation_id:
        return

    status = hook_input.get("status", "completed")
    workspace_roots = hook_input.get("workspace_roots", [])
    cwd = workspace_roots[0] if workspace_roots else ""

    transcript_path = find_cursor_session_file(conversation_id)
    if not transcript_path:
        return

    metadata = parse_transcript(transcript_path)
    if metadata.pop("worthless", False):
        return

    finalize_metadata(
        metadata,
        session_id=conversation_id,
        project=transcript_path.parent.parent.parent.name,
        cwd=cwd,
        ide="cursor",
        aborted=status == "aborted",
        has_errors=status == "error",
        source_override=os.environ.get("CLAUDE_SESSION_SOURCE", ""),
    )

    upload_transcript(conversation_id, metadata, transcript_path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
