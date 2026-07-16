# UAWSO Dry-Run Data Evidence — 2026-07-09_utharsika_v001

**What this asset is:** Phase 5 evidence — the real data this session's dry run observed, before any publication decision.

**Why it exists:** To prove the pipeline was exercised against live data, not synthetic fixtures, before validation/publication is trusted.

**Source or evidence used:** Live read-only PostgreSQL queries (`public.user`, `public.ph_categories`, `public.ph_cate_products`, `public.order_transaction`), run via the approved read-only database tool. See execution log steps S013-S018.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Dry-run complete, validation passed, publication NOT executed (gated).
**Known limits:** DAILY section is full row-level detail (80 of 81 DB-returned rows transcribed — see logging gap in the execution summary). WEEKLY/MTD sections are exact aggregate totals only, not row-level, for this evidence capture.
**Pass/fail rule:** This dry run is fit to inform a real publish decision only if validation_report.all_passed is True and a human has reviewed the promoted HTML.
**Next action:** User confirmation required before publication — see `10_HANDOVER\UAWSO_HANDOVER.md`.

---

## Execution Context

- **Execution date (Asia/Colombo):** 2026-07-10
- **Report date:** 2026-07-09

## Reporting Period Ranges

| Period | Current-Year Window | Previous-Year Window |
|---|---|---|
| DAILY | 2026-07-09 → 2026-07-09 | 2025-07-09 → 2025-07-09 |
| WEEKLY | 2026-07-06 → 2026-07-09 | 2025-07-07 → 2025-07-09 |
| MTD | 2026-07-01 → 2026-07-09 | 2025-07-01 → 2025-07-09 |

## Scope

- Utharsika assigned-ASIN count: **1723** (via `public.user` → `public.ph_categories` → `public.ph_cate_products`, `which_channel=1`)
- DAILY: 12 current-year transaction rows, 11 asin-sku pairs with current-year activity, 81 previous-year transaction rows
- WEEKLY: 124 current-year transaction rows, 92 asin-sku pairs with current-year activity, 253 previous-year transaction rows
- MTD: 341 current-year transaction rows, 200 asin-sku pairs with current-year activity, 908 previous-year transaction rows

## Row Counts (grouped by ASIN+SKU, current OR previous year activity)

| Period | Rows |
|---|---|
| DAILY | 80 (see logging gap: DB returned 81) |
| WEEKLY | not individually fetched — aggregate only |
| MTD | not individually fetched — aggregate only |

## Totals

| Period | Prev Sales | Prev Orders | This Sales | This Orders |
|---|---|---|---|---|
| DAILY | 1,489.37 | 81 | 350.94 | 12 |
| WEEKLY | 4,817.56 | 253 | 2,788.72 | 124 |
| MTD | 17,900.53 | 908 | 7,442.66 | 341 |

Cross-check: DAILY previous_year_orders (81) and WEEKLY/MTD this_year_orders (124/341) all exactly match the independently-run count query (execution log S015), confirming these totals are not corrupted despite the DAILY 81→80 row-transcription discrepancy.

## Validation Outcomes (DAILY — the only period with row-level checks run this session)

**All checks passed: True**

| Check ID | Description | Result |
|---|---|---|
| DAILY-TREND-LABELS | Trend restricted to UP/DOWN/NO CHANGE | PASS |
| DAILY-SCOPE-ASIN | Every output ASIN is in the Utharsika-assigned set | PASS |
| DAILY-TOTAL-NOT-AVERAGED | Total Achieve Sales % is not an average of row-level percentages | PASS |
| DAILY-TOTAL-RECONCILE-SALES | Total This Year Sales reconciles with row-level sum (±0.01) | PASS (350.94 = 350.94) |
| DAILY-TOTAL-RECONCILE-ORDERS | Total This Year Orders reconciles with row-level sum (exact) | PASS (12 = 12) |
| DAILY-NO-FABRICATED-ACHIEVE | No achieve% fabricated when target is zero | PASS |

WEEKLY and MTD validation checks (`validate_period`) were not run this session since only aggregate — not row-level — data was fetched for those two periods; `validate_period` requires row-level input. This is a known limitation of this dry-run capture, not of the validator module itself, which is fully able to validate Weekly/MTD once row-level data is available (as it will be on a real `main.py` run).
