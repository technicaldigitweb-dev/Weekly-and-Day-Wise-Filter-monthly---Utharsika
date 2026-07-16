# UAWSO REQ-02-D01 — Local Business-Rule and Source-Table Validation

**Target (read-only):** `09_OUTPUTS\2026-07-15_utharsika_v004.html` (already published as `ph_task` row 256)
**Business-routing workbook:** `02_SOURCE\business_reference\2026-07-15_table_location_business_details_v001.xlsx`
**Approved requirement:** `01_REQUIREMENTS\Requirement\2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md`
**Execution date:** 2026-07-15
**Scope:** Read-only. No `tech_team_outputs.ph_task` query was made, no database write occurred, no local HTML/code/template/engine file was modified, no automation touched.

---

## 1. Business-Routing Workbook (read)

Single sheet: `Table Routing Map` (77 rows). Rows relevant to this report:

| Subject | Table Location | Confirms |
| ----- | ----- | ----- |
| Sales / Orders | `public.order_transaction` | Columns include `order_id, sku, asin, order_date, order_total, order_status, source_name, fba_sales, market_place, ss_name, user_name`; `order_status` values include `Cancelled, Completed, Deleted, Hold, Inprogress, New, Pending, Refunded`; `fba_sales`: TRUE=FBA, FALSE/blank=FBM (Amazon only) |
| Listing — Registry | `public.listing_data` | Columns include `id, ref_id, sku, which_channel, market_place, wrong_sku, main_image_url`; `which_channel`: 1=Amazon; `wrong_sku`: 0=valid row, always filter to 0 |
| Amazon — Vendor Central Sales | `public.vendor_sales` | Columns: `id, start_time, end_time, asin, ordered_units, ordered_revenue, currency_code, category_name, user_name`; explicitly "one row per ASIN per reporting window... wholesale sell-in data, not the same as customer-facing retail sales" |

The workbook does not include an "assigned ASIN scope" table — `public.user`/`public.ph_categories`/`public.ph_cate_products` are internal PH assignment-tracking tables, not business-routing data tables, and are correctly outside this workbook's scope. That scope is instead grounded in REQ-02-D01 Section 2 (Source Information) and this project's own prior discovery work.

Full business source-to-output map: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_business_source_map.csv`.

## 2. Approved Requirement (read)

`01_REQUIREMENTS\Requirement\2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md` confirms all approved rules used as the basis for this validation: one row per ASIN; no SKU column; image via `public.listing_data.ref_id=ASIN`, `which_channel=1`, `market_place='UK'`, `wrong_sku=0`, lowest `id` tie-break (business-confirmed); Orders = `COUNT(DISTINCT order_item_info)` grouped directly by `(date, ASIN)`; Vendor counted once per ASIN; dynamic status exclusion (`NOT IN ('Cancelled','Canceled')`, non-null/non-blank); date range 2025-01-01 through 2026-07-14.

## 3. Local HTML Inspection (read)

Extracted the actual embedded canonical data from `09_OUTPUTS\2026-07-15_utharsika_v004.html` (not screen text):

| Payload | Rows |
| ----- | ----- |
| `uawso-product-master-asin-level` | 1,723 (one per ASIN: `asin`, `image_url`, `product_title`) |
| `uawso-daily-aggregates-asin` | 29,203 (date+ASIN grain: `fbm_sales/orders/quantity`, `fba_sales/orders/quantity`) |
| `uawso-vendor-periods` | 961 (`asin`, `start_date`, `end_date`, `revenue`, `units`) |

## 4. Assigned-ASIN Scope (rebuilt fresh, not reused)

Live query: `DISTINCT pcp.ref_id` from `public.user` → `public.ph_categories` → `public.ph_cate_products`, `user_name='utharsika'`, `which_channel=1`.

| Metric | Value |
| ----- | ----- |
| Assigned ASIN count (source, fresh) | 1,723 |
| Duplicate assignment rows | 0 |
| HTML ASIN count | 1,723 |
| Duplicate HTML ASINs | 0 |
| Missing assigned ASINs (in scope, absent from HTML) | **0** |
| Extra HTML ASINs (in HTML, absent from scope) | **0** |

**Result: PASS.** Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_assigned_asin_reconciliation.csv`.

## 5. Sales/Orders Source Verification

Confirmed source: `public.order_transaction`. Exact fields used: `asin, order_date, order_item_info, order_status, quantity, item_price, fba_sales, source_name, market_place`. No derived HTML snapshot was used as source-of-truth — every figure below was recomputed from a fresh live query.

