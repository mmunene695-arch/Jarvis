"""Short-term conversation memory.

The memory lives only for the lifetime of the running assistant and is cleared
when JARVIS exits. Nothing is persisted to disk.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    at: float

    def as_dict(self) -> dict[str, Any]:
        return {"role": self.role, "content": self.content, "at": self.at}


@dataclass
class ShortTermMemory:
    """Bounded rolling transcript of the current session."""

    max_turns: int = 20
    clock: Callable[[], float] = field(default=time.monotonic)
    _messages: list[Message] = field(default_factory=list, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self) -> None:
        if self.max_turns < 1:
            raise ValueError("max_turns must be at least 1")

    def add(self, role: str, content: str) -> Message:
        if role not in {"user", "assistant", "system"}:
            raise ValueError(f"invalid role: {role!r}")
        message = Message(role=role, content=content, at=float(self.clock()))
        with self._lock:
            self._messages.append(message)
            # Keep complete exchanges: two messages per turn.
            overflow = len(self._messages) - self.max_turns * 2
            if overflow > 0:
                del self._messages[:overflow]
        return message

    def exchange(self, user_text: str, assistant_text: str) -> None:
        self.add("user", user_text)
        self.add("assistant", assistant_text)

    @property
    def messages(self) -> list[Message]:
        with self._lock:
            return list(self._messages)

    def recent(self, limit: int | None = None) -> list[Message]:
        messages = self.messages
        if limit is None:
            return messages
        if limit <= 0:
            return []
        return messages[-limit:]

    def transcript(self, limit: int | None = None) -> str:
        return "\n".join(f"{m.role}: {m.content}" for m in self.recent(limit))

    def last_user_message(self) -> str | None:
        for message in reversed(self.messages):
            if message.role == "user":
                return message.content
        return None

    def clear(self) -> None:
        with self._lock:
            self._messages.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._messages)

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    def extend(self, pairs: Iterable[tuple[str, str]]) -> None:
        for role, content in pairs:
            self.add(role, content)
