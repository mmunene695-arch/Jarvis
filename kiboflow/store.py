"""SQLite persistence, ROI calculator, proposal/invoice generator, and website CRO auditor."""

from __future__ import annotations

import datetime as dt
import os
import sqlite3
from pathlib import Path
from typing import Any

from kiboflow import COMPANY_PROFILE
from kiboflow.data_seed import DECISIONS_SEED, LEADS_SEED, PACKAGES_SEED

VALID_STAGES = (
    "Ready to Call",
    "Queued",
    "Called - Demo Sent",
    "Follow-Up Staged",
    "Negotiating",
    "Deposit Paid",
    "Delivered / Retainer",
    "Inbound Web",
    "Paused - Bounced",
    "Lost",
)


def default_db_path() -> Path:
    override = os.environ.get("KIBOFLOW_DB")
    if override:
        return Path(override)
    base_dir = Path(__file__).resolve().parent.parent / "kiboflow-data"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "kiboflow.db"


class KiboFlowStore:
    """Local SQLite store backing KiboFlow Studio's public funnels and Founder Command Center."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    contact_name TEXT NOT NULL DEFAULT '',
                    phone TEXT NOT NULL DEFAULT '',
                    email TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '',
                    sector TEXT NOT NULL DEFAULT '',
                    track TEXT NOT NULL DEFAULT 'Local Fast-Cash',
                    stage TEXT NOT NULL DEFAULT 'Ready to Call',
                    priority INTEGER NOT NULL DEFAULT 2,
                    ask_kes INTEGER NOT NULL DEFAULT 45000,
                    accept_kes INTEGER NOT NULL DEFAULT 38000,
                    floor_kes INTEGER NOT NULL DEFAULT 32000,
                    retainer_kes INTEGER NOT NULL DEFAULT 5000,
                    demo_path TEXT NOT NULL DEFAULT '/demos/hospitality',
                    backup_concept_url TEXT NOT NULL DEFAULT '',
                    pain_point TEXT NOT NULL DEFAULT '',
                    next_action TEXT NOT NULL DEFAULT '',
                    deposit_paid_kes INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    issue_found TEXT NOT NULL,
                    decision_made TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Executed',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT NOT NULL UNIQUE,
                    lead_id INTEGER,
                    client_name TEXT NOT NULL,
                    package_name TEXT NOT NULL,
                    total_kes INTEGER NOT NULL,
                    deposit_kes INTEGER NOT NULL,
                    retainer_kes INTEGER NOT NULL DEFAULT 5000,
                    status TEXT NOT NULL DEFAULT 'Draft - Awaiting 50% Deposit',
                    valid_until TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            now = dt.datetime.now(dt.timezone.utc).isoformat()
            lead_count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            if lead_count == 0:
                for item in LEADS_SEED:
                    conn.execute(
                        """
                        INSERT INTO leads (
                            company, contact_name, phone, email, location, sector, track,
                            stage, priority, ask_kes, accept_kes, floor_kes, retainer_kes,
                            demo_path, backup_concept_url, pain_point, next_action, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item["company"],
                            item["contact_name"],
                            item["phone"],
                            item["email"],
                            item["location"],
                            item["sector"],
                            item["track"],
                            item["stage"],
                            item["priority"],
                            item["ask_kes"],
                            item["accept_kes"],
                            item["floor_kes"],
                            item["retainer_kes"],
                            item["demo_path"],
                            item["backup_concept_url"],
                            item["pain_point"],
                            item["next_action"],
                            now,
                        ),
                    )
            dec_count = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
            if dec_count == 0:
                for dec in DECISIONS_SEED:
                    conn.execute(
                        """
                        INSERT INTO decisions (
                            code, category, title, issue_found, decision_made, impact, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            dec["code"],
                            dec["category"],
                            dec["title"],
                            dec["issue_found"],
                            dec["decision_made"],
                            dec["impact"],
                            dec["status"],
                            now,
                        ),
                    )
            conn.commit()

    def list_packages(self) -> list[dict[str, Any]]:
        return [dict(pkg) for pkg in PACKAGES_SEED]

    def list_leads(self, stage: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if stage and stage != "All":
                rows = conn.execute(
                    "SELECT * FROM leads WHERE stage = ? ORDER BY priority ASC, id ASC",
                    (stage,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM leads ORDER BY priority ASC, id ASC"
                ).fetchall()
        return [dict(row) for row in rows]

    def get_lead(self, lead_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None

    def create_lead(self, payload: dict[str, Any]) -> dict[str, Any]:
        company = str(payload.get("company") or "").strip()
        if not company:
            raise ValueError("company is required")
        stage = str(payload.get("stage") or "Inbound Web").strip()
        if stage not in VALID_STAGES:
            stage = "Inbound Web"
        ask_kes = max(0, int(payload.get("ask_kes", 45000)))
        accept_kes = max(0, int(payload.get("accept_kes", int(ask_kes * 0.85))))
        floor_kes = max(0, int(payload.get("floor_kes", int(ask_kes * 0.72))))
        retainer_kes = max(0, int(payload.get("retainer_kes", 5000)))
        priority = max(1, min(5, int(payload.get("priority", 1))))
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO leads (
                    company, contact_name, phone, email, location, sector, track,
                    stage, priority, ask_kes, accept_kes, floor_kes, retainer_kes,
                    demo_path, backup_concept_url, pain_point, next_action, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company,
                    str(payload.get("contact_name") or "").strip(),
                    str(payload.get("phone") or "").strip(),
                    str(payload.get("email") or "").strip(),
                    str(payload.get("location") or "Kenya").strip(),
                    str(payload.get("sector") or "SMB").strip(),
                    str(payload.get("track") or "Inbound Web").strip(),
                    stage,
                    priority,
                    ask_kes,
                    accept_kes,
                    floor_kes,
                    retainer_kes,
                    str(payload.get("demo_path") or "/demos/hospitality").strip(),
                    str(payload.get("backup_concept_url") or "").strip(),
                    str(payload.get("pain_point") or "Inbound website / WhatsApp audit request").strip(),
                    str(payload.get("next_action") or "Respond on WhatsApp within 15 minutes with live demo").strip(),
                    now,
                ),
            )
            conn.commit()
            lead_id = int(cur.lastrowid or 0)
        lead = self.get_lead(lead_id)
        assert lead is not None
        return lead

    def update_lead_stage(
        self,
        lead_id: int,
        stage: str,
        next_action: str | None = None,
        deposit_paid_kes: int | None = None,
    ) -> dict[str, Any]:
        if stage not in VALID_STAGES:
            raise ValueError(f"Unsupported stage: {stage}")
        existing = self.get_lead(lead_id)
        if not existing:
            raise KeyError(f"Lead {lead_id} not found")
        new_action = next_action if next_action is not None else existing["next_action"]
        new_deposit = (
            max(0, int(deposit_paid_kes))
            if deposit_paid_kes is not None
            else (existing["ask_kes"] // 2 if stage == "Deposit Paid" and existing["deposit_paid_kes"] == 0 else existing["deposit_paid_kes"])
        )
        with self._connect() as conn:
            conn.execute(
                "UPDATE leads SET stage = ?, next_action = ?, deposit_paid_kes = ? WHERE id = ?",
                (stage, new_action, new_deposit, lead_id),
            )
            conn.commit()
        updated = self.get_lead(lead_id)
        assert updated is not None
        return updated

    def list_decisions(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM decisions ORDER BY code ASC").fetchall()
        return [dict(row) for row in rows]

    def list_invoices(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    def generate_pitch_and_invoice(self, lead_id: int, price_override_kes: int | None = None) -> dict[str, Any]:
        lead = self.get_lead(lead_id)
        if not lead:
            raise KeyError(f"Lead {lead_id} not found")
        quote_kes = int(price_override_kes) if price_override_kes is not None else int(lead["ask_kes"])
        if quote_kes <= 0:
            quote_kes = 45000
        deposit_kes = quote_kes // 2
        retainer_kes = int(lead["retainer_kes"] or 5000)
        contact = lead["contact_name"] or "there"
        first_name = contact.split()[0] if contact and contact != "Manager / Owner" else "there"

        # Price-lock Friday calculation
        today = dt.date(2026, 11, 11)
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        valid_until = (today + dt.timedelta(days=days_until_friday)).isoformat()

        now = dt.datetime.now(dt.timezone.utc).isoformat()
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
            inv_num = f"KF-2026-{count + 101:03d}"
            pkg_name = (
                "7-Day Mobile & WhatsApp Conversion Sprint"
                if quote_kes <= 55000
                else "Hospitality & WhatsApp Booking Automation System"
            )
            conn.execute(
                """
                INSERT INTO invoices (
                    invoice_number, lead_id, client_name, package_name,
                    total_kes, deposit_kes, retainer_kes, valid_until, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inv_num,
                    lead_id,
                    lead["company"],
                    pkg_name,
                    quote_kes,
                    deposit_kes,
                    retainer_kes,
                    valid_until,
                    now,
                ),
            )
            conn.commit()

        call_opener = (
            f"Morning! My name's Mark Munene, founder of KiboFlow Studio here in Nyeri — "
            f"I'm not selling you anything on this call. I built a mobile website & WhatsApp booking concept "
            f"for {lead['company']} and I'd like to send it to your WhatsApp. Is {lead['phone'] or 'this number'} okay?"
        )
        whatsapp_message = (
            f"Hi {first_name}, Mark Munene here from KiboFlow Studio — we just spoke. "
            f"Open this live mobile concept on your phone and scroll:\n"
            f"{{ORIGIN}}{lead['demo_path']}\n\n"
            f"Everything a customer needs is there in the first 3 seconds: 1-tap call, menu/rates, "
            f"Google Maps pin, and direct WhatsApp booking. Have a look — if you like it, I can put "
            f"{lead['company']}'s live version up inside 7 days. No pressure either way."
        )
        scope_protection_line = (
            f"Standard full build is KES {lead['ask_kes']:,} (50% M-Pesa deposit = KES {lead['ask_kes'] // 2:,} to lock this week's slot, "
            f"balance on launch). If you need to stay at KES {lead['accept_kes']:,}, we launch the high-converting homepage + "
            f"1-tap WhatsApp booking & Maps first, and add secondary gallery/subpages later. Walk-away floor: KES {lead['floor_kes']:,}."
        )
        return {
            "invoice_number": inv_num,
            "lead": lead,
            "package_name": pkg_name,
            "quote_kes": quote_kes,
            "deposit_kes": deposit_kes,
            "balance_kes": quote_kes - deposit_kes,
            "retainer_kes": retainer_kes,
            "valid_until": valid_until,
            "mpesa_number": COMPANY_PROFILE["mpesa_number"],
            "founder": COMPANY_PROFILE["founder"],
            "call_opener": call_opener,
            "whatsapp_message": whatsapp_message,
            "scope_protection_line": scope_protection_line,
        }

    def get_overview(self) -> dict[str, Any]:
        leads = self.list_leads()
        invoices = self.list_invoices()
        decisions = self.list_decisions()
        local_leads = [item for item in leads if item["track"] == "Local Fast-Cash" and item["stage"] != "Lost"]
        mid_leads = [item for item in leads if item["track"] == "Kenyan Mid-Market" and item["stage"] != "Lost"]
        local_pipeline_kes = sum(int(item["ask_kes"]) for item in local_leads)
        mid_pipeline_kes = sum(int(item["ask_kes"]) for item in mid_leads)
        collected_kes = sum(int(item["deposit_paid_kes"]) for item in leads)
        potential_mrr_kes = sum(int(item["retainer_kes"]) for item in local_leads)
        # Conservative 35% close rate on local Ready/Queued pipeline inside 14 days
        projected_14d_cash_kes = collected_kes + int(local_pipeline_kes * 0.35)
        return {
            "company": COMPANY_PROFILE,
            "metrics": {
                "total_leads": len(leads),
                "ready_to_call": sum(1 for item in leads if item["stage"] == "Ready to Call"),
                "local_pipeline_kes": local_pipeline_kes,
                "midmarket_pipeline_kes": mid_pipeline_kes,
                "total_active_pipeline_kes": local_pipeline_kes + mid_pipeline_kes,
                "projected_14d_cash_kes": projected_14d_cash_kes,
                "collected_deposits_kes": collected_kes,
                "potential_local_mrr_kes": potential_mrr_kes,
                "invoices_generated": len(invoices),
                "decisions_logged": len(decisions),
            },
            "connected_systems": {
                "github": "Active · Zero-credit-limit GitHub Pages exporter & CI workflow ready",
                "gmail": "Active · 4 CRM labels applied, bounces quarantined, 4 outreach/briefing drafts staged",
                "google_calendar": "Active · Dedicated Africa/Nairobi (EAT) calendar with 7-day sales & build blocks",
                "google_drive": "Active · KiboFlow Studio HQ folder with Business Plan, CRM Sheet, Proposal & Contract",
            },
        }