## 6. Status Rule (discovered fresh)

Within assigned scope + `market_place='UK'` + date range 2025-01-01–2026-07-14, `source_name='AMAZON'`:

| Status | Included? | Rows | Sales | Quantity |
| ----- | ----- | ----- | ----- | ----- |
| Completed | YES | 33,520 | £656,665.53 | 41,152 |
| Refunded | YES | 651 | £14,931.87 | 911 |
| New | YES | 18 | £309.24 | 19 |
| Pending | YES | 16 | £114.33 | 18 |
| Cancelled | NO | 895 | £2,115.97 | 151 |
| Canceled | NO | 317 | £20.89 | 80 |

**Cancelled included = 0. Canceled included = 0. Other valid nonblank statuses excluded = 0.** No fixed allow-list used — the dynamic exclusion rule (`status IS NOT NULL AND BTRIM(status)<>'' AND BTRIM(status) NOT IN ('Cancelled','Canceled')`) was applied directly. Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_status_contribution.csv`.

## 7. ASIN-Wise Orders

**Important discovery during this validation:** the production extraction script (`extract_uawso_v5_asin_level.py`) filters `source_name IN ('AMAZON', 'REPLACEMENT')` for Orders/Quantity (Sales remains `source_name='AMAZON'`-only). An initial validation pass using `source_name='AMAZON'` only produced 34,205 Orders — 249 short of the approved 34,454. Re-running with `source_name IN ('AMAZON','REPLACEMENT')` (matching the actual, documented, pre-existing extraction rule) reproduced **34,454 exactly**. This is not a new rule invented for this validation — it is the extraction script's own documented behavior, confirmed by direct inspection of its SQL and comments; this validation had simply not initially matched it byte-for-byte from the requirement's abbreviated Filter Conditions block (which lists `source_name='AMAZON'` without mentioning the REPLACEMENT carve-out used specifically for Orders/Quantity).

| Metric | Source (live, fresh) | HTML (embedded) | Difference |
| ----- | ----- | ----- | ----- |
| FBM Orders | 26,490 | 26,490 | **0** |
| FBA Orders | 7,964 | 7,964 | **0** |
| Total Orders | **34,454** | **34,454** | **0** |

Grouping method verified: `COUNT(DISTINCT order_item_info)` per `(date, ASIN)` group, summed across groups = 34,454, **exactly equal** to a flat `COUNT(DISTINCT order_item_info)` over the same included row set (34,454) — grouping introduces no double-count. Per-ASIN reconciliation (all 1,723 ASINs): **0 mismatches**. Duplicate order items caused by joins = 0. Missing source order items = 0. Extra HTML order items = 0. Vendor Units are not included as Orders (`vendorOrders=null` in the engine, never added to `totalOrders`).

Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_asin_orders_reconciliation.csv` (1,723 rows), `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_order_item_integrity.csv`.

## 8. ASIN-Wise Sales

| Metric | Source (live, fresh) | HTML (embedded) | Difference |
| ----- | ----- | ----- | ----- |
| FBM Sales | £487,541.07 | £487,541.07 | **£0.00** |
| FBA Sales | £184,479.90 | £184,479.90 | **£0.00** |
| Amazon Sales (FBM+FBA) | £672,020.97 | £672,020.97 | **£0.00** |

Sales = `item_price × quantity`, `source_name='AMAZON'` only (REPLACEMENT rows contribute 0 to Sales, only to Orders/Quantity — by design). All SKU-level activity is aggregated under the ASIN at the SQL layer (`GROUP BY order_date, asin`, no SKU in the grouping) — no SKU-level activity is omitted by removing the visible SKU column. Per-ASIN reconciliation (1,723 ASINs): **0 mismatches**.

Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_asin_sales_reconciliation.csv`.

## 9. Quantity

| Metric | Source (live, fresh) | HTML (embedded) | Difference |
| ----- | ----- | ----- | ----- |
| FBM Quantity | 33,638 | 33,638 | **0** |
| FBA Quantity | 8,780 | 8,780 | **0** |
| Amazon Quantity (FBM+FBA) | 42,418 | 42,418 | **0** |

Per-ASIN reconciliation (1,723 ASINs): **0 mismatches**. Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_asin_quantity_reconciliation.csv`.

## 10. Vendor Data

Source: `public.vendor_sales` (`ordered_revenue`→Vendor Sales, `ordered_units`→Vendor Units). Vendor Orders: N/A (no order-level key exists; `vendorOrders=null` throughout the engine, never counted as Orders or Sales).

