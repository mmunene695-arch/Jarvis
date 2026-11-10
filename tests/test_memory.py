"""Short-term memory behaviour."""

from __future__ import annotations

import pytest

from jarvis.memory import ShortTermMemory


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        self.now += 1.0
        return self.now


def test_memory_records_exchanges():
    memory = ShortTermMemory(max_turns=5)
    memory.exchange("hello", "hi there")
    assert len(memory) == 2
    assert memory.last_user_message() == "hello"
    assert "user: hello" in memory.transcript()


def test_memory_is_bounded():
    memory = ShortTermMemory(max_turns=3)
    for i in range(20):
        memory.exchange(f"question {i}", f"answer {i}")
    assert len(memory) <= 6
    assert "question 19" in memory.transcript()


def test_memory_clear():
    memory = ShortTermMemory()
    memory.exchange("a", "b")
    memory.clear()
    assert memory.is_empty
    assert memory.last_user_message() is None


def test_invalid_role_rejected():
    with pytest.raises(ValueError):
        ShortTermMemory().add("robot", "hello")


def test_recent_limits():
    memory = ShortTermMemory(max_turns=10)
    memory.exchange("a", "b")
    memory.exchange("c", "d")
    assert len(memory.recent(2)) == 2
    assert memory.recent(0) == []
    assert len(memory.recent()) == 4


def test_memory_has_no_persistence(tmp_path, monkeypatch):
    """Memory must not create any file on disk."""
    memory = ShortTermMemory()
    memory.exchange("secret", "kept in RAM only")
    assert list(tmp_path.iterdir()) == []