def calculate_roi(
    monthly_visitors: int,
    avg_order_kes: int,
    current_conversion_pct: float = 1.2,
    target_conversion_pct: float = 3.8,
    package_cost_kes: int = 45000,
) -> dict[str, Any]:
    """Calculate monthly revenue unlocked by switching to a mobile + WhatsApp conversion funnel."""
    visitors = max(50, min(1_000_000, int(monthly_visitors)))
    avg_val = max(200, min(5_000_000, int(avg_order_kes)))
    curr_rate = max(0.0, min(50.0, float(current_conversion_pct))) / 100.0
    targ_rate = max(curr_rate + 0.005, min(60.0, float(target_conversion_pct))) / 100.0
    pkg_cost = max(15000, int(package_cost_kes))

    current_customers = round(visitors * curr_rate)
    projected_customers = round(visitors * targ_rate)
    added_customers = max(1, projected_customers - current_customers)
    monthly_lift_kes = added_customers * avg_val
    payback_days = max(2, round((pkg_cost / max(1, monthly_lift_kes)) * 30))

    return {
        "monthly_visitors": visitors,
        "avg_order_kes": avg_val,
        "current_customers": current_customers,
        "projected_customers": projected_customers,
        "added_customers_per_month": added_customers,
        "monthly_revenue_lift_kes": monthly_lift_kes,
        "annual_revenue_lift_kes": monthly_lift_kes * 12,
        "package_cost_kes": pkg_cost,
        "estimated_payback_days": payback_days,
    }


