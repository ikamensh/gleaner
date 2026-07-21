"""Gleaner CLI: setup, status, and hook management.

Usage:
    gleaner setup URL TOKEN    Configure and install the session hook
    gleaner status             Show current configuration
    gleaner on                 Enable the session upload hook
    gleaner off                Disable the session upload hook
    gleaner auth TOKEN         Update the API token
    gleaner remote ...         Manage server instances (list/add/use/remove/show)
    gleaner backfill           Upload existing sessions
"""

import argparse
import os
import sys

from gleaner.remote import GleanerClient
from gleaner.setup.config import (
    CONFIG_FILE,
    add_remote,
    get_active,
    get_credentials,
    list_remotes,
    remove_remote,
    use_remote,
    write_config,
)
from gleaner.setup.installers import (
    CLAUDE_SETTINGS,
    CURSOR_HOOKS,
    install_backfill_agent,
    install_cursor_hook,
    install_hook,
    is_backfill_agent_installed,
    is_cursor_hook_installed,
    is_hook_installed,
    remove_backfill_agent,
    remove_cursor_hook,
    remove_hook,
)


def cmd_setup(args):
    add_remote(args.name, args.url, args.token, activate=True)
    print(f"  Config  remote '{args.name}' saved to {CONFIG_FILE}")

    if install_hook():
        print(f"  Claude  hook installed in {CLAUDE_SETTINGS}")
    else:
        print(f"  Claude  hook already in {CLAUDE_SETTINGS}")

    if install_cursor_hook():
        print(f"  Cursor  hook installed in {CURSOR_HOOKS}")
    else:
        print(f"  Cursor  hook already in {CURSOR_HOOKS}")

    if install_backfill_agent():
        print(f"  Sync    backfill agent started — codex + cursor + claude (every 5 min)")
    else:
        print(f"  Sync    backfill agent already running")

    user = GleanerClient(args.url, args.token).whoami()
    if user:
        print(f"  Auth    connected as {user}")
    else:
        print(f"  Auth    could not verify — check URL and token")

    print("\nDone. New sessions will upload automatically.")


def cmd_status(args):
    url, token = get_credentials()
    active, _ = get_active()

    print("Gleaner\n")

    if CONFIG_FILE.exists():
        print(f"  Config  {CONFIG_FILE}")
    else:
        src = "env" if url else "not configured"
        print(f"  Config  {src}")

    print(f"  Remote  {active or '—'}")
    print(f"  URL     {url or '—'}")
    print(f"  Token   {token[:8]}..." if token else "  Token   —")
    print(f"  Claude  hook {'enabled' if is_hook_installed() else 'disabled'}")
    print(f"  Cursor  hook {'enabled' if is_cursor_hook_installed() else 'disabled'}")
    print(f"  Sync    {'running' if is_backfill_agent_installed() else 'stopped'}")

    if url and token:
        user = GleanerClient(url, token).whoami()
        print(f"  Auth    {user}" if user else "  Auth    failed")

    others = [n for n in list_remotes() if n != active]
    if others:
        print(f"\n  Other remotes: {', '.join(others)}  (switch with 'gleaner remote use NAME')")
    print()


def cmd_on(args):
    claude_new = install_hook()
    cursor_new = install_cursor_hook()
    backfill_new = install_backfill_agent()
    if claude_new or cursor_new or backfill_new:
        print("Hooks enabled")
    else:
        print("Hooks already enabled")


def cmd_off(args):
    claude_removed = remove_hook()
    cursor_removed = remove_cursor_hook()
    backfill_removed = remove_backfill_agent()
    if claude_removed or cursor_removed or backfill_removed:
        print("Hooks disabled")
    else:
        print("Hooks not installed")


def cmd_auth(args):
    name, remote = get_active()
    url = remote.get("url", "")
    if not url:
        print("Run 'gleaner setup URL TOKEN' first", file=sys.stderr)
        sys.exit(1)
    add_remote(name, url, args.token, activate=True)
    print(f"Token updated for remote '{name}' ({args.token[:8]}...)")

    user = GleanerClient(url, args.token).whoami()
    if user:
        print(f"Connected as {user}")
    else:
        print("Could not verify — check the token")


def cmd_remote(args):
    action = args.remote_action

    if action == "list":
        remotes = list_remotes()
        if not remotes:
            print("No remotes configured. Add one with 'gleaner remote add NAME URL TOKEN'.")
            return
        active, _ = get_active()
        for name, r in remotes.items():
            mark = "*" if name == active else " "
            print(f"{mark} {name:<12} {r.get('url', '')}")
        return

    if action == "add":
        add_remote(args.name, args.url, args.token, activate=not args.no_activate)
        is_active = get_active()[0] == args.name
        print(f"Remote '{args.name}' " + ("added and active" if is_active else "added (inactive)"))
        user = GleanerClient(args.url, args.token).whoami()
        print(f"Connected as {user}" if user else "Could not verify — check URL and token")
        return

    if action == "use":
        if use_remote(args.name):
            print(f"Active remote is now '{args.name}'")
        else:
            print(f"No remote named '{args.name}'", file=sys.stderr)
            sys.exit(1)
        return

    if action == "remove":
        if remove_remote(args.name):
            active, _ = get_active()
            print(f"Removed remote '{args.name}'" + (f"; active is now '{active}'" if active else ""))
        else:
            print(f"No remote named '{args.name}'", file=sys.stderr)
            sys.exit(1)
        return

    if action == "show":
        remotes = list_remotes()
        name = args.name or get_active()[0]
        if not name or name not in remotes:
            print(f"No remote named '{name}'" if name else "No active remote", file=sys.stderr)
            sys.exit(1)
        r = remotes[name]
        print(f"Remote  {name}")
        print(f"URL     {r.get('url', '')}")
        token = r.get("token", "")
        print(f"Token   {token[:8]}..." if token else "Token   —")
        user = GleanerClient(r.get("url", ""), token).whoami()
        print(f"Auth    {user}" if user else "Auth    failed")
        return


