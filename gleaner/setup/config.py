"""Gleaner config file (~/.config/gleaner.json) and credential resolution."""

import json
import os
from pathlib import Path

CONFIG_FILE = Path.home() / ".config" / "gleaner.json"


def read_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_config(url: str, token: str):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"url": url, "token": token}, indent=2) + "\n")


def get_credentials() -> tuple[str, str]:
    """Get URL and token from env vars (preferred) or config file (fallback)."""
    url = os.environ.get("GLEANER_URL", "")
    token = os.environ.get("GLEANER_TOKEN", "")
    if url and token:
        return url, token
    cfg = read_config()
    return url or cfg.get("url", ""), token or cfg.get("token", "")
