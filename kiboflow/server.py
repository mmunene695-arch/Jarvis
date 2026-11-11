"""Zero-dependency HTTP server for KiboFlow Studio (Storefront + Demos + Founder Command Center)."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from kiboflow.store import KiboFlowStore, calculate_roi, run_instant_audit

WEB_DIR = Path(__file__).resolve().parent / "web"

STATIC_ROUTES: dict[str, tuple[str, str]] = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/ops": ("ops.html", "text/html; charset=utf-8"),
    "/ops/": ("ops.html", "text/html; charset=utf-8"),
    "/ops.html": ("ops.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/ops.js": ("ops.js", "application/javascript; charset=utf-8"),
    "/demos/hospitality": ("demos/hospitality.html", "text/html; charset=utf-8"),
    "/demos/hospitality.html": ("demos/hospitality.html", "text/html; charset=utf-8"),
    "/demos/clinic": ("demos/clinic.html", "text/html; charset=utf-8"),
    "/demos/clinic.html": ("demos/clinic.html", "text/html; charset=utf-8"),
    "/demos/hardware": ("demos/hardware.html", "text/html; charset=utf-8"),
    "/demos/hardware.html": ("demos/hardware.html", "text/html; charset=utf-8"),
}


def make_handler(store: KiboFlowStore) -> type[BaseHTTPRequestHandler]:
    class KiboFlowHandler(BaseHTTPRequestHandler):
        server_version = "KiboFlowStudio/1.0"

        def log_message(self, fmt: str, *args: Any) -> None:
            # Keep logs concise and readable
            return

        def _send_json(self, status: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_static(self, rel_path: str, content_type: str) -> None:
            target = (WEB_DIR / rel_path).resolve()
            if not str(target).startswith(str(WEB_DIR.resolve())) or not target.is_file():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                return
            data = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                return {}
            raw = self.rfile.read(min(length, 1_048_576))
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if path == "/api/health":
                self._send_json(HTTPStatus.OK, {"ok": True, "service": "KiboFlow Studio"})
                return
            if path == "/api/overview":
                self._send_json(HTTPStatus.OK, store.get_overview())
                return
            if path == "/api/packages":
                self._send_json(HTTPStatus.OK, {"packages": store.list_packages()})
                return
            if path == "/api/leads":
                stage = query.get("stage", [None])[0]
                self._send_json(HTTPStatus.OK, {"leads": store.list_leads(stage=stage)})
                return
            if path == "/api/decisions":
                self._send_json(HTTPStatus.OK, {"decisions": store.list_decisions()})
                return
            if path == "/api/invoices":
                self._send_json(HTTPStatus.OK, {"invoices": store.list_invoices()})
                return
            if path == "/api/roi":
                visitors = int(query.get("visitors", ["1200"])[0])
                avg_order = int(query.get("avg_order_kes", ["3500"])[0])
                curr_pct = float(query.get("current_pct", ["1.2"])[0])
                targ_pct = float(query.get("target_pct", ["3.8"])[0])
                pkg_cost = int(query.get("package_cost_kes", ["45000"])[0])
                self._send_json(
                    HTTPStatus.OK,
                    calculate_roi(visitors, avg_order, curr_pct, targ_pct, pkg_cost),
                )
                return

            route = STATIC_ROUTES.get(path)
            if route:
                self._send_static(route[0], route[1])
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Unknown route: {path}"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            try:
                body = self._read_json_body()
            except (ValueError, UnicodeDecodeError):
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON payload"})
                return

            if path == "/api/leads":
                try:
                    created = store.create_lead(body)
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                self._send_json(HTTPStatus.CREATED, {"lead": created})
                return

            if path == "/api/audit":
                audit = run_instant_audit(
                    business_name=str(body.get("business_name") or ""),
                    website_url=str(body.get("website_url") or ""),
                    sector=str(body.get("sector") or "Hospitality & Local Services"),
                )
                if body.get("save_lead") and str(body.get("business_name") or "").strip():
                    store.create_lead(
                        {
                            "company": str(body.get("business_name")).strip(),
                            "contact_name": str(body.get("contact_name") or "").strip(),
                            "phone": str(body.get("phone") or "").strip(),
                            "email": str(body.get("email") or "").strip(),
                            "location": str(body.get("location") or "Kenya").strip(),
                            "sector": str(body.get("sector") or "SMB").strip(),
                            "track": "Inbound Web",
                            "stage": "Inbound Web",
                            "priority": 1,
                            "ask_kes": audit["recommended_package"]["price_kes"],
                            "pain_point": audit["headline"],
                            "next_action": "Follow up via WhatsApp with custom audit & live demo",
                        }
                    )
                self._send_json(HTTPStatus.OK, {"audit": audit})
                return

            if path == "/api/pitch":
                try:
                    lead_id = int(body.get("lead_id") or 0)
                    override = body.get("price_override_kes")
                    override_int = int(override) if override is not None and str(override).strip() else None
                    bundle = store.generate_pitch_and_invoice(lead_id, override_int)
                except KeyError as exc:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                    return
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                self._send_json(HTTPStatus.OK, bundle)
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Unknown POST route: {path}"})

        def do_PATCH(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            if path.startswith("/api/leads/"):
                raw_id = path.rsplit("/", 1)[-1]
                try:
                    lead_id = int(raw_id)
                    body = self._read_json_body()
                    stage = str(body.get("stage") or "")
                    next_action = body.get("next_action")
                    deposit_paid = body.get("deposit_paid_kes")
                    deposit_int = int(deposit_paid) if deposit_paid is not None else None
                    updated = store.update_lead_stage(
                        lead_id=lead_id,
                        stage=stage,
                        next_action=str(next_action) if next_action is not None else None,
                        deposit_paid_kes=deposit_int,
                    )
                except KeyError as exc:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                    return
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                self._send_json(HTTPStatus.OK, {"lead": updated})
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Unknown PATCH route: {path}"})

    return KiboFlowHandler


def create_server(host: str = "0.0.0.0", port: int = 8000, store: KiboFlowStore | None = None) -> ThreadingHTTPServer:
    active_store = store or KiboFlowStore()
    return ThreadingHTTPServer((host, port), make_handler(active_store))
