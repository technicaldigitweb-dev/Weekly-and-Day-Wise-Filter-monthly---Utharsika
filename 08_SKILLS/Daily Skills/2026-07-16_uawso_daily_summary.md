# UAWSO Daily Summary — 2026-07-16

**Project:** Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report (UAWSO)
**Developer:** Satheskanth
**Requirement:** REQ-02-D02
**Status:** COMPLETE

---

## What was done today

Fixed a real counting mistake in Orders, published a fresh report with the fix applied, then built a complete "push-button" system so this whole process can run by itself every day going forward.

**1. Fixed a real Orders mistake — REPLACEMENT orders were being counted.**
Orders were previously being counted from two sources: normal Amazon orders and "REPLACEMENT" orders (Amazon's own replacement-item transactions). We traced a specific case (product B0FX2XDLT5, June 2026) where the business-expected Orders count was 16, but the report showed 17. Investigation proved the cancellation logic itself was working correctly — the extra "17th" order was a REPLACEMENT-source row that should never have been counted as an Order in the first place. We changed the rule so only real Amazon orders count as Orders (`source_name = 'AMAZON'` only); REPLACEMENT rows no longer count. This did not touch Sales, which was already correct.

**2. Published a fresh report with the fix, using entirely new data pulled today.**
Rather than patch the old file, we pulled completely fresh data straight from the database (not reused from yesterday) and built a brand-new report: `2026-07-16_utharsika_v001.html`. Every number was independently re-checked a second way (a separate database query, not just re-reading what the report itself calculated) before publishing. It was then published to the company system as a new record (`ph_task`, row 262) — the 2026-07-15 report and its record were left completely untouched.

**3. Built a complete automation system — the report can now be produced with one command.**
Until today, producing a report meant a person running several scripts by hand, in the right order, checking things manually along the way. We built a single reusable program (`uawso_daily`) that does the entire job by itself: checks the database has today's data ready, pulls it fresh, calculates everything, checks the result against the database one more time before allowing it to be published, safely saves the new report file (never overwriting an existing one), publishes it, and then double-checks what actually got saved in the company system matches the file on disk exactly.

**4. Registered a simple day-to-day command: "update for today."**
From now on, saying "update for today" runs the whole automation above in one step — no need to re-explain the process each time. The system itself is careful: if today's report already exists and is correct, it does nothing (no duplicate files, no duplicate database records) and just confirms that. We proved this live twice today — the system correctly recognized that today's report was already done and made zero changes both times.

**5. Made sure it can never create a mess — duplicate protection, locking, and safety checks.**
Several protections were built in and tested: it will not let two copies run at the same time; it will not create two "active" reports for the same day; it will never touch a previous day's report or database record; and after publishing, it re-reads what was actually saved in the company system and compares it byte-for-byte against the local file, to catch any publishing problem instead of assuming it worked.

**6. Prepared — but did not turn on — scheduled running.**
We prepared the instructions needed to eventually have a server run this automatically every day at 12:00 PM (Colombo time), but did **not** install or activate any scheduled job. That is intentionally left for a separate, explicit decision later, once a server is set up for it.

**7. Recorded both pieces of today's work in the daily work log.**
Saved two entries in the project's daily-task tracker: one for the Orders fix and fresh report, and one for the automation-system build — each on record separately.

---

## Key numbers (2026-07-16 report)

| Metric | Value |
|---|---|
| Products covered | 1,723 (all assigned products) |
| Report period | 2025-01-01 through 2026-07-15 |
| FBM Sales | £487,957.12 |
| FBA Sales | £184,681.80 |
| Vendor Sales | £46,814.94 |
| **Total Sales** | **£719,453.86** |
| FBM Orders | 26,271 |
| FBA Orders | 7,975 |
| Vendor Orders | 4,748 |
| **Total Orders** | **38,994** |
| Automation self-checks passed | 42 of 42 |
| Live validation checks passed (today's report) | 8 of 8 |
| Unwanted duplicate files/records created today | 0 |

---

## What is not finished yet — and why that is fine

The automation itself is complete and works correctly today, right now, on request. What remains is only the **scheduling** step — actually having a server run it automatically every day without anyone asking. That needs a server to be set up first, one test run on that server, and then a separate, explicit "yes, turn it on" decision before the 12:00 PM daily schedule is switched on. Nothing about today's work is blocked by this — it only affects whether the report can run completely unattended in the future.

**Next step:** Set up the server, do one trial run on it, then get explicit sign-off before switching on the daily 12:00 PM schedule.

---

## Where to find the details

- Full technical write-up (Orders fix, automation system): `08_SKILLS\Daily Skills\2026-07-16__satheskanth__uawso__REQ-02-D02.md`
- Business-rule change record (Orders fix): `01_REQUIREMENTS\Requirement Updates\2026-07-16_satheskanth_REQ-UAWSO_REQ-02-D01_amazon_only_orders_update.md`
- Automation system, full build and test proof: `07_EVIDENCE\2026-07-16_uawso_daily_automation_system_validation.md`
- "update for today" live run proof: `07_EVIDENCE\2026-07-16_uawso_daily_uawso_20260716_165137.md`
- Fresh report validation proof: `07_EVIDENCE\2026-07-16_utharsika_v001_fresh_amazon_only_orders_validation.md`
- Publication proof: `07_EVIDENCE\2026-07-16_utharsika_v001_ph_task_publication.md`
- Orders-mistake investigation: `07_EVIDENCE\2026-07-16_B0FX2XDLT5_june_cancelled_order_diagnosis.md`
- Automation system source code: `05_IMPLEMENTATION\uawso_daily\` (see its `README.md` for full instructions)
- Final report file: `09_OUTPUTS\2026-07-16_utharsika_v001.html`
- Company system record: `ph_task`, row 262
- Daily work log records: `daily_task.tbl_uawso_satheskanth`, rows 3 (previous day, unaffected) and 4 (today's automation-system entry)
