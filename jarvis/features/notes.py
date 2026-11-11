"""Local notes store on top of a JSON document."""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..storage import JsonFileStore

MAX_NOTES = 5000


@dataclass
class NoteStore:
    path: Path
    clock: Callable[[], float] = field(default=time.time)

    def __post_init__(self) -> None:
        self._store = JsonFileStore(self.path, default_factory=list)

    def _load(self) -> list[dict[str, Any]]:
        data = self._store.read()
        return data if isinstance(data, list) else []

    def add(self, text: str, *, tags: list[str] | None = None) -> dict[str, Any]:
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("a note needs some text")
        now = self.clock()
        note = {
            "id": f"note-{uuid.uuid4().hex[:8]}",
            "text": cleaned[:4000],
            "tags": [t.strip().lower() for t in (tags or []) if t.strip()],
            "created": now,
            "created_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
        }
        notes = self._load()
        notes.append(note)
        if len(notes) > MAX_NOTES:
            notes = notes[-MAX_NOTES:]
        self._store.write(notes)
        return note

    def all(self) -> list[dict[str, Any]]:
        return self._load()

    def search(self, query: str) -> list[dict[str, Any]]:
        terms = [t for t in re.split(r"\W+", (query or "").lower()) if t]
        if not terms:
            return []
        results: list[tuple[int, dict[str, Any]]] = []
        for note in self._load():
            haystack = (note.get("text", "") + " " + " ".join(note.get("tags", []))).lower()
            score = sum(haystack.count(term) for term in terms if term in haystack)
            if score:
                results.append((score, note))
        results.sort(key=lambda pair: pair[0], reverse=True)
        return [note for _, note in results]

    def clear(self) -> None:
        self._store.write([])

    def describe(self, notes: list[dict[str, Any]]) -> str:
        if not notes:
            return "I have no notes matching that."
        lines = [f"I found {len(notes)} note(s):"]
        for note in notes[:15]:
            stamp = note.get("created_iso", "")
            lines.append(f"• [{note.get('id')}] {note.get('text')}  ({stamp})")
        if len(notes) > 15:
            lines.append(f"…and {len(notes) - 15} more.")
        return "\n".join(lines)
