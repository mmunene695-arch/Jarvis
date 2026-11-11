"""Online service wrappers: provider selection and error handling."""

from __future__ import annotations

import io
import json
import urllib.error

import pytest

from jarvis import cloud
from jarvis.errors import AuthenticationError, NetworkError, ValidationError

OPENAI_ENV = {"OPENAI_API_KEY": "sk-test-key"}
GEMINI_ENV = {"GEMINI_API_KEY": "gem-key"}


def fake_response(payload: dict):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(payload).encode()

    return FakeResponse()


def test_no_provider_without_keys():
    assert cloud.active_provider({}) is None
    assert cloud.available({}) is False


def test_openai_preferred_when_both_keys(monkeypatch: pytest.MonkeyPatch):
    provider = cloud.active_provider({**OPENAI_ENV, **GEMINI_ENV})
    assert provider.name == "openai"


def test_gemini_used_when_only_gemini_key():
    assert cloud.active_provider(GEMINI_ENV).name == "gemini"


def test_provider_override():
    assert cloud.active_provider({**OPENAI_ENV, **GEMINI_ENV, "JARVIS_LLM_PROVIDER": "gemini"}).name == "gemini"


def test_complete_without_key():
    with pytest.raises(AuthenticationError):
        cloud.complete("hello", env={})


def test_complete_empty_prompt():
    with pytest.raises(ValidationError):
        cloud.complete("   ", env=OPENAI_ENV)


def test_openai_chat_round_trip(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode())
        return fake_response({"choices": [{"message": {"content": "Four seconds."}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert cloud.complete("how fast?", env=OPENAI_ENV) == "Four seconds."
    assert captured["url"].endswith("/chat/completions")
    assert captured["body"]["messages"][0]["role"] == "system"


def test_gemini_chat_round_trip(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(request, timeout=None):
        return fake_response({"candidates": [{"content": {"parts": [{"text": "Gemini reply"}]}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert cloud.complete("hi", env=GEMINI_ENV) == "Gemini reply"


def test_http_401_is_authentication_error(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 401, "no", {}, io.BytesIO(b"bad key"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(AuthenticationError):
        cloud.complete("hi", env=OPENAI_ENV)


def test_url_error_is_network_error(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(NetworkError):
        cloud.complete("hi", env=OPENAI_ENV)


def test_rate_limit_message(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 429, "slow", {}, io.BytesIO(b""))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(NetworkError):
        cloud.complete("hi", env=OPENAI_ENV)


def test_transcribe_without_key():
    with pytest.raises(AuthenticationError):
        cloud.transcribe(b"RIFF....", env={})


def test_transcribe_builds_multipart(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["body"] = request.data
        return fake_response({"text": "open notepad"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert cloud.transcribe(b"AUDIO", env=OPENAI_ENV) == "open notepad"
    assert captured["url"].endswith("/audio/transcriptions")
    assert b'name="file"' in captured["body"]


def test_describe_image_requires_key():
    with pytest.raises(AuthenticationError):
        cloud.describe_image(b"png", env={})


def test_describe_image_round_trip(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(request, timeout=None):
        body = json.loads(request.data.decode())
        parts = body["messages"][0]["content"]
        assert any(p.get("type") == "image_url" for p in parts)
        return fake_response({"choices": [{"message": {"content": "A code editor."}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert "code editor" in cloud.describe_image(b"PNGDATA", env=OPENAI_ENV)
