"""Cross-OS contract for gleaner's install surface.

gleaner must install and uninstall cleanly on macOS, Linux, and Windows:

- `gleaner setup` / `on` / `off` exit 0 on every OS — no launchctl crashes
  outside macOS.
- The periodic sync agent registers with the *native* scheduler:
  launchd (macOS), a systemd user timer (Linux), Task Scheduler (Windows).
- `is_backfill_agent_installed()` tells the truth on every OS: False before
  install, True after install, False after remove.
- Installing never leaves foreign-OS artifacts (no ~/Library/LaunchAgents
  on Linux or Windows).
- IDE hooks are registered with an absolute path to an existing executable,
  because GUI-launched IDEs don't inherit the shell PATH that `uv tool
  install` relies on.

CLI tests run in a subprocess with HOME/USERPROFILE redirected to a temp
dir and GLEANER_SYNC_NAME set to a throwaway per-test name, so they never
disturb a real gleaner installation on the machine running them.
"""

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

import gleaner.setup.installers as installers
import gleaner.setup.sync_agent as sync_agent

DEAD_URL = "http://127.0.0.1:9"  # connection refused instantly; whoami returns None


def _run(argv, home: Path, sync_name: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)  # Path.home() on Windows
    env["GLEANER_SYNC_NAME"] = sync_name
    for var in ("GLEANER_URL", "GLEANER_TOKEN", "GLEANER_REMOTE"):
        env.pop(var, None)
    return subprocess.run(
        [sys.executable, *argv], capture_output=True, text=True, env=env, timeout=120
    )


def run_cli(*args, home: Path, sync_name: str) -> subprocess.CompletedProcess:
    return _run(["-m", "gleaner.cli", *args], home=home, sync_name=sync_name)


