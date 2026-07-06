"""Install/remove arcade hooks from ~/.claude/settings.json."""

import json
import sys
from pathlib import Path

CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
ARCADE_CONFIG = Path.home() / ".config" / "arcade.json"

ARCADE_HOOKS = {
    "PostToolUse": [
        {
            "matcher": "Write|Edit|Bash|Grep|Glob|Read|Agent",
            "hooks": [{"type": "command", "command": "arcade-hook", "timeout": 5}],
        }
    ],
    "PreToolUse": [
        {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "arcade-hook", "timeout": 5}],
        }
    ],
    "Stop": [
        {"hooks": [{"type": "command", "command": "arcade-hook", "timeout": 5}]}
    ],
    "SessionStart": [
        {"hooks": [{"type": "command", "command": "arcade-hook", "timeout": 5}]}
    ],
    "SessionEnd": [
        {"hooks": [{"type": "command", "command": "arcade-hook", "timeout": 10}]}
    ],
    "Notification": [
        {"hooks": [{"type": "command", "command": "arcade-hook", "timeout": 5}]}
    ],
}

MARKER = "arcade-hook"


def _read_settings():
    if not CLAUDE_SETTINGS.exists():
        return {}
    try:
        return json.loads(CLAUDE_SETTINGS.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _write_settings(settings):
    CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    CLAUDE_SETTINGS.write_text(json.dumps(settings, indent=2) + "\n")


def _has_arcade(settings):
    for event_groups in settings.get("hooks", {}).values():
        for group in event_groups:
            for hook in group.get("hooks", []):
                if MARKER in hook.get("command", ""):
                    return True
    return False


def _remove_arcade(settings):
    hooks = settings.get("hooks", {})
    for event in list(hooks.keys()):
        hooks[event] = [
            group
            for group in hooks[event]
            if not any(MARKER in h.get("command", "") for h in group.get("hooks", []))
        ]
        if not hooks[event]:
            del hooks[event]
    return settings


def install():
    settings = _read_settings()
    if _has_arcade(settings):
        print("Arcade hooks already installed.")
        return False
    settings.setdefault("hooks", {})
    for event, groups in ARCADE_HOOKS.items():
        settings["hooks"].setdefault(event, [])
        settings["hooks"][event].extend(groups)
    _write_settings(settings)
    print("Arcade hooks installed. Restart Claude Code to activate.")
    return True


def uninstall():
    settings = _read_settings()
    if not _has_arcade(settings):
        print("Arcade hooks not installed.")
        return False
    _remove_arcade(settings)
    _write_settings(settings)
    print("Arcade hooks removed.")
    return True


def _read_config():
    if ARCADE_CONFIG.exists():
        try:
            return json.loads(ARCADE_CONFIG.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _write_config(config):
    ARCADE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    ARCADE_CONFIG.write_text(json.dumps(config, indent=2) + "\n")


def sounds(on_off):
    config = _read_config()
    config["sounds"] = on_off == "on"
    _write_config(config)
    print(f"Sounds: {'on' if config['sounds'] else 'off'}")


def status():
    settings = _read_settings()
    config = _read_config()
    if _has_arcade(settings):
        events = []
        for event, groups in settings.get("hooks", {}).items():
            for group in groups:
                if any(MARKER in h.get("command", "") for h in group.get("hooks", [])):
                    events.append(event)
        print(f"Arcade: ON ({', '.join(events)})")
    else:
        print("Arcade: OFF")
    sounds_on = config.get("sounds", True)
    print(f"Sounds: {'on' if sounds_on else 'off'}")


def main():
    if len(sys.argv) < 2:
        print("Usage: arcade <on|off|status|sounds on|sounds off>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "on":
        install()
    elif cmd == "off":
        uninstall()
    elif cmd == "status":
        status()
    elif cmd == "sounds" and len(sys.argv) >= 3 and sys.argv[2] in ("on", "off"):
        sounds(sys.argv[2])
    else:
        print("Usage: arcade <on|off|status|sounds on|sounds off>")
        sys.exit(1)


if __name__ == "__main__":
    main()
