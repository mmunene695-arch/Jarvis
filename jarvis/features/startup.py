"""Optional, visible JARVIS startup launcher.

Nothing is installed automatically. ``enable()`` writes a launcher the user can
inspect and delete; ``disable()`` removes it. JARVIS never installs a hidden
background service.
"""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path

SUPPORTED = sys.platform.startswith("win") or sys.platform == "darwin" or sys.platform.startswith("linux")


def _entry_command() -> list[str]:
    """The command that starts the visible JARVIS window."""
    if getattr(sys, "frozen", False):  # PyInstaller build
        return [sys.executable, "--voice"]
    return [sys.executable, "-m", "jarvis", "--voice"]


def _windows_startup_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise OSError("APPDATA is not set, so I cannot find your Startup folder")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _macos_launch_agent() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / "ai.jarvis.assistant.plist"


def _linux_desktop_entry() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / "autostart" / "jarvis.desktop"


def launcher_path() -> Path:
    if sys.platform.startswith("win"):
        return _windows_startup_dir() / "JARVIS.lnk.start.cmd"
    if sys.platform == "darwin":
        return _macos_launch_agent()
    return _linux_desktop_entry()


def _launcher_body() -> str:
    command = " ".join(shlex.quote(part) for part in _entry_command())
    if sys.platform.startswith("win"):
        exe, *args = _entry_command()
        return f'@echo off\r\nstart "JARVIS" "{exe}" {" ".join(args)}\r\n'
    if sys.platform == "darwin":
        exe, *args = _entry_command()
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0"><dict>\n'
            "  <key>Label</key><string>ai.jarvis.assistant</string>\n"
            "  <key>ProgramArguments</key><array>\n"
            + "".join(f"    <string>{part}</string>\n" for part in [exe, *args])
            + "  </array>\n"
            "  <key>RunAtLoad</key><true/>\n"
            "  <key>ProcessType</key><string>Interactive</string>\n"
            "</dict></plist>\n"
        )
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=JARVIS\n"
        "Comment=Visible JARVIS voice assistant\n"
        f"Exec={command}\n"
        "Terminal=true\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


def enable() -> str:
    if not SUPPORTED:
        raise OSError("The startup launcher is not supported on this platform")
    path = launcher_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_launcher_body(), encoding="utf-8")
    if not sys.platform.startswith("win"):
        try:
            path.chmod(0o755)
        except OSError:
            pass
    return (
        f"Startup enabled. I added a visible launcher at {path}. "
        "You can delete that file at any time, or ask me to disable startup."
    )


def disable() -> str:
    path = launcher_path()
    if not path.exists():
        return "Startup was not enabled, so there was nothing to remove."
    path.unlink()
    return f"Startup disabled and {path.name} was removed."


def is_enabled() -> bool:
    return launcher_path().exists()


def status() -> str:
    path = launcher_path()
    if path.exists():
        return (
            f"Startup is enabled through a visible launcher at {path}. "
            "JARVIS starts after you sign in, and only while the computer is on and awake."
        )
    return (
        "Startup is not enabled. I do not install myself as a hidden background service — "
        'say "enable startup" to add a visible launcher.'
    )
