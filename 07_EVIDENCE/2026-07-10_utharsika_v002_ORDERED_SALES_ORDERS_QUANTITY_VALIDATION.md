# UAWSO v002 — Ordered Sales, Orders and Quantity: Implementation and Validation

**What this asset is:** Build record and validation evidence for `09_OUTPUTS\2026-07-10_utharsika_v002.html` — a new report version implementing the Ordered Product Sales / Total Orders / Total Quantity business rules, alongside the unmodified `v001.html`.

**Owner:** Satheskanth
**Current status:** Implemented, validated, **PASS**.

---

## Resume Context

This session resumed after a prior run was stopped mid-way (during file discovery, before any code was written). Resume inspection confirmed:
- Not a git repository (`git status` correctly reports "not a git repository" — no version control in use for this project).
- `v001.html` SHA-256 = `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3`, identical to the value recorded in prior evidence — **confirmed unmodified**.
- No partial v002 template, engine, extraction script, generator, HTML, or evidence file existed anywhere on disk. The interrupted run had only located the existing v001 file paths and had not begun editing.
- **No prior work was discarded or reverted** — this session built the full v002 implementation fresh, reusing only the already-established v001 architecture as a reference pattern (additive extension, not modification).

## 1. Vendor_sales Column Metadata (re-confirmed, corrected count)

`public.vendor_sales` has **13 columns** (not 12, as an earlier prompt assumed — corrected per live metadata):

| # | Column | Type | Nullable | Default | Comment |
|---|---|---|---|---|---|
| 1 | id | bigint | YES | — | — |
| 2 | start_time | timestamp without time zone | YES | — | — |
| 3 | end_time | timestamp without time zone | YES | — | — |
| 4 | asin | text | YES | — | — |
| 5 | ordered_units | bigint | YES | — | — |
| 6 | ordered_revenue | double precision | YES | — | — |
| 7 | currency_code | text | YES | — | — |
| 8 | created_at | timestamp without time zone | YES | — | — |
| 9 | updated_at | timestamp without time zone | YES | — | — |
| 10 | category_id | bigint | YES | — | — |
| 11 | category_name | text | YES | — | — |
| 12 | user_id | bigint | YES | — | — |
| 13 | user_name | text | YES | — | — |

No column comments exist on this table. Confirmed column roles: ASIN = `asin`; reporting basis = `start_time`/`end_time` (a period, not a single date); ordered revenue = `ordered_revenue`; ordered units = `ordered_units`; SKU = **none**; order ID/PO key = **none**; marketplace/account/source = **none**. `id` is a surrogate row identifier only.

