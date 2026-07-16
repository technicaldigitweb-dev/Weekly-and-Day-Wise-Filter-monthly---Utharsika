# UAWSO — Diagnosis: B0FX2XDLT5 June 2026 Order Count vs Business Expectation

**Scope:** Read-only diagnosis only. No HTML generated or modified. No requirement, production code, or database write. No `ph_task` access. No automation touched.
**ASIN:** B0FX2XDLT5
**Period:** `order_date >= '2026-06-01' AND order_date < '2026-07-01'`
**Execution date:** 2026-07-16

---

## 1. Active Order Logic Inspected (read-only)

| Concern | File / Function |
| ----- | ----- |
| Order extraction, status filtering, FBM/FBA classification, ASIN-date aggregation | `05_IMPLEMENTATION\src\extract_uawso_v5_asin_level.py` — `STATUS_FILTER_SQL` constant and the daily-aggregates query (lines ~149-176) |
| Status filter text | `STATUS_FILTER_SQL = "ot.order_status IS NOT NULL AND BTRIM(ot.order_status) <> '' AND BTRIM(ot.order_status) NOT IN ('Cancelled', 'Canceled')"` |
| Orders source scope | `ot.source_name IN ('AMAZON', 'REPLACEMENT')` — same query, `WHERE` clause |
| Sales source scope (for contrast) | `ot.source_name = 'AMAZON'` only, inside the `CASE WHEN` for `fbm_sales`/`fba_sales` |
| FBM/FBA classification | `COALESCE(ot.fba_sales, FALSE) = FALSE` → FBM; `ot.fba_sales = TRUE` → FBA |
| HTML embedded data generation | `05_IMPLEMENTATION\src\dashboard_renderer.py` (`render_dashboard_v5`) — embeds the `daily_aggregates_asin` JSON verbatim, no recalculation |
| Visible Orders calculation (client-side) | `05_IMPLEMENTATION\src\uawso_client_engine.js` — `sumRangeByAsinV5()` sums `fbm_orders`/`fba_orders` straight from the embedded per-(date,ASIN) rows; `computeRowsV5()` sets `totalOrders = fbmOrders + fbaOrders (+ vendorOrders)` — no additional status filtering happens client-side; all status filtering happens once, server-side, at extraction |

**No file was modified during this inspection.**

## 2. Raw Source Data (read-only, `public.order_transaction`)

18 rows found for `asin='B0FX2XDLT5'`, `order_date` in `[2026-06-01, 2026-07-01)` (no other filter applied at this stage). Full detail: `07_EVIDENCE\generated_data\2026-07-16_B0FX2XDLT5_june_order_item_reconciliation.csv`.

| source_name | count |
| ----- | ----- |
| AMAZON | 17 |
| REPLACEMENT | 1 |
| **Total** | **18** |

| raw_status | count |
| ----- | ----- |
| Completed | 16 |
| Canceled | 1 |
| Refunded | 1 |

## 3. Calculated Counts

| Item | Value |
| ----- | ----- |
| A. Raw qualifying rows (asin + date range, no other filter) | 18 |
| B. Raw distinct `order_item_info` | 18 (no duplicates - every value is distinct) |
| C. Exact status counts | Completed=16, Canceled=1, Refunded=1 |
| D. Distinct **Cancelled** (double-L) orders | 0 |
| E. Distinct **Canceled** (single-L) orders | 1 |
| F. Distinct normalized cancelled/canceled orders (D+E, no overlap) | 1 |
| G. Final valid distinct **Amazon-source-only** orders (`source_name='AMAZON'`, status-filtered) | **16** — matches business expectation exactly |

**Business-expected figures (17 raw / 1 cancelled / 16 valid) are exactly reproduced when the calculation is restricted to `source_name='AMAZON'` only.**

## 4. Cancelled Row — Full Detail

| Field | Value |
| ----- | ----- |
| `order_item_info` | 1034130000000 |
| `order_date` | 2026-06-24 13:58:27 |
| Raw status | `Canceled` |
| Raw length | 8 characters |
| Trimmed status | `Canceled` (identical - no leading/trailing whitespace) |
| Trimmed length | 8 characters |
| Normalized (lowercase) | `canceled` |
| Extended/compound text (e.g. "Cancelled by buyer") | NO - exact bare word only |
| Hidden Unicode / mixed case | NO - clean ASCII, exact case `Canceled` |
| `source_name` | AMAZON |
| Fulfilment type | FBA (`fba_sales = TRUE`) |
| `item_price` | NULL |
| `quantity` | 0 |

**No data-quality issue found in the cancelled row itself.** It is a clean, single-L `Canceled` value, correctly matched and excluded by `BTRIM(order_status) NOT IN ('Cancelled', 'Canceled')` at every pipeline stage tested (see Section 5).

## 5. Pipeline Stage Trace

