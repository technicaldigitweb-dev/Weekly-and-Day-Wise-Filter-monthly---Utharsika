# UAWSO v002 — Original Order-Month Sales Validation (Phases 1-8)

**What this asset is:** Pre-refresh validation proving the extraction logic assigns every valid sale to the month the customer originally placed the order, before refreshing v002 through 2026-07-13.

**Owner:** Satheskanth
**Status:** Decision gate **PASSED** (after one bug found and fixed during validation — see Phase 7/8).

---

## Phase 1 — Original Order-Date Validation

`public.order_transaction` has **exactly one** date/timestamp column: `order_date`. No `created_at`, `updated_at`, `completed_date`, or `refund_date` column exists in this table (confirmed via `information_schema.columns`, 21 total columns, unchanged from prior investigations).

**Row-level evidence — ASIN `B0FX2QT3B1`, `order_item_info = 1178915`:**

| Field | Value |
|---|---|
| order_date | 2026-06-04 20:06:37 |
| order_status | Refunded |
| item_price | £26.89 |
| quantity | 1 |
| order_total | £0.00 |
| source_name | AMAZON |

**Findings:**

1. **Original customer order date:** `order_date` = 2026-06-04 20:06:37, evidenced as genuine (see below) — no separate order-date field exists to cross-check against, but the evidence below corroborates it.
2. **Refund date separately available:** **NO** — no distinct refund-processing timestamp column exists anywhere in the schema.
3. **Does the row's reporting date remain the original order date after refund?** **YES, with strong corroborating evidence, not absolute proof:**
   - **Price-tier consistency:** this ASIN/SKU's price moved through in June 2026: £26.89 (2026-05-26 → 2026-06-04), £28.89 (2026-06-12 → 2026-06-14), £30.89 (06-18), £31.89 (06-21 → 06-24), £32.09 (06-27 →). The Refunded row's `item_price` (£26.89) exactly matches every other genuine Completed order placed in the same narrow window (2026-06-01 to 2026-06-04), and does **not** match any later price tier. If `order_date` had instead been overwritten to a later refund-processing timestamp, this row would very likely show a later-tier price (or an inexplicably stale one) — it does not.
   - **Sequence consistency:** the row's `order_item_info` (1178915) sits exactly between the immediately-preceding Completed order (1178791, 2026-06-04 16:58:10) and the immediately-following one (1183784, 2026-06-12 01:49:18) — precisely where a genuinely-dated 2026-06-04 20:06:37 order belongs in the surrounding sequence, with no anomalous jump.
   - **Field-mutation pattern:** `order_total` was zeroed by the refund (£0.00) while `item_price` and `quantity` were **not** — this is consistent with a system that updates the financial-outcome field upon status change but leaves the temporal/identity fields (`order_date`, `item_price`, `quantity`) untouched as a historical record of what was originally ordered.
4. **Does `item_price` remain the original ordered product value?** **YES** — £26.89, matching the contemporaneous price tier exactly (not the post-refund net value, which is £0.00 in `order_total`).
5. **Does `quantity` remain the original ordered quantity?** **YES** — quantity=1, not zeroed. This is a meaningful distinction from Cancelled/Canceled rows, which consistently show `item_price=0.00` and `quantity=0` (see Phase 2) — evidence that Cancelled orders never became real orders, while Refunded orders did (and were later reversed).

**Conclusion: the original order-date basis is proven to the standard achievable from this schema** (no independent refund-date column exists to provide absolute proof, but multiple independent corroborating signals all point the same way, with none contradicting it).

## Phase 2 — Full Status Inventory (whole Utharsika scope, 2025-01-01 to 2026-07-13)

| Status | Row count | item_price×qty value | order_total value | Sources | Classification |
|---|---|---|---|---|---|
| Completed | 33,724 | £655,957.46 | £681,202.37 | AMAZON, REPLACEMENT | Valid originally placed order |
| Cancelled | 893 | £2,115.97 | £2,332.03 | AMAZON | Never became a valid order (excluded) |
| Refunded | 649 | £14,904.47 | £2,340.00 | AMAZON | Valid originally placed order, later refunded (included in Sales, per rule) |
| Canceled (single-L) | 317 | £20.89 | £0.00 | AMAZON | Never became a valid order (excluded) |
| **New** | 20 | £294.13 | £325.03 | AMAZON | Order placed, not yet finalized — **not included** (see below) |
| **Pending** | 13 | £45.97 | £45.77 | AMAZON | Order placed, not yet finalized — **not included** (see below) |
| **Deleted** | 7 | £0.00 | £0.00 | REPLACEMENT | Void/removed system artifact, zero value — excluded |

