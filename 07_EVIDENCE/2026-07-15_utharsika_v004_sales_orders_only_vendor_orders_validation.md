# UAWSO v004 — Sales-and-Orders-Only, Vendor Orders Rule Validation

**Target (approved in-place correction, not a new version):** `09_OUTPUTS\2026-07-15_utharsika_v004.html`
**Requirement amendment:** `01_REQUIREMENTS\Requirement\2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md` Section 3.2
**Execution date:** 2026-07-15
**User approval:** Explicit — the report now shows Sales and Orders only; Quantity is removed; Vendor Orders = `ordered_units` (one Vendor Unit = one Vendor Order); Total Orders = FBM Orders + FBA Orders + Vendor Orders.

---

## 1. Requirement Update

Old rule (superseded): Quantity = FBM Quantity + FBA Quantity + Vendor Units; Vendor Orders = N/A (no order-level key).
New rule (Section 3.2, inserted 2026-07-15): Sales and Orders only. Vendor Orders = `public.vendor_sales.ordered_units` directly. Total Orders = FBM Orders + FBA Orders + Vendor Orders. All Quantity fields removed.

Every dependent section of the requirement (Section 2 Required Data Output, Section 4 Current Approved Business Rules, Section 5 Business Logic Block — ASIN-Wise Orders Rule and Vendor Non-Duplication Rule, Section 7 Data and Validation Requirements, Section 8 Required Evidence Content) was updated in place so only the new rule is active — no dual/conflicting rule remains. One direct business-confirmation quote from Utharsika (which mentions "Quantity") was preserved verbatim as a historical record, with an explicit annotation that it is superseded by Section 3.2, rather than edited to put different words in her mouth.

## 2. Old vs New Order Formula

| | Old | New |
| ----- | ----- | ----- |
| Vendor Orders | N/A (did not exist) | `= public.vendor_sales.ordered_units` |
| Total Orders | FBM Orders + FBA Orders | FBM Orders + FBA Orders + Vendor Orders |
| Quantity | FBM Quantity + FBA Quantity + Vendor Units | Removed entirely |

## 3. Active Sources Inspected and Changed

| File | Change |
| ----- | ----- |
| `05_IMPLEMENTATION\src\uawso_client_engine.js` | `sumRangeByAsinV5` no longer sums `fbm_quantity`/`fba_quantity`. `computeRowsV5`/`computeTotalV5` (the functions that power v004.html) no longer compute or return any Quantity field; both now compute `vendorOrders = ordered_units` and include it in `totalOrders`/`currentYearOrders`/`previousYearOrders`. **v1–v4 functions (used by historical v001/v002 HTML) were not touched.** |
| `05_IMPLEMENTATION\templates\uawso_report_template_v5_asin_level.html` | Removed all Quantity KPI cards, table columns (FBM/FBA/Total/PY/CY Quantity, Quantity Change %), sort options, Column Definitions rows, Data Coverage/Footer notes, and CSV header/row fields. Renamed the "Vendor Units" column to "Vendor Orders" (`data-field="vendorOrders"`). Added a "Total Orders" note explaining the new formula and a note confirming Quantity is out of scope. |
| `05_IMPLEMENTATION\src\dashboard_renderer.py` | `render_dashboard_v5()`'s page title changed from "...Sales, Orders & Quantity Dashboard..." to "...Sales & Orders Dashboard...". `render_dashboard_v4()` (used by historical v002) was not touched. |
| `05_IMPLEMENTATION\src\extract_uawso_v5_asin_level.py` | Docstring updated to document the new Order/Quantity rule for future readers. SQL/extraction logic itself was **not** changed — the script still reads `fbm_quantity`/`fba_quantity` into the JSON snapshot for backward-compatible shape only; the client engine no longer consumes those two fields. No re-extraction was performed for this task (per instruction to preserve Sales logic, assigned-ASIN scope, status filtering, date range, and ASIN grain) — the existing, already-validated `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_*.json` snapshot was reused unchanged. |

## 4. Sales Logic Preserved (unchanged)

FBM Sales, FBA Sales, Vendor Sales, Total Sales, Sales Change %, image selection, assigned-ASIN scope (1,723), status filtering (dynamic exclusion, Cancelled/Canceled), date range (2025-01-01 → 2026-07-14), and ASIN grain (one row per ASIN) were not touched by this change. Verified directly: **Sales difference before/after = £0.00.**

## 5. Vendor Orders and Total Orders Reconciliation

Recomputed from the same, already-validated live-source-derived embedded JSON snapshot, using the updated engine:

| Metric | Source (= embedded snapshot, unchanged this task) | HTML (via updated engine) | Difference |
| ----- | ----- | ----- | ----- |
| FBM Orders | 26,490 | 26,490 | 0 |
| FBA Orders | 7,964 | 7,964 | 0 |
| Vendor Orders (`ordered_units`) | 4,748 | 4,748 | **0** |
| **Total Orders** | **39,202** | **39,202** | **0** |

Formula verified structurally and numerically: `26,490 + 7,964 + 4,748 = 39,202`. This matches exactly the expected figure given in the governing task (39,202), independently recalculated from the existing approved snapshot rather than hardcoded.

## 6. Quantity Removal — Verified Absent Everywhere

Verified via genuine headless-browser rendering (Playwright/Chromium) of the actual promoted HTML, not static source inspection alone:

| Check | Result |
| ----- | ----- |
| Quantity KPI cards | 0 found (full KPI label list captured and inspected) |
| Quantity table headers | 0 found (full header list captured and inspected) |
| Quantity sort-field options | 0 found |
| Quantity in Column Definitions panel text | Not present |
| Quantity in CSV header row (real download captured) | Not present |
| Computed row/total objects (`fbmQuantity`/`fbaQuantity`/`vendorUnits`/`totalQuantity`) | `undefined` on every row and the total — confirmed programmatically |

