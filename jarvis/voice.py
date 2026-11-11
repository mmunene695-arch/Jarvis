"""Optional voice layer: wake-word matching, recording, transcription, speech.

Heavy dependencies (``sounddevice``, ``pyttsx3``, ``vosk``) are imported inside
functions so the rest of JARVIS runs on a bare Python install.
"""

from __future__ import annotations

import io
import os
import re
import struct
import wave
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Callable

from . import cloud
from .config import JarvisConfig
from .errors import FeatureUnavailable, NetworkError


# ----------------------------------------------------------------------
# Wake word
# ----------------------------------------------------------------------
def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
            )
        previous = current
    return previous[-1]


def _close_word(candidate: str, word: str) -> bool:
    """True when ``candidate`` is the same word or a small mis-hearing of it."""
    if not candidate or not word:
        return False
    if candidate == word:
        return True
    allowed = 1 if len(word) <= 6 else 2
    if len(word) <= 3:
        return False
    return _levenshtein(candidate, word) <= allowed


class WakeWordMatcher:
    """Matches "hey jarvis" in imperfect transcriptions.

    The wake phrase is matched word by word with a small edit distance, so
    variants such as "hey jervis", "ok jarvas" or a bare "jarvis" wake the
    assistant, while unrelated phrases ("hey marvin", "hello there") do not.
    """

    _FILLERS = ("hey", "hi", "ok", "okay", "yo", "hello")

    def __init__(self, wake_word: str = "hey jarvis", *, threshold: float = 0.78) -> None:
        self.wake_word = wake_word.strip().lower()
        self.threshold = threshold
        tokens = self._tokenise(self.wake_word)
        if not tokens:
            raise ValueError("the wake word must contain at least one word")
        self._name = tokens[-1]
        self._greetings = tuple(dict.fromkeys(tokens[:-1] + list(self._FILLERS)))

    @staticmethod
    def _tokenise(text: str) -> list[str]:
        return [token for token in re.split(r"[^a-z0-9']+", (text or "").lower()) if token]

    def _name_index(self, tokens: list[str]) -> int | None:
        for index, token in enumerate(tokens):
            if _close_word(token, self._name):
                if index == 0 or any(
                    _close_word(tokens[j], greet) for greet in self._greetings for j in range(index)
                ):
                    return index
        return None

    def matches(self, transcript: str) -> bool:
        tokens = self._tokenise(transcript)
        if not tokens:
            return False
        return self._name_index(tokens) is not None

    def strip(self, transcript: str) -> str:
        """Remove the wake phrase and return the remaining command."""
        text = transcript or ""
        tokens = list(re.finditer(r"[A-Za-z0-9']+", text))
        words = [m.group(0).lower() for m in tokens]
        index = self._name_index(words)
        if index is None:
            return text.strip()
        remainder = text[tokens[index].end():]
        return remainder.lstrip(" \t,.:;!?-")


# ----------------------------------------------------------------------
# Follow-up window
# ----------------------------------------------------------------------
@dataclass
class FollowUpWindow:
    """Time box during which no new wake word is needed."""

    seconds: float = 60.0
    clock: Callable[[], float] = field(default_factory=lambda: __import__("time").monotonic)
    _deadline: float | None = field(default=None, repr=False)

    def open(self) -> None:
        self._deadline = self.clock() + self.seconds

    def is_open(self) -> bool:
        return self._deadline is not None and self.clock() < self._deadline

    def extend(self) -> None:
        if self.is_open():
            self._deadline = self.clock() + self.seconds

    def close(self) -> None:
        self._deadline = None

    def remaining(self) -> float:
        if self._deadline is None:
            return 0.0
        return max(0.0, self._deadline - self.clock())

    @property
    def expired(self) -> bool:
        return not self.is_open()


# ----------------------------------------------------------------------
# Capabilities
# ----------------------------------------------------------------------
def _have(module: str) -> bool:
    try:
        __import__(module)
        return True
    except Exception:
        return False


def microphone_available() -> bool:
    return _have("sounddevice")


def local_tts_available() -> bool:
    return _have("pyttsx3")


def vosk_available() -> bool:
    return _have("vosk")


def capabilities() -> dict[str, bool]:
    return {
        "microphone": microphone_available(),
        "local_tts": local_tts_available(),
        "local_wake_word": vosk_available(),
        "cloud_llm": cloud.available(),
        "cloud_stt": bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("JARVIS_LLM_API_KEY")),
    }


RECORD_RATE = 16000
RECORD_CHANNELS = 1