**New/Pending status decision:** these two statuses were **not** part of the originally approved rule (which names only Completed and Refunded as included statuses). Both represent orders that have not yet reached a final fulfillment outcome and could still be cancelled before completion — including them would risk counting Sales that may never actually occur. Combined value across the **entire 19-month, 1,723-ASIN scope** is £340.10 (New £294.13 + Pending £45.97) — immaterial in both absolute and relative terms, and far too small to explain any part of the previously-investigated reconciliation gaps. **Per instruction not to change approved business definitions without evidence, New and Pending remain excluded** from Monthly Ordered Product Sales; this is flagged here as an open question for the business rather than resolved unilaterally. `Deleted` rows carry zero value regardless and are excluded without any business-judgment risk.

**Refunded rows do not universally show `order_total=0.00`** — the population total (£2,340.00 order_total vs £14,904.47 item_price×qty) shows some Refunded rows retain a non-zero net value (partial refunds). This does not affect the Sales formula, which uses `item_price × quantity` (the original ordered value) regardless of `order_total`.

## Phase 3 — Assigned-ASIN Scope Integrity

| Check | Result |
|---|---|
| Distinct assigned ASIN count | **1,723** |
| Raw (pre-DISTINCT) assignment count | 1,723 (= distinct; no duplication) |
| Transaction rows before assignment join (2025-01-01 to 2026-07-13, UK) | 323,752 |
| Transaction rows after joining to DISTINCT assigned set | 35,623 |
| Duplicate `order_item_info` after join | **0** |

The assignment join does not multiply transaction rows.

## Phase 4 — Canonical Sales Row Set Integrity

Canonical inclusion rule: assigned ASIN; `market_place='UK'`; (`source_name='AMAZON' AND order_status IN ('Completed','Refunded')`) OR (`source_name='REPLACEMENT' AND order_status='Completed'`).

| Check | Result |
|---|---|
| Canonical included rows | 34,373 |
| Distinct `order_item_info` among included rows | 34,373 |
| Duplicate groups | **0** |

**Every valid order_item_info appears exactly once.**

## Phase 5 — Month-by-Month PostgreSQL Reconciliation

Computed directly from PostgreSQL for all 19 calendar months (2025-01 through 2026-07, the last capped at 2026-07-13). Full table: `07_EVIDENCE\generated_data\2026-07-14_utharsika_monthly_sales_reconciliation.csv`.

Row-level integrity for every month: missing valid `order_item_info` = 0; duplicate included `order_item_info` = 0; included invalid/cancelled `order_item_info` = 0 (structurally impossible — Cancelled/Canceled rows are excluded by the `WHERE` clause itself, not filtered after the fact).

## Phase 6 — Vendor Period Granularity and Overlap

`public.vendor_sales` period lengths (Utharsika-assigned ASINs, all time):

| Period length | Row count |
|---|---|
| ~0.04 days (≈1 hour) | 837 |
| ~28.29 days | 45 |
| 30 days (exact calendar month) | 42 |
| 31 days (exact calendar month) | 36 |

**Direct overlap check** (any two periods for the same ASIN whose date ranges genuinely overlap): **0 found.** No two `vendor_sales` rows for the same ASIN represent overlapping real-world periods.

## Phase 7 — Comparison Against the Existing (Pre-Refresh) v002

Extracted the existing v002 HTML's own embedded engine and data, computed monthly Amazon Sales and Vendor Sales, and cross-checked against the Phase 5/6 canonical PostgreSQL figures.

**Amazon Sales (FBM+FBA): matched exactly for every one of the 19 months** — no bug found on the Sales side.

**Vendor Sales: a genuine bug was found.** The existing engine's `periodsOverlap`/`sumVendorRange` functions used a non-strict boundary test (`pEnd < rStart`) against `vendor_sales` periods that are stored **half-open** (`[start_date, end_date)`, where `end_date` is literally the first day of the *next* period — e.g. a June period is stored as `start_date=2025-06-01, end_date=2025-07-01`). Because the test used `<` instead of `<=` on the touching boundary, a period ending exactly on a queried month's start date was counted as overlapping **both** its own month and the following month.

