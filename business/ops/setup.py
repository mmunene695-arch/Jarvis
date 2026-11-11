#!/usr/bin/env python3
"""
Propagate your brand details into every file that needs them.

Edit business/brand/config.json first, then:

    python3 business/ops/setup.py            # apply
    python3 business/ops/setup.py --check    # show what is still unfilled
    python3 business/ops/setup.py --revert   # put all placeholders back

It is safe to run repeatedly: each run first undoes the previous run's
substitutions (recorded in brand/.last-applied.json) before applying new ones.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
BUSINESS = HERE.parent
CONFIG = BUSINESS / "brand" / "config.json"
SNAPSHOT = BUSINESS / "brand" / ".last-applied.json"
TEMPLATE = BUSINESS / "sales" / "landing" / "template.html"
OUTPUT = BUSINESS / "sales" / "landing" / "index.html"

PLACEHOLDERS = ("[YOUR NAME]", "[YOUR WHATSAPP]", "[YOUR MPESA NAME]",
                "[TILL NUMBER]", "[BRAND]", "[NAME]", "[WHATSAPP]", "[TILL]")
UNFILLED_MARKERS = ("[YOUR", "07XX", "ASK ME", "XX XXX")


def load_config() -> dict:
    if not CONFIG.exists():
        sys.exit(f"Missing {CONFIG}. Create it from brand/config.json first.")
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def whatsapp_int(raw: str) -> str:
    """'0712 345 678' -> '254712345678'. Falls back if the number is incomplete."""
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if digits.startswith("254") and len(digits) >= 11:
        return digits[:12]
    if digits.startswith("0") and len(digits) >= 10:
        return "254" + digits[1:13]
    return "254700000000"


def build_map(cfg: dict) -> dict[str, str]:
    brand = cfg.get("brand", "KaziPesa Digital")
    name = cfg.get("name", "[YOUR NAME]")
    phone = cfg.get("whatsapp", "07XX XXX XXX")
    till = cfg.get("till", "ASK ME")
    till_name = cfg.get("till_name", "[YOUR MPESA NAME]")
    wa_int = whatsapp_int(phone)

    def wa(text: str) -> str:
        return quote(text)

    return {
        # markdown placeholders
        "[YOUR NAME]": name,
        "[NAME]": name,
        "[YOUR WHATSAPP]": phone,
        "[WHATSAPP]": phone,
        "[TILL NUMBER]": till,
        "[TILL]": till,
        "[YOUR MPESA NAME]": till_name,
        "[BRAND]": brand,
        # landing page tokens
        "{{BRAND}}": brand,
        "{{NAME}}": name,
        "{{WHATSAPP}}": phone,
        "{{WHATSAPP_INT}}": wa_int,
        "{{TILL}}": till,
        "{{TILL_NAME}}": till_name,
        "{{WA_HELLO}}": wa(f"Hi {brand}! I saw your page and I'd like to ask about your services."),
        "{{WA_CV}}": wa(f"Hi {brand}! I want the CV Makeover (KES 800). Here is my current CV:"),
        "{{WA_LINKEDIN}}": wa(f"Hi {brand}! I want the CV + LinkedIn Combo (KES 1,500)."),
        "{{WA_SOCIAL}}": wa(f"Hi {brand}! I want the Social Starter Pack (KES 2,000) for my business."),
        "{{WA_PLAN}}": wa(f"Hi {brand}! I need a funding-ready business plan (KES 3,500). Which fund: "),
        "{{WA_KIT_CV}}": wa(f"Hi {brand}! I want the CV & Cover Letter Kit (KES 300)."),
        "{{WA_KIT_PESA}}": wa(f"Hi {brand}! I want the Pesa Tracker (KES 500)."),
        "{{WA_KIT_PLAN}}": wa(f"Hi {brand}! I want the Biashara Plan Pack (KES 1,500)."),
        "{{WA_BUNDLE}}": wa(f"Hi {brand}! I want the KaziPesa Complete bundle (KES 1,900)."),
        "{{WA_FREE}}": wa("Hi! Please send me the free guide: 7 CV Mistakes."),
        "{{WA_PAID}}": wa(f"Hi {brand}! I've paid via M-Pesa. Screenshot attached. My order: "),
        "{{WA_ORDERED}}": wa(f"Hi {brand}! I just placed an order on your page."),
    }


def target_files() -> list[Path]:
    files = sorted(BUSINESS.rglob("*.md"))
    return [f for f in files if ".git" not in f.parts]


MIN_REVERT_LEN = 6


def revert(snapshot: dict[str, str]) -> None:
    """Put placeholders back using the previous run's value map.

    Short values are skipped: a two-character value like "07" would match inside
    unrelated text ("07XX XXX XXX") and corrupt the files it is meant to restore.
    """
    if not snapshot:
        return
    for path in target_files():
        text = path.read_text(encoding="utf-8")
        new = text
        for placeholder, value in snapshot.items():
            if value and value != placeholder and len(value) >= MIN_REVERT_LEN:
                new = new.replace(value, placeholder)
        if new != text:
            path.write_text(new, encoding="utf-8")
            print(f"  reverted  {path.relative_to(BUSINESS)}")


def apply_map(mapping: dict[str, str]) -> None:
    for path in target_files():
        text = path.read_text(encoding="utf-8")
        new = text
        for placeholder, value in mapping.items():
            new = new.replace(placeholder, value)
        if new != text:
            path.write_text(new, encoding="utf-8")
            print(f"  updated   {path.relative_to(BUSINESS)}")

    if TEMPLATE.exists():
        html = TEMPLATE.read_text(encoding="utf-8")
        for placeholder, value in mapping.items():
            html = html.replace(placeholder, value)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(html, encoding="utf-8")
        print(f"  built     {OUTPUT.relative_to(BUSINESS)}")


def cmd_apply(args: argparse.Namespace) -> int:
    cfg = load_config()
    mapping = build_map(cfg)
    if SNAPSHOT.exists():
        try:
            revert(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
        except Exception as exc:  # noqa: BLE001
            print(f"  ! could not revert previous run ({exc}); placeholders may be doubled up")
    print("Applying brand details…")
    apply_map(mapping)
    SNAPSHOT.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nDone. Reminders:")
    print("  • Start the order page:  python3 business/app.py")
    print("  • Log a sale:            python3 business/ops/track.py add --product cv-makeover --amount 800 --channel whatsapp")
    print("  • See your dashboard:    python3 business/ops/track.py dashboard")
    return cmd_check(args)


def cmd_check(args: argparse.Namespace) -> int:
    print("\nChecking for unfilled details…")
    problems = 0
    paths = target_files() + ([OUTPUT] if OUTPUT.exists() else [])
    for path in paths:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            hit = next((m for m in UNFILLED_MARKERS if m in line), None)
            if hit:
                problems += 1
                rel = path.relative_to(BUSINESS)
                print(f"  {rel}:{number}: {line.strip()[:100]}")
    if problems:
        print(f"\n{problems} line(s) still contain placeholder text — fill them in or re-run setup after editing brand/config.json.")
    else:
        print("  Clean. No placeholders left. You are ready to sell.")
    return 0


def cmd_revert(args: argparse.Namespace) -> int:
    if not SNAPSHOT.exists():
        print("Nothing to revert (no previous run recorded).")
        return 0
    revert(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
    SNAPSHOT.unlink()
    if OUTPUT.exists():
        OUTPUT.unlink()
    print("Reverted every file back to placeholders.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply brand details across the business folder.")
    parser.add_argument("--check", action="store_true", help="only report unfilled placeholders")
    parser.add_argument("--revert", action="store_true", help="restore all placeholders")
    args = parser.parse_args()
    if args.revert:
        return cmd_revert(args)
    if args.check:
        return cmd_check(args)
    return cmd_apply(args)


if __name__ == "__main__":
    sys.exit(main())