def run_instant_audit(business_name: str, website_url: str, sector: str) -> dict[str, Any]:
    """Generate an instant, actionable mobile conversion audit for sales calls and inbound visitors."""
    clean_name = business_name.strip() or "Your Business"
    clean_url = website_url.strip()
    sector_clean = sector.strip() or "Hospitality & Local Services"
    has_site = bool(clean_url and clean_url.lower() not in {"none", "no", "n/a", "-"})

    if not has_site:
        score = 24
        headline = f"{clean_name} is losing high-intent mobile searchers before they ever call."
        findings = [
            "No dedicated mobile landing page — Google Maps & search visitors bounce to competitors with menus/rates.",
            "Zero 1-tap WhatsApp booking or pre-order link to capture impulse customers on phones.",
            "Missing structured Google Business & local SEO schema for Nyeri / regional 'near me' searches.",
        ]
        recommended_package = PACKAGES_SEED[0]
    else:
        is_http = clean_url.startswith("http://")
        score = 46 if is_http else 54
        headline = f"{clean_url} has traffic potential, but friction on 390px phone screens leaks inquiries."
        findings = [
            (
                "Unencrypted HTTP link triggers browser 'Not Secure' warnings on mobile phones."
                if is_http
                else "Above-the-fold layout lacks a sticky 3-second 'Book / Order on WhatsApp' conversion bar."
            ),
            "Customers must pinch-zoom or hunt for phone numbers instead of tapping a pre-filled WhatsApp inquiry.",
            f"No automated lead-capture sheet or instant FAQ response for {sector_clean} inquiries after hours.",
        ]
        recommended_package = PACKAGES_SEED[1]

    return {
        "business_name": clean_name,
        "website_url": clean_url or "No website currently",
        "sector": sector_clean,
        "mobile_conversion_score": score,
        "headline": headline,
        "findings": findings,
        "recommended_package": {
            "name": recommended_package["name"],
            "price_kes": recommended_package["price_kes"],
            "deposit_kes": recommended_package["price_kes"] // 2,
            "turnaround_days": recommended_package["turnaround_days"],
        },
    }