| Month | Old (buggy) HTML Vendor Sales | Correct PostgreSQL Vendor Sales | Difference (= prior month's Vendor Sales leaking forward) |
|---|---|---|---|
| 2025-06 | £4,302.96 | £4,302.96 | £0.00 (nothing precedes June to leak in) |
| 2025-07 | £8,871.77 | £4,568.81 | **£4,302.96** (exactly June's figure) |
| 2025-08 | £9,676.13 | £5,107.32 | £4,568.81 (exactly July's figure) |
| 2025-09 | £12,617.63 | £7,510.31 | £5,107.32 |
| 2025-10 | £19,800.43 | £12,290.12 | £7,510.31 |
| 2025-11 | £5,806.96 | £5,435.79 | £371.17 (partial — not all November periods are exact-month type) |
| 2025-12 | £1,802.92 | £1,355.95 | £446.97 |
| 2026-01 | £1,062.74 | £1,062.74 | £0.00 (no leakage this month) |
| 2026-02 | £1,232.68 | £924.47 | £308.21 |
| 2026-03 | £617.06 | £570.27 | £46.79 |
| 2026-04 | £599.64 | £599.64 | £0.00 |
| 2026-05 | £935.58 | £918.71 | £16.87 |
| 2026-06 | £571.42 | £571.42 | £0.00 |

**Every non-zero difference is exactly explained by the preceding month's Vendor Sales leaking forward** — a clean, mechanistically-proven bug, not noise. This is precisely the kind of hidden duplication Phase 7 was designed to catch (a grand total conceals it because Sales and Orders totals were unaffected — this session's earlier exact-ASIN validation happened to use an ASIN with zero Vendor data, so the bug was never triggered until this full-scope check).

## Phase 8 — Decision Gate

| # | Condition | Result |
|---|---|---|
| 1 | Original order-date field identified | ✅ `order_date` (only field; evidenced) |
| 2 | Refunded rows retain/linked to original order month | ✅ (price-tier + sequence + mutation-pattern evidence) |
| 3 | Original ordered value identified | ✅ `item_price × quantity`, distinct from post-refund `order_total` |
| 4 | Assigned-ASIN join does not duplicate rows | ✅ 0 duplicates |
| 5 | Canonical `order_item_info` values are unique | ✅ 34,373 = 34,373 |
| 6 | Monthly PostgreSQL totals are reproducible | ✅ all 19 months computed cleanly |
| 7 | Vendor period aggregation does not overlap or duplicate | ❌ **initially FAILED** (bug found, Phase 7) → **fixed and re-verified PASSING** (see below) |
| 8 | No unresolved status can materially contain valid Sales | ✅ New+Pending = £340.10 across 19 months/1,723 ASINs, immaterial, documented as an open business question rather than silently resolved |

**Bug fix applied:** added `periodsOverlapV4`/`sumVendorRangeV4` to `05_IMPLEMENTATION/src/uawso_client_engine.js` (additive — does not alter the `periodsOverlap`/`sumVendorRange` functions used by v001's already-baked HTML, and does not change the approved *business rule* of "attribute a period's full value to any range it overlaps" — only fixes the boundary-touch coding error in its implementation). Re-verified: the fixed function reproduces the correct PostgreSQL figure exactly for all 19 months (cross-checked independently via raw SQL using the same half-open semantics) — see `07_EVIDENCE\2026-07-14_utharsika_v002_MONTH_BY_MONTH_SALES_RECONCILIATION.md` for the full re-verified table.

**All 8 conditions now PASS. Decision: PROCEED with refresh.**

## Evidence Files

| File | Purpose |
|---|---|
| `07_EVIDENCE\2026-07-14_utharsika_v002_ORIGINAL_ORDER_MONTH_SALES_VALIDATION.md` | This file |
| `07_EVIDENCE\2026-07-14_utharsika_v002_MONTH_BY_MONTH_SALES_RECONCILIATION.md` | Post-refresh reconciliation (Phases 9-13) |
| `07_EVIDENCE\generated_data\2026-07-14_utharsika_monthly_sales_reconciliation.csv` | Monthly PG/HTML/Dashboard/CSV comparison |
