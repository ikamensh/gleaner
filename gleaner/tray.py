"""Gleaner in the macOS menu bar / Linux & Windows system tray.

    gleaner tray             run the tray icon (blocks)
    gleaner tray install     also start it at every login
    gleaner tray uninstall   stop starting it at login

The icon shows at a glance whether capture is on (green dot) or paused
(gray), and the menu offers the quick actions: toggle capture, run a
backfill now, open the dashboard.

Pure state/label logic lives at module level and is unit-tested headless;
pystray and Pillow are imported only inside run_tray(), so machines
without a display never touch them.
"""

import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from gleaner.setup import installers
from gleaner.setup.autostart import install_tray_autostart, remove_tray_autostart
from gleaner.setup.config import get_active
from gleaner.setup.sync_agent import find_script

GREEN = "#34a853"
GRAY = "#9aa0a6"


@dataclass
class TrayStatus:
    capturing: bool
    remote: str
    url: str
    last_backfill: float | None  # unix timestamp


def get_status() -> TrayStatus:
    name, remote = get_active()
    capturing = (
        installers.is_hook_installed()
        or installers.is_cursor_hook_installed()
        or installers.is_backfill_agent_installed()
    )
    log = Path.home() / ".gleaner" / "backfill.log"
    last = log.stat().st_mtime if log.exists() else None
    return TrayStatus(capturing, name, remote.get("url", ""), last)


def set_capturing(on: bool):
    """Install or remove all capture paths (both IDE hooks + sync agent)."""
    if on:
        installers.install_hook()
        installers.install_cursor_hook()
        installers.install_backfill_agent()
    else:
        installers.remove_hook()
        installers.remove_cursor_hook()
        installers.remove_backfill_agent()


def status_line(status: TrayStatus) -> str:
    state = "capturing" if status.capturing else "paused"
    if not status.remote:
        return f"Gleaner: {state} — no remote configured"
    return f"Gleaner: {state} → {status.remote}"


def sync_line(status: TrayStatus, now: float | None = None) -> str:
    if status.last_backfill is None:
        return "no backfill yet"
    age = max(0.0, (now if now is not None else time.time()) - status.last_backfill)
    if age < 90:
        return "synced just now"
    if age < 5400:
        return f"synced {round(age / 60)} min ago"
    if age < 129600:
        return f"synced {round(age / 3600)} h ago"
    return f"synced {round(age / 86400)} d ago"


def run_backfill_now():
    """Fire-and-forget backfill; it writes its own log in ~/.gleaner."""
    subprocess.Popen(
        [find_script("gleaner-backfill-quiet"), "--source", "all"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def open_dashboard():
    url = get_status().url
    if url:
        webbrowser.open(url)


def _make_image(capturing: bool):
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=GREEN if capturing else GRAY)
    draw.ellipse((24, 24, 40, 40), fill=(255, 255, 255, 230))
    return img


def run_tray():
    try:
        import pystray
    except Exception as e:  # backend selection can fail on headless machines
        raise SystemExit(
            f"tray unavailable: {e}\n"
            "On Linux this needs a desktop session (X11/Wayland; GNOME may "
            "need the AppIndicator extension)."
        )

    def on_toggle(icon, item):
        set_capturing(not get_status().capturing)
        icon.icon = _make_image(get_status().capturing)
        icon.update_menu()

    menu = pystray.Menu(
        pystray.MenuItem(lambda item: status_line(get_status()), None, enabled=False),
        pystray.MenuItem(lambda item: sync_line(get_status()), None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Capture sessions",
            on_toggle,
            checked=lambda item: get_status().capturing,
            default=True,
        ),
        pystray.MenuItem("Run backfill now", lambda icon, item: run_backfill_now()),
        pystray.MenuItem(
            "Open dashboard",
            lambda icon, item: open_dashboard(),
            enabled=lambda item: bool(get_status().url),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", lambda icon, item: icon.stop()),
    )
    icon = pystray.Icon(
        "gleaner", _make_image(get_status().capturing), title="Gleaner", menu=menu
    )
    icon.run()


def _say(message: str):
    """print() that survives windowed mode, where stdout doesn't exist."""
    if sys.stdout is not None:
        print(message)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(prog="gleaner tray", description=__doc__)
    parser.add_argument(
        "tray_action", nargs="?", choices=["run", "install", "uninstall"], default="run"
    )
    args = parser.parse_args(argv)

    if args.tray_action == "install":
        newly = install_tray_autostart()
        _say("Tray will start at login" if newly else "Tray autostart already installed")
        _say("Run 'gleaner tray' to start it right now.")
    elif args.tray_action == "uninstall":
        removed = remove_tray_autostart()
        _say("Tray autostart removed" if removed else "Tray autostart was not installed")
    else:
        run_tray()


if __name__ == "__main__":
    main()
