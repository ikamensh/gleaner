"""Rebuild counter documents from all existing sessions in Firestore.

Run once after deploying the counter-based stats, or any time counters
get out of sync. Safe to re-run — it overwrites counters from scratch.

Replays the same per-session deltas (backend.stats.counter_deltas) that
store_session applies incrementally, so a rebuild always matches what the
live path would have produced.

Usage:
    python ops/backfill_counters.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from backend import db, stats


def build_counters_from_sessions() -> dict:
    """Scan all sessions and replay the counter deltas from scratch.

    Returns {counter_doc_name: doc} ready to write.
    """
    print("Scanning sessions...", flush=True)
    sessions = []
    for doc in db._db().collection("sessions").stream():
        sessions.append({**(doc.to_dict() or {}), "session_id": doc.id})
        if len(sessions) % 50 == 0:
            print(f"  {len(sessions)} sessions fetched...", flush=True)

    # Oldest first, so last_active/last_session_id land on the newest session.
    counters: dict = {}
    for data in sorted(sessions, key=lambda s: s.get("first_timestamp") or ""):
        deltas = stats.counter_deltas(data["session_id"], data, data.get("provenance", {}))
        stats.apply_deltas(counters, deltas)

    n_users = len(counters.get("global:users", {}))
    n_projects = len(counters.get("global:projects", {}))
    print(f"Scanned {len(sessions)} sessions, {n_users} users, {n_projects} projects")
    return counters


def write_counters(counters: dict, dry_run: bool = False):
    """Write counter docs to Firestore (one doc per counters key)."""
    if dry_run:
        g = counters.get("global", {})
        print(f"\n[DRY RUN] Would write counters with {g.get('total_sessions', 0)} sessions:")
        for doc_name, doc in counters.items():
            print(f"  counters/{doc_name} ({len(doc)} fields)")
        return

    col = db._db().collection("counters")
    for doc_name, doc in counters.items():
        print(f"Writing counters/{doc_name}...", flush=True)
        col.document(doc_name).set(doc)
    print("Done.")


def main():
    parser = argparse.ArgumentParser(description="Rebuild counter docs from existing sessions")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written without writing")
    args = parser.parse_args()

    counters = build_counters_from_sessions()
    write_counters(counters, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
