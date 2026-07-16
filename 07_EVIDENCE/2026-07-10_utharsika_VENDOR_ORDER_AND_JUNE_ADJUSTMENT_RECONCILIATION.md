# UAWSO — Vendor Order Count and June Adjustment Reconciliation

**What this asset is:** Two read-only investigations — (1) whether a true Vendor order count exists anywhere in the database, and (2) whether tax, shipping, returns, replacements, or shipments explain the remaining £936.12 Sales / 556 Orders gap between the user's June 2025 reference figures and the current UAWSO result.

**Owner:** Satheskanth
**Current status:** WORK 1 — no valid Vendor order key exists in the database (reported honestly, not guessed). WORK 2 — tax and shipping are not testable at all (schema has no such columns); returns/replacements/shipments were re-verified and do not explain the gap.
**Related evidence:** `07_EVIDENCE\2026-07-10_utharsika_JUNE_DIFFERENCE_AND_PRODUCT_PAIR_VERIFICATION.md` (prior investigation — this file extends it with Vendor-order and adjustment-specific testing, and does not reuse or assume any of its numeric conclusions without re-verifying them here).

---

## Common Scope

| Check | Result |
|---|---|
| Resolved user | `utharsika` |
| Distinct assigned ASINs (freshly re-verified this session) | **1,723** |
| Raw vs distinct assignment-row count | 1,723 = 1,723 (no duplication) |

---

# WORK 1 — True Vendor Order Count

## 1. Vendor-Related Database Objects (full database-wide search)

Searched `information_schema.tables` across **every schema** in the database for names matching `vendor`, `vendor_order`, `purchase_order`, `po`, `shipment`, `invoice`, `vendor_transaction`, `vendor_report`. Candidate objects found and individually inspected:

| Schema | Table/View | Relevant columns | Date col | ASIN col | Order-ID col | Order-line col | Qty col | Revenue col | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| `public` | `vendor_sales` | id, start_time, end_time, asin, ordered_units, ordered_revenue, currency_code, category_id/name, user_id/name | start_time/end_time (period) | asin | **none** | **none** | ordered_units | ordered_revenue | Only real Vendor data source; no order key |
| `supplier` | `invoices` | id, final_container_id, hs_code_name, units, unit_price, fob, invoice_date, ship_by_date, created | invoice_date | **none** | none | none | units | fob/unit_price | Wrong business domain — factory/container sourcing invoices, not Amazon Vendor Central sales |
| `supplier` | `invoice_shipping_cost` | id, final_container_id, shipping_cost | none | none | none | none | none | shipping_cost | Wrong business domain — container freight cost |
| `blos` | `vw_amazon_uk_daily_payout_components` | expense_date, account_name, expense_category_code/name, expense_subcategory, net_amount, tax_amount, gross_amount, record_count, reporting_basis | expense_date | **none** | none | none | none | net/tax/gross_amount | No ASIN column at all; data starts 2025-11-09 (no June 2025 coverage) |
| `blos` | `local_postage`, `international_postage` (+ `_history`) | carrier_name, service_name, price/postage_value, vat_rate_percentage, effective_date, market_code, weight | effective_date | none | none | none | none | price (rate card) | Carrier **rate cards** for cost lookup, not per-order transactions — no order ID, no ASIN, no actual charged amount |
| `message_submission` | various (`admin__a_invoice_vat`, `delivery_master_rules_final__c_20_shipment_cancelled`, etc.) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | Customer-service **message templates** (canned responses), not transactional data |

No comments were found on `public.vendor_sales` or `supplier.invoices` via `obj_description()` (both `NULL`).

**No table or view anywhere in the database contains an actual Vendor order ID, purchase order number, invoice reference, or shipment/order reference tied to an ASIN.**

## 2. Vendor Order Key Test

| Candidate key | Source | Null count | Distinct count | Duplicate count | Business meaning | Suitable for order count |
|---|---|---|---|---|---|---|
| `vendor_sales.id` | `public.vendor_sales` | 0 | 960 (all Utharsika-linked rows) | 0 | Surrogate row ID for one ASIN-period aggregate record | **NO** |
| `vendor_sales.asin + start_time + end_time` | `public.vendor_sales` | 0 | 960 | 0 | Identifies one ASIN-period aggregate; many real orders are summed into each row | **NO** |
| Order ID / PO number / invoice reference | `public.vendor_sales` | N/A | N/A | N/A | Column does not exist in this table | **NO — COLUMN DOES NOT EXIST** |

