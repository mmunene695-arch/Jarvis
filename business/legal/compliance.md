# Legal & Compliance — do this properly, but do not wait for it

**You can legally start selling today with your personal M-Pesa.** Paperwork is for credibility and scale, not for permission. Get it done by Day 10 — not before you make your first sale.

---

## Priority 1 — Today (free, 15 minutes)

### Taking payment: your personal M-Pesa number
This is the setup, and it is all you need:

- Buyers go to **M-Pesa → Send Money**, enter your number, enter the amount, confirm.
- Tell buyers: *"Send to +254729213641 — ."* Completely normal in Kenya.
- **No Till, no Paybill, no gateway, no approval, no cost.**

**The three checks before your first sale:**
- [ ] The line is **registered in your own name**. Safaricom will not register it otherwise, and this is the single thing most likely to block your money.
- [ ] You can **receive** right now — test with KES 10 from a friend.
- [ ] Your **daily limit** is high enough. Dial `*334#` → *My M-Pesa*. Over KES 70,000/day or KES 100,000 balance → visit a Safaricom shop in Nyeri with your ID to raise your tier.

### The upgrade path (free, do it later when you're busy)
A **Lipa na M-Pesa Till** is free and makes you look established. Dial `*334#` → *Lipa na M-Pesa* → *Till Number (Buy Goods)*, or walk into any Safaricom shop with your ID. Approval takes 1–3 working days.
When you have it: set `"payment_mode": "till"` in `brand/config.json`, add the number and name, run `python3 business/ops/setup.py`. The order page rewrites itself.
Manual confirmation (buyer DMs you, you send the number, they screenshot) comfortably handles about 20 orders a day — you do not need more than that for a long while.

### Know your transaction records
- Dial **`*234#`** → *M-Pesa Statement* to get a full statement emailed to you.
- Reconcile it against your Pesa Tracker monthly. Discrepancies are either theft or forgetfulness — both need fixing.

---

## Priority 2 — When you can afford it (≈KES 1,000, 1–2 days)

*You are starting with KES 0, so this waits until the business has earned it. Nothing here blocks you from selling today. Confirm your **KRA PIN** now though — it is free.*

### Business name registration — ≈KES 1,000
1. Go to **ecitizen.go.ke** → create an account.
2. **Business Registration Service (BRS)** → reserve a business name (~KES 150).
3. Then register it as a **Business Name (sole proprietor)** (~KES 850).
4. You get a certificate of registration.

**Why bother:** a registered name lets you open the M-Pesa **Paybill**, a business bank account, and lets you invoice. Funders (Uwezo, WEF, Youth Fund, county) will not look at an unregistered business.

**Do not register a limited company yet.** It costs more, requires annual returns, and gives you nothing you need in the first 3 months.

### KRA PIN — FREE
- **itax.kra.go.ke** → register as an individual → instant PIN.
- If you already have one (most Kenyans do), log in and confirm it is active.
- Needed for: the Paybill, business bank account, and any funding application.
- **Filing:** with a PIN you are expected to file annual returns. At micro-business turnover (under KES 500k/year) you will generally owe little or nothing, but **file anyway** — an unfiled nil return is free; a penalty is not.

---

## Priority 3 — When you're established (after KES 25,000)

- **Paybill number** — KES 100/month from Safaricom. Better for invoicing and larger amounts.
- **Business bank account** — Equity, KCB, Co-op or a digital SME bank.
- **Nyeri County Single Business Permit** — required if you have a physical premises. ~KES 5,000–15,000/year depending on the trade. **Not required for a purely online business run from home.**
- **NHIF + NSSF** — if you hire anyone.
- **VAT** — only at KES 5,000,000+ annual turnover. Ignore for now.

---

## Sector-specific: what NOT to promise

You are selling documents, not outcomes. Say so.

| Never say | Say instead |
|---|---|
| "I'll get you the job." | "I'll make sure your CV passes the filters and sells you properly." |
| "Guaranteed loan approval." | "I guarantee the plan meets the funder's required format." |
| "Approved by Uwezo Fund." | "Formatted to Uwezo Fund's standard structure." |
| "Registered/affiliated with [any fund]." | Nothing of the sort. You are independent. |

Claiming a government affiliation or guaranteeing funding is how people get into real trouble. Don't.

---

## Data protection — the easy version

You will hold customers' names, phone numbers, CVs and sometimes ID numbers. Kenya's **Data Protection Act 2019** applies to you.

Four rules, and they cover you:
1. **Collect only what you need.** Don't ask for an ID number unless a funding application genuinely requires it.
2. **Use it only for the job.** Never sell, share or publish a customer's CV.
3. **Delete it when you're done.** 90 days after delivery, delete the working files.
4. **Blur names in testimonials** unless the customer says otherwise in writing.

---

## Red flags — walking away

If a "client" does any of these, stop and don't engage:
- Asks you to write a plan with **invented numbers** for a fund application. (Fraud. Your name is on the document.)
- Asks you to fake a CV — fake employers, fake dates, fake certificates.
- Asks you to write a plan **for** someone else to submit as their own business when they have no business.
- Offers you a "referral fee" to send clients to a lender.

Refuse politely: *"I can't do that one — it would put both of us at risk. Happy to help with anything else."*

---

## Scam warnings for YOU

While you build this, people will try to sell you shortcuts. Every one of these is a loss:

- ❌ Any "online job" requiring a **registration or activation fee**.
- ❌ "Task apps" paying KES 50 per tap.
- ❌ Olymp Trade / binary options / "signal groups".
- ❌ Crypto flipping via Paxful-style escrow with strangers.
- ❌ Pyramid/MLM referral schemes ("recruit 5 to unlock earnings").
- ❌ "Mentorship" or "masterclass" courses promising KES 50k/month.
- ❌ Anyone who says your M-Pesa is "locked" and needs a code.

Rule: **money flows towards you, never away from you.** If you are paying to start, it isn't a job.

---

*This is practical guidance, not legal advice. For anything contractual or large, talk to an advocate.*
