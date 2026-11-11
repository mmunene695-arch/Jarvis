# START HERE — do these 5 things today, in this order

Total time: **about 3 hours.** Do not skip ahead. Do not redesign anything.

---

## ☐ 1. Fill in your 4 details (5 minutes)

Open `business/brand/brand-kit.md` and replace every `[BRACKET]`:

- `[YOUR NAME]`
- `07XX XXX XXX` — e.g. 0712 345 678
- `ASK ME` — leave as `ASK ME` if not yet approved
- `[YOUR MPESA NAME]`

Then run:

```bash
cd /home/user/Jarvis
python3 business/ops/setup.py     # propagates your details into the landing page and scripts
```

---

## ☐ 2. Apply for a free M-Pesa Till (20 minutes)

On the Safaricom line registered to your ID:

- Dial **`*334#`** → *Lipa na M-Pesa* → *Till Number (Buy Goods)* → follow prompts.
- **Or** walk into any Safaricom shop in Nyeri town with your National ID — 30 minutes, free.

Approval: 1–3 working days. **Until it arrives, take payments on your personal M-Pesa number** ("Send Money"). Tell customers: *"Pay to 07xx xxx xxx — [YOUR NAME]."* That is completely normal in Kenya and nobody will blink.

---

## ☐ 3. Post the launch Status (10 minutes)

WhatsApp → Status → paste this image caption (use the graphic you'll make in step 4, or just plain text):

> 📄 **CV MAKEOVER — KES 800**
> Job hunting? I rewrite your CV in 24 hours so it actually gets shortlisted.
> ✅ ATS-friendly ✅ Kenyan format ✅ Cover letter included
> 📲 WhatsApp me: **07XX XXX XXX**
> Pay after you see the draft. Nyeri & nationwide.

Then **DM the same message to 10 people** — graduates, former classmates, anyone job hunting. Do not broadcast to a group; send it personally.

---

## ☐ 4. Make 3 graphics in Canva (30 minutes)

Free Canva account. Search template "Instagram Post". Make 3, in green/black:

| # | Headline | Sub-line |
|---|---|---|
| 1 | **CV MAKEOVER — KES 800** | 24 hours. Pay after you see the draft. |
| 2 | **NEED FUNDING? BUSINESS PLAN — KES 3,500** | For Uwezo Fund, Women Enterprise Fund, SACCO loans. |
| 3 | **FREE: 7 CV Mistakes That Cost You The Interview** | Comment "CV" or WhatsApp me. |

Post #3 today as a Status and in 3 Facebook groups. It is the lead magnet — it starts conversations.

---

## ☐ 5. Send 30 DMs (90 minutes — this is the whole business)

Work from `business/sales/scripts/dm-outreach.md`. Targets, in priority order:

1. **10 job seekers** — anyone whose status says "looking for a job", recent graduates, people posting "any leads?"
2. **10 small business owners in Nyeri** — salons, boutiques, butcheries, chemists, boda stages, mitumba sellers, car wash, cyber cafés. Offer the Social Starter Pack or the Biashara Plan.
3. **10 warm contacts** — church/mosque group, alumni group, family. Ask them to *share your Status*, not to buy.

**Rule: 30 DMs every single day for 14 days.** Log every reply in the tracker:

```bash
python3 business/ops/track.py add --product cv-makeover --amount 800 --channel whatsapp
```

---

## Today's score

By tonight you should have:
- [ ] Till applied for
- [ ] 1 WhatsApp Status live
- [ ] 30 DMs sent
- [ ] At least 5 replies
- [ ] **1 paying customer or 1 booked order**

The last one is the only one that matters. Everything before it is setup.

---

## When you get your first payment

1. Deliver fast — under the promised time.
2. Ask for a **screenshot testimonial** the moment they say thank you.
3. Log it: `python3 business/ops/track.py add ...`
4. Post the testimonial (name blurred if they prefer) as your next Status. Proof sells more than promises.
