# UAWSO — Reconcile Amazon Business Report Screenshot for B0FX2QT3B1 (June 2026)

**What this asset is:** Reconciliation of a user-provided Amazon Seller Central "Business Reports — Detail page sales and traffic by child item" screenshot against the current PostgreSQL/HTML result for ASIN `B0FX2QT3B1`, June 2026.

**Owner:** Satheskanth
**Current status:** **PASS** — both the £26.89 Sales difference and the 1 order-item difference are explained by two specific, identifiable, evidence-backed rows.

---

## 1. Screenshot Evidence

| Field | Value |
|---|---|
| Path | `02_SOURCE\user_provided\screenshots\2026-07-10_B0FX2QT3B1_june-2026_business-report_b01.png` |
| SHA-256 | `97d0d9916bfb1123a2891798a90546319903c4bdb8600a80903f1ca2b6393d43` |
| ASIN | B0FX2QT3B1 |
| Date range (shown) | 01/06/2026 – 30/06/2026 |
| Ordered Product Sales | **£726.65** |
| Total order items | **22** |

Image was read-only; not altered.

## 2. Utharsika Ownership Confirmation

| Check | Result |
|---|---|
| Assigned user | `utharsika` |
| Distinct assignment count (whole scope) | 1,723 |
| Categories owning this ASIN | 1 |
| Distinct users owning this ASIN | 1 (no sharing) |
| **Ownership verdict** | **CONFIRMED — Utharsika-owned, not shared** |

## 3. All SKUs for This ASIN (unrestricted query, all time)

| SKU | Row count | First tx | Latest tx | Sources | Statuses | Marketplaces | Accounts |
|---|---|---|---|---|---|---|---|
| `LSCYRO300GD2PK+RPR44WH2PK` | 40 | 2025-10-26 | 2026-06-29 | AMAZON | Cancelled, Completed, Refunded | UK | amazon Dcvoltage |
| `RPR44WH` | 1 | 2026-06-13 | 2026-06-13 | REPLACEMENT | Completed | UK | amazon Dcvoltage_amazon |

Only these two SKUs exist for this ASIN — no others found.

## 4. Reproduce Current UAWSO Result

Filters applied: `source_name='AMAZON'`, `market_place='UK'`, `order_status='Completed'`, `order_date::date` between 2026-06-01 and 2026-06-30, Utharsika assigned-ASIN scope.

| SKU | FBM Sales | FBM order items | FBA Sales | FBA order items | Total Sales | Total order items |
|---|---|---|---|---|---|---|
| `LSCYRO300GD2PK+RPR44WH2PK` | £699.76 | 21 | £0.00 | 0 | £699.76 | 21 |

**Confirmed exactly:** £699.76 / 21 order items.

## 5. Exact Pair vs Other SKU

**A. Exact pair** (`B0FX2QT3B1` + `LSCYRO300GD2PK+RPR44WH2PK`, current filters): £699.76 / 21 order items.

**B. Other SKU** (`RPR44WH`): 1 row, `order_total=£0.00`, `order_status='Completed'`, `source_name='REPLACEMENT'`, `market_place='UK'`.

**Does the extra £26.89 belong to another SKU? NO.** The only other SKU's row carries £0.00 — it cannot supply £26.89 of Sales under any interpretation. It **does**, however, supply exactly **1 extra order item** if Amazon's report counts Completed order items regardless of source (see Section 12).

## 6. Order Status Breakdown (ASIN-level, June 2026, both SKUs)

| Status | Row count | Distinct order_id | Distinct order_item_info | Quantity | Sales |
|---|---|---|---|---|---|
| Cancelled | 3 | 3 | 3 | 0 | £0.00 |
| Completed | 22 | 22 | 22 | 26 | £699.76 |
| Refunded | 1 | 1 | 1 | 1 | £0.00 |

**Completed status alone, across BOTH SKUs (any source), already equals 22 order items** — exactly the screenshot's "Total order items."

**Does one non-Completed row carry Sales=£26.89 or add 1 order item?** The single Refunded row carries `order_total=£0.00` in its current (post-refund) state, but its **original `item_price` is £26.89** (see Section 11) — it does not add an order item (it is Refunded, not Completed) but its original value explains the Sales gap.

## 7. Source Breakdown

| Source | Row count | Distinct order_item | Sales |
|---|---|---|---|
| AMAZON | 25 | 25 | £699.76 |
| REPLACEMENT | 1 | 1 | £0.00 |

**Is the extra row excluded because it is not `source_name='AMAZON'`? YES** — the single REPLACEMENT row is excluded from the current UAWSO calculation by the `source_name='AMAZON'` filter. It contributes £0.00 Sales but is a `Completed`-status order item.

