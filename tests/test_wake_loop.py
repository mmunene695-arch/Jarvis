"""Standby loop: wake word, follow-up window, reply routing."""

from __future__ import annotations

import pytest

from jarvis.voice import FollowUpWindow, WakeWordMatcher
from jarvis.wake import StandbyLoop, VoiceSession


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def loop() -> StandbyLoop:
    clock = FakeClock()
    return StandbyLoop(WakeWordMatcher("hey jarvis"), FollowUpWindow(seconds=60, clock=clock), clock=clock)


def test_wake_classification(loop: StandbyLoop):
    assert loop.classify("hey jarvis") == "wake"
    assert loop.in_follow_up


def test_follow_up_needs_no_wake_word(loop: StandbyLoop):
    loop.classify("hey jarvis")
    assert loop.classify("what time is it") == "follow_up"


def test_ignored_without_wake_word(loop: StandbyLoop):
    assert loop.classify("open notepad") == "ignored"
    assert not loop.in_follow_up


def test_window_expires(loop: StandbyLoop):
    loop.classify("hey jarvis")
    loop.clock.now = 61
    assert loop.classify("open notepad") == "ignored"


def test_empty_transcript_ignored(loop: StandbyLoop):
    assert loop.classify("") == "ignored"
    assert loop.classify("   ") == "ignored"


def test_command_from_strips_wake_phrase(loop: StandbyLoop):
    assert loop.command_from("hey jarvis open notepad") == "open notepad"
    assert loop.command_from("just a command") == "just a command"


class FakeSpeaker:
    def __init__(self) -> None:
        self.said: list[str] = []

    def say(self, text: str) -> None:
        self.said.append(text)


def test_voice_session_runs_a_command(engine):
    transcripts = iter(["hey jarvis system status", "what time is it"])
    speaker = FakeSpeaker()
    session = VoiceSession(
        engine=engine,
        matcher=WakeWordMatcher("hey jarvis"),
        speaker=speaker,
        transcriber=lambda seconds: next(transcripts, ""),
        printer=lambda text: None,
    )
    assert session.step() == "wake"
    assert session.step() == "follow_up"
    assert speaker.said  # the reply was spoken
    assert session.step() == "ignored"  # transcription ended: nothing was heard


def test_voice_session_prompts_on_bare_wake_word(engine):
    speaker = FakeSpeaker()
    session = VoiceSession(
        engine=engine,
        matcher=WakeWordMatcher("hey jarvis"),
        speaker=speaker,
        transcriber=lambda seconds: "hey jarvis",
        printer=lambda text: None,
    )
    session.step()
    assert speaker.said == ["I am listening."]
