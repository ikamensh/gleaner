"""Install Gleaner's capture into the user's system.

Three integration points: the Claude Code SessionEnd hook
(~/.claude/settings.json), the Cursor stop hook (~/.cursor/hooks.json),
and a periodic sync agent registered with the OS-native scheduler
(see gleaner.setup.sync_agent).

Hook commands are written as absolute paths: GUI-launched IDEs don't
inherit the shell PATH that would resolve a bare `gleaner-upload`.
"""

import json
from pathlib import Path

from gleaner.setup.sync_agent import (  # noqa: F401  (re-exported)
    BACKFILL_INTERVAL,
    find_script,
    install_backfill_agent,
    is_backfill_agent_installed,
    remove_backfill_agent,
)

CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
CURSOR_HOOKS = Path.home() / ".cursor" / "hooks.json"


def _hook_command(script: str) -> str:
    """Absolute, shell-safe command for a hook entry."""
    path = find_script(script)
    return f'"{path}"' if " " in path else path


def read_claude_settings() -> dict:
    if not CLAUDE_SETTINGS.exists():
        return {}
    try:
        return json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_claude_settings(settings: dict):
    CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    CLAUDE_SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def is_hook_installed() -> bool:
    settings = read_claude_settings()
    for group in settings.get("hooks", {}).get("SessionEnd", []):
        for hook in group.get("hooks", []):
            if "gleaner" in hook.get("command", ""):
                return True
    return False


def install_hook() -> bool:
    """Add gleaner-upload to SessionEnd hooks. Returns True if newly added."""
    if is_hook_installed():
        return False
    settings = read_claude_settings()
    settings.setdefault("hooks", {})
    settings["hooks"].setdefault("SessionEnd", [])
    settings["hooks"]["SessionEnd"].append(
        {
            "hooks": [
                {
                    "type": "command",
                    "command": _hook_command("gleaner-upload"),
                    "timeout": 30,
                }
            ]
        }
    )
    write_claude_settings(settings)
    return True


def remove_hook() -> bool:
    """Remove gleaner-upload from SessionEnd hooks. Returns True if removed."""
    settings = read_claude_settings()
    session_end = settings.get("hooks", {}).get("SessionEnd", [])
    filtered = [
        group
        for group in session_end
        if not any("gleaner" in h.get("command", "") for h in group.get("hooks", []))
    ]
    if len(filtered) == len(session_end):
        return False
    settings["hooks"]["SessionEnd"] = filtered
    write_claude_settings(settings)
    return True


# -- Cursor hook management ----------------------------------------------------


def read_cursor_hooks() -> dict:
    if not CURSOR_HOOKS.exists():
        return {}
    try:
        return json.loads(CURSOR_HOOKS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_cursor_hooks(hooks: dict):
    CURSOR_HOOKS.parent.mkdir(parents=True, exist_ok=True)
    CURSOR_HOOKS.write_text(json.dumps(hooks, indent=2) + "\n", encoding="utf-8")


def is_cursor_hook_installed() -> bool:
    cfg = read_cursor_hooks()
    for entry in cfg.get("hooks", {}).get("stop", []):
        if "gleaner" in entry.get("command", ""):
            return True
    return False


def install_cursor_hook() -> bool:
    """Add gleaner-cursor-upload to Cursor stop hooks. Returns True if newly added."""
    if is_cursor_hook_installed():
        return False
    cfg = read_cursor_hooks()
    cfg["version"] = 1
    cfg.setdefault("hooks", {})
    cfg["hooks"].setdefault("stop", [])
    cfg["hooks"]["stop"].append({"command": _hook_command("gleaner-cursor-upload")})
    write_cursor_hooks(cfg)
    return True


def remove_cursor_hook() -> bool:
    """Remove gleaner-cursor-upload from Cursor stop hooks. Returns True if removed."""
    cfg = read_cursor_hooks()
    stop = cfg.get("hooks", {}).get("stop", [])
    filtered = [e for e in stop if "gleaner" not in e.get("command", "")]
    if len(filtered) == len(stop):
        return False
    cfg["hooks"]["stop"] = filtered
    write_cursor_hooks(cfg)
    return True