## 8. Marketplace Breakdown

| Marketplace | Row count | Distinct order_item | Sales |
|---|---|---|---|
| UK | 26 | 26 | £699.76 |

**All 26 rows are UK.** No blank or other-marketplace rows exist. Marketplace scope is **ruled out** as a factor.

## 9. Account/Seller Breakdown

| ss_name | order_sub_source | Row count | Distinct order_item | Sales |
|---|---|---|---|---|
| amazon Dcvoltage | 6 | 25 | 25 | £699.76 |
| amazon Dcvoltage_amazon | 116 | 1 | 1 | £0.00 |

The REPLACEMENT row is recorded under a distinct sub-source account tag (`amazon Dcvoltage_amazon` / `order_sub_source=116`) versus the standard `amazon Dcvoltage` / `order_sub_source=6` used by all real Amazon-sourced orders. This is consistent with it being a system-generated replacement record rather than a normal seller-account order, and is not itself an additional root cause beyond the source-scope finding in Section 7.

## 10. Date-Field Differences

`public.order_transaction` has **exactly one** date column: `order_date`. There is no separate completed-date, shipped-date, transaction-date, or `created_at` column in this table (confirmed via `information_schema.columns`, 21 total columns, previously enumerated in the prior Vendor/adjustment investigation).

**Month-boundary rows checked** (2026-05-31, 2026-06-01, 2026-06-30, 2026-07-01): three rows found near the boundary — 2026-05-31 20:54:51 (£26.89, Completed), 2026-06-01 21:50:55 and 2026-06-01 23:16:45 (both already counted). No rows exist on 2026-06-30 or 2026-07-01 for this ASIN.

**Timezone tests performed:**

| Basis | Sales | Order items |
|---|---|---|
| Raw `order_date` (current) | £699.76 | 21 |
| +1:00 (UK BST — the marketplace's actual local time in June) | £699.76 | 21 (**unchanged**) |
| +5:30 (Asia/Colombo) | £726.65 | 22 (**matches target exactly**) |

**Finding:** a +5:30 shift happens to push the 2026-05-31 20:54:51 row into June 1st, exactly reproducing both target numbers. However, **this is ruled out as the real explanation**: the marketplace is UK, whose actual local time in June is BST (UTC+1), and a realistic UK-timezone shift produces **no change at all** (£699.76/21, identical to the raw baseline). The +5:30 match is a coincidental artifact of one specific boundary-adjacent row, not a plausible reporting-timezone difference for a UK Business Report. **Date-field/timezone is ruled out as the root cause.**

## 11. Sales Field Differences

Monetary columns available: `item_price`, `order_total`. No tax, shipping, VAT, discount, or fee column exists (confirmed, consistent with prior investigation).

| Calculation | Result | Matches £726.65? |
|---|---|---|
| `order_total`, Completed + AMAZON (current) | £699.76 | No |
| `item_price × quantity`, Completed + AMAZON | £699.76 | No (identical — no per-row discrepancy between order_total and item_price×quantity for Completed rows) |
| Gross positive Sales, all statuses | £699.76 | No |
| **`item_price × quantity`, status IN ('Completed','Refunded'), source='AMAZON'** | **£726.65** | **YES — exact match** |

**Exact mechanism:** the Refunded row (`order_id=206-0628138-4627505`, `order_item_info=1178915`, dated 2026-06-04 20:06:37) has `item_price=£26.89` and `quantity=1`, but its `order_total` was zeroed to £0.00 upon refund, and its `order_status='Refunded'` excludes it entirely from the current UAWSO calculation. **£699.76 + £26.89 = £726.65 exactly.**

This is consistent with well-documented Amazon Business Report behavior: "Ordered Product Sales" reflects the value of the order at the time it was **placed** (order-date based) and is not retroactively reduced when a refund occurs later — the order genuinely happened within the June 2026 window, so Amazon counts its original value, while UAWSO's net/status-filtered calculation correctly excludes it as a non-Completed, zero-net-value transaction for revenue-recognition purposes.

**No unsupported tax or shipping value was added** — this calculation uses only `item_price` and `quantity`, both of which exist in the schema.

## 12. Order-Item Definition Test

| Calculation | Result | Matches 22? |
|---|---|---|
| `COUNT(*)`, Completed + AMAZON | 21 | No |
| `COUNT(DISTINCT order_id)`, Completed + AMAZON | 21 | No |
| `COUNT(DISTINCT order_item_info)`, Completed + AMAZON (current) | 21 | No |
| `SUM(quantity)`, Completed + AMAZON | 26 | No |
| Positive-Sales row count | 21 | No |
| **`COUNT(DISTINCT order_item_info)`, status='Completed', any source** | **22** | **YES — exact match** |

**Exact mechanism:** the single REPLACEMENT-sourced row (`order_id=Repla-202-0589240-4116332`, `order_item_info=1188001`, SKU `RPR44WH`, dated 2026-06-13 23:28:00) carries `order_status='Completed'` even though `source_name='REPLACEMENT'` excludes it from the current UAWSO Sales/Orders calculation. Counting all Completed-status order items regardless of source gives **21 + 1 = 22 exactly**, matching the screenshot. Its `order_total=£0.00` means including it has zero Sales impact — consistent with the Sales gap being fully and independently explained by the Refunded row in Section 11.

## 13. Vendor Check

| Metric | Value |
|---|---|
| Vendor Sales (ASIN level) | £0.00 |
| Vendor Units | 0 |
| Row count | 0 |

**Re-confirmed: zero Vendor data exists for this ASIN, any period.** Not allocated to any SKU.

## 14. Exact Difference Row

Full row-level dataset: `07_EVIDENCE\generated_data\2026-07-10_B0FX2QT3B1_june-2026_reconciliation_rows.csv` (all 26 June-2026 rows for the ASIN).

**Two specific rows, together, explain both differences exactly — no single row explains both:**

| Difference | Exact row | Mechanism |
|---|---|---|
| £26.89 Sales | `order_item_info=1178915`, order_id `206-0628138-4627505`, Refunded, 2026-06-04, `item_price=£26.89` | Original order value, zeroed by refund and excluded by status filter |
| 1 Order item | `order_item_info=1188001`, order_id `Repla-202-0589240-4116332`, REPLACEMENT, 2026-06-13, `order_total=£0.00` | Completed-status order item excluded by source filter |

Both are independently verifiable, non-overlapping, and evidence-backed — no arbitrary row combination was searched; both rows were identified directly from the status/source dimension tests in Sections 6–7 and 11–12.

## 15. HTML Verification

Extracted the HTML's own embedded JSON and engine code from `09_OUTPUTS\2026-07-10_utharsika_v001.html` (same method as prior investigations — Node `vm` sandbox execution of the file's actual embedded engine, not the on-disk source file) and computed the June 2026 row for this ASIN.

