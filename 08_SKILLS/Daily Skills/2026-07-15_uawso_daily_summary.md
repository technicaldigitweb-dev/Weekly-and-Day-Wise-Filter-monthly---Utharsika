# UAWSO Daily Summary — 2026-07-15

**Project:** Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report (UAWSO)
**Developer:** Satheskanth
**Requirement:** REQ-02-D01
**Status:** COMPLETE

---

## What was done today

Rebuilt the report around products instead of SKUs, added a product picture, made the table much easier to use, and published the result.

**1. One row per product, not one row per SKU.**
Before today, a product with 3 SKUs could show as 3 (or more) separate rows, which made the report harder to read and created a real risk of counting the same order twice. We rebuilt the report so every product (ASIN) now gets exactly one row, with all its SKU activity combined underneath it. This wasn't just a display change — the underlying database query itself was changed to add everything up per product directly, not per SKU-then-summed, which is the part that actually closes the double-counting risk.

**2. Added a product picture.**
The report now shows a picture for each product instead of the SKU code. Pictures come from the same product-listing data Amazon itself uses. When a product has more than one possible picture, the report always picks the same one every time it's regenerated (so the picture doesn't randomly change between refreshes) — Utharsika confirmed any valid picture is fine, since all SKUs under one product are the same item for this report.

**3. Checked everything against the live database, independently, one more time.**
Rather than trust the numbers already in the file, we re-pulled every figure straight from the database again — for all 1,723 products, one at a time — and compared it to what the report actually shows. Every single product matched exactly: same Sales, same Orders, same Quantity, same picture. Zero differences anywhere. Along the way we found one thing worth flagging honestly: two report columns ("Order Change %" and "Quantity Change %") don't yet have a written business rule behind them, even though the code calculates them consistently — we did not invent a rule to explain them; that needs a decision from the business side.

**4. Fixed the table so you can actually see 15 rows at once.**
The scrollable part of the table was sized as "70% of whatever window you have open," so depending on your screen it might only show a handful of rows before you had to scroll. We measured the real height of the header, a row, and the bottom bar with an actual browser, and fixed the table to always show exactly 15 full rows, no matter what size window you're using. The number of rows per page (50) did not change — that's a separate setting from how many rows you can see without scrolling.

**5. Made the table itself easier to work with.**
Added a header that stays visible while you scroll down, and the first two columns (product and picture) stay visible while you scroll sideways. Added a scrolling bar at the bottom with Previous/Next buttons and a "go to page" box. Kept exactly one "download everything" button, which always downloads all the currently filtered rows, not just the ones on screen.

**6. Published the update, then corrected it in place.**
The finished report replaced the previous version stored in the company system (`ph_task`, row 256). After it was published, we found the table-height problem described in point 4, fixed it, and updated the same row again — no new report version was created, no new row was added, and both the old file and the old database row were safely backed up first, just in case.

**7. Recorded today's work in the daily work log.**
Saved a summary of today's work in the project's daily-task tracker so it's on record.

---

## Key numbers after the fix

| Metric | Value |
|---|---|
| Products covered | 1,723 (all assigned products) |
| Report rows | 1,723 (one per product — no duplicates) |
| Products with a picture | 1,699 |
| Products with no picture available | 24 |
| Products with more than one possible picture | 227 (a single one is always picked, consistently) |
| Total Sales (full period) | £718,835.91 |
| Total Orders (full period) | 34,454 |
| Total Quantity (full period) | 47,166 |
| Products re-checked against the live database today | 1,723 of 1,723 |
| Differences found in that re-check | 0 |
| Rows visible without scrolling (table height fix) | 15, on any screen size |
| Rows per page (unchanged) | 50 |

---

## One open question — not resolved yet

Two columns on the report ("Order Change %" and "Quantity Change %") show a percentage the system calculates the same way as the approved "Sales Change %" column, but there is no written business rule confirming that's the correct way to show Orders/Quantity movement over time. We did not remove the columns or invent a justification — we're flagging it so the business side can confirm or correct it.

**Next step:** Business validator (Utharsika) to confirm the intended rule for "Order Change %" and "Quantity Change %", or confirm the existing calculation is correct as-is.

---

## Where to find the details

- Full technical write-up: `08_SKILLS\Daily Skills\2026-07-15__satheskanth__uawso__REQ-02-D01.md`
- Requirement document: `01_REQUIREMENTS\Requirement\2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md`
- Build and validation proof: `07_EVIDENCE\2026-07-15_utharsika_REQ-02-D01_complete_real_data_html_validation.md`
- Independent re-check against the live database: `07_EVIDENCE\2026-07-15_utharsika_v004_local_business_rule_data_validation.md`
- Sticky header/columns/download proof: `07_EVIDENCE\2026-07-15_utharsika_v004_sticky_columns_export_and_definitions_validation.md`
- Sticky page-navigation proof: `07_EVIDENCE\2026-07-15_utharsika_v004_sticky_pagination_validation.md`
- Publication proof: `07_EVIDENCE\2026-07-15_utharsika_v004_ph_task_publication.md`
- Table-height fix proof: `07_EVIDENCE\2026-07-15_utharsika_v004_15_row_view_and_row_256_replacement.md`
- Final report file: `09_OUTPUTS\2026-07-15_utharsika_v004.html`
- Company system record: `ph_task`, row 256
- Daily work log record: `daily_task.tbl_uawso_satheskanth`, row 3