def agent_installed(home: Path, sync_name: str) -> bool:
    """What gleaner itself believes, evaluated under the fake home."""
    result = _run(
        ["-c", "from gleaner.setup.installers import is_backfill_agent_installed; "
               "print(is_backfill_agent_installed())"],
        home=home,
        sync_name=sync_name,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip() == "True"


def native_registration_exists(home: Path, sync_name: str) -> bool:
    """Ground truth: is the backfill registered with the OS scheduler?

    Checked independently of gleaner's own accounting, so a lying
    is_backfill_agent_installed() can't make both sides agree.
    """
    if sys.platform == "darwin":
        agents = home / "Library" / "LaunchAgents"
        return any(agents.glob("*gleaner*.plist")) if agents.exists() else False
    if sys.platform.startswith("linux"):
        units = home / ".config" / "systemd" / "user"
        if not units.exists():
            return False
        return any(units.glob("*gleaner*.timer")) and any(units.glob("*gleaner*.service"))
    if sys.platform == "win32":
        rc = subprocess.run(
            ["schtasks", "/Query", "/TN", sync_name], capture_output=True
        ).returncode
        return rc == 0
    raise NotImplementedError(f"unsupported platform: {sys.platform}")


@pytest.fixture
def fake_home(tmp_path):
    """Isolated home + per-test sync name; tears down any real scheduler
    registrations the test created, even on assertion failure."""
    sync_name = f"com.gleaner.test-{uuid.uuid4().hex[:8]}"
    yield tmp_path, sync_name
    if sys.platform == "darwin":
        agents = tmp_path / "Library" / "LaunchAgents"
        if agents.exists():
            for plist in agents.glob("*.plist"):
                subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    elif sys.platform.startswith("linux"):
        subprocess.run(
            ["systemctl", "--user", "disable", "--now", f"{sync_name}.timer"],
            capture_output=True,
        )
    elif sys.platform == "win32":
        subprocess.run(
            ["schtasks", "/Delete", "/F", "/TN", sync_name], capture_output=True
        )


class TestCliLifecycle:
    """gleaner setup / on / off must work natively on every supported OS."""

    def test_setup_exits_zero(self, fake_home):
        """`gleaner setup` is the first command every user runs; it must
        succeed on macOS, Linux, and Windows alike."""
        home, name = fake_home
        result = run_cli("setup", DEAD_URL, "gl_test", home=home, sync_name=name)
        assert result.returncode == 0, result.stderr
        assert "Traceback" not in result.stderr

    def test_setup_registers_native_scheduler(self, fake_home):
        """After setup, the periodic backfill is registered with the
        scheduler this OS actually has — not just claimed."""
        home, name = fake_home
        run_cli("setup", DEAD_URL, "gl_test", home=home, sync_name=name)
        assert native_registration_exists(home, name)

    def test_on_off_roundtrip_is_truthful(self, fake_home):
        """on → installed; off → gone, both in gleaner's accounting and in
        the OS scheduler. `gleaner status` derives from the same call, so
        this is also the 'status never lies' test."""
        home, name = fake_home

        on = run_cli("on", home=home, sync_name=name)
        assert on.returncode == 0, on.stderr
        assert agent_installed(home, name)
        assert native_registration_exists(home, name)

        off = run_cli("off", home=home, sync_name=name)
        assert off.returncode == 0, off.stderr
        assert not agent_installed(home, name)
        assert not native_registration_exists(home, name)

    @pytest.mark.skipif(sys.platform == "darwin", reason="~/Library is native here")
    def test_no_mac_artifacts_on_other_oses(self, fake_home):
        """Setup on Linux/Windows must not plant launchd leftovers that make
        is_backfill_agent_installed() report a phantom agent forever."""
        home, name = fake_home
        run_cli("setup", DEAD_URL, "gl_test", home=home, sync_name=name)
        assert not (home / "Library").exists()


def _command_path(command: str) -> Path:
    """First token of a hook command line, unquoting if needed."""
    if command.startswith('"'):
        return Path(command[1 : command.index('"', 1)])
    return Path(command.split()[0])


class TestHookCommandsResolvable:
    """Hooks must survive GUI-launched IDEs.

    Cursor (and Claude Code started outside a terminal) runs hooks without
    the user's shell PATH, so `~/.local/bin/gleaner-upload` is not findable
    by bare name. The installed hook command must therefore be an absolute
    path to an existing executable. These pass once install writes resolved
    paths; they are PATH-independent, so they hold on any machine where the
    gleaner scripts are installed at all.
    """

    @pytest.fixture(autouse=True)
    def isolated_settings(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            installers, "CLAUDE_SETTINGS", tmp_path / ".claude" / "settings.json"
        )
        monkeypatch.setattr(
            installers, "CURSOR_HOOKS", tmp_path / ".cursor" / "hooks.json"
        )

    def test_claude_hook_is_absolute_existing_path(self):
        installers.install_hook()
        settings = installers.read_claude_settings()
        (group,) = settings["hooks"]["SessionEnd"]
        (hook,) = group["hooks"]
        path = _command_path(hook["command"])
        assert path.is_absolute(), f"hook command not absolute: {hook['command']}"
        assert path.exists(), f"hook command does not exist: {path}"

    def test_cursor_hook_is_absolute_existing_path(self):
        installers.install_cursor_hook()
        cfg = installers.read_cursor_hooks()
        (entry,) = cfg["hooks"]["stop"]
        path = _command_path(entry["command"])
        assert path.is_absolute(), f"hook command not absolute: {entry['command']}"
        assert path.exists(), f"hook command does not exist: {path}"


class _FakeScheduler:
    """Records scheduler commands instead of running them; emulates enough
    schtasks state (create/query/delete by /TN) for lifecycle tests."""

    def __init__(self):
        self.calls: list[tuple[str, ...]] = []
        self.tasks: set[str] = set()

    def __call__(self, *argv: str) -> bool:
        self.calls.append(argv)
        if argv[0] != "schtasks":
            return True
        action, name = argv[1], argv[argv.index("/TN") + 1]
        if action == "/Query":
            return name in self.tasks
        if action == "/Create":
            self.tasks.add(name)
            return True
        if action == "/Delete":
            self.tasks.discard(name)
            return True
        return True


@pytest.fixture
def unit_home(tmp_path, monkeypatch):
    """In-process fake home + name seam, scheduler commands stubbed.

    sync_agent computes every path lazily from Path.home(), so redirecting
    HOME/USERPROFILE is enough — no module constants to patch.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("GLEANER_SYNC_NAME", "com.gleaner.unittest")
    fake = _FakeScheduler()
    monkeypatch.setattr(sync_agent, "_run_quiet", fake)
    return tmp_path, fake


class TestSchedulerBackends:
    """Content checks for what each backend registers.

    The registration must survive reboots and point at an absolute
    executable, because schedulers run with a minimal PATH.
    """

    def test_lifecycle_roundtrip(self, unit_home):
        """Install/remove invariants hold on whichever OS runs this."""
        assert sync_agent.install_backfill_agent() is True
        assert sync_agent.is_backfill_agent_installed() is True
        assert sync_agent.install_backfill_agent() is False  # idempotent
        assert sync_agent.remove_backfill_agent() is True
        assert sync_agent.is_backfill_agent_installed() is False
        assert sync_agent.remove_backfill_agent() is False

    @pytest.mark.skipif(sys.platform != "darwin", reason="launchd backend")
    def test_launchd_plist_content(self, unit_home):
        import plistlib

        home, fake = unit_home
        sync_agent.install_backfill_agent()
        plist_path = home / "Library" / "LaunchAgents" / "com.gleaner.unittest.plist"
        plist = plistlib.loads(plist_path.read_bytes())
        assert plist["Label"] == "com.gleaner.unittest"
        cmd = Path(plist["ProgramArguments"][0])
        assert cmd.is_absolute() and cmd.exists()
        assert plist["ProgramArguments"][1:] == ["--source", "all"]
        assert plist["StartInterval"] == sync_agent.BACKFILL_INTERVAL
        assert plist["RunAtLoad"] is True
        assert ("launchctl", "load", str(plist_path)) in fake.calls

    @pytest.mark.skipif(not sys.platform.startswith("linux"), reason="systemd backend")
    def test_systemd_unit_content(self, unit_home):
        home, fake = unit_home
        sync_agent.install_backfill_agent()
        units = home / ".config" / "systemd" / "user"
        service = (units / "com.gleaner.unittest.service").read_text()
        timer = (units / "com.gleaner.unittest.timer").read_text()

        exec_line = next(l for l in service.splitlines() if l.startswith("ExecStart="))
        cmd = Path(exec_line.removeprefix('ExecStart="').split('"')[0])
        assert cmd.is_absolute() and cmd.exists()
        assert exec_line.endswith("--source all")
        assert f"OnUnitActiveSec={sync_agent.BACKFILL_INTERVAL}" in timer
        assert "WantedBy=timers.target" in timer
        assert "Unit=com.gleaner.unittest.service" in timer
        assert ("systemctl", "--user", "enable", "--now", "com.gleaner.unittest.timer") in fake.calls

    @pytest.mark.skipif(sys.platform != "win32", reason="schtasks backend")
    def test_schtasks_registration(self, unit_home):
        home, fake = unit_home
        sync_agent.install_backfill_agent()
        create = next(c for c in fake.calls if c[:2] == ("schtasks", "/Create"))
        args = dict(zip(create, create[1:]))
        assert args["/TN"] == "com.gleaner.unittest"
        assert args["/SC"] == "MINUTE"
        assert int(args["/MO"]) == sync_agent.BACKFILL_INTERVAL // 60
        command = args["/TR"]
        assert command.endswith(" --source all")
        exe = Path(command[1 : command.index('"', 1)])
        assert exe.is_absolute() and exe.exists()
