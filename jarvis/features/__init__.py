"""Local feature modules (files, notes, reminders, system, apps, ...)."""

from __future__ import annotations

from . import apps, bluetooth, files, knowledge, notes, reminders, startup, system_info, windows_control
from .files import FileManager
from .knowledge import KnowledgeBase
from .notes import NoteStore
from .reminders import ReminderStore

__all__ = [
    "apps",
    "bluetooth",
    "files",
    "knowledge",
    "notes",
    "reminders",
    "startup",
    "system_info",
    "windows_control",
    "FileManager",
    "KnowledgeBase",
    "NoteStore",
    "ReminderStore",
]
