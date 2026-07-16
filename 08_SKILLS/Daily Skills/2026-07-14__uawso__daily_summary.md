# UAWSO Daily Summary — 2026-07-14

**Project:** Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report (UAWSO)
**Developer:** Satheskanth
**Requirement:** REQ-01-D02
**Status:** COMPLETE

---

## What was done today

Found and fixed the real reason the dashboard's Sales and Orders numbers could drift from what people expected, then rebuilt and republished the report using the fix.

**1. Found the root cause: a fixed list instead of a smart rule.**
The dashboard was deciding which order statuses counted toward Sales and Orders using a fixed list written into the code: Completed, Refunded, Deleted, New, Pending, Inprogress, Hold. That list happened to be correct on the day it was written, but it was frozen — if Amazon ever introduced a brand-new status tomorrow, the dashboard would silently leave it out until a developer noticed and manually added it to the list.

**2. Replaced it with a rule that can't go stale.**
Instead of a fixed "include these statuses" list, the dashboard now uses a smarter rule: "include every status except Cancelled and Canceled." We checked the full order database and found exactly 9 statuses in use today — the same 7 as before, plus the two cancellation types, which are correctly excluded. Any new status that appears in the future will now be included automatically, with no code change needed. (A new status can still be reviewed and excluded later if it turns out it shouldn't count — but it will never be silently missed.)

**3. Rebuilt the report from scratch with the new rule.**
We didn't just patch numbers — we re-pulled the entire dataset fresh from the database (every order from 1 January 2025 through 13 July 2026, all 1,723 assigned products) and rebuilt the report file completely using the new rule.

**4. Checked every single month, not just the total.**
We compared the database, the report file, the on-screen dashboard, and the downloadable spreadsheet for all 19 months in the date range, one at a time. Every month matched exactly — down to the penny, and down to the exact order count. We also checked that no order was missing, no order was duplicated, and no order was counted twice.

**5. Tested against a real reference file.**
A business-provided spreadsheet with 7 real products was checked against the new report. 6 of the 7 matched exactly. The 7th needed a small correction — it turned out that product's SKU code in the spreadsheet had never actually been used in any real order; the sales were recorded under a slightly different (but related) SKU code instead. We documented this clearly rather than quietly merging the two SKU codes together.

**6. Published the update.**
The verified report replaced the previous version stored in the company system (`ph_task`, row 237). We updated the existing record in place — no new row was created, and the older report (`ph_task` row 157) was left completely untouched.

---

## Key numbers after the fix

| Metric | Value |
|---|---|
| Statuses found in the database | 9 (Canceled, Cancelled, Completed, Deleted, Hold, Inprogress, New, Pending, Refunded) |
| Statuses now included | 7 (everything except the 2 cancellation types) |
| Assigned products covered | 1,723 (all) |
| Date range rebuilt | 1 Jan 2025 – 13 Jul 2026 (19 months) |
| Months checked, differences found | 19 checked, 0 differences |
| Missing / duplicated orders found | 0 |
| Reference spreadsheet rows matched | 6 of 7 exactly (1 explained, not forced) |
| Total Sales (full period) | £717,994.56 |
| Total Orders (full period) | 34,413 |
| Total Quantity (full period) | 47,117 |

---

## No open questions today

Everything set out to be checked today was checked and matched exactly. Nothing was left unresolved or forced to match a number we couldn't prove.

**Next thing to watch:** whenever this report is refreshed again in the future, check for any status that isn't in today's list of 9 — a new one will be included automatically by the new rule, but someone should still glance at it to confirm it's really meant to count as a sale.

---

## Where to find the details

- Full technical write-up: `08_SKILLS\Daily Skills\2026-07-14__satheskanth__uawso__REQ-01-D02.md`
- Proof of the fix and full validation: `07_EVIDENCE\2026-07-14_utharsika_v002_DYNAMIC_STATUS_FINAL_BUILD_AND_PUBLICATION.md`
- Month-by-month check: `07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_dynamic_status_monthly_reconciliation.csv`
- Reference spreadsheet check: `07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_dynamic_status_reference_reconciliation.csv`
- Final report file: `09_OUTPUTS\2026-07-14_utharsika_v002.html`
- Company system record: `ph_task`, row 237
