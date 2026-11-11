# DM Outreach Scripts — send 30 of these a day

**Rule: never paste the same message to everyone.** Change the first line so it is clearly written for that person. Spam gets blocked and ignored.

**Rule: never open with the price.** Open with a question or a gift.

**Rule: 3 follow-ups, then stop.** Most sales happen on follow-up 2.

---

## Script 1 — Job seeker (the volume play)

**First message:**
> Hi [Name] 👋 Hope you're good. Saw your post about job hunting — are you still looking?

*(Wait for a reply. Do not pitch in message 1.)*

**If yes:**
> I actually do CV rewriting — I take your current CV and rebuild it so it passes the software most employers use to filter applications, then match it to the specific job you're applying for. KES 800, 24 hours, and you only pay after you've seen the draft.
> Want me to have a look at yours first? Free, no obligation. Just send it over.

**If they hesitate / "let me think":**
> No pressure at all. Tell you what — send me your CV and I'll point out the 3 biggest things I'd change. Free. If you want me to do the full rewrite after that, great. If not, you still walk away with a better CV.

**Follow-up 2 (2 days later):**
> Hey [Name], still happy to look at your CV for free whenever you're ready. Also — I'm doing a launch price of KES 500 for the first 10 people this month if that helps.

**Follow-up 3 (4 days later) — the close:**
> Last one from me [Name] 👋 If now's not the time, no problem at all. If you know anyone else job hunting, a share would mean a lot. All the best.

---

## Script 2 — Small business owner (the high-ticket play)

**First message:**
> Hi [Name], I've been following [their business] — you're doing well with [specific thing: the new location / your TikTok videos / the Saturday crowd]. Quick question: are you planning to expand or bring in stock this side of Christmas?

**If they engage:**
> The reason I ask — I write business plans for funding applications. Uwezo Fund, Women Enterprise Fund, Youth Fund, SACCOs, even the county. Most people near here never apply simply because they can't write the plan.
> I do the whole thing for KES 3,500 — one 30-minute call with you, I write it, you get it in 72 hours. Happy to show you a sample first?

**Objection: "I don't need funding":**
> Fair enough — plenty of people grow without it. In that case the thing that usually helps most is visibility. I do a Social Starter Pack: your bio, your profile, and 9 ready-to-post designs so your [shop/salon] looks sharp on WhatsApp and TikTok. KES 2,000. Want me to send you a sample design? Free.

**Objection: "KES 3,500 is a lot":**
> It is — until you compare it to what it unlocks. Uwezo is typically KES 50,000–100,000 per group. The plan costs less than 5% of that, and without it the answer is automatically no. If it doesn't get you approved, I'll refund you. That's the deal.

---

## Script 3 — Warm contact / friend (the amplifier)

> Hey [Name]! Quick one — I've started doing CV rewriting and business plans on the side (KaziPesa Digital). KES 800 for a CV, done in 24 hours.
> Not asking you to buy — asking you to **share my WhatsApp Status** if you see it this week. Or if you know someone job hunting or someone needing funding for a business, point them to me. Share my number: +254729213641.
> Asante! 🙏

*Warm contacts convert badly as buyers and brilliantly as distribution. Use them for reach, not revenue.*

---

## Script 4 — Facebook / WhatsApp group post (not a DM)

Post this in groups: Nyeri town buy/sell, job groups, church/mosque groups, alumni groups, boda boda groups, market groups. **Check group rules first — some ban promotion.**

> 📄 **CV MAKEOVER — KES 800** (launch price for the first 20 people)
>
> Sending out CVs and hearing nothing back? It's usually not your qualifications — it's formatting. Most employers filter CVs with software before a human ever reads them.
>
> I rebuild your CV so it passes the filter, and match it to the job you're applying for.
> ✅ 24-hour turnaround
> ✅ Cover letter included
> ✅ **You pay AFTER you see the draft**
>
> Also doing funding-ready business plans (Uwezo / WEF / Youth Fund / SACCO) — KES 3,500.
>
> 📲 WhatsApp **+254729213641**. Say "CV" and I'll send you a free guide first.

---

## Script 5 — The referral ask (after every happy customer)

> I'm really glad it worked out 🙌 One ask: who's the next person you know who needs this? A friend job hunting, a cousin whose business needs funding — even just sharing my number in your status helps more than you'd think. Asante!

---

## Objection playbook

| They say | You say |
|---|---|
| "Is this a scam?" | Fair question. I don't take money upfront — you see the draft, you like it, then you pay. If you don't like it, you don't pay. That's how confident I am. |
| "Let me think about it" | Of course. Want me to send you the free guide in the meantime? You might spot something you can fix yourself today. |
| "Too expensive" | I hear you. What's your budget? *(Then offer the KES 300 kit instead of discounting the service. Never discount — downgrade the product.)* |
| "I'll do it myself" | Honestly, go for it — the KES 300 kit has the templates and the guide. If you get halfway and hate it, I'll finish it for KES 500. |
| "Send me proof" | *Send 2–3 screenshots of testimonials immediately. Never argue — show.* |
| Silence | Follow-up 2 in 48h, follow-up 3 in 96h, then stop. Do not chase past 3. |

---

## Tracking

Log every DM, reply and sale:

```bash
python3 business/ops/track.py add --product cv-makeover --amount 800 --channel dm
```

Then check what's working:

```bash
python3 business/ops/track.py dashboard
```
