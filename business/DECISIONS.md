# Decision Register — every call made on your behalf

You said: *"run the business while making advanced decisions for me."*
This file is the receipt. Every decision, the reasoning, and what would make me reverse it.

---

## D1 — Business model: **service-first, product-second**
**Decision:** Sell done-for-you services in Week 1; launch digital products in Week 2.
**Why:** Services need no audience — you message a person and get paid. Products need traffic, which takes time to build. Doing products first means Day 14 with KES 0.
**Reverse if:** You already have 1,000+ engaged followers → launch products Day 1 instead.

## D2 — Niche: **Kenyan careers + small-business paperwork**
**Decision:** CVs, cover letters, LinkedIn, business plans, social media starter packs.
**Why:** Three things Kenyans already pay for, in KES, with M-Pesa, and where the buyer is in *pain* right now (jobless, or needs funding). High pain = fast payment. Nyeri has DeKUT, Karatina University and Nyeri National Polytechnic within reach — a dense pool of CV buyers — plus a huge informal SME market that needs business plans for Uwezo/County/Women Enterprise funds.
**Reverse if:** You have a demonstrable skill (design, video, code, tutoring) → lead with that instead; the machinery here still applies.

## D3 — Price: **KES 800 / 1,500 / 2,000 / 3,500** (services), **300 / 500 / 1,500 / 1,900** (products)
**Decision:** Deliberately above the KES 100–300 "hustle" floor.
**Why:** Kenyan creators chronically underprice. KES 800 for a CV is ~2 hours of work and reads as *professional*; KES 200 reads as desperate and attracts time-wasters. The business-plan tier at KES 3,500 exists because funding is a KES 50,000+ outcome — the price is trivial against the value.
**Reverse if:** 0 sales after 40 DMs → drop to KES 500 for the first 10 customers as a launch price, then raise.

## D4 — Payment rail: **personal M-Pesa number** (Send Money), upgrade to a Till later
**Decision:** Customers **Send Money** to your own M-Pesa number. No Till, no Paybill, no gateway.
**Why:** You chose this, and it is the right call for week one. A Till is free but takes 1–3 working days to approve — and waiting on paperwork is how people lose the two weeks they had. A Paybill costs KES 100/month, and card gateways (Paystack/Flutterwave/IntaSend) need 1–5 days of KYC plus business registration. All three are the wrong side of your deadline. Send Money is instant, free, has zero setup, and is completely normal practice in Kenya — nobody will blink.
**The one risk:** your daily and per-transaction limits are lower on a personal line. If you expect to receive over KES 70,000/day or hold over KES 100,000, visit a Safaricom shop in Nyeri with your National ID and raise your account tier.
**Reverse when** (not if) any of these becomes true:
- You are handling more than ~20 orders a day → get the free Till.
- You want to look established to a business client → get the free Till.
- A customer's employer or a fund requires a business payee → get a Paybill.
The switch is a one-line change: set `"payment_mode": "till"` in `brand/config.json`, fill in `till` and `till_name`, re-run `python3 business/ops/setup.py`. The landing page rewrites itself.

## D13 — Capital: **KES 0**, and that is genuinely fine
**Decision:** Spend nothing until the business has paid for it.
**Why:** You have no capital to deploy, and this model was chosen partly because it needs none. The only unavoidable cost is data (roughly KES 100/day). Everything else — Canva free tier, WhatsApp Business, Google Drive, Facebook groups, TikTok — is free. Anyone telling you that you must buy a course, a "starter pack", a mentorship or a website before you can earn is selling you something.
**Consequences I have already built into the plan:**
- Business name registration (≈KES 1,000) on Day 10 is now **conditional on revenue**, not scheduled.
- No paid boosting anywhere in weeks 1–2. Rule M2 (reinvest KES 1,500) only triggers *after* KES 10,000 is banked.
- Flyers are optional — your phone and your voice are enough.
**Reverse when:** you have KES 1,000 of profit sitting idle → register the business name; that is the first thing money should buy.

## D5 — Delivery channel: **WhatsApp + Google Drive**
**Decision:** Everything is delivered over WhatsApp; files live in Google Drive (folders already created).
**Why:** WhatsApp is #4 brand in Kenya and how Kenyans actually receive files. Email delivery dies — people don't check it. Drive gives you one canonical link per product that you can update without resending.
**Reverse if:** Customer base moves to a platform you can build an audience on → mirror to Telegram.

