"""Wake word, follow-up window, speaker fallbacks and voice activity."""

from __future__ import annotations

import io
import struct
import wave

import pytest

from jarvis.voice import FollowUpWindow, Speaker, WakeWordMatcher, has_speech


# ----------------------------------------------------------------------
# Wake word
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "phrase",
    [
        "hey jarvis",
        "Hey Jarvis, open notepad",
        "hey jervis",
        "HEY JARVIS!",
        "ok jarvis",
        "hey jarvis what time is it",
        "jarvis",
    ],
)
def test_wake_variants_match(phrase: str):
    assert WakeWordMatcher("hey jarvis").matches(phrase)


@pytest.mark.parametrize(
    "phrase",
    ["hello there", "open notepad", "", "   ", "the weather is nice", "hey marvin"],
)
def test_non_wake_phrases_do_not_match(phrase: str):
    assert not WakeWordMatcher("hey jarvis").matches(phrase)


def test_wake_word_is_stripped():
    matcher = WakeWordMatcher("hey jarvis")
    assert matcher.strip("Hey Jarvis, open notepad") == "open notepad"  # noqa: B005


def test_custom_wake_word():
    assert WakeWordMatcher("computer").matches("computer, status report")


# ----------------------------------------------------------------------
# Follow-up window
# ----------------------------------------------------------------------
class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_follow_up_window_closes_after_a_minute():
    clock = FakeClock()
    window = FollowUpWindow(seconds=60, clock=clock)
    assert not window.is_open()
    window.open()
    clock.now = 59.9
    assert window.is_open()
    clock.now = 60.1
    assert not window.is_open()
    assert window.expired


def test_follow_up_extends_on_each_command():
    clock = FakeClock()
    window = FollowUpWindow(seconds=60, clock=clock)
    window.open()
    clock.now = 50
    window.extend()
    clock.now = 100
    assert window.is_open()


def test_follow_up_close():
    window = FollowUpWindow(seconds=60, clock=FakeClock())
    window.open()
    window.close()
    assert not window.is_open()
    assert window.remaining() == 0


# ----------------------------------------------------------------------
# Speaker fallbacks
# ----------------------------------------------------------------------
def test_speaker_prints_when_audio_is_off():
    printed: list[str] = []
    speaker = Speaker("off", printer=printed.append)
    speaker.say("hello")
    assert printed == ["hello"]
    assert speaker.describe() == "text only"


def test_speaker_ignores_empty_text():
    printed: list[str] = []
    Speaker("off", printer=printed.append).say("   ")
    assert printed == []


def test_speaker_auto_without_keys_or_pyttsx3_prints(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("jarvis.voice.local_tts_available", lambda: False)
    printed: list[str] = []
    speaker = Speaker("auto", env={}, printer=printed.append)
    speaker.say("offline reply")
    assert printed == ["offline reply"]


# ----------------------------------------------------------------------
# Voice activity
# ----------------------------------------------------------------------
def _wav(samples: list[int]) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(struct.pack("<" + "h" * len(samples), *samples))
    return buffer.getvalue()


def test_silence_detected():
    assert not has_speech(_wav([0] * 1600))


def test_speech_detected():
    assert has_speech(_wav([2000, -2000] * 800))


def test_empty_audio_is_not_speech():
    assert not has_speech(b"")
    assert not has_speech(b"RIFF")


def test_capabilities_never_raise():
    from jarvis.voice import capabilities

    caps = capabilities()
    assert set(caps) >= {"microphone", "local_tts", "cloud_llm"}
    assert all(isinstance(value, bool) for value in caps.values())
