# 14-Day Launch Plan

**Start: Wednesday 2026-11-11. Day 14: Tuesday 2026-11-24.**
Daily rhythm: **3 hours.** 30 DMs. 2 Status posts. 2 videos. 30 minutes learning. That's it.

*In-person market days are deliberately placed on **Saturdays** (Day 4 and Day 11) — that is when Nyeri town and the market are busiest. Sundays are lighter days.*

---

## Week 1 — CASH (first M-Pesa by Day 3, KES 3,000 by Day 7)

### Day 1 (Wed 11 Nov) — Ship ugly
- [ ] Fill `brand/config.json`, run `python3 business/ops/setup.py`
- [ ] Apply for M-Pesa Till (`*334#` → Lipa na M-Pesa → Till Number)
- [ ] Post Status #1 (CV Makeover KES 800)
- [ ] Make 3 Canva graphics (30 min max — ugly is fine)
- [ ] **30 DMs**: 10 job seekers, 10 business owners, 10 warm asks-to-share
- [ ] Post the free CV guide to 3 Facebook groups
- 🎯 **Goal: 5 replies**

### Day 2 (Thu 12 Nov) — First revenue
- [ ] Status #2: the free guide ("comment CV")
- [ ] **30 DMs** — follow up yesterday's replies first
- [ ] TikTok/Reel #1 and #2 (hooks 1 and 2)
- [ ] Send the free guide to everyone who asked
- 🎯 **Goal: 1 paying customer**

### Day 3 (Fri 13 Nov) — Proof
- [ ] Deliver anything outstanding **early**
- [ ] Ask for a screenshot testimonial the moment they say thanks
- [ ] Status #3: the testimonial (blurred name if needed) + "2 slots left this week"
- [ ] **30 DMs**
- [ ] TikTok #3, #4
- [ ] Rule check: 0 sales after 40 DMs? → apply P1 (launch price KES 500)
- 🎯 **Goal: KES 800–1,600 banked**

### Day 4 (Sat 14 Nov) — Market day (in person)
- [ ] **Go physically to Nyeri town.** Market, stage, shops. Talk to 20 traders face to face. This is your unfair advantage over every online-only competitor.
- [ ] Take photos for content
- [ ] Status #4: "At the market today — here's what traders told me they need"
- [ ] 10 DMs to the people you met
- 🎯 **Goal: 3 warm leads + 20 numbers in your phone**

### Day 5 (Sun 15 Nov) — Push the high ticket
- [ ] Status #5: **business plan KES 3,500**
- [ ] **30 DMs** — 20 to business owners today, not job seekers
- [ ] Post in 3 more Facebook groups + 2 WhatsApp groups you're in
- [ ] TikTok #5, #6 (funding hooks 11, 12)
- 🎯 **Goal: 1 business-plan conversation booked**

### Day 6 (Mon 16 Nov) — Build the machine
- [ ] Confirm all products are in Google Drive (folders already created)
- [ ] Set up the Pesa Tracker as your own live Google Sheet — use your own product
- [ ] Batch-make 9 social posts (you'll reuse them for Social Starter Pack clients)
- [ ] Status #6: behind-the-scenes
- [ ] 30 DMs
- 🎯 **Goal: products deliverable in 2 minutes**

### Day 7 (Tue 17 Nov) — First checkpoint
- [ ] Run `python3 business/ops/track.py dashboard`
- [ ] Status #7: "Day 7 — honest numbers" (people love this)
- [ ] **30 DMs**
- [ ] TikTok #7, #8
- [ ] **Rule M1:** under KES 2,000? → drop products, 100% focus on business plans
- 🎯 **Goal: KES 3,000 cumulative**

---

## Week 2 — SCALE (KES 10,000 cumulative by Day 14)

### Day 8 (Wed 18 Nov) — Products go live
- [ ] Status #8: launch the 3 digital kits (300 / 500 / 1,500)
- [ ] Post the landing page link in bio on TikTok, Instagram, Facebook, WhatsApp
- [ ] **30 DMs** + offer the kit to everyone who said "too expensive" in Week 1
- [ ] TikTok #9, #10
- 🎯 **Goal: 3 kit sales**

### Day 9 (Thu 19 Nov) — Upsell day
- [ ] Message **every past customer** with the bundle offer (KES 1,900) — easiest money you'll make
- [ ] Status #9
- [ ] **30 DMs**
- [ ] TikTok #11, #12
- 🎯 **Goal: 2 upsells**

### Day 10 (Fri 20 Nov) — Credibility
- [ ] **Register the business name** on eCitizen (KES ~1,000) + confirm KRA PIN
- [ ] Make a "proof" album: every testimonial, every before/after
- [ ] Status #10, #11
- [ ] **30 DMs**
- [ ] TikTok #13, #14 (hooks 21–25 — your own numbers)
- 🎯 **Goal: legally real + 10 public testimonials**

### Day 11 (Sat 21 Nov) — Market day 2 (in person)
- [ ] Back to Nyeri town / market / campus **with your proof album**
- [ ] Collect 20 WhatsApp numbers in person — face-to-face converts ~5× better than a DM
- [ ] Status #12
- [ ] 20 DMs
- 🎯 **Goal: 20 new contacts in your phone**

### Day 12 (Sun 22 Nov) — Volume
- [ ] Biggest outreach day: **50 DMs**
- [ ] Launch offer with a deadline: "KES 500 CV — last 10 slots, closes tomorrow"
- [ ] Status #13
- [ ] TikTok #15, #16
- 🎯 **Goal: KES 2,500 in one day**

### Day 13 (Mon 23 Nov) — Convert
- [ ] DM all new contacts + all 12 days of warm leads with a final deadline offer
- [ ] Status #14: "Closing my launch price tonight"
- [ ] 20 DMs
- 🎯 **Goal: KES 3,000**

### Day 14 (Tue 24 Nov) — Review and decide
- [ ] Run `python3 business/ops/track.py dashboard`
- [ ] Post your honest 14-day numbers (hook 24 — this post will outperform everything else)
- [ ] Keep every process that produced a sale; delete everything that didn't
- [ ] Set the Day 30 target
- 🎯 **Goal: KES 10,000 cumulative. Then keep going.**

---

## The daily scorecard

Copy this into your notes every morning:

```
Date:            ______
DMs sent:        ______ / 30
Replies:         ______
Status posts:    ______ / 2
Videos posted:   ______ / 2
Orders:          ______
Revenue (KES):   ______
Best channel:    ______
One thing to repeat tomorrow: ______________________
```

Log every sale:
```bash
python3 business/ops/track.py add --product cv-makeover --amount 800 --channel whatsapp
python3 business/ops/track.py log --dms 30 --replies 4
```