**Valid Vendor order key found: NO.** No column or table anywhere in the database (confirmed by the prior session's full database-wide search, re-affirmed here) represents a genuine Vendor order or purchase-order reference. **Vendor Orders = N/A** throughout v002 — never estimated from `id`, row count, `ordered_units`, or an ASIN-date count.

## 2. Files Changed / Created

| File | Type | Purpose |
|---|---|---|
| `05_IMPLEMENTATION/src/uawso_client_engine.js` | **Modified (additive only)** | Added `sumRangeSplitByAsinSkuV4`, `computeRowsV4`, `computeTotalV4` — new exported functions alongside untouched v1/v2/v3 functions |
| `05_IMPLEMENTATION/src/dashboard_renderer.py` | **Modified (additive only)** | Added `TEMPLATE_PATH_V4` constant and `render_dashboard_v4()` function; existing `render_dashboard()` used by v001 untouched |
| `05_IMPLEMENTATION/templates/uawso_report_template_v4.html` | **New file** | Reusable v4 template: new table columns (FBM/FBA/Vendor/Total Quantity, Total Orders, Total Sales, PY/CY Orders, PY/CY Quantity, 3 change-% columns), new KPI cards, dual CSV export (filtered + full dataset) |
| `05_IMPLEMENTATION/src/extract_uawso_v4_ordered_sales.py` | **New file** | Extraction script implementing the Ordered Product Sales / Total Orders / Total Quantity SQL rules, widened SKU discovery |
| `05_IMPLEMENTATION/tests/generate_v002_dashboard.py` | **New file** | Generator driver producing `09_OUTPUTS\2026-07-10_utharsika_v002.html` |
| `05_IMPLEMENTATION/tests/verify_v002_html.js` | **New file** | Validation script executing the v002 HTML's own embedded engine in a Node sandbox |
| `09_OUTPUTS\2026-07-10_utharsika_v002.html` | **New file** | The v002 report itself |
| `09_OUTPUTS\staging\2026-07-10_utharsika_v002.staging.html` | **New file** | Staging copy (identical bytes to final) |
| `07_EVIDENCE\generated_data\2026-07-10_utharsika_v002_*.json` (4 files) | **New files** | Extracted product master, daily split, vendor periods, assigned-ASIN list |

**Template path:** `05_IMPLEMENTATION/templates/uawso_report_template_v4.html`
**Renderer path:** `05_IMPLEMENTATION/src/dashboard_renderer.py` (`render_dashboard_v4`)
**Extraction path:** `05_IMPLEMENTATION/src/extract_uawso_v4_ordered_sales.py`
**Generator path:** `05_IMPLEMENTATION/tests/generate_v002_dashboard.py`

`v001`'s generator (`tests/generate_final_dashboard_v3.py`), template (`templates/uawso_report_template.html`), and renderer function (`render_dashboard`) are **completely untouched** — v001 remains regenerable identically at any time.

## 3. Business Rules Implemented

**Ordered Product Sales:** `SUM(item_price * quantity)` for `source_name='AMAZON' AND order_status IN ('Completed','Refunded')`, grouped by `order_date::date` (the original order date — so a later-month refund never removes value from the month the order was placed, because the refunded row is still grouped under its original order date). Cancelled/Canceled rows are excluded entirely by the extraction `WHERE` clause. No tax/shipping value was added (schema has no such columns, per prior investigation).

**Total Orders:** `COUNT(DISTINCT order_item_info)` for `order_status='Completed' AND source_name IN ('AMAZON','REPLACEMENT')`. Refunded rows contribute to Sales but not to Total Orders. A Completed, zero-value REPLACEMENT row contributes exactly one order item and zero Sales. Total Orders = FBM Orders + FBA Orders; **Vendor Units are never added.**

**Total Quantity:** FBM Quantity + FBA Quantity (same row-inclusion scope as Total Orders) + Vendor Units (`public.vendor_sales.ordered_units`). Never labelled "Orders."

**Vendor:** `ordered_revenue` → Vendor Sales, `ordered_units` → Vendor Units, one dedicated ASIN-level row per ASIN (never duplicated across SKU rows, never attached to a SKU-specific row). **Vendor Orders = N/A.**

## 4. Assigned ASIN / SKU Grain

Resolved via `public.user` → `public.ph_categories` → `public.ph_cate_products` (`which_channel=1`), `DISTINCT` applied.

| Check | Result |
|---|---|
| Assigned ASIN count | **1,723** |
| Total output rows | **2,549** |
| ASIN+SKU rows | 2,111 (1,617 ASINs now show at least one SKU — widened from 1,610 under the v3 rule, since 7 ASINs' only visible SKU comes from a Refunded-AMAZON or Completed-REPLACEMENT row that v3's Completed-AMAZON-only SKU discovery could not see) |
| No-SKU rows | 106 |
| Vendor-only rows | 332 |
| Duplicate ASIN–SKU pairs | **0** |
| Rows containing multiple (comma-joined) SKUs | **0** |

All checks verified by executing `buildCanonicalRows` against the v002 HTML's own embedded product master (Node sandbox, not assumed).

## 5. Exact ASIN Validation — B0FX2QT3B1 / LSCYRO300GD2PK+RPR44WH2PK

Computed by executing the v002 HTML's own embedded engine and data (not the source files) in a Node sandbox.

| Period | FBM Sales | FBM Orders | FBM Qty | FBA Sales | FBA Orders | FBA Qty | Vendor Sales | Vendor Units | **Total Sales** | **Total Orders** | **Total Quantity** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| June 2025 (exact-pair SKU) | £0.00 | 0 | 0 | £0.00 | 0 | 0 | £0.00 | 0 | £0.00 | 0 | 0 |
| June 2026 (exact-pair SKU) | £726.65 | 21 | 24 | £0.00 | 0 | 0 | £0.00 | 0 | £726.65 | 21 | 24 |
| June 2026 (RPR44WH SKU, same ASIN) | £0.00 | 1 | 2 | £0.00 | 0 | 0 | £0.00 | 0 | £0.00 | 1 | 2 |
| **June 2026 — ASIN-level total** | | | | | | | | | **£726.65** | **22** | **26** |

**June 2025 expected £0.00/0 — CONFIRMED EXACTLY.**
**June 2026 expected £726.65/22 — CONFIRMED EXACTLY**, decomposed as: Completed AMAZON Sales £699.76 + Refunded original Sales £26.89 = £726.65; Completed AMAZON order items 21 + Completed REPLACEMENT order item 1 = 22. Vendor Sales/Units = £0/0 (confirmed — no `vendor_sales` rows exist for this ASIN, any period). Total Quantity = 26 (24 from the exact-pair SKU + 2 from the REPLACEMENT SKU).

## 6. June 2025 Full-Scope Validation (all 1,723 ASINs)

| Metric | Value |
|---|---|
| FBM Sales | £27,797.40 |
| FBA Sales | £9,293.56 |
| Vendor Sales | £4,302.96 |
| **Total Sales** | **£41,393.92** |
| FBM Orders | 1,514 |
| FBA Orders | 350 |
| **Total Orders** | **1,864** |
| FBM Quantity | 1,948 |
| FBA Quantity | 386 |
| Vendor Units | 528 |
| **Total Quantity** | **2,862** |

**Comparison to user reference (£42,082.96 / 2,412):**

| | Recalculated | User reference | Difference |
|---|---|---|---|
| Sales | £41,393.92 | £42,082.96 | **−£689.04** |
| Orders | 1,864 | 2,412 | **−548** |

**Not forced to match.** This is a genuine improvement over the prior (pre-v002) figures (£41,146.84/1,856 → −£936.12/−556), because the new rule now correctly includes each ASIN's Refunded-original Sales and Completed-REPLACEMENT order items across the full 1,723-ASIN scope, not just the single validated ASIN. The **remaining £689.04 Sales gap and 548 Orders gap are not explained by any rule implemented in v002** — this matches the unresolved conclusion from the prior WORK 1 investigation (`07_EVIDENCE\2026-07-10_utharsika_VENDOR_ORDER_AND_JUNE_ADJUSTMENT_RECONCILIATION.md`), which found that tax and shipping are not testable at all (no schema columns exist) and that no evidence-backed combination of tested dimensions closes the full gap. **Exact remaining cause: unresolved — requires the business to clarify how the £42,082.96/2,412 reference figure was originally derived**, since every schema-supported rule has now been applied and a material portion of the gap (£247.08 Sales, 8 Orders) has been closed by this exact same Refunded/Replacement rule at the individual-ASIN level, but a further, currently unidentified amount remains across the wider ASIN set.

## 7. June 2026 Full-Scope Validation (all 1,723 ASINs)

| Metric | Value |
|---|---|
| FBM Sales | £18,494.15 |
| FBA Sales | £7,171.01 |
| Vendor Sales | £571.42 |
| **Total Sales** | **£26,236.58** |
| FBM Orders | 936 |
| FBA Orders | 398 |
| **Total Orders** | **1,334** |
| FBM Quantity | 1,166 |
| FBA Quantity | 439 |
| Vendor Units | 41 |
| **Total Quantity** | **1,646** |

No external reference figure was supplied for the full June 2026 scope; the exact single-ASIN validation (Section 5) is the confirmed check for this period.

## 8. Date-Mode / Full-History Validation

Full historical scope confirmed embedded: `2025-01-01` → `2026-07-09` (not June-only). All five comparison modes resolve correctly against this scope (verified by executing `Engine.resolvePeriod` from the v002 HTML directly):

| Mode | Input | Resolved CY | Resolved PY |
|---|---|---|---|
| DAILY | 2026-06-15 | 2026-06-15 → 2026-06-15 | 2025-06-15 → 2025-06-15 |
| WEEKLY | week start 2026-06-15 | 2026-06-15 → 2026-06-21 | 2025-06-15 → 2025-06-21 |
| MONTH | 2026-06 | 2026-06-01 → 2026-06-30 | 2025-06-01 → 2025-06-30 |
| MTD | (latest completed 2026-07-09) | 2026-07-01 → 2026-07-09 | 2025-07-01 → 2025-07-09 |
| CUSTOM | 2026-06-01 → 2026-06-30 | 2026-06-01 → 2026-06-30 | 2025-06-01 → 2025-06-30 |

## 9. Quality Gate Results (19 gates)

| # | Gate | Result |
|---|---|---|
| 1 | v001 remains byte-for-byte unchanged | ✅ SHA-256 identical |
| 2 | v002 exists | ✅ |
| 3 | Reusable template is updated | ✅ new `uawso_report_template_v4.html` + additive engine/renderer functions |
| 4 | Full historical dataset included | ✅ 2025-01-01 → 2026-07-09 |
| 5 | Daily/Weekly/Monthly/MTD filters work | ✅ all 5 modes verified |
| 6 | Assigned ASIN count = 1,723 | ✅ |
| 7 | Duplicate ASIN–SKU pairs = 0 | ✅ |
| 8 | Rows containing multiple SKUs = 0 | ✅ |
| 9 | Refunded original Sales included once | ✅ verified on exact ASIN (£26.89 present exactly once) |
| 10 | Completed replacement items counted once | ✅ verified (RPR44WH row = 1 order) |
| 11 | Cancelled/Canceled rows excluded | ✅ excluded by extraction WHERE clause (structurally impossible to include) |
| 12 | Vendor Units excluded from Total Orders | ✅ `totalOrders = fbmOrders + fbaOrders` only, by code construction |
| 13 | Vendor Units included in Total Quantity | ✅ `totalQuantity = fbmQuantity + fbaQuantity + vendorUnits`, by code construction |
| 14 | Vendor Sales/Units not duplicated | ✅ `isVendorRow` gating (unchanged, proven v3 pattern) |
| 15 | Exact ASIN result is £726.65 and 22 Orders | ✅ CONFIRMED EXACTLY |
| 16 | KPI cards reconcile with filtered rows | ✅ same `computeTotalV4` feeds both |
| 17 | CSV reconciles with KPI cards | ✅ same row objects feed both CSV export and footer totals |
| 18 | No credentials embedded | ✅ structural check passed (no PGHOST/PGPASSWORD/connection string literal) |
| 19 | No unrelated files modified | ✅ only new files created; two existing files extended additively |

**All 19 gates PASS.**

## 10. v001 / v002 Identity

| File | SHA-256 |
|---|---|
| `09_OUTPUTS\2026-07-10_utharsika_v001.html` | `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` |
| `09_OUTPUTS\2026-07-10_utharsika_v002.html` | `cb8e15fb9813ff01a0dc3f1a2597f67644879f0cfe45663d6d2fe70c4cae95e4` |

`tech_team_outputs.ph_task` write: **NO** (not performed as part of this evidence file; see the separate publication evidence file for the publish-phase record, if and only if publication proceeds after this validation).

## Final Verdict: **PASS**

All mandatory quality gates pass. The exact ASIN validation (B0FX2QT3B1, June 2026 = £726.65/22 Orders) is confirmed exactly, matching the user-supplied Amazon Business Report screenshot. v001 is provably unmodified. The full June 2025 1,723-ASIN reconciliation against the user's £42,082.96/2,412 reference remains partially unresolved (−£689.04/−548) and is reported honestly as such, per instruction not to force totals — this is not a blocking condition per the stated quality gates, which require only the single-ASIN exact match.
