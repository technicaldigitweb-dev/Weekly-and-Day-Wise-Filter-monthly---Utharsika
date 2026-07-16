# public.order_transaction — Full Status Discovery

**What this asset is:** A pure, read-only discovery of every distinct `order_status` value stored in `public.order_transaction`, across the whole table (all users, all sources, all time), plus a June 2025 / June 2026-specific breakdown. **No business-rule decision is made in this document** — this is discovery only, ahead of checking these statuses against user-provided KPI data in a later task.

**Owner:** Satheskanth
**Scope:** Full table, all users/sources — not restricted to Utharsika's assigned ASINs (this task did not request that scope).
**Status:** Discovery complete.

---

## Method

Direct read-only PostgreSQL queries (`GROUP BY order_status`, and a separate `LOWER(TRIM(...))` normalization pass to detect case/spelling variants). No rows were modified. Full detail: `07_EVIDENCE\generated_data\2026-07-14_order_transaction_status_summary.csv`.

## 1. Full Status Discovery (all time, all users)

**9 distinct exact status values found.** No `NULL` status rows (0). No blank (`''`) status rows (0).

| Exact status | Normalized | Row count | Distinct order_item_info | Distinct order_id | Total quantity | Sum(item_price×qty) | Sum(order_total) | Earliest order_date | Latest order_date | Distinct source_names | Distinct fba_sales | Distinct ss_name count |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Completed | completed | 1,198,909 | 1,198,909 | 1,097,679 | 1,945,069 | £25,172,631.08 | £24,992,022.48 | *see note* | 2026-07-13 14:36:22 | AMAZON, AVASAM, B&Q, BOL, EBAY, ETSY, FAIRE, MANOMANO, MANUAL OM, MANUALORDER, ONBUY, REPLACEMENT, RESEND, SHOPIFY, WAYFAIR | false, true | 132 |
| Refunded | refunded | 20,108 | 20,108 | 17,555 | 36,770 | £557,308.41 | £147,472.02 | 2020-09-10 14:56:56 | 2026-07-11 22:42:36 | AMAZON, AVASAM, B&Q, EBAY, ETSY, MANUAL OM, MANUALORDER, ONBUY, REPLACEMENT, RESEND, SHOPIFY, WAYFAIR | false | 47 |
| Cancelled | cancelled | 10,632 | 10,632 | 10,024 | 5,452 | £101,849.51 | £104,003.66 | *see note* | 2026-07-13 20:05:41 | AMAZON, AVASAM, B&Q, BOL, EBAY, ETSY, FAIRE, MANUAL OM, MANUALORDER, ONBUY, REPLACEMENT, RESEND, SHOPIFY, WAYFAIR | false | 59 |
| Deleted | deleted | 1,615 | 1,615 | 1,117 | 3,843 | £41,341.57 | £41,160.65 | 2022-05-16 00:00:00 | 2026-06-21 15:58:53 | AMAZON, B&Q, BOL, EBAY, ETSY, FAIRE, MANOMANO, MANUAL OM, MANUALORDER, REPLACEMENT, RESEND, SHOPIFY, WAYFAIR | false | 64 |
| Canceled (single-L) | canceled | 1,395 | 1,395 | 1,385 | 270 | £88.47 | £67.58 | 2024-01-04 21:05:09 | 2026-07-11 13:09:57 | AMAZON only | true | 2 |
| New | new | 416 | 416 | 363 | 692 | £10,010.35 | £10,771.30 | 2026-02-04 16:51:58 | 2026-07-14 01:06:41 | AMAZON, B&Q, EBAY, REPLACEMENT, SHOPIFY | false | 24 |
| Pending | pending | 58 | 58 | 50 | 83 | £898.49 | £942.41 | 2024-03-11 21:43:50 | 2026-07-12 21:29:28 | AMAZON, MANUAL OM | false, true | 3 |
| Inprogress | inprogress | 9 | 9 | 8 | 10 | £400.72 | £446.00 | 2026-07-12 18:26:39 | 2026-07-13 01:11:16 | AMAZON, EBAY, SHOPIFY | false | 4 |
| Hold | hold | 3 | 3 | 2 | 7 | £145.03 | £160.01 | 2026-07-13 10:22:36 | 2026-07-13 10:35:42 | AMAZON only | false | 1 |

**Data-quality note:** the raw `earliest_order_date` for `Completed` and `Cancelled` returned an apparent 2-digit-year anomaly (year `0025` instead of `2025`) on at least one row each — this is flagged here as a discovery observation only; no row was excluded, corrected, or otherwise filtered as part of this task, and no business-rule decision was made about it.

**Distinct order_item_info always equals row count for every status** — confirming `order_item_info` is a unique per-row key (no duplicate rows) across the entire table, for every status.

