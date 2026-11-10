"""Notes, knowledge storage and reminders."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.features.knowledge import KnowledgeBase
from jarvis.features.notes import NoteStore
from jarvis.features.reminders import ReminderStore


class FakeTime:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


# ----------------------------------------------------------------------
# Notes
# ----------------------------------------------------------------------
def test_note_saved_and_listed(tmp_path: Path):
    store = NoteStore(tmp_path / "notes.json")
    note = store.add("buy milk")
    assert note["id"].startswith("note-")
    assert store.all()[0]["text"] == "buy milk"


def test_note_search(tmp_path: Path):
    store = NoteStore(tmp_path / "notes.json")
    store.add("buy milk and bread")
    store.add("call the plumber")
    hits = store.search("milk")
    assert len(hits) == 1 and "milk" in hits[0]["text"]


def test_empty_note_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        NoteStore(tmp_path / "notes.json").add("   ")


def test_corrupt_store_recovers(tmp_path: Path):
    path = tmp_path / "notes.json"
    path.write_text("not json", encoding="utf-8")
    store = NoteStore(path)
    assert store.all() == []
    assert (tmp_path / "notes.json.corrupt").exists()


def test_knowledge_search(tmp_path, config):
    kb = KnowledgeBase(config)
    kb.add("Batteries", "Solid state batteries use a solid electrolyte.")
    assert kb.search("electrolyte")[0]["title"] == "Batteries"
    assert "empty" in kb.describe([]).lower()


# ----------------------------------------------------------------------
# Reminders
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "text,expected",
    [
        ("10 minutes", 600),
        ("2 hours", 7200),
        ("30 seconds", 30),
        ("1 day", 86400),
        ("5 min", 300),
        ("now", 0),
        ("", 0),
        ("sometime later", 0),
    ],
)
def test_parse_delay(text: str, expected: float):
    assert ReminderStore.parse_delay(text) == expected


def test_humanise():
    store = ReminderStore(Path("/tmp/unused-reminders.json"))
    assert store.humanise(45) == "45 seconds"
    assert store.humanise(600) == "10 minutes"
    assert store.humanise(7200) == "2 hours"
    assert store.humanise(172800) == "2 days"


def test_reminder_fires_once(tmp_path: Path):
    clock = FakeTime()
    fired: list[dict] = []
    store = ReminderStore(tmp_path / "reminders.json", clock=clock, on_due=fired.append)
    store.add("stretch", delay_seconds=60)
    assert store.poll() == []
    clock.advance(61)
    assert len(store.poll()) == 1
    assert store.poll() == []
    assert len(fired) == 1


def test_reminders_merge_many_units():
    assert ReminderStore.parse_delay("1 hour 30 minutes") == 5400


def test_clear_reminders(tmp_path: Path):
    store = ReminderStore(tmp_path / "reminders.json")
    store.add("one")
    store.clear()
    assert store.all() == []
    assert "no reminders" in store.describe().lower()
