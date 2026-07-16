# UAWSO — June 2025 Difference Investigation and Exact ASIN–SKU Verification

**What this asset is:** Two independent read-only investigations — (1) why Utharsika's user-confirmed June 2025 figures (£42,082.96 / 2,412 orders) differ from the current PostgreSQL/HTML result (£41,146.84 / 1,856 orders), and (2) full verification of one exact ASIN–SKU pair across database, workbook, and HTML.

**Why it exists:** To exhaustively test every supported business-rule variant for the June difference, and to prove one specific product's figures are correct end-to-end.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran / whoever holds the £42,082.96 reference figure
**Current status:** WORK 1 — root cause not found despite exhaustive testing (FAIL per stop conditions). WORK 2 — fully verified, exact match across DB and HTML (PASS).
**Pass/fail rule:** Per task Sections 20–21.
**Next action:** Route WORK 1's unresolved £936.12/556-order gap to whoever can explain how the £42,082.96/2,412 reference figure was derived — no database-supported combination reproduces it.

---

## COMMON SCOPE — Utharsika-Owned ASINs (freshly re-verified)

| Check | Result |
|---|---|
| Resolved username | `utharsika` |
| Raw assignment-row count | 1,723 |
| Distinct assigned ASIN count | 1,723 |
| Duplicate assignment-row count | **0** (raw = distinct; no duplication observed today) |
| Blank ASIN count | 0 |
| ASINs shared with another user | **0** |
| Final canonical scope count | **1,723** |

Every query in both investigations below used this exact 1,723-ASIN scope.

---

# WORK 1 — Why June 2025 Totals Differ

## 1. Current UAWSO Calculation (reproduced fresh this session)

**Source tables:** `public.order_transaction`, `public.vendor_sales`
**Assigned-ASIN join:** `public.user` → `public.ph_categories` → `public.ph_cate_products` (`which_channel=1`), `DISTINCT`
**Date column:** `order_transaction.order_date` (timestamp without time zone), cast to `::date`
**Date boundaries:** `2025-06-01` to `2025-06-30` inclusive
**Timezone handling:** No explicit shift applied to `order_date` in the current calculation (tested with an Asia/Colombo shift separately — see Section 9)
**Source filter:** `source_name = 'AMAZON'`
**Marketplace filter:** `market_place = 'UK'`
**Order-status filter:** `order_status = 'Completed'`
**Sales field:** `SUM(COALESCE(order_total, 0))`
**Order-count expression:** `COUNT(DISTINCT order_item_info)`
**FBA/FBM rule:** `fba_sales = TRUE` → FBA; `fba_sales = FALSE` or `NULL` → FBM
**Vendor inclusion:** `public.vendor_sales`, period-overlap allocation, `ordered_revenue`/`ordered_units`, ASIN-level only (no SKU)
**SKU requirement:** None — SKU is never used as a filter in the current calculation

| Metric | Reference (from task) | Reproduced this session | Match |
|---|---|---|---|
| FBM Sales | £29,180.13 | £29,180.13 | ✅ exact |
| FBA Sales | £7,663.75 | £7,663.75 | ✅ exact |
| Vendor Sales | £4,302.96 | £4,302.96 | ✅ exact |
| Total Sales | £41,146.84 | £41,146.84 | ✅ exact |
| FBM/FBA Orders | 1,856 | 1,856 | ✅ exact |
| Vendor Units | 528 | 528 | ✅ exact |

No stale-data issue — all reference values confirmed current and stable. Query run at this session's timestamp (2026-07-14).

## 2. Database Column Inventory

**`public.order_transaction`** (confirmed live, not assumed): `order_item_info` (bigint, PK), `order_id` (text), `item_id` (text), `asin` (text), `product_id` (text), `sku` (text), `item_price` (numeric), `quantity` (bigint), `order_status` (text), `order_date` (timestamp without time zone), `order_total` (double precision), `order_sub_source` (bigint), `ss_name` (text), `source` (bigint), `source_name` (text), `market_place` (text), `fba_sales` (boolean), `category_id`, `category_name`, `user_id`, `user_name`.

**`public.vendor_sales`**: `id`, `start_time`, `end_time` (both timestamp — a period, not a single date), `asin` (text, no SKU column), `ordered_units` (bigint), `ordered_revenue` (double precision), `currency_code`, `created_at`, `updated_at`, `category_id`, `category_name`, `user_id`, `user_name`.

## 3. Status Differences

