"""Register the periodic backfill with the OS-native scheduler.

One backend per OS behind a single contract:

    install_backfill_agent() -> bool   # newly registered?
    remove_backfill_agent() -> bool    # was it registered?
    is_backfill_agent_installed() -> bool

macOS    launchd agent        ~/Library/LaunchAgents/<name>.plist
Linux    systemd user timer   ~/.config/systemd/user/<name>.{service,timer}
Windows  Task Scheduler job   schtasks, task name <name>

The agent runs `gleaner-backfill --source all` every BACKFILL_INTERVAL
seconds. Codex has no realtime hook, so this is its primary auto-store
path; for Claude/Cursor it is a safety net behind their session hooks.
Re-uploads are idempotent server-side, so repeats never double-count.

Activation commands (launchctl/systemctl) are best-effort: on macOS and
Linux the unit files on disk are the source of truth for is_installed, so
a machine without a reachable user service manager (headless CI, WSL
without systemd) still gets valid units that activate on next login. On
Windows, schtasks itself is the source of truth.

GLEANER_SYNC_NAME overrides the registered name so tests can operate on a
throwaway agent without touching a real installation.
"""

import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

BACKFILL_INTERVAL = 300  # seconds
# Older single-source agent labels to clean up on (un)install.
_LEGACY_LAUNCHD_LABELS = ["com.gleaner.cursor-backfill"]


def find_script(name: str) -> str:
    """Absolute path of a gleaner console script.

    Prefers the environment that is running right now (a sibling of the
    current interpreter), so hooks and agents point at the same
    installation that performed the setup — not at a stale shim that
    happens to shadow it on PATH.
    """
    scripts_dir = Path(sys.executable).parent
    for candidate in (scripts_dir / name, scripts_dir / f"{name}.exe"):
        if candidate.exists():
            return str(candidate)
    return shutil.which(name) or name


def _sync_name(default: str) -> str:
    return os.environ.get("GLEANER_SYNC_NAME") or default


def _log_file() -> Path:
    log_dir = Path.home() / ".gleaner"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "backfill.log"


def _run_quiet(*argv: str) -> bool:
    """Run a scheduler command, tolerating a missing binary or dead bus."""
    try:
        return subprocess.run(argv, capture_output=True).returncode == 0
    except OSError:
        return False


# -- macOS: launchd --------------------------------------------------------


def _plist_path() -> Path:
    label = _sync_name("com.gleaner.sync")
    return Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"


def _remove_legacy_agents():
    for label in _LEGACY_LAUNCHD_LABELS:
        plist = _plist_path().parent / f"{label}.plist"
        if plist.exists():
            _run_quiet("launchctl", "unload", str(plist))
            plist.unlink()


def _launchd_install() -> bool:
    _remove_legacy_agents()
    plist_path = _plist_path()
    if plist_path.exists():
        return False
    plist = {
        "Label": plist_path.stem,
        "ProgramArguments": [find_script("gleaner-backfill"), "--source", "all"],
        "StartInterval": BACKFILL_INTERVAL,
        "StandardOutPath": str(_log_file()),
        "StandardErrorPath": str(_log_file()),
        "RunAtLoad": True,
    }
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_bytes(plistlib.dumps(plist))
    _run_quiet("launchctl", "load", str(plist_path))
    return True


def _launchd_remove() -> bool:
    plist_path = _plist_path()
    existed = plist_path.exists()
    if existed:
        _run_quiet("launchctl", "unload", str(plist_path))
        plist_path.unlink()
    _remove_legacy_agents()
    return existed


# -- Linux: systemd user timer ----------------------------------------------


def _unit_paths() -> tuple[Path, Path]:
    name = _sync_name("gleaner-backfill")
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    return unit_dir / f"{name}.service", unit_dir / f"{name}.timer"


def _systemd_install() -> bool:
    service, timer = _unit_paths()
    if service.exists() and timer.exists():
        return False
    log = _log_file()
    service.parent.mkdir(parents=True, exist_ok=True)
    service.write_text(
        "[Unit]\n"
        "Description=Gleaner backfill: upload local coding-agent sessions\n"
        "\n"
        "[Service]\n"
        "Type=oneshot\n"
        f'ExecStart="{find_script("gleaner-backfill")}" --source all\n'
        f"StandardOutput=append:{log}\n"
        f"StandardError=append:{log}\n"
    )
    timer.write_text(
        "[Unit]\n"
        f"Description=Run gleaner backfill every {BACKFILL_INTERVAL} seconds\n"
        "\n"
        "[Timer]\n"
        "OnBootSec=120\n"
        f"OnUnitActiveSec={BACKFILL_INTERVAL}\n"
        f"Unit={service.name}\n"
        "\n"
        "[Install]\n"
        "WantedBy=timers.target\n"
    )
    _run_quiet("systemctl", "--user", "daemon-reload")
    _run_quiet("systemctl", "--user", "enable", "--now", timer.name)
    return True


def _systemd_remove() -> bool:
    service, timer = _unit_paths()
    existed = service.exists() or timer.exists()
    if existed:
        _run_quiet("systemctl", "--user", "disable", "--now", timer.name)
        for unit in (service, timer):
            if unit.exists():
                unit.unlink()
        _run_quiet("systemctl", "--user", "daemon-reload")
    return existed


# -- Windows: Task Scheduler -------------------------------------------------


def _task_name() -> str:
    return _sync_name("GleanerBackfill")


def _schtasks_query() -> bool:
    return _run_quiet("schtasks", "/Query", "/TN", _task_name())


def _schtasks_install() -> bool:
    if _schtasks_query():
        return False
    # gleaner-backfill-quiet is a gui-script: windowed on Windows, so the
    # scheduled run doesn't flash a console; it logs to ~/.gleaner itself.
    command = f'"{find_script("gleaner-backfill-quiet")}" --source all'
    created = _run_quiet(
        "schtasks", "/Create", "/F",
        "/SC", "MINUTE", "/MO", str(max(1, BACKFILL_INTERVAL // 60)),
        "/TN", _task_name(), "/TR", command,
    )
    if not created:
        raise RuntimeError("schtasks /Create failed — could not register the Gleaner sync task")
    return True


def _schtasks_remove() -> bool:
    if not _schtasks_query():
        return False
    return _run_quiet("schtasks", "/Delete", "/F", "/TN", _task_name())


# -- Dispatch -----------------------------------------------------------------


def install_backfill_agent() -> bool:
    if sys.platform == "darwin":
        return _launchd_install()
    if sys.platform.startswith("linux"):
        return _systemd_install()
    if sys.platform == "win32":
        return _schtasks_install()
    raise NotImplementedError(f"no sync scheduler backend for {sys.platform}")


def remove_backfill_agent() -> bool:
    if sys.platform == "darwin":
        return _launchd_remove()
    if sys.platform.startswith("linux"):
        return _systemd_remove()
    if sys.platform == "win32":
        return _schtasks_remove()
    raise NotImplementedError(f"no sync scheduler backend for {sys.platform}")


def is_backfill_agent_installed() -> bool:
    if sys.platform == "darwin":
        return _plist_path().exists()
    if sys.platform.startswith("linux"):
        service, timer = _unit_paths()
        return service.exists() and timer.exists()
    if sys.platform == "win32":
        return _schtasks_query()
    raise NotImplementedError(f"no sync scheduler backend for {sys.platform}")
