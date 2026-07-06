"""Session scoring: combo counter, score tracking, daily streaks."""

import json
import time
from pathlib import Path

COMBO_WINDOW = 5.0  # seconds between tool uses to keep combo alive

TOOL_POINTS = {
    "Write": 3,
    "Edit": 3,
    "Bash": 5,
    "Read": 1,
    "Grep": 1,
    "Glob": 1,
    "Agent": 2,
}
DEFAULT_POINTS = 1

STREAK_FILE = Path.home() / ".config" / "arcade_streak.json"


def _state_file(session_id):
    return Path(f"/tmp/arcade_{session_id}.json")


def load_state(session_id):
    path = _state_file(session_id)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"score": 0, "combo": 0, "last_tool_time": 0, "tool_count": 0}


def save_state(session_id, state):
    _state_file(session_id).write_text(json.dumps(state))


def record_tool_use(session_id, tool_name):
    """Record a tool use. Returns (score, combo, is_new_combo_level)."""
    state = load_state(session_id)
    now = time.time()

    # Combo logic
    elapsed = now - state["last_tool_time"] if state["last_tool_time"] else COMBO_WINDOW + 1
    if elapsed <= COMBO_WINDOW:
        state["combo"] += 1
    else:
        state["combo"] = 1

    state["last_tool_time"] = now
    state["tool_count"] += 1

    # Points (with combo multiplier at 5+)
    points = TOOL_POINTS.get(tool_name, DEFAULT_POINTS)
    if state["combo"] >= 5:
        points *= 2
    state["score"] += points

    # Check if we just crossed a combo threshold
    is_new_combo = state["combo"] in (5, 10, 20, 50)

    save_state(session_id, state)
    return state["score"], state["combo"], is_new_combo


def finalize_session(session_id):
    """End session: update streak, return final stats, clean up state file."""
    state = load_state(session_id)
    _update_streak()
    path = _state_file(session_id)
    if path.exists():
        path.unlink()
    return state


def _update_streak():
    """Track consecutive days of usage."""
    today = time.strftime("%Y-%m-%d")
    data = {"last_date": "", "streak": 0}
    if STREAK_FILE.exists():
        try:
            data = json.loads(STREAK_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    last = data.get("last_date", "")
    if last == today:
        return data["streak"]

    # Check if yesterday
    import datetime

    try:
        last_dt = datetime.date.fromisoformat(last)
        today_dt = datetime.date.fromisoformat(today)
        if (today_dt - last_dt).days == 1:
            data["streak"] += 1
        else:
            data["streak"] = 1
    except ValueError:
        data["streak"] = 1

    data["last_date"] = today
    STREAK_FILE.parent.mkdir(parents=True, exist_ok=True)
    STREAK_FILE.write_text(json.dumps(data))
    return data["streak"]


def get_streak():
    if STREAK_FILE.exists():
        try:
            return json.loads(STREAK_FILE.read_text()).get("streak", 0)
        except (json.JSONDecodeError, OSError):
            pass
    return 0