## D6 — Free lead magnet before any pitch
**Decision:** Give away "7 CV Mistakes" to every contact before selling anything.
**Why:** Reciprocity is the cheapest trust-builder that exists. It converts a cold DM into a conversation without you sounding like a scammer.
**Reverse if:** Never.

## D7 — Traffic: **owned network first, algorithms second**
**Decision:** Days 1–7 = 30 targeted DMs/day + 2 WhatsApp Status posts/day + 6 Facebook group posts/week. TikTok/Reels start Day 1 but are treated as a lottery ticket, not the plan.
**Why:** Your 200 WhatsApp contacts are worth more in Week 1 than 20,000 TikTok views, because they already trust you. Algorithms pay later.
**Reverse if:** A video passes 10,000 views → reallocate 50% of DM time to content that week.

## D8 — Sales motion: **show the work, then ask for payment**
**Decision:** For first-time customers, deliver a watermarked draft *before* full payment; take KES 200 deposit, balance on delivery.
**Why:** Kills the trust objection that blocks 90% of Kenyan online sales. Your marginal cost of being burned is one hour.
**Reverse if:** You have 20+ public testimonials → switch to 100% payment upfront.

## D9 — Refund policy: unconditional, no questions
**Decision:** Full refund, same day, no argument, if not satisfied.
**Why:** A refund costs you one hour. A public complaint in a Nyeri WhatsApp group costs you the market.
**Reverse if:** Never.

## D10 — Legal: register + KRA PIN, but do not wait for it
**Decision:** Start selling on Day 1 with your personal M-Pesa while the business name registration (~KES 1,000, 1–2 days) and KRA PIN are in process.
**Why:** Waiting 2 weeks for paperwork wastes the 2 weeks you have. Registration is for *credibility and scale*, not permission to sell.
**Reverse if:** Never — but complete it by Day 10. See `legal/compliance.md`.

## D11 — What we refuse to do
**Decision:** No forex/crypto/Olymp Trade, no "task apps" with registration fees, no pyramid/MLM referrals, no betting tips, no paid-survey grind.
**Why:** These are the top answers on Kenyan "make money online" blogs and they are where people lose money. They are excluded by policy, not by oversight.
**Reverse if:** Never.

## D12 — Reinvestment rule
**Decision:** First KES 5,000 of profit is not spent. It goes to: data bundles, a Canva Pro month (KES ~1,300), and ~KES 1,000 of Facebook/TikTok boost on your single best-performing post.
**Why:** The fastest-growing asset in this business is *proof* (testimonials + reach). Buy both.
**Reverse if:** You need the money for essentials — take it, no guilt.

---

## Decisions I could not make for you — **now supplied and applied**

| # | Question | Answer | Applied to |
|---|---|---|---|
| 1 | Full name | **Mark Munene** | `brand/config.json` → `name` |
| 2 | WhatsApp / M-Pesa number | **+254 729 213 641** (shown to buyers as `0729 213 641`) | `whatsapp`, `personal_number` |
| 3 | Name shown on M-Pesa | **Mark Munene** | `mpesa_registered_name` |
| 4 | Payment rail | **Personal M-Pesa — Send Money** | `payment_mode: "personal"` |
| 5 | Starting capital | **KES 0** | `decision-engine.md`, rule M5 |

`setup.py` has been run: every script, product file, the landing page and all three email drafts now carry these details, and the Drive product copies were updated to match.

### The one thing still to confirm

**Is 0729 213 641 registered to you personally at Safaricom?**

The whole business runs through that one number. If it is registered to a relative or a friend, two things break: you cannot raise your transaction limits, and a customer disputing a payment has no clean trail back to you. Check it before your first sale. If it is not in your name, sort that out first — it is the single most likely thing to block your money.

### Still open, but nothing here blocks you from selling today

- **KRA PIN** — confirm it is active (`itax.kra.go.ke`, free). Needed by Day 10, not today.
- **Business name registration** (~KES 1,000) — only once KES 1,000 of profit exists. See D13.
- **Lipa na M-Pesa Till** (free) — upgrade when you pass ~20 orders a day. See D4.
