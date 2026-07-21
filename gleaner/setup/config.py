"""Gleaner config file (~/.config/gleaner.json) and credential resolution.

A machine can be configured with several named *remotes* (Gleaner server
instances), one of which is active. The active remote is what the CLI and
session hooks upload to. The on-disk shape is:

    {"active": "prod", "remotes": {"prod": {"url": ..., "token": ...}, ...}}

A legacy flat file ({"url": ..., "token": ...}) is transparently read as a
single remote named "default" and rewritten to the current shape on the next
write.
"""

import json
import os
from pathlib import Path

CONFIG_FILE = Path.home() / ".config" / "gleaner.json"

DEFAULT_REMOTE = "default"


def read_config() -> dict:
    """Raw config file contents (may be legacy or current shape, or {})."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def load() -> dict:
    """Config normalized to the current {active, remotes} shape.

    Does not write. A legacy flat {url, token} becomes a single "default"
    remote; anything else without remotes becomes empty.
    """
    cfg = read_config()
    if "remotes" in cfg:
        remotes = cfg.get("remotes") or {}
        active = cfg.get("active")
        if active not in remotes:
            active = next(iter(remotes), None)
        return {"active": active, "remotes": remotes}
    # legacy flat shape
    if cfg.get("url") or cfg.get("token"):
        return {
            "active": DEFAULT_REMOTE,
            "remotes": {DEFAULT_REMOTE: {"url": cfg.get("url", ""), "token": cfg.get("token", "")}},
        }
    return {"active": None, "remotes": {}}


def _write(state: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(state, indent=2) + "\n")


def list_remotes() -> dict:
    """All configured remotes: name -> {url, token}."""
    return load()["remotes"]


def get_active() -> tuple[str, dict]:
    """Active remote name and its {url, token}, or ("", {}) if none."""
    state = load()
    name = state["active"]
    if name and name in state["remotes"]:
        return name, state["remotes"][name]
    return "", {}


def add_remote(name: str, url: str, token: str, activate: bool = True):
    """Insert or replace a remote, optionally making it active."""
    state = load()
    state["remotes"][name] = {"url": url, "token": token}
    if activate or state["active"] is None:
        state["active"] = name
    _write(state)


def use_remote(name: str) -> bool:
    """Make `name` the active remote. Returns False if it is unknown."""
    state = load()
    if name not in state["remotes"]:
        return False
    state["active"] = name
    _write(state)
    return True


def remove_remote(name: str) -> bool:
    """Delete a remote. If it was active, active repoints to a remaining one
    (or None). Returns False if it was unknown."""
    state = load()
    if name not in state["remotes"]:
        return False
    del state["remotes"][name]
    if state["active"] == name:
        state["active"] = next(iter(state["remotes"]), None)
    _write(state)
    return True


def write_config(url: str, token: str):
    """Set the active remote's url+token (creating "default" if none exists).

    Kept for the single-remote setup/auth flows.
    """
    name = get_active()[0] or DEFAULT_REMOTE
    add_remote(name, url, token, activate=True)


def get_credentials() -> tuple[str, str]:
    """Resolve (url, token).

    Precedence: GLEANER_URL/GLEANER_TOKEN env vars, then a remote named by
    GLEANER_REMOTE, then the active remote. Env url/token fill in individually
    over whichever remote was selected.
    """
    env_url = os.environ.get("GLEANER_URL", "")
    env_token = os.environ.get("GLEANER_TOKEN", "")
    if env_url and env_token:
        return env_url, env_token

    state = load()
    selected = os.environ.get("GLEANER_REMOTE") or state["active"]
    remote = state["remotes"].get(selected, {}) if selected else {}
    return env_url or remote.get("url", ""), env_token or remote.get("token", "")
