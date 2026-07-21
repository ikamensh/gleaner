"""Redaction markers and regex patterns shared by the scrub backends."""

import re

REDACTED = "[secret-redacted]"
PII_REDACTED = "[pii-redacted]"

SECRET_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    (?P<prefix>
        (?:["'])?
        (?P<key>[a-z0-9_.-]*(?:api[_-]?key|secret|token|password|passwd|private[_-]?key|access[_-]?key)[a-z0-9_.-]*)
        (?:["'])?
        \s*(?P<sep>=|:)\s*
    )
    (?P<quote>["'])?
    (?P<value>[^"',\s}]+)
    (?P=quote)?
    """
)

PEM_BLOCK_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]+(?:PRIVATE KEY|KEY BLOCK)-----"
    r"[\s\S]*?"
    r"-----END [A-Z0-9 ]+(?:PRIVATE KEY|KEY BLOCK)-----"
)
