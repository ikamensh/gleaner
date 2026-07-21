"""The shared upload pipeline: enrich metadata, scrub, send to the server.

Every path that ships a session to the server (Claude hook, Cursor hook,
backfill) goes through finalize_metadata + upload_transcript, so the
enrichment fields and the scrub-before-upload invariant are defined once.
"""

from pathlib import Path

from gleaner.enrich import collect_provenance, tag_session
from gleaner.remote import GleanerClient
from gleaner.scrub import scrub_jsonl
from gleaner.setup.config import get_credentials


def finalize_metadata(
    metadata: dict,
    *,
    session_id: str,
    project: str,
    cwd: str,
    ide: str,
    aborted: bool = False,
    has_errors: bool = False,
    source_override: str = "",
) -> dict:
    """Add identity, classification, and status fields to parsed metadata.

    `source_override` (e.g. from CLAUDE_SESSION_SOURCE set by an orchestrator)
    beats the heuristic classification; hooks pass it for the live session,
    backfill does not because old sessions predate the current environment.
    """
    metadata["cwd"] = cwd
    metadata["session_id"] = session_id
    metadata["project"] = project
    tags = tag_session(project, metadata.get("topic", ""), collect_provenance()["host"], cwd, ide=ide)
    metadata["source"] = source_override or tags["source"]
    metadata["task_type"] = tags["task_type"]
    metadata["ide"] = ide
    metadata["aborted"] = aborted
    metadata["has_errors"] = has_errors
    return metadata


def upload_transcript(session_id: str, metadata: dict, transcript_path: Path):
    """Scrub a transcript and upload it with its metadata to the Gleaner server."""
    url, token = get_credentials()

    text = transcript_path.read_bytes().decode("utf-8")
    # JSONL-aware so scrubbing never breaks the transcript's JSON structure
    # (Codex rollouts carry bare-int epoch fields that plain text scrubbing
    # would mangle into invalid JSON).
    scrubbed, stats = scrub_jsonl(text)
    if stats.redactions:
        metadata["redactions"] = stats.redactions

    client = GleanerClient(url, token)
    client.upload_session(
        session_id, metadata, scrubbed.encode("utf-8"), collect_provenance()
    )