| Field | HTML value |
|---|---|
| SKUs included | `LSCYRO300GD2PK+RPR44WH2PK` only |
| FBM Sales | £699.76 |
| FBM Orders | 21 |
| FBA Sales | £0.00 |
| FBA Orders | 0 |
| Vendor Sales | £0.00 |
| Vendor Units | 0 |
| Filters applied (embedded engine) | Same as PostgreSQL — Completed status, AMAZON source, UK marketplace, assigned-ASIN/SKU scope |

**Confirmed: the HTML excludes the exact same two rows as PostgreSQL** (the Refunded row and the REPLACEMENT row) — HTML and PostgreSQL match exactly, both showing £699.76/21.

---

## Evidence Outputs

| File | Purpose |
|---|---|
| `07_EVIDENCE\2026-07-10_B0FX2QT3B1_JUNE_2026_BUSINESS_REPORT_RECONCILIATION.md` | This file |
| `07_EVIDENCE\generated_data\2026-07-10_B0FX2QT3B1_june-2026_reconciliation_rows.csv` | Full 26-row transaction-level dataset with inclusion/exclusion reasons |

## Recommended HTML Action

**No HTML change is recommended.** The HTML correctly and consistently reproduces the same PostgreSQL-approved business rules (Completed status, AMAZON source, UK marketplace). The difference versus the Amazon Business Report screenshot is not a defect in UAWSO — it is a **methodology difference**: Amazon's "Ordered Product Sales" counts orders gross of same-window refunds (order-date based, not netted), and its order-item count appears to include Completed-status replacement shipments regardless of source. UAWSO's net, status/source-filtered approach is an intentional and internally consistent revenue-recognition choice (matching Sales actually retained, not gross ordered value). If the business wants UAWSO to match Amazon's Business Report figures exactly, that would require a deliberate, approved change to the Sales/Orders definitions (e.g., including original refunded-order value and/or including replacement order items) — a business-policy decision, not a bug fix.

## Pass/Fail

| Requirement | Status |
|---|---|
| Screenshot values confirmed | ✅ |
| PostgreSQL current values reproduced | ✅ (£699.76 / 21) |
| HTML values reproduced | ✅ (£699.76 / 21, matches PostgreSQL) |
| £26.89 difference explained | ✅ (Refunded row's original item_price) |
| 1 order-item difference explained | ✅ (REPLACEMENT row's Completed status) |
| No database or HTML modifications | ✅ confirmed |

**Final verdict: PASS.**