Full detail: `07_EVIDENCE\generated_data\2026-07-10_utharsika_vendor_order_candidates.csv`.

**No candidate key qualifies as a Vendor order.** `ordered_units` was explicitly not used as Orders, per instruction.

## 3. Vendor Orders Calculation

**Result: `VENDOR_ORDER_COUNT_NOT_AVAILABLE_FROM_CURRENT_DATABASE`**

**Exact missing source required:** an Amazon Vendor Central "Purchase Orders" table/report containing a genuine PO-number or vendor-order-ID column at the ASIN/order-line grain. No such table exists anywhere in this database. `public.vendor_sales` is a period-aggregate revenue/units summary only.

What **can** be reported (Sales and Units, not Orders — never combined):

| Period | Vendor row count (period-aggregate records) | Distinct ASINs | Vendor Units | Vendor Sales |
|---|---|---|---|---|
| June 2025 | 13 | 13 | **528** | **£4,302.96** |
| June 2026 | 37 | 33 | **41** | **£571.42** |

Both figures re-verified two independent ways this session: (a) direct SQL against the live database with corrected period-overlap boundary logic, and (b) execution of the HTML's own embedded `sumVendorRange` engine function against its embedded data — both methods agree exactly for June 2025 (£4,302.96/528 units/13 rows), confirming the deployed system's Vendor figure is correct and current.

**Note on a self-caught query error:** An initial SQL attempt at the period-overlap join used an inclusive timestamp boundary (`start_time <= end_date + 1 day`) that incorrectly included the *adjacent* July-2025 monthly period alongside the June period for several ASINs, inflating the apparent total to £8,871.77/1,099 units/31 rows. This was identified as a boundary bug (not a real second data source) by cross-checking against the deployed engine's own `periodsOverlap` logic and re-running with a corrected half-open boundary (`NOT (end_time::date < start OR start_time::date > end)`), which reproduced the confirmed £4,302.96 figure exactly. This is documented for transparency; **the corrected, confirmed figure is £4,302.96, not £8,871.77.**

---

# WORK 2 — Tax, Shipping, Returns, Replacements, Shipments

## 4. Monetary Column Inspection

`public.order_transaction` full column list (21 columns, all confirmed via `information_schema.columns`):

`order_item_info, order_id, item_id, asin, product_id, sku, item_price, quantity, order_status, order_date, order_total, order_sub_source, ss_name, source, source_name, market_place, fba_sales, category_id, category_name, user_id, user_name`

**There is no tax, VAT, shipping, postage, shipping-tax, promotion, discount, refund-amount, return-amount, replacement-amount, fee, charge, gross-amount, or net-amount column of any kind.** `order_total` and `item_price` are the only two monetary fields, and neither is documented or structurally decomposable into sub-components — both are single flat totals per order line.

## 5. Tax Effect

| Calculation | Sales | Diff from target | Tax amount included | Supported by schema |
|---|---|---|---|---|
| Sales excluding tax | — | — | — | **NO** |
| Tax amount | — | — | — | **NO — no tax column exists** |
| Sales including tax | — | — | — | **NO** |
| VAT-inclusive total | — | — | — | **NO** |

**The £936.12 difference cannot be tested as a tax effect — the schema provides no basis to test it, exactly or partially.** `order_total` cannot be proven to be gross or net of tax from the schema alone; no adjacent table provides a per-order/per-ASIN tax breakdown for June 2025 (`blos.vw_amazon_uk_daily_payout_components` has tax_amount but no ASIN column and no data before 2025-11-09).

## 6. Shipping/Postage Effect

| Calculation | Value | Diff from target | Supported by schema |
|---|---|---|---|
| Product Sales only | £41,146.84 (= current UAWSO Sales) | -£936.12 | current baseline |
| Shipping/postage amount | — | — | **NO — no shipping revenue column exists** |
| Shipping tax | — | — | **NO** |
| Product Sales + shipping | — | — | **NO** |
| Product Sales + shipping + tax | — | — | **NO** |

`blos.local_postage` / `blos.international_postage` were inspected in full: both are **carrier rate-card configuration tables** (service name, price-per-weight-band, VAT rate, effective date) used for cost estimation — they contain no order ID, no ASIN, and no actual per-order charged amount, so they cannot be used to calculate real shipping revenue collected on any specific order.

**The £936.12 difference cannot be tested as a shipping/postage effect for the same reason — no shipping revenue field exists anywhere in the order-level data.**

## 7. Return/Refund Effect (re-verified)

