"""Scrub PII and secrets from text before it leaves the machine.

Two backends:
  "legacy"   — piicleaner + detect-secrets + regex
  "presidio" — Microsoft Presidio pattern recognizers + custom secret patterns

Auto-selects presidio when installed, falls back to legacy.
Override with GLEANER_SCRUB_ENGINE=legacy or GLEANER_SCRUB_ENGINE=presidio.

Public API: scrub_text, scrub_jsonl, ScrubStats, SCRUB_ENGINE.
This package is self-contained: text in, text out.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

_log = logging.getLogger(__name__)


def _has_presidio() -> bool:
    try:
        import presidio_analyzer  # noqa: F401
        import presidio_anonymizer  # noqa: F401
        import spacy  # noqa: F401
        return True
    except ImportError:
        return False


def _resolve_engine() -> str:
    explicit = os.environ.get("GLEANER_SCRUB_ENGINE", "")
    if explicit:
        return explicit
    return "presidio" if _has_presidio() else "legacy"


SCRUB_ENGINE = _resolve_engine()


@dataclass(frozen=True)
class ScrubStats:
    redactions: int = 0

    def __add__(self, other: ScrubStats) -> ScrubStats:
        return ScrubStats(redactions=self.redactions + other.redactions)


def scrub_text(text: str) -> tuple[str, ScrubStats]:
    """Scrub secrets and PII from text. Returns (scrubbed_text, stats)."""
    try:
        if SCRUB_ENGINE == "presidio":
            from gleaner.scrub import presidio as backend
        else:
            from gleaner.scrub import legacy as backend
        text, total = backend.scrub(text)
        if total:
            _log.info("Scrubbed %d sensitive item(s) [engine=%s]", total, SCRUB_ENGINE)
        return text, ScrubStats(redactions=total)
    except Exception as exc:
        _log.warning("Scrubbing failed (uploading as-is): %s", exc)
        return text, ScrubStats()


def _scrub_json_value(value):
    """Recursively scrub only the string values of a parsed JSON document.

    Numbers/bools/null pass through untouched, so structural data (epoch
    timestamps, counts, ids) is preserved and the document stays valid JSON.
    Returns (scrubbed_value, ScrubStats).
    """
    if isinstance(value, str):
        scrubbed, stats = scrub_text(value)
        return scrubbed, stats
    if isinstance(value, list):
        stats = ScrubStats()
        out = []
        for item in value:
            s, st = _scrub_json_value(item)
            out.append(s)
            stats = stats + st
        return out, stats
    if isinstance(value, dict):
        stats = ScrubStats()
        out = {}
        for k, v in value.items():
            s, st = _scrub_json_value(v)
            out[k] = s
            stats = stats + st
        return out, stats
    return value, ScrubStats()


def scrub_jsonl(text: str) -> tuple[str, ScrubStats]:
    """Scrub a JSONL transcript without breaking its JSON structure.

    Each line is parsed and only its string values are scrubbed, so PII in
    conversation text is removed while numeric fields stay intact and every
    line remains valid JSON. Lines that are not JSON fall back to plain text
    scrubbing. Returns (scrubbed_text, stats).
    """
    out_lines = []
    stats = ScrubStats()
    for line in text.split("\n"):
        if not line.strip():
            out_lines.append(line)
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            scrubbed, st = scrub_text(line)
            out_lines.append(scrubbed)
            stats = stats + st
            continue
        scrubbed_obj, st = _scrub_json_value(obj)
        out_lines.append(json.dumps(scrubbed_obj, ensure_ascii=False, separators=(",", ":")))
        stats = stats + st
    return "\n".join(out_lines), stats
