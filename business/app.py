#!/usr/bin/env python3
"""
KaziPesa Digital — live order page.

Standard library only. Serves the landing page, accepts orders, writes them
straight into ops/ledger.csv so `track.py dashboard` picks them up.

    python3 business/app.py              # http://localhost:8000
    python3 business/app.py --port 8080
    python3 business/app.py --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
LANDING = HERE / "sales" / "landing"
LEDGER = HERE / "ops" / "ledger.csv"
TEMPLATE = LANDING / "template.html"
CONFIG = HERE / "brand" / "config.json"

LEDGER_HEADER = ["date", "product", "amount_kes", "channel", "customer", "note"]

PRODUCTS = {
    "cv-makeover": ("CV Makeover", 800),
    "cv-linkedin": ("CV + LinkedIn Combo", 1_500),
    "social-pack": ("Social Starter Pack", 2_000),
    "business-plan": ("Biashara Plan (done for you)", 3_500),
    "kit-cv": ("CV & Cover Letter Kit", 300),
    "kit-pesa": ("Pesa Tracker", 500),
    "kit-plan": ("Biashara Plan Pack", 1_500),
    "bundle": ("KaziPesa Complete", 1_900),
    "free-guide": ("Free CV guide (lead magnet)", 0),
    "other": ("Other / custom", 0),
}

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".webmanifest": "application/manifest+json",
}


def clean(value: str, limit: int = 300) -> str:
    """Defend the ledger against CSV injection and line breaks."""
    out = str(value or "").replace("\r", " ").replace("\n", " ").replace(",", " ")
    return out.strip().lstrip("=+-@\t")[:limit]


def brand() -> str:
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8")).get("brand", "KaziPesa Digital")
    except Exception:  # noqa: BLE001
        return "KaziPesa Digital"


def whatsapp_int() -> str:
    try:
        raw = json.loads(CONFIG.read_text(encoding="utf-8")).get("whatsapp", "")
    except Exception:  # noqa: BLE001
        raw = ""
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if digits.startswith("254") and len(digits) >= 11:
        return digits[:12]
    if digits.startswith("0") and len(digits) >= 10:
        return "254" + digits[1:13]
    return "254700000000"


def render_index() -> bytes:
    """Prefer the generated page; fall back to rendering the template."""
    index = LANDING / "index.html"
    if index.exists():
        return index.read_bytes()
    if not TEMPLATE.exists():
        return (b"<h1>Run <code>python3 business/ops/setup.py</code> first.</h1>")
    html = TEMPLATE.read_text(encoding="utf-8")
    mapping = {"{{BRAND}}": brand(), "{{WHATSAPP_INT}}": whatsapp_int()}
    for token, value in mapping.items():
        html = html.replace(token, value)
    return html.encode("utf-8")


def log_order(data: dict) -> tuple[dict, int]:
    product = clean(data.get("product", "other"), 40)
    if product not in PRODUCTS:
        return {"ok": False, "message": f"Unknown product '{product}'."}, 400
    name = clean(data.get("name", ""), 80)
    phone = clean(data.get("phone", ""), 40)
    notes = clean(data.get("notes", ""), 300)
    if not name or not phone:
        return {"ok": False, "message": "Name and WhatsApp number are required."}, 400

    label, price = PRODUCTS[product]
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    fresh = not LEDGER.exists() or LEDGER.stat().st_size == 0
    with LEDGER.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEDGER_HEADER)
        if fresh:
            writer.writeheader()
        writer.writerow({
            "date": date.today().isoformat(),
            "product": product,
            "amount_kes": f"{price:.0f}",
            "channel": "landing",
            "customer": name,
            "note": f"{phone} | {notes}".strip(" |"),
        })

    if product == "free-guide":
        message = "On its way! Check WhatsApp shortly for your free guide."
    else:
        message = f"Order received — {label}, KES {price:,}. I'll confirm on WhatsApp within the hour."
    return {"ok": True, "message": message, "product": label, "amount": price}, 200


def ledger_stats() -> dict:
    if not LEDGER.exists():
        return {"orders": 0, "revenue": 0}
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if any(v.strip() for v in r.values())]
    revenue = 0
    orders = 0
    for row in rows:
        try:
            revenue += float(row.get("amount_kes") or 0)
        except ValueError:
            pass
        if (row.get("product") or "") != "free-guide":
            orders += 1
    return {"orders": orders, "revenue": revenue}


class Handler(BaseHTTPRequestHandler):
    server_version = "KaziPesa/1.0"

    def _send(self, body: bytes, status: int = 200, ctype: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self):  # noqa: N802
        self.do_GET()

    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if path == "/favicon.ico":
            self._send(b"", 204, "image/x-icon")
            return
        if path == "/api/stats":
            self._send(json.dumps(ledger_stats()).encode(), 200, "application/json")
            return
        if path == "/healthz":
            self._send(b"ok", 200, "text/plain; charset=utf-8")
            return

        if path in ("/", "/index.html"):
            self._send(render_index())
            return

        target = (LANDING / path.lstrip("/")).resolve()
        if LANDING.resolve() in target.parents and target.is_file():
            self._send(target.read_bytes(), 200,
                       MIME.get(target.suffix.lower(), "application/octet-stream"))
            return

        self._send(b"<h1>404</h1><p><a href='/'>Back to the shop</a></p>", 404)

    def do_POST(self):  # noqa: N802
        if self.path.split("?", 1)[0].rstrip("/") != "/api/order":
            self._send(json.dumps({"ok": False, "message": "Not found"}).encode(),
                       404, "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, OSError):
            payload = {}
        result, status = log_order(payload)
        self._send(json.dumps(result).encode(), status, "application/json")

    def log_message(self, fmt: str, *args) -> None:  # noqa: A002
        sys.stderr.write("  %s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    parser = argparse.ArgumentParser(description="KaziPesa Digital order page server.")
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="port (default 8000)")
    args = parser.parse_args()

    if not (LANDING / "index.html").exists() and not TEMPLATE.exists():
        print("No landing page found. Expected business/sales/landing/index.html")
        return 1

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print()
    print("  KaziPesa Digital — order page running")
    print(f"  Local:   http://localhost:{args.port}")
    print(f"  Orders:  logged to {LEDGER.relative_to(HERE.parent)}")
    print(f"  Stats:   http://localhost:{args.port}/api/stats")
    print("\n  Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