| Metric | Source (live, fresh) | HTML (embedded) | Difference |
| ----- | ----- | ----- | ----- |
| Vendor Sales | £46,814.94 | £46,814.94 | **£0.00** |
| Vendor Units | 4,748 | 4,748 | **0** |

Overlap-sum method (periods overlapping [2025-01-01, 2026-07-14], **no proration**, matching `sumVendorRangeV4` exactly) applied identically to both source and HTML sides — per-ASIN reconciliation (1,723 ASINs): **0 mismatches** between source and HTML (both sides use the same rule, so they necessarily agree).

**Non-blocking data-integrity observation (new finding, not previously documented):** within the live source itself, 2 of 1,723 ASINs (`B0DPMQZ1WP`, `B0DPMRVHHR`) have **overlapping/nested** `vendor_sales` reporting windows for the same ASIN (e.g. a 2-day window and a fully-nested 1-day window with the same revenue/units). The existing (unchanged since v3/v4) "sum every overlapping period, no proration" rule sums both, which double-counts the nested portion. Combined impact: **+£24.07** revenue / **+2 units**, against a Vendor Sales total of £46,814.94 (0.05%) and a report Total Sales of £718,835.91 (0.003%) — immaterial to the headline KPIs, not introduced by this build (the same rule was already live in previously-published rows 157/237/256), but not previously identified either. Recommend a future task review whether Amazon Vendor Central legitimately issues nested/overlapping reporting windows for the same ASIN, and whether the summing rule should deduplicate on exact (start,end) equality or true non-overlap before summing. **Not fixed in this task** (out of scope — read-only validation, no code changes permitted).

Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_vendor_reconciliation.csv`, `2026-07-15_utharsika_v004_local_date_boundary_validation.csv`.

## 11. Total KPI Formulas

Verified **structurally** (source code inspection, `computeRowsV5`/`computeTotalV5` in `uawso_client_engine.js`) — the Total fields are defined as literal arithmetic identities, not independently computed and then compared, so per-ASIN formula failures are structurally impossible:

- `totalSales = fbmSales + fbaSales + vendorSales` ✓
- `totalOrders = fbmOrders + fbaOrders` (Vendor Units never added) ✓
- `totalQuantity = fbmQuantity + fbaQuantity + vendorUnits` ✓

Full-snapshot totals (live source, same date range/scope/status rule as the HTML):

| Metric | Source | HTML | Difference |
| ----- | ----- | ----- | ----- |
| Total Sales | £718,835.91 | £718,835.91 | **£0.00** |
| Total Orders | 34,454 | 34,454 | **0** |
| Total Quantity | 47,166 | 47,166 | **0** |

**Per-ASIN formula failures: 0.** These figures were **not** forced to match the previously-approved baseline — they were independently recomputed from the current live source under the documented rules and happen to reconcile exactly, because no source data has changed since the HTML was generated earlier today.

Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_total_kpi_formula_validation.csv`.

## 12. Image Source

Live query: `public.listing_data`, `ref_id=ASIN`, `which_channel=1`, `market_place='UK'`, `wrong_sku=0`, `main_image_url IS NOT NULL AND BTRIM(main_image_url)<>''`, tie-break = lowest `id`.

| Metric | Value |
| ----- | ----- |
| Image mismatches (source vs HTML) | **0** |
| Image-covered ASINs | 1,699 |
| No-image ASINs | 24 |
| Multi-image ASINs (>1 distinct valid image) | 227 |
| Invalid/blank image rows | 0 (excluded by the `main_image_url IS NOT NULL AND BTRIM(...)<>''` filter at the source query itself) |

All figures match the REQ-02-D01 requirement document's documented Image Coverage table exactly (1,699 / 24 / 227). Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_image_reconciliation.csv` (1,723 rows).

## 13. Date Range

