"""Main hook handler. Reads Claude Code hook JSON from stdin, dispatches effects."""

import json
import sys
import time
from pathlib import Path

from arcade import effects, scoring

UPLOAD_STATUS_POLL_ATTEMPTS = 6
UPLOAD_STATUS_POLL_INTERVAL = 0.5  # seconds


def _handle_session_start(data):
    session_id = data.get("session_id", "")
    effects.play_sound("session_start")
    effects.show_overlay("start", "GLEANER ON", duration=3.0)


def _check_upload_status(session_id):
    """Poll for gleaner upload status file. Returns ("ok", None) or ("error", message)."""
    status_file = Path(f"/tmp/gleaner_upload_{session_id}")
    for _ in range(UPLOAD_STATUS_POLL_ATTEMPTS):
        if status_file.exists():
            content = status_file.read_text().strip()
            status_file.unlink(missing_ok=True)
            if content == "ok":
                return "ok", None
            return "error", content
        time.sleep(UPLOAD_STATUS_POLL_INTERVAL)
    return "unknown", None


def _handle_session_end(data):
    session_id = data.get("session_id", "")
    state = scoring.finalize_session(session_id)
    streak = scoring.get_streak()
    score = state.get("score", 0)
    tools = state.get("tool_count", 0)

    # Wait for gleaner upload result
    upload_status, upload_error = _check_upload_status(session_id)

    if upload_status == "error":
        error_short = (upload_error or "unknown error")[:60]
        effects.play_sound("error")
        effects.flash_tab("red", duration=1.0)
        effects.show_overlay("error", f"Upload failed: {error_short}", duration=4.0)
    else:
        msg = f"Score: {score}  |  Tools: {tools}  |  Streak: {streak}d"
        if upload_status == "ok":
            msg = f"Uploaded  |  {msg}"
        effects.play_sound("session_end")
        effects.show_overlay("success", msg, duration=4.0)


def _handle_pre_tool_use(data):
    tool = data.get("tool_name", "")
    if tool == "Bash":
        effects.play_sound("tool_start")
        effects.flash_tab("amber")


def _handle_post_tool_use(data):
    tool = data.get("tool_name", "")
    session_id = data.get("session_id", "")

    score, combo, is_new_combo = scoring.record_tool_use(session_id, tool)

    # Sound based on tool type
    if tool in ("Write", "Edit"):
        effects.play_sound("file_write")
        effects.flash_tab("green")
    elif tool == "Bash":
        effects.play_sound("bash_done")
        effects.flash_tab("blue")
    elif tool in ("Grep", "Glob"):
        effects.play_sound("search_done")

    # Combo bonus sound
    if is_new_combo:
        effects.play_sound("combo")



def _handle_stop(data):
    effects.play_sound("stop")
    effects.flash_tab("green", duration=0.6)


def _handle_notification(data):
    effects.play_sound("notification")
    effects.flash_tab("yellow")


HANDLERS = {
    "SessionStart": _handle_session_start,
    "SessionEnd": _handle_session_end,
    "PreToolUse": _handle_pre_tool_use,
    "PostToolUse": _handle_post_tool_use,
    "Stop": _handle_stop,
    "Notification": _handle_notification,
}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return

    event = data.get("hook_event_name", "")
    handler = HANDLERS.get(event)
    if handler:
        handler(data)


if __name__ == "__main__":
    main()