**"New", "Pending", "Inprogress", and "Hold"** are four statuses beyond the previously-catalogued set (Completed, Refunded, Cancelled, Canceled, Deleted). `Inprogress` and `Hold` had not been observed in any prior investigation in this project — both are very recent (all rows dated 2026-07-12/13) and very small in volume (9 and 3 rows respectively, database-wide).

## 2. Case/Spelling Variant Check

Every normalized status maps to **exactly one** exact-string variant — **no case-duplicate or spelling-variant statuses were found** (e.g., no `"completed"` lowercase coexisting with `"Completed"`). `Cancelled` (double-L) and `Canceled` (single-L) are confirmed as two genuinely distinct stored strings, not a case variant of each other (they normalize to different values: `cancelled` vs `canceled`).

## 3. June 2025 Breakdown (2025-06-01 to 2025-06-30, all users)

| Status | Row count | Distinct order items | Quantity | Original Sales (item_price×qty) | order_total | Source names |
|---|---|---|---|---|---|---|
| Completed | 18,174 | 18,174 | 29,130 | £368,856.84 | £386,804.07 | AMAZON, B&Q, EBAY, FAIRE, MANUAL OM, ONBUY, REPLACEMENT, RESEND, SHOPIFY, WAYFAIR |
| Refunded | 397 | 397 | 736 | £12,814.61 | £3,778.93 | AMAZON, EBAY, SHOPIFY |
| Cancelled | 303 | 303 | 139 | £1,543.55 | £1,675.38 | AMAZON, EBAY, REPLACEMENT, SHOPIFY, WAYFAIR |
| Canceled | 43 | 43 | 0 | £0.00 | £0.00 | AMAZON |
| Deleted | 5 | 5 | 18 | £0.00 | £0.00 | REPLACEMENT, RESEND |

No `New`, `Pending`, `Inprogress`, or `Hold` rows fall within June 2025 (consistent with their very recent `earliest_order_date` values, all in 2024 or later, mostly 2026).

**Source breakdown within status:** see the CSV for the full per-source detail. Notably, `Completed`/AMAZON in June 2025 = 8,069 rows / £176,574.75 (this is the whole-table AMAZON figure, not restricted to Utharsika's assigned ASINs — it will not match Utharsika-scoped figures from prior evidence).

## 4. June 2026 Breakdown (2026-06-01 to 2026-06-30, all users)

| Status | Row count | Distinct order items | Quantity | Original Sales (item_price×qty) | order_total | Source names |
|---|---|---|---|---|---|---|
| Completed | 18,983 | 18,983 | 30,781 | £424,069.77 | £463,471.48 | AMAZON, B&Q, EBAY, MANUAL OM, ONBUY, REPLACEMENT, RESEND, SHOPIFY, WAYFAIR |
| Refunded | 367 | 367 | 627 | £9,381.65 | £2,170.64 | AMAZON, B&Q, EBAY, MANUAL OM, SHOPIFY |
| Cancelled | 342 | 342 | 126 | £1,928.75 | £2,206.95 | AMAZON, B&Q, EBAY, RESEND, SHOPIFY, WAYFAIR |
| Canceled | 68 | 68 | 25 | £67.58 | £67.58 | AMAZON |
| Deleted | 4 | 4 | 6 | £0.00 | £0.00 | REPLACEMENT |
| Pending | 2 | 2 | 3 | £0.00 | £15.29 | AMAZON |
| New | 2 | 2 | 3 | £0.00 | £0.00 | REPLACEMENT |

No `Inprogress` or `Hold` rows fall within June 2026 (both statuses only appear on 2026-07-12/13 dates, entirely outside this window).

**Source breakdown within status:** see the CSV for full detail.

## Evidence Outputs

| File | Purpose |
|---|---|
| `07_EVIDENCE\2026-07-14_utharsika_ORDER_TRANSACTION_STATUS_DISCOVERY.md` | This file |
| `07_EVIDENCE\generated_data\2026-07-14_order_transaction_status_summary.csv` | Full status discovery + June 2025/2026 breakdowns + per-source detail |

## Scope and Limitations

- This discovery is **whole-table, all-users** — it is intentionally not restricted to Utharsika's assigned ASINs, per the task's plain wording. Figures here will not match any Utharsika-scoped total from prior evidence in this project.
- **No decision was made** about which statuses should count toward Sales, Orders, or any KPI. `New`, `Pending`, `Inprogress`, and `Hold` are reported purely as discovered facts (row counts, values, dates) for a later task to evaluate against user-provided KPI data.
- The apparent 2-digit-year anomaly on at least one `Completed` and one `Cancelled` row's `order_date` is noted but not investigated further here (out of scope for a pure status discovery).

## Final Verdict: **PASS** (discovery complete, no PostgreSQL/HTML/template/ph_task/prior-evidence modification occurred)