| Stage | Scope used | Result for B0FX2XDLT5, June 2026 | Cancelled row excluded? |
| ----- | ----- | ----- | ----- |
| 1. Raw distinct source orders (no status/source filter) | all 18 rows | 18 | N/A (not yet filtered) |
| 1b. Raw distinct, `source_name='AMAZON'` only | 17 rows | 17 | N/A (not yet filtered) |
| 2. SQL-filtered orders, **AMAZON-only**, status-excluded (business's implicit definition) | AMAZON only | **16** | YES |
| 2b. SQL-filtered orders, **production rule** (`source_name IN ('AMAZON','REPLACEMENT')`, status-excluded, grouped by date+ASIN, summed) | AMAZON + REPLACEMENT | **17** | YES |
| 3. Python-extracted `daily_aggregates_asin` (re-derived directly from live SQL, matching the extraction script's own query) | AMAZON + REPLACEMENT | 17 (sum of `fbm_orders`+`fba_orders` across all June-2026 dates for this ASIN) | YES |
| 4. Embedded HTML `daily_aggregates_asin` JSON (extracted from the actual live `09_OUTPUTS\2026-07-15_utharsika_v004.html`) | AMAZON + REPLACEMENT | 17 (12 date-rows, `fbm_orders` sum=15, `fba_orders` sum=2) | YES |
| 5. Client-engine computed Orders (`sumRangeByAsinV5`/`computeRowsV5`, the same functions that render the visible table) | AMAZON + REPLACEMENT | 17 (pure pass-through sum of stage 4's data - no re-filtering) | YES (already excluded upstream) |

**The count becomes 17 (instead of the business's expected 16) at Stage 2b — the very first SQL query** — and is then faithfully carried unchanged through every later stage (Python, embedded HTML JSON, client engine, visible table). No stage after the SQL query introduces any further change or re-introduces the cancelled row.

## 6. Root Cause

**The cancellation filter is working correctly at every stage.** The single `Canceled` row (`order_item_info=1034130000000`) is excluded identically whether the AMAZON-only or AMAZON+REPLACEMENT scope is used — confirmed directly in Section 5 (row 2 vs row 2b both exclude it; the only difference between 16 and 17 is the REPLACEMENT row, not the cancelled row).

**Exact root cause:** `extract_uawso_v5_asin_level.py`'s Orders query (and its mirror in the daily-aggregates SQL) counts `order_item_info` from **both** `source_name='AMAZON'` and `source_name='REPLACEMENT'` rows as valid Orders (`ot.source_name IN ('AMAZON', 'REPLACEMENT')`). For this ASIN in June 2026 there is exactly one `REPLACEMENT`-source row (`order_item_info=1177733`, status `Completed`, June 1) that is **not cancelled** and therefore correctly counted as a valid Order under that rule — adding 1 to the AMAZON-only count of 16, producing 17.

This matches failure-mode candidate **"filter applied to AMAZON but not REPLACEMENT"** from the governing task's checklist — but precisely stated: it is not that the *cancellation* filter skips REPLACEMENT rows (it is applied identically to both sources, and correctly would have excluded a cancelled REPLACEMENT row too, had one existed). It is that the **Orders scope itself** intentionally includes REPLACEMENT rows as a separate, distinct-order-counting source, which the business's manual "raw distinct Amazon orders" framing for this spot-check did not anticipate.

**Important context — this is not a newly-introduced defect.** The `source_name IN ('AMAZON', 'REPLACEMENT')` Orders rule is a pre-existing, deliberately-established rule, confirmed earlier in this project (`07_EVIDENCE\2026-07-15_utharsika_v004_local_business_rule_data_validation.md`, Section 7) to be necessary to reconcile the full-scope historical Total Orders baseline (an AMAZON-only calculation produced 34,205 against an approved baseline of 34,454; adding REPLACEMENT rows closed that exact 249-row gap). It was not introduced or changed by this diagnosis, and this diagnosis did not change it either.

## 7. Why the Cancelled Order Appeared "Included" at First Glance

The coincidence that the business's *raw* AMAZON-only count (17) numerically equals the pipeline's *final* AMAZON+REPLACEMENT count (17) is what created the appearance that "cancellation was never applied." It was applied correctly (16 valid AMAZON rows, not 17) — the pipeline's 17 comes from a completely different row (a non-cancelled REPLACEMENT record) landing in the same numeric slot the cancelled row would have occupied if it had NOT been excluded. This is a pure numeric coincidence for this specific ASIN/month, not evidence of a shared defect.

## 8. Final PASS/FAIL (diagnosis-level)

```
- cancellation filter correctly excludes the Canceled row at every stage    YES
- AMAZON-only calculation reproduces the business's expected 16              YES
- production (AMAZON+REPLACEMENT) calculation produces 17, not 16            YES (confirmed, not a defect - see Section 6)
- root cause identified with exact file/function                            YES
- no file modified                                                          YES
- no HTML generated or modified                                             YES
- no database write                                                         YES
```

**Diagnosis: CONFIRMED.** A real, reproducible discrepancy exists between the business's manual expectation (16) and the report's actual Orders figure (17) for this ASIN/month, and it is now fully explained with file/function-level precision. The cancellation-exclusion mechanism itself has **no defect** — the discrepancy is caused by the existing, deliberate Vendor/Seller-Central-adjacent `REPLACEMENT` source inclusion rule in Total Orders, which is out of scope for this diagnosis-only task to change.