| Status | Row count | Distinct order ID | Distinct order-item | Quantity | Sales |
|---|---|---|---|---|---|
| Completed | 1,856 | 1,783 | 1,856 | 2,325 | £36,843.88 |
| Cancelled | 49 | 48 | 49 | 12 | £195.20 |
| Refunded | 35 | 34 | 35 | 44 | £40.98 |
| Canceled *(single-L, distinct string)* | 7 | 7 | 7 | 0 | £0.00 |

- **Approved status only (Completed):** £36,843.88 / 1,856 orders
- **All non-cancelled** (excludes only `'Cancelled'`, includes Refunded + Canceled): £36,884.86 / 1,898 orders
- **All positive-Sales rows:** identical to Completed-only (£36,843.88) — no positive-Sales rows exist outside Completed
- **All statuses:** £37,080.06 / 1,947 orders

**Amount excluded by the Completed-only filter:** £236.18 Sales (Cancelled £195.20 + Refunded £40.98 + Canceled £0.00), 91 rows/orders. **This does not reach £936.12.**

## 4. Marketplace Differences

| Marketplace | Row count | Distinct order-item | Sales |
|---|---|---|---|
| UK (approved) | 1,856 | 1,856 | £36,843.88 |
| Germany | 224 | 224 | £5,285.16 |
| Italy | 75 | 75 | £2,592.57 |
| France | 45 | 45 | £1,364.32 |
| Ireland | 43 | 43 | £1,274.73 |
| Sweden | 2 | 2 | £861.98 |
| Spain | 7 | 7 | £255.48 |
| Netherlands | 2 | 2 | £187.25 |
| Belgium | 2 | 2 | £119.60 |
| Canada | 1 | 1 | £42.93 |

Blank marketplace rows: **0** (none found).

**Exhaustive brute-force test:** every one of the 2⁹ = 512 possible combinations of the 9 non-UK marketplaces was checked programmatically for a subset summing to exactly £936.12. **No combination matches** (within a 2-pence tolerance). Marketplace inclusion is **ruled out** as the explanation.

## 5. Source Differences

| Source | Row count | Distinct order-item | Sales |
|---|---|---|---|
| AMAZON (source=1, approved) | 1,856 | 1,856 | £36,843.88 |
| REPLACEMENT (source=11) | 8 | 8 | **£0.00** |

No other source values found linked to the assigned ASINs in this window. REPLACEMENT rows carry **zero Sales** — including them cannot explain any part of the £936.12 Sales gap, though they would add up to 8 to an Orders count if counted (see Section 8).

## 6. Account/Seller Differences

| Account (`ss_name`) | FBM Sales | FBA Sales | Orders | Quantity |
|---|---|---|---|---|
| amazon Dcvoltage | £15,267.97 | £5,394.32 | 1,056 | 1,288 |
| amazon Ledsone | £13,896.87 | £2,269.43 | 799 | 1,036 |
| amazon SRM Amazon | £15.29 | £0.00 | 1 | 1 |

All three known accounts are **already fully included** in the current calculation (sum = £36,843.88, matching exactly). No account is currently excluded that could be added to increase the total — ruling out an account-scope explanation.

## 7. Sales Definition Tests

| Definition | Sales | Rows |
|---|---|---|
| Net Sales, Completed (current) | £36,843.88 | 1,856 |
| Positive Sales only | £36,843.88 | 1,856 (identical — no negative `order_total` rows exist) |
| All non-cancelled | £36,884.86 | 1,898 |
| All statuses | £37,080.06 | 1,947 |
| No SKU restriction | £36,843.88 | 1,856 (identical — SKU was never a filter) |
| `item_price × quantity` (alternate Sales definition) | £36,324.79 | — (**lower** than `order_total`, wrong direction) |
| `item_price` alone | £28,828.87 | — (**much lower**, wrong direction) |

**No tested Sales definition adds exactly £936.12.** Gross-vs-net is not a factor (no negative rows exist). Alternate revenue definitions (`item_price×quantity`, `item_price` alone) both move in the wrong direction (lower, not higher).

## 8. Order-Count Definition Tests