| Status | Row count | Distinct order-item | Positive Sales | Negative Sales |
|---|---|---|---|---|
| Completed | 1,856 | 1,856 | £36,843.88 | £0.00 |
| Cancelled | 49 | 49 | £195.20 | £0.00 |
| Refunded | 35 | 35 | £40.98 | £0.00 |
| Canceled (single-L) | 7 | 7 | £0.00 | £0.00 |

No negative `order_total` rows exist anywhere in this scope — refunds/cancellations are represented by status changes on otherwise-positive rows, not by negative adjustment entries.

- **Gross Sales before returns** (all statuses) = £37,080.06 (FBM/FBA) + £4,302.96 Vendor = **£41,383.02** — still £699.94 short of target.
- **Net Sales after returns** (current, Completed only) = £41,146.84 — the current UAWSO figure.
- **Exact amount explained by gross-vs-net:** £236.18 (Cancelled £195.20 + Refunded £40.98 + Canceled £0.00) — **does not reach £936.12.**

The user figure is **not** exactly "gross Sales" nor exactly "net Sales" under any tested definition — both fall short of or diverge from £42,082.96.

## 8. Replacement Effect (re-verified from database)

| Metric | Re-verified value | Reference value from task |
|---|---|---|
| Replacement row count | **8** | 8 ✅ matches |
| Distinct replacement orders | **8** | — |
| Replacement Sales | **£0.00** | £0.00 ✅ matches |
| Replacement quantity | **9** | — |

All 8 rows carry `order_id` prefixed `Repla-…`, `source_name='REPLACEMENT'`, `order_status='Completed'`, `order_total=0.00`. These are **not counted as Orders** in the current UAWSO figure (excluded by `source_name='AMAZON'` filter). Including them would add **+8 Orders, +£0.00 Sales** — this does not materially affect the 556-order difference (8 is far short of 556, and even combined with every other tested exclusion category, no combination reaches 556 or 28).

## 9. Shipment Effect

No shipment ID, tracking reference, dispatched-status, or shipment-charge field exists anywhere in `order_transaction` or in any other table in the database (confirmed by the same database-wide object search as Section 1 — no shipment-transaction table for Amazon orders exists; only unrelated supplier-container shipment tables were found).

| Metric | Value |
|---|---|
| Distinct order IDs (Completed, Jun 2025) | 1,783 |
| Distinct shipment IDs | **NOT AVAILABLE — no such column/table exists** |
| Distinct order items | 1,856 |
| Shipped quantity (proxy = `SUM(quantity)`) | 2,325 |
| Shipment rows | **NOT AVAILABLE** |

**The user's 2,412 figure cannot be tested as a shipment count — no shipment-level data exists in this database to test against.**

## 10. Metric Comparison Matrix

Full detail: `07_EVIDENCE\generated_data\2026-07-10_utharsika_june_tax_shipping_return_replacement_matrix.csv`.

**Sales variants (A–H):**

| Variant | Value | Diff from £42,082.96 |
|---|---|---|
| A. Current UAWSO Sales | £41,146.84 | -£936.12 |
| B. Sales + tax | NOT_SUPPORTED_BY_SCHEMA | — |
| C. Sales + shipping | NOT_SUPPORTED_BY_SCHEMA | — |
| D. Sales + shipping + tax | NOT_SUPPORTED_BY_SCHEMA | — |
| E. Gross Sales before refunds | £41,383.02 | -£699.94 |
| F. Sales including refunded rows only | £41,187.82 | -£895.14 |
| G. Sales including replacements | £41,146.84 | -£936.12 (unchanged) |
| H. Vendor Sales included / excluded | £41,146.84 / £36,843.88 | -£936.12 / -£5,239.08 |

**Orders variants (A–J):**

| Variant | Value | Diff from 2,412 |
|---|---|---|
| A. Distinct order IDs | 1,783 | -629 |
| B. Distinct order-item IDs (current) | 1,856 | -556 |
| C. Distinct shipment IDs | NOT_AVAILABLE | — |
| D. Row count | 1,856 | -556 |
| E. Sum quantity | 2,325 | -87 |
| F. True Vendor Orders | VENDOR_ORDER_COUNT_NOT_AVAILABLE_FROM_CURRENT_DATABASE | — |
| G. FBM/FBA Orders + true Vendor Orders | NOT_COMPUTABLE | — |
| H. FBM/FBA Orders + Vendor row count (disclaimed, not a true order count) | 1,869 | -543 |
| I. FBM/FBA Orders + replacements | 1,864 | -548 |
| J. FBM/FBA Orders + shipment count | NOT_AVAILABLE | — |

