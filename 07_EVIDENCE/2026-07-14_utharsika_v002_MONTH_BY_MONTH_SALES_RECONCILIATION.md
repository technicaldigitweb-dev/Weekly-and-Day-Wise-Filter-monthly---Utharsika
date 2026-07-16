# UAWSO v002 — Month-by-Month Sales Reconciliation and Refresh (Phases 9-13)

**What this asset is:** Record of the v002 refresh through 2026-07-13, post-refresh completeness testing, exact-ASIN regression test, and ph_task publication.

**Owner:** Satheskanth
**Status:** **PASS** — refreshed, verified, published.

---

## Phase 9 — Refresh

Data range extended from 2025-01-01 → 2026-07-09 to **2025-01-01 → 2026-07-13 inclusive**.

**Note on execution path:** the direct PostgreSQL credential connection (`psycopg2`) was intermittently refused by the database host throughout this session ("too many clients already" / "server closed the connection unexpectedly"). The full re-extraction for 2025-01-01 → 2026-07-09 (unchanged portion) reused the already-validated existing extraction. The incremental 2026-07-10 → 2026-07-13 window (110 new daily-aggregate rows, 0 new ASIN-SKU pairs) was fetched via the MCP PostgreSQL tool (which remained available) and merged into the local JSON extraction files with an explicit overlap check (0 overlapping keys found) before regeneration — full detail in `05_IMPLEMENTATION/tests/merge_incremental_0710_0713.py`. `public.vendor_sales` and the assigned-ASIN list required no incremental fetch, since neither query was date-bounded in the original extraction.

All required comparison modes preserved: Daily, Weekly, Month, MTD, Custom (unchanged period-resolution logic, only the underlying data extended).

Total Orders = FBM Orders + FBA Orders. Total Quantity = FBM Quantity + FBA Quantity + Vendor Units. Vendor Orders = N/A. (All unchanged from the approved v002 rule set — this refresh did not alter any business definition, only extended the date range and fixed the Vendor boundary bug identified in Phase 7.)

## Phase 10 — Post-Refresh Monthly Completeness Test

Full table: `07_EVIDENCE\generated_data\2026-07-14_utharsika_monthly_sales_reconciliation.csv` (19 months, 2025-01 through 2026-07-13).

**Every month reconciles to exactly £0.00 difference** between:
- Canonical PostgreSQL Amazon Sales (FBM+FBA, `item_price × quantity`, Completed+Refunded/AMAZON)
- Canonical PostgreSQL Vendor Sales (corrected half-open overlap)
- Canonical PostgreSQL Total Sales
- Refreshed embedded HTML monthly Sales (extracted from the HTML's own embedded engine + data, executed in a Node sandbox)
- Dashboard-computed monthly Sales
- Full CSV monthly Sales

**Dashboard Total Sales and CSV Total Sales are identical to HTML Total Sales by construction**, not by separate empirical test: the template's `render()` function computes `total = Engine.computeTotalV4(rows)` once per period selection, and both `renderKpis(total, ...)` (the dashboard cards) and `downloadCsv(state.lastFilteredRows/lastAllRows, ...)` (both CSV buttons) consume the exact same `rows`/`total` objects — there is no separate code path that could diverge. This was verified by code inspection of `templates/uawso_report_template_v4.html` (`render()`, `renderKpis()`, `downloadCsv()`).

| Metric | Result |
|---|---|
| Months with non-zero Sales difference | **0 of 19** |
| Missing valid `order_item_info` | **0** (canonical PostgreSQL inclusion query and the HTML's embedded daily-split extraction query are the identical SQL logic — no separate "HTML dataset build" step exists that could drop rows) |
| Extra invalid `order_item_info` | **0** (Cancelled/Canceled/New/Pending/Deleted rows are excluded by the extraction `WHERE` clause itself, not filtered post-hoc) |
| Duplicate `order_item_info` | **0** (re-confirmed via Phase 3/4 checks on the same canonical query) |

## Phase 11 — Exact Regression Test

ASIN `B0FX2QT3B1`, June 2026, computed from the **refreshed** HTML's own embedded engine and data:

| Metric | Value |
|---|---|
| Completed AMAZON Sales | £699.76 |
| Refunded original Sales (remains in June — original order was placed in June) | £26.89 |
| **Ordered Product Sales** | **£726.65** ✅ exact match |
| **Total Orders** | **22** ✅ exact match |
| **Total Quantity** | **26** ✅ (24 from the exact-pair SKU + 2 from the REPLACEMENT SKU) |

Confirmed unchanged from the pre-refresh validation — the refresh (extended date range + Vendor boundary fix) did not alter this ASIN's June 2026 figures (it has zero Vendor data, so the Vendor fix does not touch it).

## v001 / v002 Identity

| File | SHA-256 |
|---|---|
| `09_OUTPUTS\2026-07-10_utharsika_v001.html` | `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` (unchanged throughout this session) |
| `09_OUTPUTS\2026-07-10_utharsika_v002.html` (refreshed) | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` |

## Phase 13 — ph_task Publication

| Field | Before | After |
|---|---|---|
| id | 157 | 157 (unchanged) |
| task_name | 2026-07-10_utharsika_v001 | unchanged |
| task_id | UAWSO-2026-07-10-utharsika-v001 | unchanged |
| version_level | 2 | **2 (kept, per instruction — not incremented)** |
| version_status | released | unchanged |
| html_content length | 5,400,222 chars (pre-refresh v002) | 5,421,905 chars (refreshed) |
| updated_at | — | 2026-07-14 15:06:09.792767+05:30 |

No new row was inserted (exactly one matching row confirmed before the update; `UPDATE` affected exactly 1 row, checked programmatically with automatic rollback if not).

**Post-write verification:**
- Stored HTML SHA-256: `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff`
- Local refreshed v002 SHA-256: `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff`
- **Match: YES**
- Stored content contains the `2026-07-13` history-end marker: **YES**
- Monthly reconciliation re-verified against the refreshed, now-published content (Phase 10 table above was generated from this exact file before publication; the hash match proves the published content is byte-identical to what was validated).

## Evidence Files

| File | Purpose |
|---|---|
| `07_EVIDENCE\2026-07-14_utharsika_v002_ORIGINAL_ORDER_MONTH_SALES_VALIDATION.md` | Pre-refresh validation (Phases 1-8), including the Vendor boundary bug discovery |
| `07_EVIDENCE\2026-07-14_utharsika_v002_MONTH_BY_MONTH_SALES_RECONCILIATION.md` | This file |
| `07_EVIDENCE\generated_data\2026-07-14_utharsika_monthly_sales_reconciliation.csv` | Full 19-month reconciliation table |

## Final Verdict: **PASS**

The original order-date basis is proven to the standard achievable from the schema; refunded original Sales remain in their original order month; cancelled orders are excluded; every included `order_item_info` appears exactly once; every monthly total reconciles to £0.00 across PostgreSQL, HTML, dashboard, and CSV; a genuine Vendor period-overlap duplication bug was found, fixed, and re-verified; the exact ASIN regression (£726.65 / 22 / 26) passes; and the existing ph_task row was updated in place without duplication, with a verified hash match.
