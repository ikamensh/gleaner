"""Tray model + login-item registration, tested headless.

pystray is deliberately never imported here: these tests cover the pure
state and label logic behind the tray menu, and the per-OS autostart
backends. So they run on every CI OS without a display. On Windows the
autostart tests write a throwaway value to the real HKCU Run key and
clean it up; on macOS/Linux everything lands in a redirected fake home.
"""

import sys
import uuid
from pathlib import Path

import pytest

import gleaner.setup.autostart as autostart
import gleaner.setup.config as config
import gleaner.setup.installers as installers
import gleaner.setup.sync_agent as sync_agent
import gleaner.tray as tray
from conftest import FakeScheduler


@pytest.fixture
def capture_env(tmp_path, monkeypatch):
    """Everything the tray touches, redirected: config, hook files, and the
    sync agent (lazy Path.home() + name seam), scheduler commands stubbed."""
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "gleaner.json")
    monkeypatch.setattr(installers, "CLAUDE_SETTINGS", tmp_path / ".claude" / "settings.json")
    monkeypatch.setattr(installers, "CURSOR_HOOKS", tmp_path / ".cursor" / "hooks.json")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("GLEANER_SYNC_NAME", "com.gleaner.traytest")
    monkeypatch.setattr(sync_agent, "_run_quiet", FakeScheduler())
    return tmp_path


class TestCaptureToggle:
    """set_capturing drives all three capture paths; get_status reports them.

    This is the tray's on/off switch — if these invariants break, the icon
    shows green while nothing uploads (or the reverse).
    """

    def test_roundtrip(self, capture_env):
        assert tray.get_status().capturing is False

        tray.set_capturing(True)
        assert tray.get_status().capturing is True
        assert installers.is_hook_installed()
        assert installers.is_cursor_hook_installed()
        assert installers.is_backfill_agent_installed()

        tray.set_capturing(False)
        assert tray.get_status().capturing is False
        assert not installers.is_hook_installed()
        assert not installers.is_cursor_hook_installed()
        assert not installers.is_backfill_agent_installed()

    def test_partial_capture_counts_as_on(self, capture_env):
        """One live capture path means sessions are still being uploaded,
        so the tray must show 'on' — and the toggle must clear everything."""
        installers.install_hook()
        assert tray.get_status().capturing is True
        tray.set_capturing(False)
        assert tray.get_status().capturing is False

    def test_status_carries_active_remote(self, capture_env):
        config.add_remote("work", "https://gleaner.example.com", "gl_x")
        status = tray.get_status()
        assert status.remote == "work"
        assert status.url == "https://gleaner.example.com"


class TestMenuLabels:
    """Label helpers are pure string functions; pin their meaning."""

    def test_status_line_states(self):
        on = tray.TrayStatus(True, "work", "https://x", None)
        off = tray.TrayStatus(False, "work", "https://x", None)
        unconfigured = tray.TrayStatus(True, "", "", None)
        assert "capturing" in tray.status_line(on)
        assert "work" in tray.status_line(on)
        assert "paused" in tray.status_line(off)
        assert "no remote" in tray.status_line(unconfigured)

    def test_sync_line_ages(self):
        now = 1_000_000.0

        def line(age):
            return tray.sync_line(tray.TrayStatus(True, "r", "u", now - age), now=now)

        assert tray.sync_line(tray.TrayStatus(True, "r", "u", None)) == "no backfill yet"
        assert line(30) == "synced just now"
        assert line(600) == "synced 10 min ago"
        assert line(7200) == "synced 2 h ago"
        assert line(2 * 86400) == "synced 2 d ago"

    def test_sync_line_never_negative(self):
        """Clock skew between log mtime and now must not produce nonsense."""
        now = 1_000_000.0
        assert tray.sync_line(tray.TrayStatus(True, "r", "u", now + 300), now=now) == (
            "synced just now"
        )


@pytest.fixture
def autostart_env(tmp_path, monkeypatch):
    """Fake home + throwaway registration name; cleans up real registry
    entries on Windows even if an assertion failed first."""
    name = f"GleanerTrayTest-{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("GLEANER_TRAY_NAME", name)
    monkeypatch.setattr(autostart, "_run_quiet", FakeScheduler())
    yield tmp_path, name
    if sys.platform == "win32":
        try:
            autostart.remove_tray_autostart()
        except OSError:
            pass


class TestTrayAutostart:
    def test_lifecycle_roundtrip(self, autostart_env):
        """Same invariants as the sync agent: idempotent install, truthful
        is_installed, clean removal — on whichever OS runs this."""
        assert autostart.install_tray_autostart() is True
        assert autostart.is_tray_autostart_installed() is True
        assert autostart.install_tray_autostart() is False
        assert autostart.remove_tray_autostart() is True
        assert autostart.is_tray_autostart_installed() is False
        assert autostart.remove_tray_autostart() is False

    @pytest.mark.skipif(sys.platform != "darwin", reason="launchd backend")
    def test_launchd_content(self, autostart_env):
        import plistlib

        home, name = autostart_env
        autostart.install_tray_autostart()
        plist = plistlib.loads(
            (home / "Library" / "LaunchAgents" / f"{name}.plist").read_bytes()
        )
        assert plist["Label"] == name
        assert plist["RunAtLoad"] is True
        cmd = Path(plist["ProgramArguments"][0])
        assert cmd.is_absolute() and cmd.exists()
        assert plist["ProgramArguments"][1] == "tray"

    @pytest.mark.skipif(not sys.platform.startswith("linux"), reason="XDG backend")
    def test_xdg_desktop_content(self, autostart_env):
        home, name = autostart_env
        autostart.install_tray_autostart()
        desktop = (home / ".config" / "autostart" / f"{name}.desktop").read_text()
        assert "Type=Application" in desktop
        exec_line = next(l for l in desktop.splitlines() if l.startswith("Exec="))
        cmd = Path(exec_line.removeprefix('Exec="').split('"')[0])
        assert cmd.is_absolute() and cmd.exists()
        assert exec_line.endswith(" tray")

    @pytest.mark.skipif(sys.platform != "win32", reason="registry backend")
    def test_registry_content(self, autostart_env):
        import winreg

        home, name = autostart_env
        autostart.install_tray_autostart()
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"
        ) as key:
            value, kind = winreg.QueryValueEx(key, name)
        assert kind == winreg.REG_SZ
        exe = Path(value.strip('"'))
        assert exe.is_absolute() and exe.exists()
        assert "gleaner-tray" in exe.name
