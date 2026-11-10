"""Twilio SMS and outbound calls.

These actions can incur charges on your Twilio account. JARVIS always asks for
confirmation before sending, and a gesture cannot start a message or a call.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..errors import AuthenticationError, IntegrationError, NetworkError, ValidationError
from .whatsapp import normalise_number

API_BASE = "https://api.twilio.com/2010-04-01"


@dataclass(frozen=True)
class TwilioConfig:
    account_sid: str
    auth_token: str
    from_number: str
    to_number: str | None = None
    call_message: str = "Hello from JARVIS. Goodbye."
    default_country: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> TwilioConfig | None:
        env = os.environ if env is None else env
        sid = env.get("TWILIO_ACCOUNT_SID") or ""
        token = env.get("TWILIO_AUTH_TOKEN") or ""
        sender = env.get("TWILIO_FROM_NUMBER") or ""
        if not (sid and token and sender):
            return None
        return cls(
            account_sid=sid,
            auth_token=token,
            from_number=sender,
            to_number=env.get("TWILIO_TO_NUMBER") or None,
            call_message=env.get("TWILIO_CALL_MESSAGE") or "Hello from JARVIS. Goodbye.",
            default_country=env.get("JARVIS_DEFAULT_COUNTRY_CODE") or None,
        )


def configured(env: Mapping[str, str] | None = None) -> bool:
    return TwilioConfig.from_env(env) is not None


def _post(config: TwilioConfig, path: str, fields: dict[str, str], timeout: float = 20.0) -> dict[str, Any]:
    url = f"{API_BASE}/Accounts/{config.account_sid}/{path}"
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    token = base64.b64encode(f"{config.account_sid}:{config.auth_token}".encode()).decode()
    request.add_header("Authorization", f"Basic {token}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        if exc.code in (401, 403):
            raise AuthenticationError("Twilio rejected the account credentials.") from exc
        raise IntegrationError(f"Twilio returned HTTP {exc.code}. {detail}".strip()) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise NetworkError("I could not reach Twilio.") from exc


def send_sms(to: str | None, body: str, *, env: Mapping[str, str] | None = None) -> str:
    config = TwilioConfig.from_env(env)
    if config is None:
        raise AuthenticationError(
            "SMS is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and "
            "TWILIO_FROM_NUMBER. See INTEGRATIONS.md."
        )
    text = (body or "").strip()
    if not text:
        raise ValidationError("The SMS text was empty.")
    if len(text) > 1600:
        raise ValidationError("That SMS is too long (maximum 1600 characters).")
    recipient = to or config.to_number
    if not recipient:
        raise ValidationError("I need a destination number, or TWILIO_TO_NUMBER to be set.")
    number = "+" + normalise_number(recipient, config.default_country)
    data = _post(config, "Messages.json", {"To": number, "From": config.from_number, "Body": text})
    return f"SMS sent to {number} (SID {data.get('sid', 'unknown')}). Charges may apply."


def place_call(to: str | None, *, message: str | None = None, env: Mapping[str, str] | None = None) -> str:
    config = TwilioConfig.from_env(env)
    if config is None:
        raise AuthenticationError(
            "Calls are not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and "
            "TWILIO_FROM_NUMBER. See INTEGRATIONS.md."
        )
    recipient = to or config.to_number
    if not recipient:
        raise ValidationError("I need a number to call.")
    number = "+" + normalise_number(recipient, config.default_country)
    twiml = f"<Response><Say>{_escape(message or config.call_message)}</Say></Response>"
    data = _post(
        config,
        "Calls.json",
        {"To": number, "From": config.from_number, "Twiml": twiml},
    )
    return f"Outbound call placed to {number} (SID {data.get('sid', 'unknown')}). Charges may apply."


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
