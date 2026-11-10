"""One-time Google OAuth helper for read-only Gmail access.

Run this on a machine with a browser::

    python -m jarvis.integrations.gmail_auth

It prints the refresh token so you can export ``GMAIL_REFRESH_TOKEN``. The
authorisation is read-only (``gmail.readonly``); JARVIS cannot send or delete
mail. Nothing is written into your Gmail account.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser

from .gmail import SCOPE, TOKEN_URL

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
REDIRECT = "http://localhost:8765/"


def authorise(client_id: str, client_secret: str, *, port: int = 8765) -> dict[str, str]:
    """Run the installed-app loopback flow and return the token payload."""
    import http.server
    import threading

    state = secrets.token_urlsafe(16)
    redirect = f"http://localhost:{port}/"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    captured: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            captured.update({k: v[0] for k, v in query.items() if v})
            body = (
                b"<html><body style='font-family:sans-serif;padding:2rem'>"
                b"<h2>JARVIS: Gmail authorisation received</h2>"
                b"<p>You can close this tab and return to the terminal.</p></body></html>"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args) -> None:  # silence the default logger
            return

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    print("Open this URL in your browser and grant read-only Gmail access:\n")
    print(url + "\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    thread.join(timeout=300)
    server.server_close()

    if "error" in captured:
        raise SystemExit(f"Google returned an error: {captured['error']}")
    if captured.get("state") != state:
        raise SystemExit("State mismatch: the redirect did not come from this request.")
    code = captured.get("code")
    if not code:
        raise SystemExit("No authorisation code was received (timed out?).")

    payload = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect,
        }
    ).encode()
    request = urllib.request.Request(TOKEN_URL, data=payload, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    client_id = os.environ.get("GMAIL_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print(__doc__)
        print("Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET first (from Google Cloud Console,")
        print("OAuth client type: Desktop app). See INTEGRATIONS.md.\n")
        return 2
    try:
        tokens = authorise(client_id, client_secret)
    except SystemExit as exc:
        print(exc)
        return 1
    refresh = tokens.get("refresh_token")
    if not refresh:
        print("Google did not return a refresh token. Revoke the app's access and try again")
        print("(a refresh token is only issued with prompt=consent on a first consent).")
        return 1
    print("\nSuccess. Add these to your environment (or your .env / system variables):\n")
    print(f"  GMAIL_CLIENT_ID={client_id}")
    print(f"  GMAIL_CLIENT_SECRET={client_secret}")
    print(f"  GMAIL_REFRESH_TOKEN={refresh}")
    print("\nJARVIS only has read-only access and cannot send or delete mail.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