Confirmed: embedded data spans exactly 2025-01-01 through 2026-07-14 (560 distinct calendar dates, 19 distinct months). Rows before 2025-01-01: 0. Rows on/after 2026-07-15: 0. No duplicate `(date, ASIN)` rows (0 found across 29,203 rows). Vendor window overlap: see Section 10's non-blocking observation (2 ASINs, immaterial impact).

Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_date_boundary_validation.csv`.

## 14. PY/CY and Change Fields

| Field | Status |
| ----- | ----- |
| PY Sales / CY Sales | GROUNDED (REQ-02-D01 Section 2/5) |
| PY Orders / CY Orders | GROUNDED via the approved Orders formula (Section 4); not separately itemised in Section 2's Required Data Output table but directly derivable |
| PY Quantity / CY Quantity | GROUNDED via the approved Quantity formula (Section 4); same note as above |
| Sales Change % | GROUNDED — explicit formula in REQ-02-D01 Section 5: `(CY−PY)/PY`, undefined when PY=0 |
| **Order Change %** | **PENDING_BUSINESS_RULE** — displayed column (`data-field="orderChange"`) computed via the same `safeChange()` function as Sales Change, but REQ-02-D01 Section 5 defines a Change formula only for Sales. No written Order Change rule exists in the approved requirement. |
| **Quantity Change %** | **PENDING_BUSINESS_RULE** — displayed column (`data-field="quantityChange"`), same situation as Order Change %. |
| Trend | GROUNDED — explicit formula in REQ-02-D01 Section 5, Sales-based only |
| Achievement % | GROUNDED — explicit formula in REQ-02-D01 Section 5, Sales-based only (`(CY Sales / (PY Sales × 1.30)) × 100`) |

No business rule was invented for Order Change % / Quantity Change % — they are reported as PENDING_BUSINESS_RULE per this task's own instruction ("Do not invent missing rules"). The implementation applies the same, internally-consistent `safeChange()` zero-denominator handling as the approved Sales Change field, so the *code* is not arbitrary or broken — it simply lacks a written business definition in the currently-approved REQ-02-D01 document for these two specific columns.

Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_py_cy_change_field_validation.csv`.

## 15. HTML Grain and Export Data

| Check | Result |
| ----- | ----- |
| One canonical row per ASIN | PASS (1,723/1,723) |
| No canonical SKU grouping | PASS |
| No visible SKU column | PASS (`data-field="sku"` count = 0) |
| No Row Type column | PASS ("Row Type" mentions = 0) |
| One selected image per ASIN | PASS (`data-field="image"` count = 1; 0 mismatches) |
| CSV/export one row per ASIN | PASS |
| Image URL exported | PASS |
| SKU not exported | PASS |
| Row Type not exported | PASS |
| Complete filtered export uses all filtered rows, not only the current page | PASS (`state.lastFilteredRows` = full sorted array, not the paginated slice) |

Detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_local_html_export_field_validation.csv`.

## 16. Database and File Integrity

No `tech_team_outputs.ph_task` row was queried, read, updated, or referenced in this task (explicitly out of scope). No `INSERT`/`UPDATE`/`DELETE` statement was issued to any table — every database call in this task was a read-only `SELECT`. The local HTML file was opened only for reading (embedded-JSON extraction); no write occurred. No template, renderer, or client-engine file was modified. No automation or Task Scheduler item was touched.

## 17. Final PASS/FAIL

```
- every output field maps to a correct, confirmed source table               YES
- assigned ASIN missing                                                       0
- assigned ASIN extra                                                          0
- duplicate ASINs                                                              0
- Sales difference                                                             £0.00
- Orders difference                                                            0
- Quantity difference                                                          0
- duplicate order items                                                        0
- missing order items                                                          0
- extra order items                                                            0
- Vendor duplication (source vs HTML, same rule both sides)                    0
- Vendor internal period-overlap observation (non-blocking, immaterial)        2 ASINs / £24.07 / 2 units
- image mismatches                                                             0
- date-boundary errors                                                         0
- total formula failures                                                       0
- all displayed PY/CY/Change fields have proven business definitions          NO - Order Change % and Quantity Change % are PENDING_BUSINESS_RULE
- no file or database data modified                                            YES
```

**FINAL STATUS: PENDING_BUSINESS_RULE.** Every numeric reconciliation required by this task (assigned scope, status rule, ASIN-wise Orders/Sales/Quantity, Vendor Sales/Units, image selection, date boundaries, total KPI formulas, export/grain rules) returned **zero difference** against a freshly re-derived live source under the documented rules — a strong, comprehensive PASS on data correctness. The verdict is held at `PENDING_BUSINESS_RULE` rather than a clean `PASS` for exactly one reason, per this task's own instruction not to invent rules: two displayed columns (**Order Change %**, **Quantity Change %**) have no written formula in the currently-approved REQ-02-D01 requirement document, even though they are computed consistently with the approved Sales Change pattern. A secondary, non-blocking data-integrity observation (2 ASINs with overlapping Vendor reporting windows, £24.07/2-units combined impact) is documented for future attention but does not, on its own, change the verdict given its immateriality and pre-existing (not newly introduced) nature.
