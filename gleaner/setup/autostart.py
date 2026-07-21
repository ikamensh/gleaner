"""Start `gleaner tray` at login.

Per-OS login items behind one contract, mirroring sync_agent:

    install_tray_autostart() -> bool   # newly registered?
    remove_tray_autostart() -> bool    # was it registered?
    is_tray_autostart_installed() -> bool

macOS    launchd agent   ~/Library/LaunchAgents/<name>.plist (RunAtLoad)
Linux    XDG autostart   ~/.config/autostart/<name>.desktop
Windows  HKCU Run key    value <name>, running the windowed gleaner-tray

GLEANER_TRAY_NAME overrides the registered name so tests can operate on a
throwaway entry without touching a real installation.
"""

import os
import plistlib
import sys
from pathlib import Path

from gleaner.setup.sync_agent import _run_quiet, find_script

_WIN_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _tray_name(default: str) -> str:
    return os.environ.get("GLEANER_TRAY_NAME") or default


# -- macOS: launchd ------------------------------------------------------------


def _plist_path() -> Path:
    label = _tray_name("com.gleaner.tray")
    return Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"


def _launchd_install() -> bool:
    plist_path = _plist_path()
    if plist_path.exists():
        return False
    plist = {
        "Label": plist_path.stem,
        "ProgramArguments": [find_script("gleaner"), "tray"],
        "RunAtLoad": True,
    }
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_bytes(plistlib.dumps(plist))
    _run_quiet("launchctl", "load", str(plist_path))
    return True


def _launchd_remove() -> bool:
    plist_path = _plist_path()
    if not plist_path.exists():
        return False
    _run_quiet("launchctl", "unload", str(plist_path))
    plist_path.unlink()
    return True


# -- Linux: XDG autostart --------------------------------------------------------


def _desktop_path() -> Path:
    name = _tray_name("gleaner-tray")
    return Path.home() / ".config" / "autostart" / f"{name}.desktop"


def _xdg_install() -> bool:
    desktop = _desktop_path()
    if desktop.exists():
        return False
    desktop.parent.mkdir(parents=True, exist_ok=True)
    desktop.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Gleaner\n"
        "Comment=Coding-agent session capture\n"
        f'Exec="{find_script("gleaner")}" tray\n'
        "X-GNOME-Autostart-enabled=true\n"
    )
    return True


def _xdg_remove() -> bool:
    desktop = _desktop_path()
    if not desktop.exists():
        return False
    desktop.unlink()
    return True


# -- Windows: HKCU Run key --------------------------------------------------------


def _win_value_name() -> str:
    return _tray_name("GleanerTray")


def _win_query() -> bool:
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WIN_RUN_KEY) as key:
        try:
            winreg.QueryValueEx(key, _win_value_name())
            return True
        except FileNotFoundError:
            return False


def _win_install() -> bool:
    import winreg

    if _win_query():
        return False
    # gleaner-tray is a gui-script: windowed, so login doesn't flash a console.
    command = f'"{find_script("gleaner-tray")}"'
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _WIN_RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, _win_value_name(), 0, winreg.REG_SZ, command)
    return True


def _win_remove() -> bool:
    import winreg

    if not _win_query():
        return False
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _WIN_RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.DeleteValue(key, _win_value_name())
    return True


# -- Dispatch ---------------------------------------------------------------------


def install_tray_autostart() -> bool:
    if sys.platform == "darwin":
        return _launchd_install()
    if sys.platform.startswith("linux"):
        return _xdg_install()
    if sys.platform == "win32":
        return _win_install()
    raise NotImplementedError(f"no tray autostart backend for {sys.platform}")


def remove_tray_autostart() -> bool:
    if sys.platform == "darwin":
        return _launchd_remove()
    if sys.platform.startswith("linux"):
        return _xdg_remove()
    if sys.platform == "win32":
        return _win_remove()
    raise NotImplementedError(f"no tray autostart backend for {sys.platform}")


def is_tray_autostart_installed() -> bool:
    if sys.platform == "darwin":
        return _plist_path().exists()
    if sys.platform.startswith("linux"):
        return _desktop_path().exists()
    if sys.platform == "win32":
        return _win_query()
    raise NotImplementedError(f"no tray autostart backend for {sys.platform}")
