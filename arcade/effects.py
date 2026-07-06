"""Sound and visual effect primitives for macOS + iTerm2."""

import os
import subprocess
import sys
from pathlib import Path

SOUNDS_DIR = Path("/System/Library/Sounds")

SOUND_MAP = {
    # Event sounds
    "tool_start": "Tink.aiff",
    "file_write": "Pop.aiff",
    "bash_done": "Morse.aiff",
    "search_done": "Tink.aiff",
    "stop": "Glass.aiff",
    "session_start": "Hero.aiff",
    "session_end": "Hero.aiff",
    "notification": "Submarine.aiff",
    "error": "Basso.aiff",
    # Combo bonus
    "combo": "Ping.aiff",
}

TAB_COLORS = {
    "green": (50, 205, 50),
    "red": (220, 50, 50),
    "blue": (70, 130, 230),
    "amber": (220, 180, 50),
    "yellow": (240, 220, 80),
}


def _sounds_enabled():
    cfg = Path.home() / ".config" / "arcade.json"
    if cfg.exists():
        try:
            import json
            return json.loads(cfg.read_text()).get("sounds", True)
        except (ValueError, OSError):
            pass
    return True


def play_sound(name, volume=1.0):
    """Play a named sound via afplay in the background. Non-blocking."""
    if not _sounds_enabled():
        return
    filename = SOUND_MAP.get(name)
    if not filename:
        return
    path = SOUNDS_DIR / filename
    if not path.exists():
        return
    cmd = ["afplay", str(path)]
    if volume != 1.0:
        cmd += ["-v", str(volume)]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _write_tty(data):
    """Write escape sequence to /dev/tty (iTerm2 terminal). Returns True on success."""
    try:
        fd = os.open("/dev/tty", os.O_WRONLY)
        os.write(fd, data.encode())
        os.close(fd)
        return True
    except OSError:
        return False


def flash_tab(color_name, duration=0.4):
    """Flash iTerm2 tab to a color, then reset. Forks a background process."""
    rgb = TAB_COLORS.get(color_name)
    if not rgb:
        return
    r, g, b = rgb

    pid = os.fork()
    if pid != 0:
        return  # Parent returns immediately

    # Child: set color, sleep, reset, exit
    try:
        set_seq = (
            f"\033]6;1;bg;red;brightness;{r}\a"
            f"\033]6;1;bg;green;brightness;{g}\a"
            f"\033]6;1;bg;blue;brightness;{b}\a"
        )
        reset_seq = "\033]6;1;bg;*;default\a"

        if _write_tty(set_seq):
            import time

            time.sleep(duration)
            _write_tty(reset_seq)
    finally:
        os._exit(0)



def show_overlay(effect, message, duration=3.0):
    """Launch the overlay window as a subprocess. Non-blocking."""
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "arcade.overlay",
            "--effect",
            effect,
            "--message",
            message,
            "--duration",
            str(duration),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
