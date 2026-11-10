"""WhatsApp Cloud API (Meta) outbound messages.

Outbound only. Receiving incoming messages requires a Meta webhook and a
publicly reachable HTTPS endpoint, which JARVIS does not host for you.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..errors import AuthenticationError, IntegrationError, NetworkError, ValidationError

DEFAULT_API_VERSION = "v21.0"
MAX_TEXT = 4096


def _env(env: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if env is None else env


def normalise_number(raw: str, default_country: str | None = None) -> str:
    """Normalise a phone number to E.164 digits without the plus sign."""
    cleaned = re.sub(r"[\s\-().]", "", (raw or "").strip())
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    if cleaned.startswith("+"):
        digits = cleaned[1:]
    else:
        prefix = (default_country or os.environ.get("JARVIS_DEFAULT_COUNTRY_CODE", "")).lstrip("+")
        if prefix:
            local = cleaned[1:] if cleaned.startswith("0") else cleaned
            digits = f"{prefix}{local}"
        else:
            digits = cleaned
    if not digits.isdigit() or not 7 <= len(digits) <= 15:
        raise ValidationError(
            "That phone number is not valid. Use the international format, for example +254700000000."
        )
    return digits


@dataclass(frozen=True)
class WhatsAppConfig:
    token: str
    phone_number_id: str
    api_version: str = DEFAULT_API_VERSION
    default_country: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> WhatsAppConfig | None:
        env = _env(env)
        token = env.get("WHATSAPP_TOKEN") or ""
        phone_id = env.get("WHATSAPP_PHONE_NUMBER_ID") or ""
        if not token or not phone_id:
            return None
        return cls(
            token=token,
            phone_number_id=phone_id,
            api_version=env.get("WHATSAPP_API_VERSION") or DEFAULT_API_VERSION,
            default_country=env.get("JARVIS_DEFAULT_COUNTRY_CODE") or None,
        )


def configured(env: Mapping[str, str] | None = None) -> bool:
    return WhatsAppConfig.from_env(env) is not None


def send_text(to: str, body: str, *, env: Mapping[str, str] | None = None, timeout: float = 20.0) -> str:
    """Send one text message. Raises an actionable error when unconfigured."""
    config = WhatsAppConfig.from_env(env)
    if config is None:
        raise AuthenticationError(
            "WhatsApp is not configured. Set WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID. "
            "See INTEGRATIONS.md."
        )
    text = (body or "").strip()
    if not text:
        raise ValidationError("The WhatsApp message was empty.")
    if len(text) > MAX_TEXT:
        raise ValidationError(f"WhatsApp messages are limited to {MAX_TEXT} characters.")
    number = normalise_number(to, config.default_country)
    payload: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    url = f"https://graph.facebook.com/{config.api_version}/{config.phone_number_id}/messages"
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), method="POST"
    )
    request.add_header("Authorization", f"Bearer {config.token}")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        if exc.code in (401, 403):
            raise AuthenticationError("Meta rejected the WhatsApp token.") from exc
        raise IntegrationError(f"WhatsApp returned HTTP {exc.code}. {detail}".strip()) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise NetworkError("I could not reach the WhatsApp Cloud API.") from exc
    message_id = ((data.get("messages") or [{}])[0] or {}).get("id", "")
    return f"WhatsApp message sent to +{number}" + (f" (id {message_id})." if message_id else ".")
