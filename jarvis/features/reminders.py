"""Reminders that fire while JARVIS is running.

Alerts are best effort: they only work while the assistant process is alive and
the computer is awake.
"""

from __future__ import annotations

import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..storage import JsonFileStore

_UNIT_SECONDS = {
    "second": 1,
    "sec": 1,
    "s": 1,
    "minute": 60,
    "min": 60,
    "m": 60,
    "hour": 3600,
    "hr": 3600,
    "h": 3600,
    "day": 86400,
    "d": 86400,
}


@dataclass
class ReminderStore:
    path: Path
    clock: Callable[[], float] = field(default=time.time)
    on_due: Callable[[dict[str, Any]], None] | None = None

    def __post_init__(self) -> None:
        self._store = JsonFileStore(self.path, default_factory=list)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    @staticmethod
    def parse_delay(text: str | None) -> float:
        """Convert "5 minutes" / "2h" / "an hour and a half" into seconds."""
        if not text:
            return 0.0
        lowered = text.lower().strip().strip(".!?")
        if lowered in {"now", "right now", "immediately"}:
            return 0.0
        total = 0.0
        found = False
        for value, unit in re.findall(r"(\d+(?:\.\d+)?)\s*([a-z]+)", lowered):
            unit_key = unit.rstrip("s")
            if unit_key in _UNIT_SECONDS:
                total += float(value) * _UNIT_SECONDS[unit_key]
                found = True
        if found:
            return total
        words = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "ten": 10, "fifteen": 15, "twenty": 20, "thirty": 30, "forty-five": 45}
        for word, number in words.items():
            if re.search(rf"\b{re.escape(word)}\s+(second|minute|hour|day)s?\b", lowered):
                unit = re.search(rf"\b{re.escape(word)}\s+(second|minute|hour|day)s?\b", lowered).group(1)
                return number * _UNIT_SECONDS[unit]
        if "half an hour" in lowered or "half hour" in lowered:
            return 1800.0
        return 0.0

    def humanise(self, seconds: float) -> str:
        seconds = int(max(0, seconds))
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        if seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        if seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''}"
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''}"

    # ------------------------------------------------------------------
    def _load(self) -> list[dict[str, Any]]:
        data = self._store.read()
        return data if isinstance(data, list) else []

    def add(self, text: str, *, delay_seconds: float = 0.0) -> dict[str, Any]:
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("a reminder needs some text")
        now = self.clock()
        reminder = {
            "id": f"rem-{uuid.uuid4().hex[:8]}",
            "text": cleaned[:500],
            "created": now,
            "due": now + max(0.0, float(delay_seconds)),
            "done": False,
            "fired": False,
        }
        with self._lock:
            reminders = self._load()
            reminders.append(reminder)
            self._store.write(reminders)
        return reminder

    def all(self, *, include_done: bool = False) -> list[dict[str, Any]]:
        reminders = self._load()
        if include_done:
            return reminders
        return [r for r in reminders if not r.get("done")]

    def clear(self) -> None:
        with self._lock:
            self._store.write([])

    def due_now(self) -> list[dict[str, Any]]:
        now = self.clock()
        due: list[dict[str, Any]] = []
        with self._lock:
            reminders = self._load()
            changed = False
            for reminder in reminders:
                if reminder.get("done") or reminder.get("fired"):
                    continue
                if float(reminder.get("due", 0)) <= now:
                    reminder["fired"] = True
                    due.append(reminder)
                    changed = True
            if changed:
                self._store.write(reminders)
        return due

    def poll(self) -> list[dict[str, Any]]:
        """Fire every due reminder through ``on_due``."""
        fired = self.due_now()
        if self.on_due is not None:
            for reminder in fired:
                try:
                    self.on_due(reminder)
                except Exception:  # pragma: no cover - notification is best effort
                    pass
        return fired

    def describe(self) -> str:
        reminders = self.all()
        if not reminders:
            return "You have no reminders."
        now = self.clock()
        lines = [f"You have {len(reminders)} reminder(s):"]
        for reminder in reminders:
            remaining = float(reminder.get("due", now)) - now
            when = "now" if remaining <= 0 else f"in {self.humanise(remaining)}"
            lines.append(f"• {reminder['text']} — {when}")
        return "\n".join(lines)