def record_wav(seconds: float = 5.0, *, rate: int = RECORD_RATE) -> bytes:
    """Record mono 16-bit audio from the default microphone as WAV bytes."""
    if not microphone_available():
        raise FeatureUnavailable(
            'The microphone needs the sounddevice library. Install it with: pip install "jarvis-assistant[voice]"'
        )
    import sounddevice as sd  # type: ignore

    frames = max(1, int(seconds * rate))
    try:
        recording = sd.rec(frames, samplerate=rate, channels=RECORD_CHANNELS, dtype="int16")
        sd.wait()
    except Exception as exc:  # pragma: no cover - hardware dependent
        raise FeatureUnavailable(f"I could not open the microphone: {exc}") from exc
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(RECORD_CHANNELS)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(recording.tobytes())
    return buffer.getvalue()


def has_speech(wav_bytes: bytes, *, threshold: int = 350) -> bool:
    """Cheap voice-activity check used to skip silent recordings."""
    if len(wav_bytes) <= 44:
        return False
    payload = wav_bytes[44:]
    if not payload:
        return False
    peak = 0
    for (sample,) in struct.iter_unpack("<h", payload[: len(payload) - (len(payload) % 2)]):
        peak = max(peak, abs(sample))
        if peak >= threshold:
            return True
    return False


def listen(seconds: float = 5.0, *, language: str | None = None) -> str:
    """Record and transcribe speech through the online service."""
    audio = record_wav(seconds)
    if not has_speech(audio):
        return ""
    return cloud.transcribe(audio, language=language)


# ----------------------------------------------------------------------
# Speech output
# ----------------------------------------------------------------------
class Speaker:
    """Speaks replies, falling back to printed text.

    Backends: ``cloud`` (online TTS), ``local`` (pyttsx3), ``off`` (print only).
    """

    def __init__(
        self,
        backend: str = "auto",
        *,
        config: JarvisConfig | None = None,
        env: Mapping[str, str] | None = None,
        printer: Callable[[str], None] = print,
    ) -> None:
        self.config = config or JarvisConfig()
        self.env = os.environ if env is None else env
        self.printer = printer
        self.backend = self._choose(backend)
        self._engine: Any = None
        self.spoken_messages: list[str] = []

    def _choose(self, backend: str) -> str:
        requested = (backend or "auto").lower()
        if requested in {"off", "text", "none"}:
            return "off"
        if requested in {"local", "pyttsx3"}:
            return "local" if local_tts_available() else "off"
        if requested in {"cloud", "online"}:
            return "cloud" if self._cloud_ready() else "off"
        if self._cloud_ready():
            return "cloud"
        if local_tts_available():
            return "local"
        return "off"

    def _cloud_ready(self) -> bool:
        return bool(self.env.get("OPENAI_API_KEY") or self.env.get("JARVIS_LLM_API_KEY"))

    # ------------------------------------------------------------------
    def say(self, text: str) -> None:
        message = (text or "").strip()
        if not message:
            return
        self.spoken_messages.append(message)
        if self.backend == "cloud":
            try:
                return self._say_cloud(message)
            except NetworkError:
                self.backend = "local" if local_tts_available() else "off"
        if self.backend == "local":
            try:
                return self._say_local(message)
            except Exception:  # pragma: no cover - audio device dependent
                self.backend = "off"
        self.printer(message)

    def _say_local(self, message: str) -> None:  # pragma: no cover - needs audio device
        import pyttsx3  # type: ignore

        if self._engine is None:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 175)
        self._engine.say(message)
        self._engine.runAndWait()

    def _say_cloud(self, message: str) -> None:
        """Speak with the online text-to-speech endpoint (best effort)."""
        key = self.env.get("OPENAI_API_KEY") or self.env.get("JARVIS_LLM_API_KEY")
        if not key:
            raise NetworkError("no cloud speech key configured")
        audio = cloud.speak(message, env=self.env)
        play_wav(audio)

    def describe(self) -> str:
        labels = {"cloud": "online speech", "local": "local speech", "off": "text only"}
        return labels.get(self.backend, "text only")


def play_wav(audio: bytes) -> None:  # pragma: no cover - needs audio device
    """Play WAV bytes through the default output device."""
    if not microphone_available():
        raise FeatureUnavailable("audio playback needs the sounddevice library")
    import sounddevice as sd  # type: ignore

    with wave.open(io.BytesIO(audio), "rb") as handle:
        rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
    import numpy as np  # type: ignore

    samples = np.frombuffer(frames, dtype=np.int16)
    sd.play(samples, rate)
    sd.wait()
