# KaziPesa Digital — Business-in-a-Box

**Owner:** [YOUR NAME] · Nyeri, Kenya
**Model:** Kenyan career & small-business **digital services + digital products**, paid straight to **M-Pesa**
**Built:** 2026-11-11 · **Target: first M-Pesa shilling in 72 hours, KES 10,000+ by Day 14**

---

## 1. Why this business (the short answer)

You asked for an online business that pays **to M-Pesa**, **as fast as possible**, **within 1–2 weeks**.

Here is the honest constraint that kills most "online business" advice in Kenya:

| Model | Time to first M-Pesa | Why |
|---|---|---|
| Blogging / YouTube / SEO ads | 3–12 months | Needs traffic you don't have yet |
| Affiliate marketing | 1–3 months | Needs an audience; Jumia pays monthly |
| Dropshipping / e-commerce | 2–6 weeks | Needs stock, delivery, trust, capital |
| Forex / crypto / "task apps" | — | Mostly scams. Avoid. |
| **Micro-tasks (Remotasks, Prolific)** | 24–72h | Real but pays KES 200–900/day. A job, not a business. |
| **Selling a service you message people about today** | **24–72h** | ✅ No traffic needed. No stock. No capital. |
| **Selling a digital product** | 3–14 days | ✅ Zero marginal cost, but needs reach |

**Decision: run BOTH, in sequence.**
- **Week 1 = services** (fast cash, sold by direct message — no audience required)
- **Week 2 = digital products** (scale, sold from the same audience you just built)

That gives you cash in the first 72 hours *and* something that keeps earning after the two weeks.

---

## 2. What we actually sell

### Services (Week 1 — this is how the first money arrives)

| Service | Price | Delivery | Why it sells |
|---|---|---|---|
| **CV Makeover** | **KES 800** | 24h | Every graduate in Nyeri needs one. DeKUT, Karatina University, Nyeri National Poly = thousands of job seekers. |
| **CV + LinkedIn Combo** | **KES 1,500** | 48h | Upsell. Higher ticket, same customer. |
| **Biashara Plan (funding-ready)** | **KES 3,500** | 72h | Required for Uwezo Fund, Women Enterprise Fund, county/youth funds, SACCO loans, bank SME loans. High pain = high price. |
| **Social Starter Pack** (bio + 9 posts + logo) | **KES 2,000** | 72h | Every mama mboga / salon / boutique wants to be on TikTok and doesn't know how. |

### Digital products (Week 2 — this is how it scales)

| Product | Price | Format |
|---|---|---|
| **CV & Cover Letter Kit** | **KES 300** | PDF + editable docs |
| **Pesa Tracker** (sales/expenses/profit sheet) | **KES 500** | Excel / CSV / Google Sheets |
| **Biashara Plan Pack** (template + 12-month cashflow) | **KES 1,500** | PDF + spreadsheet |
| **KaziPesa Complete Bundle** (all 3) | **KES 1,900** | Everything |

Free lead magnet: **"7 CV Mistakes That Cost You the Interview"** — 1 page, given away to collect WhatsApp numbers.

---

## 3. The money math (14-day target)

| Channel | Daily volume | Conv. | Unit | 14-day revenue |
|---|---|---|---|---|
| WhatsApp Status (own contacts) | 200 views/day | 1% | KES 800 avg | ~KES 1,600 |
| Direct DMs (30/day targeted) | 30 | 5% | KES 1,200 avg | ~KES 2,500 |
| Facebook + TikTok organic | 400 views/day | 0.4% | KES 700 avg | ~KES 1,600 |
| Referrals + repeat + upsell | — | — | — | ~KES 2,300 |
| **Conservative total** | | | | **≈ KES 8,000** |
| **With 2 business-plan clients** | | | | **≈ KES 15,000** |

**Floor target: KES 10,000 by Day 14. Stretch: KES 25,000.**

**Starting capital: KES 0.** Your only cost is data — roughly KES 100/day, about KES 1,400 over the fortnight. Canva, WhatsApp Business, Google Drive, Facebook and TikTok are all free. Nothing in the plan requires you to spend money before the business has earned it.

---

## 4. Repository map

```
business/
├── 00-START-HERE.md        ← the 5 things you do today, in order
├── DECISIONS.md            ← every decision made for you, and why
├── README.md               ← this file
├── brand/brand-kit.md      ← name, colours, tone, bio, logo prompt
├── products/               ← the actual products (sellable as-is)
│   ├── cv-kit/
│   ├── pesa-tracker/
│   └── biashara-plan/
├── services/menu.md        ← service menu, scope, upsell scripts
├── sales/
│   ├── landing/index.html  ← live order page (M-Pesa + WhatsApp)
│   └── scripts/            ← DM scripts, 30 TikTok hooks, follow-ups
├── ops/
│   ├── 14-day-launch.md    ← day-by-day operating plan
│   ├── decision-engine.md  ← IF/THEN rules that run the business
│   ├── ledger.csv          ← every sale
│   └── track.py            ← CLI: log sales + auto-fire decisions
├── legal/compliance.md     ← KRA PIN, registration, tax — do this right
└── app.py                  ← local server for the order page
```

---

## 5. How to run it

```bash
# Start the live order page (http://localhost:8000)
python3 business/app.py

# Log a sale
python3 business/ops/track.py add --product cv-makeover --amount 800 --channel whatsapp

# See revenue vs target + what to do next
python3 business/ops/track.py dashboard
```

---

## 6. The honest risks

1. **Trust.** Strangers won't pay first. → Fix: payment *after* draft is shown, KES 200 deposit + balance, and post real screenshots of work.
2. **Scam fatigue.** Kenyans have been burned. → Fix: never ask for registration fees, show your ID/face, deliver before full payment on first orders.
3. **TikTok reach is random.** → Fix: services don't depend on it. Products are the bonus.
4. **Copycats.** → Fix: your speed, your Nyeri network, and your name are the moat. Don't compete on price.
5. **This is still work.** ~3–4 focused hours/day for 14 days. No shortcuts exist.
