"""Integrations: request building, validation and error messages (no live calls)."""

from __future__ import annotations

import base64
import io
import json
import urllib.error

import pytest

from jarvis.errors import AuthenticationError, IntegrationError, ValidationError
from jarvis.integrations import gmail, twilio_client, whatsapp


# ----------------------------------------------------------------------
# WhatsApp
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("+254700000000", "254700000000"),
        ("+254 700 000 000", "254700000000"),
        ("00254700000000", "254700000000"),
        ("(254) 700-000-000", "254700000000"),
    ],
)
def test_whatsapp_number_normalisation(raw: str, expected: str):
    assert whatsapp.normalise_number(raw) == expected


def test_whatsapp_country_code_default(monkeypatch: pytest.MonkeyPatch):
    assert whatsapp.normalise_number("0700000000", "254") == "254700000000"


@pytest.mark.parametrize("bad", ["", "abc", "+12"])
def test_whatsapp_invalid_numbers(bad: str):
    with pytest.raises(ValidationError):
        whatsapp.normalise_number(bad)


def test_whatsapp_not_configured():
    assert not whatsapp.configured({})
    with pytest.raises(AuthenticationError):
        whatsapp.send_text("+254700000000", "hello", env={})


def test_whatsapp_payload_shape(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"messages": [{"id": "wamid.TEST"}]}).encode()

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode())
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    env = {"WHATSAPP_TOKEN": "token-123", "WHATSAPP_PHONE_NUMBER_ID": "999"}
    message = whatsapp.send_text("+254700000000", "I am on my way", env=env)
    assert "sent" in message
    assert captured["body"]["text"]["body"] == "I am on my way"
    assert captured["body"]["to"] == "254700000000"
    assert captured["body"]["messaging_product"] == "whatsapp"
    assert "graph.facebook.com" in captured["url"]
    assert captured["headers"]["Authorization"] == "Bearer token-123"


def test_whatsapp_rejects_empty_text(monkeypatch: pytest.MonkeyPatch):
    env = {"WHATSAPP_TOKEN": "t", "WHATSAPP_PHONE_NUMBER_ID": "1"}
    with pytest.raises(ValidationError):
        whatsapp.send_text("+254700000000", "  ", env=env)


def test_whatsapp_http_error_is_integration_error(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 500, "boom", {}, io.BytesIO(b"oops"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    env = {"WHATSAPP_TOKEN": "t", "WHATSAPP_PHONE_NUMBER_ID": "1"}
    with pytest.raises(IntegrationError):
        whatsapp.send_text("+254700000000", "hello", env=env)


# ----------------------------------------------------------------------
# Twilio
# ----------------------------------------------------------------------
def test_twilio_not_configured():
    assert not twilio_client.configured({})
    with pytest.raises(AuthenticationError):
        twilio_client.send_sms("+254700000000", "hi", env={})
    with pytest.raises(AuthenticationError):
        twilio_client.place_call("+254700000000", env={})


def test_twilio_sms_request(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"sid": "SM123"}).encode()

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["body"] = request.data.decode()
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    env = {
        "TWILIO_ACCOUNT_SID": "ACxxxxxxxx",
        "TWILIO_AUTH_TOKEN": "secret",
        "TWILIO_FROM_NUMBER": "+15550001111",
    }
    result = twilio_client.send_sms("+254700000000", "hello there", env=env)
    assert "SM123" in result
    assert "hello+there" in captured["body"] or "hello%20there" in captured["body"]
    expected = base64.b64encode(b"ACxxxxxxxx:secret").decode()
    assert captured["auth"] == f"Basic {expected}"
    assert "Messages.json" in captured["url"]


def test_twilio_call_escapes_twiml(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"sid": "CA123"}).encode()

    def fake_urlopen(request, timeout=None):
        captured["body"] = request.data.decode()
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    env = {
        "TWILIO_ACCOUNT_SID": "ACxxxxxxxx",
        "TWILIO_AUTH_TOKEN": "secret",
        "TWILIO_FROM_NUMBER": "+15550001111",
        "TWILIO_CALL_MESSAGE": 'Hi <b>& "you"',
    }
    twilio_client.place_call("+254700000000", env=env)
    body = captured["body"]
    assert "Calls.json" not in body  # the TwiML is the body, not the URL
    assert "%3CResponse%3E" in body or "<Response>" in body
    assert "%26" in body or "&amp;" in body


# ----------------------------------------------------------------------
# Gmail
# ----------------------------------------------------------------------
def test_gmail_not_configured():
    client = gmail.GmailClient.from_env({})
    assert not client.configured()
    with pytest.raises(AuthenticationError):
        gmail.unread_summary(env={})


def test_gmail_readonly_scope():
    assert gmail.SCOPE.endswith("gmail.readonly")


def test_gmail_unread_summary_formats_messages(monkeypatch: pytest.MonkeyPatch):
    client = gmail.GmailClient(access_token="token")

    def fake_get(path, params=None):
        if path == "/messages":
            return {"messages": [{"id": "1"}, {"id": "2"}]}
        if path == "/messages/1":
            return {
                "snippet": "hello",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "Alice <alice@example.com>"},
                        {"name": "Subject", "value": "Lunch?"},
                    ]
                },
            }
        return {
            "snippet": "",
            "payload": {"headers": [{"name": "From", "value": "bob@example.com"}, {"name": "Subject", "value": "Report"}]},
        }

    monkeypatch.setattr(client, "_get", fake_get)
    messages = client.unread()
    assert len(messages) == 2
    assert messages[0]["subject"] == "Lunch?"
    assert messages[0]["from"].startswith("Alice")


def test_gmail_refresh_without_secrets_raises():
    client = gmail.GmailClient(refresh_token="r", client_id=None, client_secret=None)
    with pytest.raises(AuthenticationError):
        client.unread()


# ----------------------------------------------------------------------
# Guards used by the engine
# ----------------------------------------------------------------------
def test_integrations_expose_configured_helpers():
    for module in (whatsapp, twilio_client):
        assert isinstance(module.configured({}), bool)
    assert isinstance(gmail.GmailClient.from_env({}).configured(), bool)
