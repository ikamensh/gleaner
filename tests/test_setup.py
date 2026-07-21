"""Tests for gleaner.setup: config file I/O and hook installation.

The periodic sync agent (per-OS scheduler backends) is covered in
test_cross_os.py.
"""

import json

import pytest

import gleaner.setup.config as config
import gleaner.setup.installers as installers


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    """Redirect config and settings files to a temp directory."""
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "gleaner.json")
    monkeypatch.setattr(installers, "CLAUDE_SETTINGS", tmp_path / ".claude" / "settings.json")
    monkeypatch.setattr(installers, "CURSOR_HOOKS", tmp_path / ".cursor" / "hooks.json")


class TestConfigRoundtrip:
    """write_config sets the active remote; get_active reads it back."""

    def test_roundtrip(self):
        config.write_config("https://example.com", "gl_abc123")
        name, remote = config.get_active()
        assert remote["url"] == "https://example.com"
        assert remote["token"] == "gl_abc123"

    def test_read_missing_returns_empty(self):
        assert config.read_config() == {}
        assert config.get_active() == ("", {})

    def test_overwrite_keeps_active_remote(self):
        config.write_config("https://old.com", "gl_old")
        config.write_config("https://new.com", "gl_new")
        # write_config updates the active remote in place, not a second one
        assert len(config.list_remotes()) == 1
        _, remote = config.get_active()
        assert remote["url"] == "https://new.com"
        assert remote["token"] == "gl_new"


class TestLegacyMigration:
    """A flat {url, token} file is read as a single 'default' remote."""

    def test_flat_file_reads_as_default_remote(self):
        config.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        config.CONFIG_FILE.write_text(
            json.dumps({"url": "https://legacy.com", "token": "gl_legacy"})
        )
        name, remote = config.get_active()
        assert name == "default"
        assert remote == {"url": "https://legacy.com", "token": "gl_legacy"}

    def test_flat_file_resolves_credentials(self, monkeypatch):
        monkeypatch.delenv("GLEANER_URL", raising=False)
        monkeypatch.delenv("GLEANER_TOKEN", raising=False)
        monkeypatch.delenv("GLEANER_REMOTE", raising=False)
        config.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        config.CONFIG_FILE.write_text(
            json.dumps({"url": "https://legacy.com", "token": "gl_legacy"})
        )
        assert config.get_credentials() == ("https://legacy.com", "gl_legacy")

    def test_migrated_on_next_write(self):
        config.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        config.CONFIG_FILE.write_text(
            json.dumps({"url": "https://legacy.com", "token": "gl_legacy"})
        )
        config.write_config("https://legacy.com", "gl_new")
        on_disk = json.loads(config.CONFIG_FILE.read_text())
        assert "remotes" in on_disk
        assert on_disk["active"] == "default"
        assert on_disk["remotes"]["default"]["token"] == "gl_new"


class TestRemotes:
    """add_remote / use_remote / remove_remote invariants."""

    def test_add_activates_by_default(self):
        config.add_remote("a", "https://a.com", "gl_a")
        assert config.get_active() == ("a", {"url": "https://a.com", "token": "gl_a"})

    def test_add_no_activate_keeps_active(self):
        config.add_remote("a", "https://a.com", "gl_a")
        config.add_remote("b", "https://b.com", "gl_b", activate=False)
        assert config.get_active()[0] == "a"
        assert set(config.list_remotes()) == {"a", "b"}

    def test_use_switches_active(self):
        config.add_remote("a", "https://a.com", "gl_a")
        config.add_remote("b", "https://b.com", "gl_b", activate=False)
        assert config.use_remote("b") is True
        assert config.get_active()[0] == "b"

    def test_use_unknown_returns_false(self):
        assert config.use_remote("nope") is False

    def test_add_replaces_existing(self):
        config.add_remote("a", "https://a.com", "gl_a")
        config.add_remote("a", "https://a2.com", "gl_a2")
        assert len(config.list_remotes()) == 1
        assert config.get_active()[1]["url"] == "https://a2.com"

    def test_remove_active_repoints(self):
        config.add_remote("a", "https://a.com", "gl_a")
        config.add_remote("b", "https://b.com", "gl_b", activate=False)
        assert config.remove_remote("a") is True
        # active was 'a'; only 'b' remains, so it becomes active
        assert config.get_active()[0] == "b"

    def test_remove_last_clears_active(self):
        config.add_remote("a", "https://a.com", "gl_a")
        assert config.remove_remote("a") is True
        assert config.get_active() == ("", {})

    def test_remove_unknown_returns_false(self):
        assert config.remove_remote("nope") is False

    def test_credentials_follow_active(self, monkeypatch):
        monkeypatch.delenv("GLEANER_URL", raising=False)
        monkeypatch.delenv("GLEANER_TOKEN", raising=False)
        monkeypatch.delenv("GLEANER_REMOTE", raising=False)
        config.add_remote("a", "https://a.com", "gl_a")
        config.add_remote("b", "https://b.com", "gl_b")  # now active
        assert config.get_credentials() == ("https://b.com", "gl_b")
        config.use_remote("a")
        assert config.get_credentials() == ("https://a.com", "gl_a")

    def test_gleaner_remote_env_selects_profile(self, monkeypatch):
        monkeypatch.delenv("GLEANER_URL", raising=False)
        monkeypatch.delenv("GLEANER_TOKEN", raising=False)
        config.add_remote("a", "https://a.com", "gl_a")
        config.add_remote("b", "https://b.com", "gl_b")  # active
        monkeypatch.setenv("GLEANER_REMOTE", "a")
        assert config.get_credentials() == ("https://a.com", "gl_a")


