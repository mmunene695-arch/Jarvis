"""Standby listening loop.

While JARVIS runs it listens for the wake phrase, then keeps the conversation
open for the follow-up window (about one minute) before returning to standby.
All listening is local detection plus an online transcription of the captured
audio, so a full offline voice conversation is not supported.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Protocol

from .voice import FollowUpWindow, WakeWordMatcher


class Listener(Protocol):  # pragma: no cover - structural typing
    def listen(self, seconds: float) -> str: ...


@dataclass
class StandbyLoop:
    """Turns recogniser output into wake/follow-up decisions."""

    matcher: WakeWordMatcher
    window: FollowUpWindow
    clock: Callable[[], float] = field(default=time.monotonic)

    def classify(self, transcript: str) -> str:
        """Return ``wake``, ``follow_up`` or ``ignored``."""
        text = (transcript or "").strip()
        if not text:
            return "ignored"
        if self.matcher.matches(text):
            self.window.open()
            return "wake"
        if self.window.is_open():
            self.window.extend()
            return "follow_up"
        return "ignored"

    def command_from(self, transcript: str) -> str:
        """Strip the wake phrase, keeping the rest as the first command."""
        if self.matcher.matches(transcript):
            return self.matcher.strip(transcript)
        return (transcript or "").strip()

    @property
    def in_follow_up(self) -> bool:
        return self.window.is_open()

    def seconds_left(self) -> float:
        return self.window.remaining()


@dataclass
class VoiceSession:
    """Glue between a microphone, the engine and speech output."""

    engine: object
    matcher: WakeWordMatcher
    speaker: object
    listen_seconds: float = 5.0
    follow_up_seconds: float = 60.0
    transcriber: Callable[[float], str] | None = None
    printer: Callable[[str], None] = print
    loop: StandbyLoop = field(init=False)

    def __post_init__(self) -> None:
        self.loop = StandbyLoop(self.matcher, FollowUpWindow(seconds=self.follow_up_seconds))

    def transcribe(self, seconds: float) -> str:
        if self.transcriber is not None:
            return self.transcriber(seconds)
        from . import voice

        return voice.listen(seconds)

    def step(self) -> str:
        """One listen cycle. Returns what happened, for tests and logging."""
        transcript = self.transcribe(self.listen_seconds)
        decision = self.loop.classify(transcript)
        if decision == "ignored":
            return "ignored"
        command = self.loop.command_from(transcript)
        if not command:
            self.speaker.say("I am listening.")
            return decision
        reply = self.engine.ask(command, speak=self.speaker)  # type: ignore[attr-defined]
        self.printer(f"jarvis> {reply.text}")
        return decision

    def run(self) -> None:
        self.printer("JARVIS is in standby. Say \"hey jarvis\" to wake me. Ctrl+C to stop.")
        try:
            while getattr(self.engine, "running", True):
                self.step()
                if not getattr(self.engine, "running", True):
                    break
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.printer("\nStandby stopped.")
