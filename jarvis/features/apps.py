"""Launching desktop applications and websites.

JARVIS only ever starts a *known* application key or a web URL in the user's
default browser. It never passes user text to a shell.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import urllib.parse
import webbrowser

from ..errors import FeatureUnavailable, NotFoundError, ValidationError

_WINDOWS = sys.platform.startswith("win")
_MACOS = sys.platform == "darwin"

#: Logical app name -> per-platform launch candidates.
APP_REGISTRY: dict[str, dict[str, list[str]]] = {
    "notepad": {"windows": ["notepad.exe"], "linux": ["gedit", "kate", "xed", "mousepad"], "macos": []},
    "calculator": {
        "windows": ["calc.exe"],
        "linux": ["gnome-calculator", "kcalc", "galculator"],
        "macos": [],
    },
    "paint": {"windows": ["mspaint.exe"], "linux": ["krita", "pinta"], "macos": []},
    "file manager": {
        "windows": ["explorer.exe"],
        "linux": ["nautilus", "dolphin", "thunar", "pcmanfm"],
        "macos": ["open"],
    },
    "explorer": {"windows": ["explorer.exe"], "linux": [], "macos": []},
    "task manager": {"windows": ["taskmgr.exe"], "linux": [], "macos": []},
    "control panel": {"windows": ["control.exe"], "linux": [], "macos": []},
    "cmd": {"windows": ["cmd.exe"], "linux": [], "macos": []},
    "powershell": {"windows": ["powershell.exe"], "linux": [], "macos": []},
    "terminal": {
        "windows": ["wt.exe", "cmd.exe"],
        "linux": ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"],
        "macos": ["Terminal"],
    },
    "browser": {
        "windows": ["msedge.exe", "chrome.exe"],
        "linux": ["firefox", "google-chrome", "chromium"],
        "macos": ["Safari"],
    },
    "vs code": {"windows": ["code.cmd"], "linux": ["code"], "macos": ["code"]},
    "spotify": {"windows": ["spotify.exe"], "linux": ["spotify"], "macos": ["Spotify"]},
    "settings": {"windows": ["ms-settings:"], "linux": [], "macos": []},
}

_SITE_ALIASES: dict[str, str] = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "wikipedia": "https://www.wikipedia.org",
    "maps": "https://maps.google.com",
    "news": "https://news.google.com",
    "whatsapp web": "https://web.whatsapp.com",
    "chatgpt": "https://chat.openai.com",
}


def _platform_key() -> str:
    if _WINDOWS:
        return "windows"
    if _MACOS:
        return "macos"
    return "linux"


def available_apps() -> dict[str, list[str]]:
    """Apps that are actually installed on this machine."""
    key = _platform_key()
    installed: dict[str, list[str]] = {}
    for name, platforms in APP_REGISTRY.items():
        candidates = platforms.get(key, [])
        found = [c for c in candidates if c.endswith(":") or _find(c)]
        if found:
            installed[name] = found
    return installed


def _find(binary: str) -> str | None:
    if _MACOS:
        path = shutil.which(binary) or (
            f"/Applications/{binary}.app" if os.path.isdir(f"/Applications/{binary}.app") else None
        )
        return path
    return shutil.which(binary)


def describe_available() -> str:
    installed = available_apps()
    if not installed:
        return (
            "I could not find any of my known applications on this system. "
            'You can still ask me to open a website, for example "open youtube".'
        )
    lines = [f"I can open {len(installed)} known app(s) on this {_platform_key()} machine:"]
    for name in sorted(installed):
        lines.append(f"• {name}")
    lines.append('Websites also work: "open youtube", "open github.com".')
    return "\n".join(lines)


_URL_RE = None


def looks_like_url(target: str) -> bool:
    import re

    global _URL_RE
    if _URL_RE is None:
        _URL_RE = re.compile(r"^(https?://)?([\w-]+\.)+[a-z]{2,}(/[\w\-.~:/?#\[\]@!$&'()*+,;=%]*)?$", re.IGNORECASE)
    return bool(_URL_RE.match(target.strip()))


def normalise_url(target: str) -> str:
    cleaned = target.strip()
    if not cleaned.lower().startswith(("http://", "https://")):
        cleaned = f"https://{cleaned}"
    parsed = urllib.parse.urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(f"{target!r} is not a web address I can open")
    if " " in parsed.netloc:
        raise ValidationError(f"{target!r} is not a web address I can open")
    return cleaned


def resolve(target: str) -> tuple[str, str]:
    """Classify a spoken target.

    Returns ``("url", url)``, ``("app", key)`` or ``("unknown", target)``.
    """
    cleaned = (target or "").strip().strip(".?!").lower()
    if not cleaned:
        return "unknown", target
    if cleaned in _SITE_ALIASES:
        return "url", _SITE_ALIASES[cleaned]
    if looks_like_url(cleaned):
        return "url", normalise_url(cleaned)
    if cleaned in APP_REGISTRY:
        return "app", cleaned
    for name in APP_REGISTRY:
        if cleaned.startswith(name) or name.startswith(cleaned):
            return "app", name
    return "unknown", cleaned


def open_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    if parsed.scheme not in {"http", "https"}:
        raise ValidationError("I only open http and https addresses")
    if not webbrowser.open_new_tab(parsed.geturl()):
        raise FeatureUnavailable("I could not reach your default browser on this system")
    return f"Opened {parsed.geturl()} in your browser."


def open_app(key: str) -> str:
    """Launch a registered application without invoking a shell."""
    if key not in APP_REGISTRY:
        raise NotFoundError(f"{key} is not in my app list")
    platform_key = _platform_key()
    candidates = APP_REGISTRY[key].get(platform_key, [])
    if not candidates:
        raise FeatureUnavailable(f"{key} is not supported on {platform_key} yet")
    for candidate in candidates:
        try:
            if candidate.endswith(":") or candidate.startswith("ms-"):
                if _WINDOWS:
                    os.startfile(candidate)  # type: ignore[attr-defined]
                    return f"Opened the Windows {key} page."
                continue
            if _MACOS:
                if os.path.isdir(f"/Applications/{candidate}.app"):
                    subprocess.Popen(["open", "-a", candidate], close_fds=True)
                    return f"Opened {key}."
                path = shutil.which(candidate)
                if path:
                    subprocess.Popen([path], close_fds=True)
                    return f"Opened {key}."
                continue
            path = shutil.which(candidate)
            if path:
                kwargs = {}
                if _WINDOWS:
                    kwargs["creationflags"] = 0x00000008  # DETACHED_PROCESS
                subprocess.Popen([path], close_fds=True, **kwargs)
                return f"Opened {key}."
        except OSError:
            continue
    raise FeatureUnavailable(
        f"I could not start {key}. It may not be installed, or it may need to be in your PATH."
    )