## 11. Exact Difference Search

Tested business dimensions, in priority order: tax (unsupported), shipping/postage (unsupported), returns/refunds (£236.18 max, insufficient), replacements (£0.00 Sales / +8 Orders, insufficient), shipments (unsupported), true Vendor Orders (unavailable), status scope (already covered under returns), marketplace scope and source scope (both already ruled out in the prior investigation and not re-litigated here since no new evidence emerged to revisit them).

**No evidence-backed combination of tax, shipping, returns, replacements, or shipments explains £936.12 Sales or 556 Orders.** Two of the five requested dimensions (tax, shipping) are **not testable at all** due to a genuine schema gap — this is a definitive finding, not an inconclusive one: those columns simply do not exist. The remaining three testable dimensions (returns, replacements, shipments-as-quantity) collectively explain at most £236.18 of the £936.12 Sales gap and at most 8 of the 556 Orders gap.

---

# Exact ASIN–SKU Pair Check (re-run with adjustment dimensions)

**ASIN:** `B0FX2QT3B1` **SKU:** `LSCYRO300GD2PK+RPR44WH2PK`

Full detail: `07_EVIDENCE\generated_data\2026-07-10_B0FX2QT3B1_LSCYRO300GD2PK_RPR44WH2PK_adjustment_check.csv`.

| Metric | June 2025 | June 2026 |
|---|---|---|
| FBM Sales | £0.00 | £699.76 |
| FBM Orders | 0 | 21 |
| FBA Sales | £0.00 | £0.00 |
| FBA Orders | 0 | 0 |
| Tax amount | NOT_SUPPORTED_BY_SCHEMA | NOT_SUPPORTED_BY_SCHEMA |
| Shipping amount | NOT_SUPPORTED_BY_SCHEMA | NOT_SUPPORTED_BY_SCHEMA |
| Refund/return amount | £0.00 (no rows exist) | £0.00 (4 non-Completed rows, all zero-value) |
| Replacement rows (this exact SKU) | 0 | 0 |
| Shipment count | NOT_AVAILABLE | NOT_AVAILABLE |
| True Vendor Orders (ASIN level) | VENDOR_ORDER_COUNT_NOT_AVAILABLE_FROM_CURRENT_DATABASE | VENDOR_ORDER_COUNT_NOT_AVAILABLE_FROM_CURRENT_DATABASE |
| Vendor Sales (ASIN level) | £0.00 | £0.00 |
| Vendor Units (ASIN level) | 0 | 0 |

No Vendor value was allocated to the SKU (Vendor has zero rows for this ASIN, ever). The separate SKU `RPR44WH` under the same ASIN has one REPLACEMENT-source, zero-value row on 2026-06-13 — correctly excluded from this exact-pair check, as it belongs to a different SKU string.

---

## Stop Conditions Check

| Condition | Triggered? |
|---|---|
| No valid Vendor order key found | **YES** — reported as `VENDOR_ORDER_COUNT_NOT_AVAILABLE_FROM_CURRENT_DATABASE`, not guessed |
| A metric definition had to be guessed | NO — every unsupported metric was left as `NOT_SUPPORTED_BY_SCHEMA` / `NOT_AVAILABLE` rather than estimated |
| Another user's ASINs would be included | NO |
| Database changes required | NO |
| Tax/shipping/refund logic could not be proven from schema | **YES for tax and shipping** (no columns exist); refund logic **was** provable from schema (status + order_total) |

Per instruction, `ordered_units` was never substituted for Vendor Orders, and Vendor Units/row counts were never presented as a valid Orders definition without an explicit disclaimer.

---

## Evidence Files

| File | Purpose |
|---|---|
| `07_EVIDENCE\2026-07-10_utharsika_VENDOR_ORDER_AND_JUNE_ADJUSTMENT_RECONCILIATION.md` | This file |
| `07_EVIDENCE\generated_data\2026-07-10_utharsika_vendor_order_candidates.csv` | Candidate Vendor order keys tested, all database objects inspected |
| `07_EVIDENCE\generated_data\2026-07-10_utharsika_june_tax_shipping_return_replacement_matrix.csv` | Sales A–H / Orders A–J full matrix |
| `07_EVIDENCE\generated_data\2026-07-10_B0FX2QT3B1_LSCYRO300GD2PK_RPR44WH2PK_adjustment_check.csv` | Exact-pair adjustment dimension check, both years |

No credentials, connection strings, or unrelated users' data appear in any file above. No database, workbook, HTML, `ph_task`, or scheduler modification occurred.
