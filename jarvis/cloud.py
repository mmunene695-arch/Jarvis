"""Online services: language-model answers, speech-to-text, vision, narration.

Only the standard library is used (``urllib`` + ``json``) so the core install
stays small. Every function raises a :class:`JarvisError` subclass with an
actionable message instead of leaking provider errors.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .errors import AuthenticationError, NetworkError, ValidationError

DEFAULT_TIMEOUT = float(os.environ.get("JARVIS_HTTP_TIMEOUT", "20"))
DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_CHAT_MODEL = os.environ.get("JARVIS_LLM_MODEL", "gpt-4o-mini")
DEFAULT_GEMINI_MODEL = os.environ.get("JARVIS_GEMINI_MODEL", "gemini-2.0-flash")
DEFAULT_STT_MODEL = os.environ.get("JARVIS_STT_MODEL", "whisper-1")
DEFAULT_VISION_MODEL = os.environ.get("JARVIS_VISION_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = (
    "You are JARVIS, a concise desktop voice assistant. Answer in at most three short "
    "sentences because your reply is spoken aloud. Never claim to have run a shell command, "
    "installed software or changed the computer. If the request is outside your abilities, say "
    "so plainly and offer a local alternative."
)


@dataclass(frozen=True)
class Provider:
    name: str
    key: str
    base: str
    model: str


def _env(env: Mapping[str, str] | None = None) -> Mapping[str, str]:
    return os.environ if env is None else env


def active_provider(env: Mapping[str, str] | None = None, task: str = "chat") -> Provider | None:
    """Pick the first configured provider for ``task``."""
    env = _env(env)
    gemini_key = env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY") or env.get("JARVIS_VISION_API_KEY", "")
    openai_key = env.get("OPENAI_API_KEY") or env.get("JARVIS_LLM_API_KEY") or env.get("JARVIS_VISION_API_KEY", "")
    preferred = (env.get("JARVIS_LLM_PROVIDER") or "auto").lower()
    openai = Provider(
        "openai",
        openai_key,
        (env.get("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE).rstrip("/"),
        env.get("JARVIS_LLM_MODEL") or DEFAULT_CHAT_MODEL,
    )
    gemini = Provider(
        "gemini",
        gemini_key,
        DEFAULT_GEMINI_BASE,
        env.get("JARVIS_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL,
    )
    if preferred == "gemini" and gemini.key:
        return gemini
    if preferred == "openai" and openai.key:
        return openai
    if openai.key:
        return openai
    if gemini.key:
        return gemini
    return None


def available(env: Mapping[str, str] | None = None, task: str = "chat") -> bool:
    provider = active_provider(env, task)
    return provider is not None and bool(provider.key)


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    for key, value in headers.items():
        request.add_header(key, value)
    return _send(request, timeout)


def _send(request: urllib.request.Request, timeout: float) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        if exc.code in (401, 403):
            raise AuthenticationError(
                f"The API key was rejected ({exc.code}). Check your environment variables."
            ) from exc
        if exc.code == 429:
            raise NetworkError("The online service is rate limiting requests. Try again shortly.") from exc
        raise NetworkError(f"The online service returned HTTP {exc.code}. {detail}".strip()) from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise NetworkError(
            f"I could not reach the online service ({reason}). Check your internet connection."
        ) from exc
    except socket.timeout as exc:
        raise NetworkError("The online service timed out.") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise NetworkError("The online service returned a response I could not read.") from exc


def _extract_openai_text(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        raise NetworkError("The model returned an empty answer.")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        return " ".join(part.get("text", "") for part in content if isinstance(part, dict)).strip()
    return str(content or "").strip()


def _extract_gemini_text(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        raise NetworkError("The model returned an empty answer.")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    return " ".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()


def complete(
    prompt: str,
    *,
    context: str | None = None,
    system: str = SYSTEM_PROMPT,
    timeout: float = DEFAULT_TIMEOUT,
    env: Mapping[str, str] | None = None,
) -> str:
    """Ask the configured language model a question."""
    if not (prompt or "").strip():
        raise ValidationError("nothing to ask")
    provider = active_provider(env)
    if provider is None:
        raise AuthenticationError(
            "No language-model key is configured. Set OPENAI_API_KEY or GEMINI_API_KEY."
        )
    contents = prompt if not context else f"Recent conversation:\n{context}\n\nUser: {prompt}"
    if provider.name == "openai":
        payload = {
            "model": provider.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": contents},
            ],
            "temperature": 0.3,
            "max_tokens": 320,
        }
        data = _post_json(
            f"{provider.base}/chat/completions",
            payload,
            {"Authorization": f"Bearer {provider.key}"},
            timeout,
        )
        return _extract_openai_text(data)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": f"{system}\n\n{contents}"}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 320},
    }
    url = f"{provider.base}/models/{provider.model}:generateContent?key={urllib.parse.quote(provider.key)}"
    data = _post_json(url, payload, {}, timeout)
    return _extract_gemini_text(data)


# ----------------------------------------------------------------------
# Speech to text
# ----------------------------------------------------------------------
def transcribe(
    audio: bytes,
    *,
    filename: str = "speech.wav",
    language: str | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Transcribe recorded audio with the configured online STT service."""
    if not audio:
        raise ValidationError("no audio was recorded")
    env = _env(env)
    key = env.get("OPENAI_API_KEY") or env.get("JARVIS_LLM_API_KEY") or ""
    if not key:
        raise AuthenticationError(
            "Speech-to-text needs an online service. Set OPENAI_API_KEY to enable it, "
            "or use the offline console instead."
        )
    boundary = "----jarvis" + base64.urlsafe_b64encode(os.urandom(9)).decode().strip("=")
    parts: list[bytes] = []

    def field(name: str, value: str) -> None:
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
        )

    field("model", env.get("JARVIS_STT_MODEL") or DEFAULT_STT_MODEL)
    field("response_format", "json")
    if language:
        field("language", language)
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"{filename}\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
    )
    parts.append(audio)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)
    base = (env.get("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE).rstrip("/")
    request = urllib.request.Request(f"{base}/audio/transcriptions", data=body, method="POST")
    request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    request.add_header("Authorization", f"Bearer {key}")
    data = _send(request, timeout)
    text = str(data.get("text") or "").strip()
    if not text:
        raise NetworkError("I could not make out any speech in that recording.")
    return text


# ----------------------------------------------------------------------
# Vision
# ----------------------------------------------------------------------
def describe_image(
    image_bytes: bytes,
    *,
    prompt: str = "Describe what is on this screen concisely.",
    mime: str = "image/png",
    env: Mapping[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Send one image to the configured vision model."""
    if not image_bytes:
        raise ValidationError("the screenshot was empty")
    provider = active_provider(env)
    if provider is None:
        raise AuthenticationError(
            "Screen analysis needs a vision-capable key. Set OPENAI_API_KEY or JARVIS_VISION_API_KEY."
        )
    encoded = base64.b64encode(image_bytes).decode("ascii")
    if provider.name == "openai":
        payload = {
            "model": env.get("JARVIS_VISION_MODEL") if env and env.get("JARVIS_VISION_MODEL") else DEFAULT_VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt + " Keep it to four sentences."},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
                    ],
                }
            ],
            "max_tokens": 400,
        }
        data = _post_json(
            f"{provider.base}/chat/completions",
            payload,
            {"Authorization": f"Bearer {provider.key}"},
            timeout,
        )
        return _extract_openai_text(data)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt + " Keep it to four sentences."},
                    {"inline_data": {"mime_type": mime, "data": encoded}},
                ],
            }
        ]
    }
    url = f"{provider.base}/models/{provider.model}:generateContent?key={urllib.parse.quote(provider.key)}"
    return _extract_gemini_text(_post_json(url, payload, {}, timeout))


def speak(
    text: str,
    *,
    voice: str | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_chars: int = 1200,
) -> bytes:
    """Synthesise speech and return WAV bytes (online TTS)."""
    if not (text or "").strip():
        raise ValidationError("nothing to speak")
    env = _env(env)
    key = env.get("OPENAI_API_KEY") or env.get("JARVIS_LLM_API_KEY") or ""
    if not key:
        raise AuthenticationError("Online speech needs OPENAI_API_KEY. Local speech uses pyttsx3.")
    base = (env.get("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE).rstrip("/")
    payload = {
        "model": env.get("JARVIS_TTS_MODEL") or "gpt-4o-mini-tts",
        "voice": voice or env.get("JARVIS_TTS_VOICE") or "alloy",
        "input": text[:max_chars],
        "response_format": "wav",
    }
    request = urllib.request.Request(
        f"{base}/audio/speech", data=json.dumps(payload).encode("utf-8"), method="POST"
    )
    request.add_header("Content-Type", "application/json")
    request.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            audio = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise AuthenticationError("The speech key was rejected.") from exc
        raise NetworkError(f"The speech service returned HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise NetworkError("I could not reach the speech service.") from exc
    if not audio:
        raise NetworkError("The speech service returned no audio.")
    return audio


