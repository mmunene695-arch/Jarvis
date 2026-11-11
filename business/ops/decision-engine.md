# Decision Engine — the business runs on rules, not on willpower

This file is the "make advanced decisions for me" part, written down.

`track.py` implements these rules in code. Run `python3 business/ops/track.py dashboard` and it will tell you which rule has fired and what to do about it today.

Every rule is **IF a measurable condition → THEN a specific action.** No vibes.

---

## Pricing rules

| # | Condition | Action |
|---|---|---|
| P1 | 0 sales after **40 DMs** | Drop CV Makeover to **KES 500** for the next 10 customers, then back to 800. Do not touch the business-plan price. |
| P2 | 0 sales after **100 DMs** (≈Day 4) | The problem is the offer, not the price. Stop selling CVs. Switch the lead service to **Social Starter Pack** (visually provable) and re-test for 2 days. |
| P3 | **>8 orders/week** | Raise CV Makeover to **KES 1,200** and business plans to **KES 4,500** immediately. Demand is the only signal that matters. |
| P4 | A customer says "too expensive" | **Never discount.** Offer the cheaper product instead: KES 800 service → KES 300 kit. Discounting trains the market to wait. |
| P5 | 3+ people ask for the same thing you don't sell | Build it. Price it at the highest existing tier. Demand you didn't create is the best demand. |

## Channel rules

| # | Condition | Action |
|---|---|---|
| C1 | A channel sends **<1 reply per 30 contacts** after 2 days | Kill it. Move the time to the next channel. |
| C2 | A channel produces **>3 sales** | Double down. 70% of tomorrow's outreach goes there. |
| C3 | A video passes **5,000 views** | Stop posting for 6h, reply to every comment, pin a comment with your number, boost it KES 500 the next day. |
| C4 | DM reply rate **>20%** but sales **<5%** | Your pitch is fine, your close is weak. Start using the "pay after you see the draft" line in message 1. |
| C5 | Reply rate **<5%** | Your opening line is the problem. Rewrite the first sentence only — nothing else. |

## Delivery & quality rules

| # | Condition | Action |
|---|---|---|
| Q1 | You are **behind on any deadline** | Message the customer *before* the deadline, not after. "It'll be with you by 8pm instead of 5pm — sorry." Silence is what loses repeat business. |
| Q2 | A customer is unhappy | Refund in full, same day, no argument. Then ask what went wrong and write it down. |
| Q3 | You are working **>6 hours/day** | Raise prices 25% (see P3). You are underpriced, not overworked. |
| Q4 | You have **10 happy customers** | Ask every one for a screenshot testimonial. Build a single "proof" album on your phone. It is your most valuable asset. |

## Money rules

| # | Condition | Action |
|---|---|---|
| M1 | Revenue **< KES 2,000 by Day 7** | Cut all product work. Spend 100% of the time on the KES 3,500 business plan — one sale fixes the week. |
| M2 | Revenue **≥ KES 10,000** | Reinvest KES 1,500: Canva Pro (~KES 1,300) + KES 500 boosting your single best post. |
| M3 | Revenue **≥ KES 25,000** | Register the business formally, open the Paybill, and raise all prices 30%. You are no longer a side hustle. |
| M4 | **Any** day with zero outreach | Non-negotiable failure. 30 DMs/day is the floor. No exceptions — this is the engine. |

## Escalation ladder (when nothing is working)

```
Day 3:  0 sales  → Change the opening line. (C5)
Day 5:  0 sales  → Change the lead service.  (P2)
Day 7:  0 sales  → Change the audience: stop DMing job seekers, DM business owners only.
Day 9:  0 sales  → Change the channel: WhatsApp Status + Facebook groups only, drop TikTok.
Day 11: 0 sales  → Change the price: launch price KES 500, publicly, with a deadline.
Day 13: 0 sales  → Change the offer entirely: sell the KES 300 kit only, in volume, to groups.
```

If you reach Day 13 at zero, the model is wrong for your network, not for Kenya. Post your real numbers honestly and ask your network directly what they would pay for. That answer is worth more than any plan.

---

## Anti-patterns — things that will kill this

- ❌ Spending a day perfecting the logo instead of sending DMs.
- ❌ Building a website when WhatsApp works.
- ❌ Waiting for the Till number before selling.
- ❌ Waiting for KRA registration before selling.
- ❌ Group-blasting the same message to 200 strangers.
- ❌ Discounting on the first objection.
- ❌ Chasing a customer past the third follow-up.
- ❌ Taking money before showing work to a first-time buyer.
- ❌ Any "opportunity" that asks you to pay to join.
