"""Legacy scrub backend: piicleaner + detect-secrets + regex."""

import re
import tempfile
from pathlib import Path

from gleaner.scrub.patterns import PEM_BLOCK_RE, REDACTED, SECRET_ASSIGNMENT_RE

_pii_cleaner = None


def _get_pii_cleaner():
    global _pii_cleaner
    if _pii_cleaner is None:
        from piicleaner import Cleaner

        _pii_cleaner = Cleaner()
    return _pii_cleaner


def _scrub_pii(text: str) -> tuple[str, int]:
    cleaner = _get_pii_cleaner()
    matches = cleaner.detect_pii(text)
    if not matches:
        return text, 0
    return cleaner.clean_pii(text, "redact"), len(matches)


def _scrub_secrets(text: str) -> tuple[str, int]:
    from detect_secrets.core import scan
    from detect_secrets.settings import default_settings

    redactions = 0

    # PEM blocks first — detect-secrets only catches the header, not the body.
    text, pem_count = PEM_BLOCK_RE.subn(REDACTED, text)
    redactions += pem_count

    with tempfile.TemporaryDirectory() as tmpdir:
        sample = Path(tmpdir) / "archive.txt"
        sample.write_text(text, encoding="utf-8")
        with default_settings():
            secrets = {
                finding.secret_value
                for finding in scan.scan_file(str(sample))
                if getattr(finding, "secret_value", "")
            }

    for secret in sorted(secrets, key=len, reverse=True):
        count = text.count(secret)
        if count:
            redactions += count
            text = text.replace(secret, REDACTED)

    def redact_assignment(match: re.Match[str]) -> str:
        quote = match.group("quote") or ""
        return f"{match.group('prefix')}{quote}{REDACTED}{quote}"

    text, assignment_count = SECRET_ASSIGNMENT_RE.subn(redact_assignment, text)
    redactions += assignment_count

    return text, redactions


def scrub(text: str) -> tuple[str, int]:
    """Scrub secrets then PII. Returns (scrubbed_text, redaction_count)."""
    text, secret_redactions = _scrub_secrets(text)
    text, pii_redactions = _scrub_pii(text)
    return text, secret_redactions + pii_redactions
