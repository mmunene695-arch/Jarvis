#!/usr/bin/env python3
"""
KaziPesa Digital — sales tracker and rule engine.

Zero third-party dependencies (standard library only), mirroring the Jarvis
project's "runs on a bare Python install" rule.

Usage
-----
    python3 business/ops/track.py add --product cv-makeover --amount 800 --channel whatsapp
    python3 business/ops/track.py log --dms 30 --replies 4
    python3 business/ops/track.py dashboard
    python3 business/ops/track.py decide
    python3 business/ops/track.py products
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

# --------------------------------------------------------------------------- paths

HERE = Path(__file__).resolve().parent
BUSINESS = HERE.parent
LEDGER = HERE / "ledger.csv"
OUTREACH = HERE / "outreach.csv"
CONFIG = BUSINESS / "brand" / "config.json"

LEDGER_HEADER = ["date", "product", "amount_kes", "channel", "customer", "note"]
OUTREACH_HEADER = ["date", "dms_sent", "replies", "channel", "note"]

# ----------------------------------------------------------------------- targets

START_DATE = date(2026, 11, 11)
TARGET_14D = 10_000
STARTUP_CAPITAL = 0

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

CHANNELS = ["whatsapp", "dm", "facebook", "tiktok", "in-person", "referral", "status"]


# ------------------------------------------------------------------- csv helpers

def _ensure(path: Path, header: list[str]) -> None:
    if not path.exists() or path.stat().st_size == 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(header)


def _read(path: Path, header: list[str]) -> list[dict]:
    _ensure(path, header)
    with path.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if any(v.strip() for v in r.values())]


def _clean(value: str, limit: int = 200) -> str:
    """Strip CSV-injection characters and newlines from user-supplied text."""
    out = str(value or "").replace("\r", " ").replace("\n", " ").replace(",", " ").strip()
    out = out.lstrip("=+-@\t")
    return out[:limit]


def _kes(amount: float) -> str:
    return f"KES {amount:,.0f}"


# ---------------------------------------------------------------------- commands

def cmd_add(args: argparse.Namespace) -> int:
    if args.product not in PRODUCTS:
        print(f"Unknown product '{args.product}'. Known products:")
        for slug, (label, price) in PRODUCTS.items():
            print(f"  {slug:<15} {label} — {_kes(price)}")
        return 2

    _ensure(LEDGER, LEDGER_HEADER)
    label, default_price = PRODUCTS[args.product]
    amount = args.amount if args.amount is not None else default_price
    when = args.date or date.today().isoformat()
    row = {
        "date": when,
        "product": args.product,
        "amount_kes": f"{amount:.0f}",
        "channel": _clean(args.channel, 40) or "unknown",
        "customer": _clean(args.customer, 80),
        "note": _clean(args.note, 200),
    }
    with LEDGER.open("a", newline="", encoding="utf-8") as fh:
        csv.DictWriter(fh, fieldnames=LEDGER_HEADER).writerow(row)
    print(f"✓ Logged: {label} — {_kes(amount)} via {row['channel']} on {when}")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    _ensure(OUTREACH, OUTREACH_HEADER)
    when = args.date or date.today().isoformat()
    row = {
        "date": when,
        "dms_sent": str(max(0, args.dms)),
        "replies": str(max(0, args.replies)),
        "channel": _clean(args.channel, 40) or "mixed",
        "note": _clean(args.note, 200),
    }
    with OUTREACH.open("a", newline="", encoding="utf-8") as fh:
        csv.DictWriter(fh, fieldnames=OUTREACH_HEADER).writerow(row)
    rate = (args.replies / args.dms * 100) if args.dms else 0.0
    print(f"✓ Logged outreach: {args.dms} sent, {args.replies} replies ({rate:.0f}% reply rate)")
    return 0


def _stats() -> dict:
    sales = _read(LEDGER, LEDGER_HEADER)
    outreach = _read(OUTREACH, OUTREACH_HEADER)

    revenue = 0
    orders = 0
    by_product: Counter = Counter()
    rev_product: Counter = Counter()
    by_channel: Counter = Counter()
    rev_channel: Counter = Counter()
    for row in sales:
        try:
            amount = float(row.get("amount_kes") or 0)
        except ValueError:
            amount = 0.0
        product = (row.get("product") or "other").strip()
        channel = (row.get("channel") or "unknown").strip()
        revenue += amount
        if product != "free-guide":
            orders += 1
        by_product[product] += 1
        rev_product[product] += amount
        by_channel[channel] += 1
        rev_channel[channel] += amount

    dms = sum(int(r.get("dms_sent") or 0) for r in outreach)
    replies = sum(int(r.get("replies") or 0) for r in outreach)

    today = date.today()
    day = max(1, (today - START_DATE).days + 1)
    logged_today = any((r.get("date") or "").strip() == today.isoformat() for r in outreach)

    week_ago = today - timedelta(days=7)
    orders_7d = sum(
        1 for r in sales
        if (r.get("product") or "") != "free-guide"
        and _parse_date(r.get("date")) >= week_ago
    )

    return {
        "sales": sales, "revenue": revenue, "orders": orders,
        "by_product": by_product, "rev_product": rev_product,
        "by_channel": by_channel, "rev_channel": rev_channel,
        "dms": dms, "replies": replies,
        "reply_rate": (replies / dms * 100) if dms else 0.0,
        "conversion": (orders / dms * 100) if dms else 0.0,
        "aov": (revenue / orders) if orders else 0.0,
        "day": day, "logged_today": logged_today, "orders_7d": orders_7d,
        "days_left": max(0, 14 - day),
    }


def _parse_date(value: str | None) -> date:
    try:
        return datetime.strptime((value or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return date(2000, 1, 1)


# ------------------------------------------------------------------- rule engine

def fire_rules(s: dict) -> list[tuple[str, str]]:
    """Return [(rule_id, action), ...] for every rule whose condition is met."""
    fired: list[tuple[str, str]] = []
    day, rev, dms = s["day"], s["revenue"], s["dms"]

    # --- outreach discipline -------------------------------------------------
    if not s["logged_today"]:
        fired.append(("M4",
                      "NO OUTREACH LOGGED TODAY. 30 DMs is the floor and it is non-negotiable. "
                      "Stop everything and send them now, then: track.py log --dms 30 --replies 0"))

    # --- pricing -------------------------------------------------------------
    if dms >= 100 and s["orders"] == 0:
        fired.append(("P2",
                      "0 sales after 100+ DMs — the OFFER is wrong, not the price. Stop selling CVs. "
                      "Lead with the Social Starter Pack (visually provable) for 2 days and re-test."))
    elif dms >= 40 and s["orders"] == 0:
        fired.append(("P1",
                      "0 sales after 40+ DMs. Drop CV Makeover to KES 500 for the next 10 customers, "
                      "then back to 800. Do NOT touch the business-plan price."))

    if s["orders_7d"] > 8:
        fired.append(("P3",
                      "More than 8 orders in 7 days — you are underpriced. Raise CV Makeover to "
                      "KES 1,200 and the Biashara Plan to KES 4,500 TODAY."))

    if dms >= 30 and s["reply_rate"] > 20 and s["conversion"] < 5:
        fired.append(("C4",
                      f"Reply rate {s['reply_rate']:.0f}% (good) but conversion {s['conversion']:.1f}% "
                      "(weak) — your CLOSE is the problem. Put 'you pay after you see the draft' "
                      "in the FIRST message."))

    if dms >= 30 and s["reply_rate"] < 5:
        fired.append(("C5",
                      f"Reply rate {s['reply_rate']:.0f}% — your OPENING LINE is the problem. "
                      "Rewrite the first sentence only. Change nothing else, then re-test 30 DMs."))

    # --- channels ------------------------------------------------------------
    for channel, count in s["by_channel"].items():
        if count >= 3:
            fired.append((f"C2:{channel}",
                          f"Channel '{channel}' has produced {count} sales — double down. "
                          "70% of tomorrow's outreach goes there."))
    if s["by_channel"]:
        best = max(s["rev_channel"], key=s["rev_channel"].get)
        fired.append(("C2",
                      f"Highest-earning channel: '{best}' at "
                      f"{_kes(s['rev_channel'][best])}. Scale it."))

    # --- money gates ---------------------------------------------------------
    if day >= 7 and rev < 2_000:
        fired.append(("M1",
                      f"Day {day} and only {_kes(rev)}. Cut all product work. Spend 100% of "
                      "your time on the KES 3,500 Biashara Plan — one sale fixes the week."))
    if rev >= 25_000:
        fired.append(("M3",
                      f"{_kes(rev)} banked — this is a real business. Register formally, open the "
                      "Paybill, and raise every price by 30%."))
    elif rev >= 10_000:
        fired.append(("M2",
                      f"{_kes(rev)} — 14-day target hit. Reinvest KES 1,500: Canva Pro "
                      "(~KES 1,300) + KES 500 boosting your single best-performing post."))

    # --- escalation ladder ---------------------------------------------------
    if s["orders"] == 0:
        ladder = {
            3:  "Change the opening line.",
            5:  "Change the lead service (CV → Social Starter Pack).",
            7:  "Change the audience: DM business owners only, stop job seekers.",
            9:  "Change the channel: WhatsApp Status + Facebook groups only, drop TikTok.",
            11: "Change the price: public launch price KES 500 with a deadline.",
            13: "Change the offer: sell the KES 300 kit only, in volume, to groups.",
        }
        for threshold, action in ladder.items():
            if day >= threshold:
                fired.append((f"ESC-D{threshold}", f"Still zero sales on Day {day}. {action}"))
                break

    return fired


# ----------------------------------------------------------------------- display

def cmd_dashboard(args: argparse.Namespace) -> int:
    s = _stats()
    line = "─" * 64

    print()
    print(line)
    print(f"  {_brand()}  ·  DAY {s['day']} OF 14".center(64))
    print(line)
    print(f"  Revenue            {_kes(s['revenue']):>16}   target {_kes(TARGET_14D)}")
    pct = min(100.0, s["revenue"] / TARGET_14D * 100)
    filled = int(round(pct / 100 * 30))
    print(f"  Progress           [{'█' * filled}{'░' * (30 - filled)}] {pct:.0f}%")
    print(f"  Orders             {s['orders']:>16}")
    print(f"  Avg order value    {_kes(s['aov']):>16}")
    print(f"  Startup capital    {_kes(STARTUP_CAPITAL):>16}")
    print(f"  Days remaining     {s['days_left']:>16}")
    print(line)

    print("  FUNNEL")
    print(f"    DMs sent         {s['dms']:>16}")
    print(f"    Replies          {s['replies']:>16}")
    print(f"    Reply rate       {s['reply_rate']:>15.0f}%")
    print(f"    DM → sale        {s['conversion']:>15.1f}%")
    if not s["dms"]:
        print("    (no outreach logged yet — run: track.py log --dms 30 --replies 0)")
    print(line)

    if s["by_product"]:
        print("  REVENUE BY PRODUCT")
        for product, rev in sorted(s["rev_product"].items(), key=lambda kv: -kv[1]):
            label = PRODUCTS.get(product, (product, 0))[0]
            print(f"    {label:<32} {_kes(rev):>12}  ×{s['by_product'][product]}")
        print(line)

    if s["by_channel"]:
        print("  REVENUE BY CHANNEL")
        for channel, rev in sorted(s["rev_channel"].items(), key=lambda kv: -kv[1]):
            print(f"    {channel:<32} {_kes(rev):>12}  ×{s['by_channel'][channel]}")
        print(line)

    print(f"  MATHS — to hit {_kes(TARGET_14D)} in {s['days_left']} day(s):")
    gap = max(0.0, TARGET_14D - s["revenue"])
    if s["days_left"] > 0 and gap > 0:
        print(f"    You need {_kes(gap)} more = {_kes(gap / s['days_left'])} per day,")
        print(f"    or {gap / 800:.1f} CV Makeovers, or {gap / 3500:.1f} business plans.")
    elif gap <= 0:
        print("    Target already hit. Raise your target — you are underpricing.")
    print(line)

    decide = fire_rules(s)
    print("  DECISIONS FIRED TODAY")
    if not decide:
        print("    None. Keep executing: 30 DMs, 2 Status posts, 2 videos.")
    for rule, action in decide:
        print(f"    [{rule}] {action}")
    print(line)
    print()
    return 0


def cmd_decide(args: argparse.Namespace) -> int:
    s = _stats()
    decide = fire_rules(s)
    if not decide:
        print("No rules fired. Keep executing the daily plan.")
        return 0
    for i, (rule, action) in enumerate(decide, 1):
        print(f"{i}. [{rule}] {action}")
    return 0


def cmd_products(args: argparse.Namespace) -> int:
    print(f"\n{'SLUG':<15}{'PRODUCT':<32}{'PRICE':>10}")
    print("─" * 57)
    for slug, (label, price) in PRODUCTS.items():
        print(f"{slug:<15}{label:<32}{_kes(price):>10}")
    print(f"\nChannels: {', '.join(CHANNELS)}\n")
    return 0


def _brand() -> str:
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8")).get("brand", "KaziPesa Digital")
    except Exception:
        return "KaziPesa Digital"


# --------------------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="track.py", description="KaziPesa Digital sales tracker and rule engine.")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="log a sale")
    p_add.add_argument("--product", required=True, help="product slug (see: track.py products)")
    p_add.add_argument("--amount", type=float, default=None, help="override the list price")
    p_add.add_argument("--channel", default="whatsapp", help=", ".join(CHANNELS))
    p_add.add_argument("--customer", default="", help="customer name or initial (optional)")
    p_add.add_argument("--note", default="", help="free-text note")
    p_add.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    p_add.set_defaults(func=cmd_add)

    p_log = sub.add_parser("log", help="log outreach volume")
    p_log.add_argument("--dms", type=int, required=True, help="DMs / contacts reached")
    p_log.add_argument("--replies", type=int, default=0, help="replies received")
    p_log.add_argument("--channel", default="mixed")
    p_log.add_argument("--note", default="")
    p_log.add_argument("--date", default=None)
    p_log.set_defaults(func=cmd_log)

    p_dash = sub.add_parser("dashboard", help="revenue, funnel and fired decisions")
    p_dash.set_defaults(func=cmd_dashboard)

    p_dec = sub.add_parser("decide", help="print only the fired decisions")
    p_dec.set_defaults(func=cmd_decide)

    p_prod = sub.add_parser("products", help="list product slugs and prices")
    p_prod.set_defaults(func=cmd_products)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