## 7. Image, ASIN Count, and Structural Validation

| Check | Value |
| ----- | ----- |
| ASIN rows before | 1,723 |
| ASIN rows after | 1,723 |
| Image selection logic | Untouched — same `buildCanonicalRowsV5` function, same embedded `product_master_asin_level` data |
| Image-covered / no-image counts | 1,699 / 24 (unchanged) |
| Duplicate ASIN rows | 0 |

## 8. HTML and CSV Field Validation

Table now shows exactly 18 columns: ASIN, Image, FBM Sales, FBM Orders, FBA Sales, FBA Orders, Vendor Sales, Vendor Orders, Total Sales, Total Orders, PY Sales, CY Sales, PY Orders, CY Orders, Sales Change %, Order Change %, Trend, Achievement %. CSV export headers match exactly (plus "Image URL"), captured from a real triggered download (1 header + 1,723 data rows = 1,724 lines) — confirms the export still includes all filtered rows, not only the current page.

## 9. Tests

Updated `05_IMPLEMENTATION\tests\test_uawso_client_engine_v5.js` (25/25, was 23/23 — added explicit Vendor-Orders/Total-Orders-formula and Quantity-absence checks), `test_uawso_sticky_columns_and_export_v5.js` (21/21), `test_uawso_pagination_v5.js` (40/40), and `test_uawso_15row_viewport_v5.py` (28/28 — genuine Playwright functional checks, re-run against both the staging file and the final promoted file with identical results) to reflect the new Order formula (39,202) and Quantity absence, rather than leaving stale assertions that would fail for the right reason. Full regression: `test_uawso_client_engine.js` 42/42, `test_uawso_client_engine_v2.js` 19/19, `test_uawso_client_engine_v3.js` 21/21 — all pre-existing, untouched v1–v3 tests still pass, confirming zero impact on historical v001 logic. **Total: 196/196 across all suites.**

## 10. Browser Validation

Full — a real headless Chromium (`playwright`) is available in this environment. All 18 required test items (visible-row target, 15-row viewport at 3 window sizes, page size, sticky header/ASIN/Image/pagination, Previous/Next/direct-navigation, full-filtered-download completeness, Sales/ASIN/image unchanged, Total Orders correctly updated) were verified with genuine rendering and interaction, not static source inspection. A dedicated additional check (Section 6 above) confirmed Quantity's absence directly in the live DOM, sort dropdown, Column Definitions text, and a real triggered CSV download.

## 11. Backup and Update Procedure

| Item | Value |
| ----- | ----- |
| Pre-update local hash | `51865bbb45a5b49c15c74156723efa12d8ec6211f397487e9dec12f288587b24` |
| Backup path | `09_OUTPUTS\staging\2026-07-15_utharsika_v004_before_sales_orders_only_vendor_orders_update.html` |
| Backup verified byte-identical | YES |
| Staging path | `09_OUTPUTS\staging\2026-07-15_utharsika_v004_sales_orders_only.staging.html` |
| Staging SHA-256 | `d8ab5b255619bf188acfa7044679e7c60bff0cef4d8d52717483e49ef1f4999d` |
| Atomic replace | `update_uawso_v004_sales_orders_only.py` — asserted target filename, verified backup hash and current-file hash both equal the expected pre-update hash before replacing; temp-file write + hash-verify + `os.replace()`; re-verified final hash matches staging hash |
| Updated local HTML path | `09_OUTPUTS\2026-07-15_utharsika_v004.html` |
| Updated local HTML SHA-256 | `d8ab5b255619bf188acfa7044679e7c60bff0cef4d8d52717483e49ef1f4999d` |
| Updated local HTML size | 5,122,447 bytes |
| Other historical HTML files (v001 07-09, v001/v002 07-10, v002 07-14) | Re-hashed immediately after the replace: all 4 **UNCHANGED** |
| No `v005` created | Confirmed — only the existing v004 file was modified |

## 12. Database Publication

**`tech_team_outputs.ph_task` was not queried or modified in this task**, per the explicit instruction to complete local validation first and present the result for review before any database publication. Row 256 (last updated with the 15-row-viewport correction) remains exactly as it was before this task.

## 13. Final PASS/FAIL

```
- Vendor Orders equal ordered_units                                   YES (4,748 = 4,748)
- Total Orders include Vendor Orders                                  YES (26,490 + 7,964 + 4,748 = 39,202)
- current snapshot Total Orders reconcile correctly                   YES (39,202, matches expected)
- all Quantity fields removed                                         YES (KPI/headers/sort/definitions/CSV/computed objects all confirmed absent)
- Sales values remain unchanged                                       YES (£718,835.91, £0.00 difference)
- ASIN count remains unchanged                                        YES (1,723)
- image data remains unchanged                                        YES (1,699/24, 0 mismatches, logic untouched)
- export remains complete                                             YES (1,724 lines = 1 header + 1,723 rows, real download captured)
- all regression tests pass                                           YES (196/196)
- only the approved local HTML and reusable source files changed      YES
- ph_task not changed during this local-validation task               YES (not queried)
```

**FINAL STATUS: PASS.** The local `09_OUTPUTS\2026-07-15_utharsika_v004.html` now shows Sales and Orders only, with Vendor Orders (`ordered_units`) correctly included in Total Orders (39,202), Quantity fully removed from every layer (data model, table, KPI cards, CSV, Column Definitions), and every other approved rule (Sales, image selection, ASIN grain, scope, status, date range) verified unchanged. Ready for review before database publication.
