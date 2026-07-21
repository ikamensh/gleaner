"""Session metadata computation shared by all transcript parsers.

`summarize` turns canonical role-bearing entries + tool-use names into the
metadata dict stored with every session (counts, topic, timestamps,
worthless flag), so the metric definitions stay identical across sources.
"""

import datetime
from pathlib import Path


def _epoch_to_iso(epoch: float) -> str:
    """Convert a Unix epoch timestamp to ISO 8601 UTC string."""
    return datetime.datetime.fromtimestamp(epoch, tz=datetime.timezone.utc).isoformat()


def entry_role(entry: dict) -> str:
    """Extract the role from a JSONL entry (Claude Code uses 'type', Cursor uses 'role')."""
    return entry.get("type") or entry.get("role") or ""


def first_text(content) -> str:
    """First text block (or the string itself) from a message's content."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                return (block.get("text") or "").strip()
    return ""


def make_topic(text: str) -> str:
    """Trim a topic string to the stored length."""
    text = (text or "").strip()
    return text[:200] + "..." if len(text) > 200 else text


def summarize(
    entries: list[dict],
    tool_uses: list[str],
    first_ts: str | None,
    last_ts: str | None,
    path: Path,
    topic: str | None = None,
) -> dict:
    """Compute session metadata from canonical entries + tool-use names.

    `entries` are role-bearing message objects in the canonical Claude-Code
    shape: {"type"|"role": "user"|"assistant", "message": {"content": ...}}.
    """
    user_messages = [m for m in entries if entry_role(m) == "user"]
    assistant_messages = [m for m in entries if entry_role(m) == "assistant"]

    tool_counts: dict[str, int] = {}
    for t in tool_uses:
        tool_counts[t] = tool_counts.get(t, 0) + 1

    if topic is None:
        topic = ""
        for m in user_messages:
            topic = make_topic(first_text(m.get("message", {}).get("content", "")))
            if topic:
                break

    # If no timestamps from the file content, fall back to file metadata
    if first_ts is None:
        stat = path.stat()
        # Use birthtime if available (macOS), otherwise mtime
        ctime = getattr(stat, "st_birthtime", stat.st_mtime)
        first_ts = _epoch_to_iso(ctime)
        last_ts = _epoch_to_iso(stat.st_mtime)

    # Worthless = no human intent at all (no user messages).
    # Sessions with user messages are always worth keeping, even if
    # rate-limited or missing assistant responses.
    worthless = not user_messages

    return {
        "message_count": len(entries),
        "user_message_count": len(user_messages),
        "assistant_message_count": len(assistant_messages),
        "tool_use_count": len(tool_uses),
        "tool_counts": tool_counts,
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "topic": topic,
        "worthless": worthless,
    }
