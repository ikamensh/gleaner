"""Local storage: the session vault at ~/.gleaner/."""

from gleaner.vault.schema import NormalizedEntry, SessionMeta
from gleaner.vault.store import (
    VAULT_DIR,
    collect,
    ingest_session,
    normalize_entry,
    update_index,
)

__all__ = [
    "NormalizedEntry",
    "SessionMeta",
    "VAULT_DIR",
    "collect",
    "ingest_session",
    "normalize_entry",
    "update_index",
]