| Definition | Value |
|---|---|
| `COUNT(*)` | 1,856 |
| `COUNT(DISTINCT order_id)` | 1,783 (lower — one invoice can span multiple line items) |
| `COUNT(DISTINCT order_item_info)` (current) | 1,856 |
| `SUM(quantity)` | 2,325 |
| Positive-Sales row count | 1,856 (identical) |
| Distinct ASIN–SKU–date records | 1,590 |
| FBM/FBA Orders + Vendor Units | 1,856 + 528 = **2,384** |
| FBM/FBA Orders + Vendor row count (13) | 1,856 + 13 = 1,869 |
| FBM/FBA Orders + distinct Vendor ASIN-date count (13) | 1,856 + 13 = 1,869 |

**User target: 2,412. Closest tested value: 2,384 (FBM/FBA Orders + Vendor Units), short by exactly 28** — matching the task's own stated remaining gap. **No combination of any tested database-supported metric reaches exactly 28 additional Utharsika-owned records in a single, clean, evidence-backed category:**
- REPLACEMENT source rows = 8 (not 28)
- Refunded rows = 35 (not 28)
- Canceled (single-L) rows = 7 (not 28)
- REPLACEMENT + Canceled = 8+7 = 15 (not 28)
- Refunded − REPLACEMENT = 35−8 = 27 (closest found, still not exact, and not a coherent business rule)

**No exact 28-row explanation was found.** The remaining 28-order gap is not reproducible from any single tested dimension.

## 9. Date Field Tests

| Variant | Sales | Orders |
|---|---|---|
| `order_date::date` (current) | £36,843.88 | 1,856 |
| Asia/Colombo (+5:30) shift applied | £36,726.81 | 1,850 |
| Inclusive-end via `< 2025-07-01` timestamp | £36,843.88 | 1,856 (identical) |

The timezone-shift variant moves **in the wrong direction** — it *decreases* both Sales and Orders slightly, which would *widen* the gap to the user's higher figure, not close it. Date-boundary/timezone handling is **ruled out**.

## 10. SKU and Assignment Effects

| Test | Result |
|---|---|
| Blank SKU rows | 0 |
| Group by ASIN only | 526 distinct ASINs, Sales unchanged (£36,843.88) |
| Group by ASIN+SKU | 539 distinct pairs, Sales unchanged (£36,843.88) |
| Assignment table without `DISTINCT` | Raw row count = 1,723 = distinct count; **no duplication present**, Sales unchanged when using the raw (undeduplicated) ASIN list in an `IN` clause |

