# Product 2 — Pesa Tracker

**Price: KES 500** · Google Sheets / Excel / CSV

## What it is

A dead-simple money tracker for Kenyan small businesses: salons, mama mboga, boda boda, mitumba, car wash, cyber café, butchery, salon, boutique, kiosk.

It answers the three questions most Kenyan business owners cannot answer:

1. **How much did I actually sell today?**
2. **Where did the money go?**
3. **Did I make a profit this month — or just move money around?**

## Files

| File | Purpose |
|---|---|
| `pesa-tracker.csv` | The tracker. Import straight into Google Sheets. |
| This README | Setup (5 minutes) + the formulas to paste |

## Setup — 5 minutes

### Google Sheets (recommended)

1. Go to **sheets.google.com** → Blank spreadsheet.
2. **File → Import → Upload** → choose `pesa-tracker.csv`.
3. Import location: *Replace spreadsheet*. Separator: *Comma*.
4. Delete the two example rows, keep the headers.
5. **File → Make a copy** named `[Your Business] Pesa Tracker`.
6. Add the formulas below.
7. Bookmark it on your phone home screen. Fill it in every single evening — 5 minutes.

### Excel / LibreOffice

Open the CSV directly. Same formulas.

---

## The formulas to paste

Put these in a **Summary** block (below the data, or on a second tab).

Assuming your data is on a sheet called `Data` with headers in row 1, and these columns:
- `B` = Date
- `C` = Description
- `D` = Category
- `E` = Money In (KES)
- `F` = Money Out (KES)
- `G` = Payment Method

```
Total money in:          =SUM(Data!E:E)
Total money out:         =SUM(Data!F:F)
Profit:                  =SUM(Data!E:E)-SUM(Data!F:F)
Profit margin:           =IF(SUM(Data!E:E)=0,0,(SUM(Data!E:E)-SUM(Data!F:F))/SUM(Data!E:E))
Number of sales:         =COUNT(Data!E:E)
Average sale:            =IFERROR(AVERAGE(Data!E:E),0)
```

**This month only** (change the month in both dates):

```
Sales this month:        =SUMIFS(Data!E:E, Data!B:B, ">="&DATE(2026,11,1), Data!B:B, "<="&DATE(2026,11,30))
Expenses this month:     =SUMIFS(Data!F:F, Data!B:B, ">="&DATE(2026,11,1), Data!B:B, "<="&DATE(2026,11,30))
Profit this month:       =<sales this month> - <expenses this month>
```

**Biggest expense category** (put this next to a list of your categories):

```
=SUMIF(Data!D:D, "Stock", Data!F:F)
```

**Cash vs M-Pesa split:**

```
M-Pesa received:         =SUMIF(Data!G:G, "M-Pesa", Data!E:E)
Cash received:           =SUMIF(Data!G:G, "Cash", Data!E:E)
```

Format all KES cells as **KES #,##0**. It makes the sheet look professional and it stops rounding errors hiding.

---

## The 8 rules that make it work

1. **Fill it in every evening.** Not weekly. Weekly is a lie you tell yourself.
2. **Record everything, including the KES 50.** Small leaks sink businesses.
3. **Separate business money from personal money.** Withdraw a fixed "salary" to yourself and record it as an expense. If you dip into the till, record it.
4. **Never pay yourself before you've recorded the day's sales.**
5. **Review every Sunday.** 15 minutes. Look at the biggest expense category and ask: can this be smaller?
6. **Count your stock monthly.** Stock you bought is not an expense until you sell it — but most small businesses find it far more useful to record stock purchase as an expense the day they buy it. Pick one method and never switch.
7. **M-Pesa statements are your friend.** Once a month, dial `*234#` → *M-Pesa Statement* and check your sheet against it. Discrepancies = theft or forgetting.
8. **If profit is negative three months running, the business is not working.** Change the price, change the product, or change the plan. Hope is not a strategy.

---

## Sales copy (use verbatim)

> **Do you actually know what your business made last month?**
> Not what came in — what *remained*.
> Pesa Tracker is a simple KES sheet that shows your sales, expenses and real profit, every single day. Built for Kenyan small businesses. Works on your phone. No accounting knowledge needed.
> **KES 500.** Instant delivery on WhatsApp.
> Want me to set it up with your numbers? **KES 1,500** — I'll import your data and build your dashboard.

---

*© KaziPesa Digital. For the personal use of the purchaser. Do not resell or redistribute.*
