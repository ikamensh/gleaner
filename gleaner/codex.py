"""Codex CLI session discovery and rollout parsing.

Codex writes one rollout transcript per session to
    ~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl

Every line is ``{"timestamp", "type", "payload"}``. Unlike Claude Code /
Cursor (flat ``type``/``role`` with ``message.content``), the conversation
is carried inside ``response_item`` entries:

    payload.type == "message"  ->  payload.role + payload.content[].{input_text|output_text}
    payload.type == "function_call" | "local_shell_call" | "custom_tool_call"  ->  a tool call

The first line is a ``session_meta`` carrying the session_id and cwd. This
module normalizes a rollout into the canonical entry shape consumed by
``gleaner.upload.summarize`` so Codex sessions produce the same metadata as
the other sources.
"""

import json
from pathlib import Path

from gleaner.upload import _first_text, make_topic, summarize

CODEX_DIR = Path.home() / ".codex"
SESSIONS_DIR = CODEX_DIR / "sessions"

# Top-level `type` values that mark a line as Codex rollout format.
_CODEX_LINE_TYPES = {"response_item", "event_msg", "session_meta", "turn_context"}

# Prefixes that mark an injected (non-human) "user" message: the AGENTS.md
# preamble and the specific context blocks Codex prepends to a session. Kept
# specific so a genuine prompt that merely starts with "<" is not dropped.
_INJECTION_PREFIXES = (
    "# AGENTS.md instructions for",
    "<environment_context",
    "<user_instructions",
    "<permissions instructions",
    "<system",
)

# response_item payload types that represent a tool call (not its output).
_TOOL_CALL_TYPES = {
    "function_call": lambda p: p.get("name", "unknown"),
    "local_shell_call": lambda p: "local_shell",
    "custom_tool_call": lambda p: p.get("name", "custom_tool"),
}


def _codex_tool_name(payload: dict) -> str:
    """Tool name for a response_item payload, or "" if it is not a tool call."""
    fn = _TOOL_CALL_TYPES.get(payload.get("type"))
    return fn(payload) if fn else ""


def _encode_project(cwd: str) -> str:
    """Encode a working directory the way Claude Code names its project dirs.

    /Users/x/code-republic/gleaner -> -Users-x-code-republic-gleaner, so the
    same repo groups together across Claude and Codex sessions.
    """
    return cwd.replace("/", "-").replace(".", "-") if cwd else "codex"


def _read_session_meta(path: Path) -> tuple[str, str]:
    """Return (session_id, cwd) from a rollout's session_meta line.

    Falls back to the uuid embedded in the filename when the meta line is
    missing or unreadable.
    """
    try:
        with open(path, encoding="utf-8") as f:
            for _ in range(5):  # session_meta is the first line; scan a few to be safe
                line = f.readline()
                if not line:
                    break
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") == "session_meta":
                    p = entry.get("payload", {})
                    return p.get("session_id") or _id_from_name(path), p.get("cwd", "")
    except OSError:
        pass
    return _id_from_name(path), ""


def _id_from_name(path: Path) -> str:
    """Extract the trailing uuid from rollout-<ts>-<uuid>.jsonl."""
    stem = path.stem  # rollout-2026-06-24T12-00-32-019ef913-00d0-7911-9dd3-9947f20e65f6
    # The uuid is the last 5 dash-joined groups.
    parts = stem.split("-")
    return "-".join(parts[-5:]) if len(parts) >= 5 else stem


def find_all_codex_sessions(
    project_filter: str | None = None,
) -> list[tuple[str, str, Path]]:
    """Find all Codex rollout files.

    Returns [(session_id, project_name, path), ...] in the same shape as
    backfill.find_all_sessions for Claude Code.
    """
    if not SESSIONS_DIR.exists():
        return []

    sessions = []
    for path in sorted(SESSIONS_DIR.rglob("rollout-*.jsonl")):
        session_id, cwd = _read_session_meta(path)
        project = _encode_project(cwd)
        if project_filter and project_filter not in project:
            continue
        sessions.append((session_id, project, path))
    return sessions


def find_codex_session_file(session_id: str) -> Path | None:
    """Find the rollout transcript for a Codex session id (uuid)."""
    if not SESSIONS_DIR.exists():
        return None
    matches = list(SESSIONS_DIR.rglob(f"rollout-*-{session_id}.jsonl"))
    return matches[0] if matches else None


def _is_injection(text: str) -> bool:
    return text.startswith(_INJECTION_PREFIXES)


def _codex_content_to_canonical(content) -> list[dict]:
    """Map Codex content blocks (input_text/output_text/text) to {type:text}."""
    out = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") in (
                "input_text",
                "output_text",
                "text",
            ):
                out.append({"type": "text", "text": block.get("text", "")})
    elif isinstance(content, str):
        out.append({"type": "text", "text": content})
    return out


def parse_codex_transcript(path: Path) -> dict:
    """Parse a Codex rollout into the same metadata dict as parse_transcript.

    Real user prompts and assistant messages become canonical entries;
    injected preambles (developer role, AGENTS.md, <context> blocks) are
    dropped so counts and the topic reflect genuine interaction.
    """
    entries: list[dict] = []
    tool_uses: list[str] = []
    first_ts = None
    last_ts = None
    goal_objective = ""

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = obj.get("timestamp")
            if ts:
                if first_ts is None:
                    first_ts = ts
                last_ts = ts

            kind = obj.get("type")
            payload = obj.get("payload", {})

            if kind == "event_msg" and payload.get("type") == "thread_goal_updated":
                goal_objective = (payload.get("goal", {}) or {}).get("objective", "") or goal_objective
                continue

            if kind != "response_item":
                continue

            ptype = payload.get("type")
            if ptype == "message":
                role = payload.get("role")
                content = _codex_content_to_canonical(payload.get("content", []))
                if role == "user":
                    if _is_injection(_first_text(content)):
                        continue  # AGENTS.md / context injection, not a human turn
                elif role != "assistant":
                    continue  # developer / system preamble
                entries.append({"type": role, "timestamp": ts, "message": {"content": content}})
            elif name := _codex_tool_name(payload):
                tool_uses.append(name)

    # Prefer the first genuine user prompt; fall back to the thread goal.
    topic = None
    for m in entries:
        if m.get("type") == "user":
            topic = make_topic(_first_text(m["message"]["content"]))
            break
    if not topic and goal_objective:
        topic = make_topic(goal_objective)

    return summarize(entries, tool_uses, first_ts, last_ts, path, topic=topic)
