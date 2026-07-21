"""Upload existing session transcripts to Gleaner.

Supports every source in gleaner.sources through a unified pipeline.

Usage:
    gleaner backfill                          # Claude Code (default)
    gleaner backfill --source cursor          # Cursor sessions
    gleaner backfill --source codex           # Codex sessions
    gleaner backfill --source all             # every local source
    gleaner backfill --source codex --dry-run
    gleaner backfill --project foo            # filter by project name

Config via environment variables:
    GLEANER_URL   - Base URL of the Gleaner API
    GLEANER_TOKEN - Bearer token for authentication
"""

import argparse
import sys
from pathlib import Path

from gleaner.pipeline import finalize_metadata, upload_transcript
from gleaner.remote import GleanerClient
from gleaner.setup.config import get_credentials
from gleaner.sources import SOURCES, parser_for_ide


def _gather(source: str, project: str | None) -> list[tuple[str, str, Path, str]]:
    """Collect (session_id, project, path, ide) tuples for one or all sources."""
    names = list(SOURCES) if source == "all" else [source]
    found = []
    for name in names:
        src = SOURCES[name]
        for sid, proj, path in src.find(project):
            found.append((sid, proj, path, src.ide))
    return found


def run(
    dry_run: bool = False,
    project: str | None = None,
    force: bool = False,
    source: str = "claude",
):
    """Run the backfill for the given source."""
    url, token = get_credentials()
    if not url or not token:
        print("Error: not configured. Run 'gleaner setup URL TOKEN' first.", file=sys.stderr)
        sys.exit(1)

    sessions = _gather(source, project)
    print(f"Found {len(sessions)} {source} session(s) on disk")

    if not force:
        try:
            existing = GleanerClient(url, token).list_session_ids()
        except Exception:
            existing = set()
        sessions = [s for s in sessions if s[0] not in existing]
        print(f"{len(sessions)} new session(s) to upload")

    if dry_run:
        for sid, proj, path, ide in sessions:
            size_kb = path.stat().st_size / 1024
            print(f"  {sid[:12]}...  [{ide}]  {proj}  ({size_kb:.0f} KB)")
        return

    success = 0
    failed = 0
    skipped = 0
    for i, (sid, proj, path, ide) in enumerate(sessions, 1):
        try:
            metadata = parser_for_ide(ide)(path)
            if metadata.pop("worthless", False):
                skipped += 1
                continue
            finalize_metadata(metadata, session_id=sid, project=proj, cwd="", ide=ide)
            upload_transcript(sid, metadata, path)
            success += 1
            print(f"  [{i}/{len(sessions)}] {sid[:12]}... [{ide}] uploaded")
        except Exception as e:
            failed += 1
            print(f"  [{i}/{len(sessions)}] {sid[:12]}... FAILED: {e}")

    print(f"\nDone: {success} uploaded, {skipped} skipped (worthless), {failed} failed")


def main():
    parser = argparse.ArgumentParser(
        description="Upload existing sessions to Gleaner"
    )
    parser.add_argument("--dry-run", action="store_true", help="List without uploading")
    parser.add_argument("--project", type=str, help="Filter by project name")
    parser.add_argument("--force", action="store_true", help="Re-upload existing")
    parser.add_argument(
        "--source",
        choices=[*SOURCES, "all"],
        default="claude",
        help="Session source (default: claude)",
    )
    args = parser.parse_args()
    run(dry_run=args.dry_run, project=args.project, force=args.force, source=args.source)


if __name__ == "__main__":
    main()
