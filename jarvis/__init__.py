"""JARVIS - a local-first voice assistant for Windows, Linux and macOS.

The package is intentionally import-safe: every optional dependency (voice,
camera, cloud integrations) is imported lazily so the assistant, the offline
console and the local test suite work on a bare Python installation.
"""

from __future__ import annotations

__version__ = "0.2.0"
VERSION = __version__
APP_NAME = "JARVIS"

__all__ = ["__version__", "VERSION", "APP_NAME"]
