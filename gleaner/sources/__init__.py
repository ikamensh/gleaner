"""Finding and parsing local coding-agent sessions.

One module per source (Claude Code, Cursor, Codex), each exposing discovery
(`find_all_*`, `find_*_session_file`) and — where the format differs — its
own transcript parser. The `SOURCES` registry is the single map from a
source name to how its sessions are found and parsed; consumers iterate it
instead of hardcoding per-IDE branches.

This package is self-contained: it reads the local filesystem and knows
nothing about config, scrubbing, or storage.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from gleaner.sources import claude, codex, cursor


@dataclass(frozen=True)
class Source:
    """How one IDE's sessions are discovered and parsed."""

    find: Callable[[str | None], list[tuple[str, str, Path]]]  # project_filter -> [(id, project, path)]
    parse: Callable[[Path], dict]  # transcript path -> metadata dict
    ide: str  # tag stored in session metadata


SOURCES: dict[str, Source] = {
    "claude": Source(claude.find_all_sessions, claude.parse_transcript, "claude_code"),
    "cursor": Source(cursor.find_all_cursor_sessions, claude.parse_transcript, "cursor"),
    "codex": Source(codex.find_all_codex_sessions, codex.parse_codex_transcript, "codex"),
}


def parser_for_ide(ide: str) -> Callable[[Path], dict]:
    """The transcript parser for an ide tag ("claude_code", "cursor", "codex")."""
    for source in SOURCES.values():
        if source.ide == ide:
            return source.parse
    raise ValueError(f"unknown ide: {ide!r}")
