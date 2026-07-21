"""Claude Code session discovery and transcript parsing.

Sessions live in ~/.claude/projects/<project>/<session_id>.jsonl. The flat
type/role JSONL parser here also handles Cursor agent transcripts, which use
the same shape with 'role' instead of 'type' and no timestamps.
"""

import json
from pathlib import Path

from gleaner.sources.summary import entry_role, summarize

CLAUDE_DIR = Path.home() / ".claude"


def find_all_sessions(project_filter: str | None = None) -> list[tuple[str, str, Path]]:
    """Find all Claude Code session JSONL files.

    Returns [(session_id, project, path), ...].
    """
    projects_dir = CLAUDE_DIR / "projects"
    if not projects_dir.exists():
        return []

    sessions = []
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        project_name = project_dir.name
        if project_filter and project_filter not in project_name:
            continue
        for jsonl in sorted(project_dir.glob("*.jsonl")):
            session_id = jsonl.stem
            sessions.append((session_id, project_name, jsonl))
    return sessions


def find_session_file(session_id: str) -> Path | None:
    """Find the JSONL transcript for a session ID."""
    projects_dir = CLAUDE_DIR / "projects"
    if not projects_dir.exists():
        return None
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue
        candidate = project_dir / f"{session_id}.jsonl"
        if candidate.exists():
            return candidate
    return None


def parse_transcript(path: Path) -> dict:
    """Parse a session JSONL file into summary metadata.

    Handles both Claude Code format (type/timestamp fields) and
    Cursor agent-transcript format (role field, no timestamps).
    """
    messages = []
    tool_uses = []
    first_ts = None
    last_ts = None

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            messages.append(entry)
            ts = entry.get("timestamp")
            if ts:
                if first_ts is None:
                    first_ts = ts
                last_ts = ts

            if entry_role(entry) == "assistant":
                content = entry.get("message", {}).get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            tool_uses.append(block.get("name", "unknown"))

    return summarize(messages, tool_uses, first_ts, last_ts, path)
