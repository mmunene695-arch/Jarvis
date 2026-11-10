"""Read-only Gmail access through Google OAuth 2.0.

Only the ``gmail.readonly`` scope is requested. JARVIS never sends, deletes or
modifies mail.

Two supported setups:

1. A refresh token you generated once with :mod:`jarvis.integrations.gmail_auth`
   and stored in ``GMAIL_REFRESH_TOKEN`` (plus client id/secret).
2. An access token in ``GMAIL_ACCESS_TOKEN`` (short lived, handy for testing).
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..errors import AuthenticationError, IntegrationError, NetworkError

SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


def _env(env: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if env is None else env


@dataclass
class GmailClient:
    """Minimal read-only Gmail client."""

    refresh_token: str | None = None
    access_token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    timeout: float = 15.0
    _cache: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> GmailClient:
        env = _env(env)
        return cls(
            refresh_token=env.get("GMAIL_REFRESH_TOKEN") or None,
            access_token=env.get("GMAIL_ACCESS_TOKEN") or None,
            client_id=env.get("GMAIL_CLIENT_ID") or None,
            client_secret=env.get("GMAIL_CLIENT_SECRET") or None,
        )

    # ------------------------------------------------------------------
    def configured(self) -> bool:
        if self.access_token:
            return True
        return bool(self.refresh_token and self.client_id and self.client_secret)

    def _token(self) -> str:
        if self.access_token and self._cache.get("access_token") != self.access_token:
            return self.access_token
        cached = self._cache.get("access_token")
        if cached and float(self._cache.get("expires_at", 0)) - 30 > time.time():
            return str(cached)
        if not (self.refresh_token and self.client_id and self.client_secret):
            raise AuthenticationError(
                "Gmail is not configured. Run `python -m jarvis.integrations.gmail_auth` once, "
                "then set GMAIL_REFRESH_TOKEN, GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET. "
                "See INTEGRATIONS.md."
            )
        payload = urllib.parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode()
        request = urllib.request.Request(TOKEN_URL, data=payload, method="POST")
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise AuthenticationError(
                f"Google rejected the Gmail credentials (HTTP {exc.code}). Re-run the "
                "authorisation helper and update your environment variables."
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise NetworkError("I could not reach Google. Check your internet connection.") from exc
        token = data.get("access_token")
        if not token:
            raise AuthenticationError("Google did not return an access token.")
        self._cache["access_token"] = token
        self._cache["expires_at"] = time.time() + float(data.get("expires_in", 3600))
        return str(token)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{API_BASE}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, method="GET")
        request.add_header("Authorization", f"Bearer {self._token()}")
        request.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise AuthenticationError("Gmail access was rejected. Re-authorise the account.") from exc
            raise IntegrationError(f"Gmail returned HTTP {exc.code}.") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise NetworkError("I could not reach Gmail. Check your internet connection.") from exc

    # ------------------------------------------------------------------
    def unread(self, limit: int = 5, *, query: str = "is:unread") -> list[dict[str, Any]]:
        """Return up to ``limit`` unread messages (metadata only)."""
        limit = max(1, min(int(limit), 25))
        listing = self._get("/messages", {"q": query, "maxResults": limit})
        messages: list[dict[str, Any]] = []
        for item in listing.get("messages", []) or []:
            message_id = item.get("id")
            if not message_id:
                continue
            detail = self._get(
                f"/messages/{message_id}",
                {
                    "format": "metadata",
                    "metadataHeaders": ["From", "Subject", "Date"],
                },
            )
            headers = {
                header.get("name", "").lower(): header.get("value", "")
                for header in (detail.get("payload", {}) or {}).get("headers", []) or []
            }
            messages.append(
                {
                    "id": message_id,
                    "from": headers.get("from", "unknown sender"),
                    "subject": headers.get("subject", "(no subject)"),
                    "date": headers.get("date", ""),
                    "snippet": detail.get("snippet", ""),
                }
            )
        return messages


def unread_summary(limit: int = 5, env: Mapping[str, str] | None = None) -> str:
    """Human readable unread summary, used by the engine."""
    client = GmailClient.from_env(env)
    if not client.configured():
        raise AuthenticationError(
            "Gmail is not connected yet. Run `python -m jarvis.integrations.gmail_auth`, then "
            "set GMAIL_REFRESH_TOKEN, GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET. See INTEGRATIONS.md."
        )
    messages = client.unread(limit)
    if not messages:
        return "You have no unread Gmail messages."
    lines = [f"You have {len(messages)} unread Gmail message(s):"]
    for message in messages:
        sender = message["from"].split("<")[0].strip().strip('"') or message["from"]
        lines.append(f"• {sender}: {message['subject']}")
    return "\n".join(lines)