def cmd_serve(args):
    if not args.no_collect:
        from gleaner.vault import collect

        added = collect()
        if added:
            print(f"Collected {added} new sessions")

    import uvicorn

    os.environ["GLEANER_LOCAL"] = "1"
    print(f"Starting local dashboard at http://127.0.0.1:{args.port}")
    uvicorn.run("server.server:app", host="127.0.0.1", port=args.port)


def cmd_collect(args):
    from gleaner.vault import VAULT_DIR, collect

    added = collect()
    index = VAULT_DIR / "index.parquet"
    total = 0
    if index.exists():
        import pyarrow.parquet as pq

        total = pq.read_metadata(index).num_rows
    if added:
        print(f"Collected {added} new sessions (total: {total})")
    else:
        print(f"Up to date ({total} sessions)")


def cmd_tray(args):
    from gleaner.tray import main as tray_main

    tray_main([args.tray_action])


def cmd_backfill(args):
    from gleaner.backfill import run

    run(dry_run=args.dry_run, project=args.project, force=args.force, source=args.source)


def cmd_pull(args):
    from gleaner.pull import run

    run(output=args.output, transcripts=args.transcripts, workers=args.workers)


def main():
    parser = argparse.ArgumentParser(prog="gleaner", description="Gleaner CLI")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("setup", help="Configure Gleaner and install the session hook")
    p.add_argument("url", help="Gleaner server URL")
    p.add_argument("token", help="API token (gl_...)")
    p.add_argument("--name", default="default", help="Remote name (default: default)")

    rp = sub.add_parser("remote", help="Manage Gleaner server instances (remotes)")
    ra = rp.add_subparsers(dest="remote_action", required=True)
    ra.add_parser("list", help="List configured remotes")
    a = ra.add_parser("add", help="Add or replace a remote")
    a.add_argument("name", help="Remote name")
    a.add_argument("url", help="Gleaner server URL")
    a.add_argument("token", help="API token (gl_...)")
    a.add_argument("--no-activate", action="store_true", help="Add without making it active")
    a = ra.add_parser("use", help="Switch the active remote")
    a.add_argument("name", help="Remote name")
    a = ra.add_parser("remove", help="Delete a remote")
    a.add_argument("name", help="Remote name")
    a = ra.add_parser("show", help="Show a remote's URL and connection status")
    a.add_argument("name", nargs="?", help="Remote name (default: active)")

    sub.add_parser("status", help="Show configuration status")
    sub.add_parser("on", help="Enable the session upload hook")
    sub.add_parser("off", help="Disable the session upload hook")

    p = sub.add_parser("auth", help="Update the API token")
    p.add_argument("token", help="New API token (gl_...)")

    p = sub.add_parser("backfill", help="Upload existing sessions to Gleaner")
    p.add_argument("--dry-run", action="store_true", help="List without uploading")
    p.add_argument("--project", type=str, help="Filter by project name")
    p.add_argument("--force", action="store_true", help="Re-upload existing")
    p.add_argument(
        "--source",
        choices=["claude", "cursor", "codex", "all"],
        default="claude",
        help="Session source (default: claude)",
    )

    sub.add_parser("collect", help="Collect local IDE sessions into the vault")

    p = sub.add_parser("tray", help="Menu bar / system tray app (status + on/off)")
    p.add_argument(
        "tray_action",
        nargs="?",
        choices=["run", "install", "uninstall"],
        default="run",
        help="run (default), install/uninstall start-at-login",
    )

    p = sub.add_parser("serve", help="Start local dashboard")
    p.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    p.add_argument("--no-collect", action="store_true", help="Skip session collection on startup")

    p = sub.add_parser("pull", help="Download sessions for local analysis")
    p.add_argument("-o", "--output", help="Output directory (default: ~/.gleaner)")
    p.add_argument("--transcripts", action="store_true", help="Also download raw transcripts")
    p.add_argument("-j", "--workers", type=int, default=4, help="Parallel downloads")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "setup": cmd_setup,
        "status": cmd_status,
        "on": cmd_on,
        "off": cmd_off,
        "auth": cmd_auth,
        "remote": cmd_remote,
        "tray": cmd_tray,
        "serve": cmd_serve,
        "collect": cmd_collect,
        "backfill": cmd_backfill,
        "pull": cmd_pull,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
