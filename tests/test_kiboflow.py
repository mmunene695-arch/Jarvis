"""Offline test suite for KiboFlow Studio CRM, ROI engine, static exporter, and HTTP server."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen

from kiboflow.exporter import export_static_site
from kiboflow.server import create_server
from kiboflow.store import KiboFlowStore, calculate_roi, run_instant_audit


def test_store_seed_and_overview(tmp_path: Path) -> None:
    store = KiboFlowStore(db_path=tmp_path / "test.db")
    overview = store.get_overview()
    assert overview["company"]["name"] == "KiboFlow Studio"
    assert overview["metrics"]["total_leads"] >= 9
    assert overview["metrics"]["local_pipeline_kes"] == 310000
    assert overview["metrics"]["decisions_logged"] >= 5


def test_lead_lifecycle_and_pitch_invoice(tmp_path: Path) -> None:
    store = KiboFlowStore(db_path=tmp_path / "test.db")
    lead = store.create_lead(
        {
            "company": "Mt Kenya Bakers",
            "contact_name": "Grace",
            "phone": "+254 712 000111",
            "location": "Nyeri",
            "sector": "Bakery",
            "ask_kes": 45000,
        }
    )
    assert lead["company"] == "Mt Kenya Bakers"
    bundle = store.generate_pitch_and_invoice(lead["id"])
    assert bundle["quote_kes"] == 45000
    assert bundle["deposit_kes"] == 22500
    assert bundle["invoice_number"].startswith("KF-2026-")

    updated = store.update_lead_stage(lead["id"], "Deposit Paid")
    assert updated["stage"] == "Deposit Paid"
    assert updated["deposit_paid_kes"] == 22500


def test_roi_and_instant_audit() -> None:
    roi = calculate_roi(monthly_visitors=1500, avg_order_kes=3000)
    assert roi["added_customers_per_month"] > 0
    assert roi["monthly_revenue_lift_kes"] > 45000

    audit_no_site = run_instant_audit("Nyeri Grill", "none", "Hospitality")
    assert audit_no_site["mobile_conversion_score"] < 40
    assert audit_no_site["recommended_package"]["price_kes"] == 45000


def test_static_exporter_creates_pages_bundle(tmp_path: Path) -> None:
    out = export_static_site(tmp_path / "pages_out")
    assert (out / "index.html").is_file()
    assert (out / "ops" / "index.html").is_file()
    assert (out / "demos" / "hospitality" / "index.html").is_file()
    assert (out / "le-pristine" / "index.html").is_file()
    assert (out / "static_data" / "bootstrap.json").is_file()
    assert (out / ".nojekyll").is_file()


def test_http_server_routes_and_api(tmp_path: Path) -> None:
    store = KiboFlowStore(db_path=tmp_path / "http.db")
    server = create_server(host="127.0.0.1", port=0, store=store)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{port}"
        with urlopen(f"{base}/") as resp:
            html = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "KiboFlow Studio" in html

        with urlopen(f"{base}/ops") as resp:
            ops_html = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "Founder HQ" in ops_html

        with urlopen(f"{base}/demos/hospitality") as resp:
            demo_html = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "1-Tap WhatsApp" in demo_html

        req = Request(
            f"{base}/api/audit",
            data=json.dumps(
                {
                    "business_name": "Karatina Timber",
                    "website_url": "",
                    "sector": "Hardware",
                    "phone": "+254700111222",
                    "save_lead": True,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            assert payload["audit"]["business_name"] == "Karatina Timber"
    finally:
        server.shutdown()
        server.server_close()