Aggregation grain (ASIN-only vs ASIN+SKU) does not change the Sales total — ruled out. Assignment-table duplication is **not present** in the current live data (freshly re-verified, differs from a prior session's finding of 2x duplication, which is not reproduced today).

## 11. Vendor Scope

| Check | Result |
|---|---|
| Vendor Sales | £4,302.96 |
| Vendor Units | 528 |
| Vendor row count | 13 |
| Distinct Vendor ASINs | 13 |
| Distinct Vendor ASIN-date rows | 13 |
| Positive / zero / negative Vendor rows | 13 / 0 / 0 |

Vendor is confirmed included once per ASIN-level record, with no negative or anomalous rows. Vendor is correctly isolated — not the source of the Sales gap.

## 12. Exact Difference Dataset

See `07_EVIDENCE\generated_data\2026-07-10_utharsika_june_difference_rows.csv` — every excluded category (status, marketplace, source) with row counts and Sales amounts, each tagged with its exclusion reason.

**No combination of these excluded categories sums to exactly £936.12 or 556/28 orders.** An `exact_difference_rows.csv` file was **not created**, per instruction, because no exact-matching row set was found — creating one would misrepresent an approximate or partial finding as exact.

## 13. Candidate User Calculations (A–J)

See `07_EVIDENCE\generated_data\2026-07-10_utharsika_june_candidate_calculations.csv` for the full table. Summary:

| Variant | Sales | Sales diff from £42,082.96 | Orders | Orders diff from 2,412 |
|---|---|---|---|---|
| A. Current UAWSO | £41,146.84 | −£936.12 | 1,856 | −556 |
| B. Current + Vendor Units as Orders | £41,146.84 | −£936.12 | 2,384 | −28 |
| C. All non-cancelled + Vendor | £41,187.82 | −£895.14 | 2,426 | **+14** |
| D. All statuses + Vendor | £41,383.02 | −£699.94 | 2,475 | +63 |
| E. UK + blank-marketplace + Vendor | £41,146.84 | −£936.12 | 2,384 | −28 |
| F. All Amazon aliases + Vendor | £41,146.84 | −£936.12 | 2,392 | −20 |
| G. Gross Sales + Vendor | £41,146.84 | −£936.12 | 1,856 | −556 |
| H. No SKU restriction | £41,146.84 | −£936.12 | 1,856 | −556 |
| I. ASIN-only aggregation | £41,146.84 | −£936.12 | 1,856 | −556 |
| J. Sum of all known accounts | £41,146.84 | −£936.12 | 1,856 | −556 |

**No variant reaches exactly £42,082.96 or 2,412.** The numerically closest Sales variant (D, all statuses) is still £699.94 short and requires including non-Completed rows, which contradicts the approved business rule. The numerically closest Orders variant (C) *overshoots* by only 14 but under-delivers Sales by £895.14 and also requires a non-approved status inclusion.

---

## WORK 1 CONCLUSION

Despite exhaustive, systematic testing across every requested dimension (status, marketplace, source, account, Sales definition, Order-count definition, date/timezone, SKU/assignment grain, Vendor scope) — including a full brute-force subset-sum search across all non-UK marketplace combinations — **no evidence-backed combination reproduces the £936.12 Sales difference or the 556/28 Orders difference exactly.** The current UAWSO calculation is confirmed stable, correctly filtered, and free of the tested defects (no duplication, no negative-row miscounting, no timezone error, no account exclusion). **The root cause remains unidentified from the database side; this requires the business to explain how the £42,082.96/2,412 reference figure was originally derived.**

---

# WORK 2 — Exact ASIN–SKU Pair Verification

**ASIN:** `B0FX2QT3B1`
**SKU:** `LSCYRO300GD2PK+RPR44WH2PK`

## 14. Ownership and Pair Mapping

| Check | Result |
|---|---|
| ASIN in Utharsika's canonical assigned scope | **YES** |
| Exact SKU exists under this ASIN | **YES** (stored form matches requested form exactly — same case, same characters, no whitespace difference) |
| Exact normalized ASIN–SKU pair exists | **YES** — 40 total rows across all time |
| Other SKUs linked to the same ASIN | **`RPR44WH`** — 1 row, dated 2026-06-13, `source_name='REPLACEMENT'`, `order_total=£0.00` (a zero-value resend/replacement record, correctly excluded by the `source_name='AMAZON'` filter — not a second real sale) |
| First transaction date (exact pair) | 2025-10-26 |
| Latest transaction date (exact pair) | 2026-06-29 |
| Total rows for the exact pair (all time) | 40 |

## 15. Exact Pair — June 2025

| Metric | Value |
|---|---|
| FBM Sales | £0.00 |
| FBM distinct Orders | 0 |
| FBA Sales | £0.00 |
| FBA distinct Orders | 0 |
| Row count | 0 |
| Total transactional Sales | £0.00 |
| Total transactional Orders | 0 |

**Explanation:** the first-ever transaction for this exact ASIN–SKU pair is dated **2025-10-26** — after June 2025 ends. **Zero is the factually correct figure for this period; there is no data to exclude.**

## 16. Exact Pair — June 2026

| Metric | Value |
|---|---|
| FBM Sales | £699.76 |
| FBM distinct Orders | 21 |
| FBA Sales | £0.00 |
| FBA distinct Orders | 0 |
| Total transactional Sales | £699.76 |
| Total transactional Orders | 21 |
| Total quantity (Completed, in-window) | 24 |

**Statuses found (in window):** Completed (21 rows), Refunded (1 row, 2026-06-04, £0.00), Cancelled (3 rows, 2026-06-21/29, £0.00).
**Marketplaces found:** UK only.
**Sources found:** AMAZON only (the `RPR44WH` REPLACEMENT row falls outside this exact SKU).
**Accounts found:** `amazon Dcvoltage` only.
**Excluded Sales:** £0.00 (the 4 non-Completed rows all have zero `order_total`).
**Excluded order count:** 4 (1 Refunded + 3 Cancelled), all zero-value.
**Exact exclusion reason:** `order_status <> 'Completed'` — standard approved filter, zero Sales impact.

Full transaction-level detail: `07_EVIDENCE\generated_data\2026-07-10_B0FX2QT3B1_LSCYRO300GD2PK_RPR44WH2PK_june_transactions.csv`.

## 17. Vendor Data for This ASIN

**Query result: 0 rows in `public.vendor_sales` for `asin='B0FX2QT3B1'`, for any period, ever.**

| Period | Vendor Sales (ASIN-level) | Vendor Units | Row count |
|---|---|---|---|
| June 2025 | £0.00 | 0 | 0 |
| June 2026 | £0.00 | 0 | 0 |

Marked `VENDOR_ASIN_LEVEL_ONLY` per instruction. **No Vendor value was or could be allocated to the SKU `LSCYRO300GD2PK+RPR44WH2PK`** — Vendor has no data for this ASIN at all.

## 18. Workbook Reference for the Pair

**Source:** `02_SOURCE\user_provided\2026-07-10_utharsika_june_july_kpi_reference_b01.xlsx`, sheet `Utharsika` only.

**Found:** row 1306, `ASIN=B0FX2QT3B1`, `SKU=LSCYRO300GD2PK+RPR44WH2PK` (exact match, `Mapped SKU` blank), `Account=DCvoltage`.

| Metric | Workbook Value |
|---|---|
| June 2025 Sales | 0 |
| June 2025 Orders | 0 |
| June 2026 Sales | 0 |
| June 2026 Orders | 0 |

**Marked `STALE_OR_UNREFRESHED_WORKBOOK_VALUE`** — consistent with the whole-workbook zero-value finding from the prior investigation. **Note:** for June 2025 specifically, the workbook's `0` happens to be **factually correct** (no transactions existed yet). For June 2026, the workbook's `0` is **incorrect** relative to the database's real £699.76/21 orders — the workbook's staleness affects this period even though it coincidentally didn't affect June 2025 for this particular product.

## 19. Current HTML Verification for the Pair

Extracted the embedded product master, daily aggregates, Vendor periods, **and the embedded engine JavaScript itself** directly from `09_OUTPUTS\2026-07-10_utharsika_v001.html` and executed it in a sandboxed Node.js VM (same method as the prior full-total verification).

| Metric | June 2025 (HTML) | June 2026 (HTML) |
|---|---|---|
| FBM Sales | £0.00 | £699.76 |
| FBM Orders | 0 | 21 |
| FBA Sales | £0.00 | £0.00 |
| FBA Orders | 0 | 0 |
| Vendor Sales (ASIN-level) | £0.00 | £0.00 |
| Vendor Units | 0 | 0 |
| Total transactional Sales | £0.00 | £699.76 |
| Total transactional Orders | 0 | 21 |

**HTML matches PostgreSQL exactly, on every component, for both periods.** `SYSTEM_OUTPUT_RECONCILES_TO_DATABASE` confirmed at the individual-product level, not just in aggregate.

**Pair difference explanation:** No difference exists between the database and HTML for this pair — both agree exactly. The only "difference" present is between the (stale) workbook and reality, already explained in Section 18.

## WORK 2 CONCLUSION

**PASS.** Ownership confirmed, exact pair confirmed unique and correctly isolated (the second SKU `RPR44WH` is a separate, zero-value REPLACEMENT-source record, correctly excluded, not silently merged). June 2025 = £0.00 (factually correct, product didn't exist yet). June 2026 = £699.76/21 orders, confirmed identical in both PostgreSQL and the live HTML. Vendor confirmed absent for this ASIN, never allocated to the SKU.

---

## Cross-User and Integrity Checks

| Check | Result |
|---|---|
| Other-user-only ASINs included | **0** |
| Other-user Sales included | **£0.00** |
| Other-user Orders included | **0** |
| Vendor duplication | **0** |
| Duplicate ASIN–SKU rows | **0** |
| Database writes | **0** |
| HTML writes | **0** |

---

## Evidence Files

| File | Purpose |
|---|---|
| `07_EVIDENCE\2026-07-10_utharsika_JUNE_DIFFERENCE_AND_PRODUCT_PAIR_VERIFICATION.md` | This file |
| `07_EVIDENCE\generated_data\2026-07-10_utharsika_june_difference_rows.csv` | WORK 1 excluded-row breakdown by dimension |
| `07_EVIDENCE\generated_data\2026-07-10_utharsika_june_candidate_calculations.csv` | WORK 1 candidate variants A–J |
| `07_EVIDENCE\generated_data\2026-07-10_B0FX2QT3B1_LSCYRO300GD2PK_RPR44WH2PK_june_transactions.csv` | WORK 2 full transaction-level detail (40 rows) |

**No `exact_difference_rows.csv` was created** — no exact-matching row set was found for the £936.12/556-order gap; creating this file would misrepresent an unresolved finding as resolved.

No credentials, connection strings, or unrelated customer data appear in any file above (order IDs and internal item IDs only — no customer name, address, or contact detail was queried or stored).