class TestGetCredentials:
    """get_credentials should prefer env vars over config file."""

    def test_env_vars_take_precedence(self, monkeypatch):
        config.write_config("https://file.com", "gl_file")
        monkeypatch.setenv("GLEANER_URL", "https://env.com")
        monkeypatch.setenv("GLEANER_TOKEN", "gl_env")
        url, token = config.get_credentials()
        assert url == "https://env.com"
        assert token == "gl_env"

    def test_falls_back_to_config(self, monkeypatch):
        config.write_config("https://file.com", "gl_file")
        monkeypatch.delenv("GLEANER_URL", raising=False)
        monkeypatch.delenv("GLEANER_TOKEN", raising=False)
        url, token = config.get_credentials()
        assert url == "https://file.com"
        assert token == "gl_file"

    def test_partial_env_partial_config(self, monkeypatch):
        """URL from env, token from config file."""
        config.write_config("https://file.com", "gl_file")
        monkeypatch.setenv("GLEANER_URL", "https://env.com")
        monkeypatch.delenv("GLEANER_TOKEN", raising=False)
        url, token = config.get_credentials()
        assert url == "https://env.com"
        assert token == "gl_file"

    def test_empty_when_nothing_configured(self, monkeypatch):
        monkeypatch.delenv("GLEANER_URL", raising=False)
        monkeypatch.delenv("GLEANER_TOKEN", raising=False)
        url, token = config.get_credentials()
        assert url == ""
        assert token == ""


class TestHookManagement:
    """install_hook / remove_hook / is_hook_installed manage ~/.claude/settings.json."""

    def test_install_on_empty(self):
        """Installing into a fresh settings.json works."""
        assert installers.install_hook() is True
        assert installers.is_hook_installed() is True

    def test_install_is_idempotent(self):
        """Second install returns False and doesn't duplicate."""
        installers.install_hook()
        assert installers.install_hook() is False
        settings = installers.read_claude_settings()
        assert len(settings["hooks"]["SessionEnd"]) == 1

    def test_remove(self):
        installers.install_hook()
        assert installers.remove_hook() is True
        assert installers.is_hook_installed() is False

    def test_remove_when_not_installed(self):
        assert installers.remove_hook() is False

    def test_preserves_other_hooks(self):
        """Installing/removing gleaner doesn't affect other hooks."""
        other_hook = {"hooks": [{"type": "command", "command": "my-other-hook"}]}
        settings = {"hooks": {"SessionEnd": [other_hook], "PreToolUse": [{"hooks": []}]}}
        installers.write_claude_settings(settings)

        installers.install_hook()
        s = installers.read_claude_settings()
        assert len(s["hooks"]["SessionEnd"]) == 2  # other + gleaner
        assert "PreToolUse" in s["hooks"]

        installers.remove_hook()
        s = installers.read_claude_settings()
        assert len(s["hooks"]["SessionEnd"]) == 1  # only other remains
        assert s["hooks"]["SessionEnd"][0] == other_hook

    def test_install_remove_roundtrip(self):
        """Install then remove leaves no gleaner trace."""
        installers.install_hook()
        installers.remove_hook()
        settings = installers.read_claude_settings()
        assert settings["hooks"]["SessionEnd"] == []


class TestCursorHookManagement:
    """install_cursor_hook / remove_cursor_hook manage ~/.cursor/hooks.json."""

    def test_install_on_empty(self):
        assert installers.install_cursor_hook() is True
        assert installers.is_cursor_hook_installed() is True

    def test_creates_valid_hooks_json(self):
        """Installed hooks.json has version and correct structure."""
        installers.install_cursor_hook()
        cfg = installers.read_cursor_hooks()
        assert cfg["version"] == 1
        assert len(cfg["hooks"]["stop"]) == 1
        assert "gleaner" in cfg["hooks"]["stop"][0]["command"]

    def test_install_is_idempotent(self):
        installers.install_cursor_hook()
        assert installers.install_cursor_hook() is False
        cfg = installers.read_cursor_hooks()
        assert len(cfg["hooks"]["stop"]) == 1

    def test_remove(self):
        installers.install_cursor_hook()
        assert installers.remove_cursor_hook() is True
        assert installers.is_cursor_hook_installed() is False

    def test_remove_when_not_installed(self):
        assert installers.remove_cursor_hook() is False

    def test_preserves_other_hooks(self):
        """Installing/removing gleaner doesn't affect other Cursor hooks."""
        cfg = {
            "version": 1,
            "hooks": {
                "stop": [{"command": "my-other-hook"}],
                "afterFileEdit": [{"command": "lint-hook"}],
            },
        }
        installers.write_cursor_hooks(cfg)

        installers.install_cursor_hook()
        cfg = installers.read_cursor_hooks()
        assert len(cfg["hooks"]["stop"]) == 2
        assert "afterFileEdit" in cfg["hooks"]

        installers.remove_cursor_hook()
        cfg = installers.read_cursor_hooks()
        assert len(cfg["hooks"]["stop"]) == 1
        assert cfg["hooks"]["stop"][0]["command"] == "my-other-hook"
