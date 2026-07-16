# UAWSO — Fresh Complete Historical Rebuild (`new_v002`) Validation

**What this asset is:** A completely fresh, independent read-only extraction and build of a **new, separate** local candidate report — `09_OUTPUTS\2026-07-14_utharsika_new_v002.html` — covering the full 2025-01-01 → 2026-07-13 historical range under the seven-approved-status rule. This does **not** overwrite `v001` or the existing `v002`, and does **not** touch `ph_task`.

**Owner:** Satheskanth
**Status:** **PASS**

---

## 1. Pre-Build Safety Check

| Check | Result |
|---|---|
| Project root | `C:\Users\LED237\Documents\Projects\Weekly and Day Wise Filter monthly` (confirmed via `pwd`) |
| `v001.html` SHA-256 (before) | `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` |
| Existing `v002.html` SHA-256 (before) | `0a7c304ba88cd6acedf26294b1f58d1dc4fe727aff1e93466aa0cb307321ca72` (the seven-status local refresh from the immediately prior task) |
| `new_v002.html` exists before build? | **NO** (confirmed absent) |
| `ph_task` id=157 hash / updated_at (before) | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` / 2026-07-14 15:06:09.792767+05:30 |
| `ph_task` id=237 hash / updated_at (before) | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` / 2026-07-14 15:54:10.089775+05:30 |
| Database write planned | **NO** — read-only extraction only |

Note: `ph_task` rows 157/237 still carry the **older, pre-seven-status** hash (`60bc...`), confirming the seven-status local refresh from the prior task was never published — consistent with that task's explicit no-publish instruction.

## 2. Complete Historical Extraction (fresh, not cached)

A brand-new extraction identity (`2026-07-14_utharsika_new_v002`) was used — this does **not** reuse or read any JSON file from the existing `2026-07-10_utharsika_v002` identity. All four extraction queries (assigned-ASIN resolution, product master, daily aggregates, Vendor periods) were re-executed against PostgreSQL from scratch.

| Metric | Value |
|---|---|
| `order_transaction` source rows (Utharsika scope, 7 approved statuses, full range) | **34,413** |
| `vendor_sales` source rows (Utharsika scope, all time) | **960** |
| Minimum included `order_date` | **2025-01-01 00:56:35** |
| Maximum included `order_date` | **2026-07-13 23:45:47** |
| Extraction timestamp | 2026-07-14 (this session) |
| Distinct months represented | **19** — 2025-01 through 2026-07 (2026-07 capped at the 13th) |

Extraction was **not** restricted to June, and **not** restricted to the 7 reference ASINs — the full 1,723-ASIN assigned scope and full date range were fetched in every query.

## 3. Utharsika Assigned Scope

| Check | Result |
|---|---|
| Raw assignment count | 1,723 |
| Distinct assigned ASIN count | **1,723** |
| Duplicate assigned ASINs (raw vs distinct) | 0 |
| Transaction rows before scope join (UK, 7 statuses, full range, all users) | not separately measured this run (measured in the prior status-discovery task); scope join itself re-validated below |
| Transaction rows after scope join | 34,413 |
| Duplicate `order_item_info` after join | **0** |

## 4. Approved Status Scope

Included: `Completed, Refunded, Deleted, New, Pending, Inprogress, Hold`. Excluded: `Cancelled, Canceled`. No null, blank, or unknown status included (confirmed absent from the table in the prior discovery task).

## 5-8. Sales / Orders / Quantity / Vendor Rules

Identical, unchanged rule set from the immediately prior seven-status validation task (same `extract_uawso_v4_ordered_sales.py`, same `uawso_client_engine.js` including the `periodsOverlapV4`/`sumVendorRangeV4` boundary fix, same `uawso_report_template_v4.html`):

- Sales = `SUM(item_price × quantity)`, `source_name='AMAZON'`, status IN 7 approved statuses (order_total never used as the primary Sales field; refunded value never deducted).
- Orders = `COUNT(DISTINCT order_item_info)`, status IN 7 approved statuses, `source_name IN ('AMAZON','REPLACEMENT')`. Total Orders = FBM Orders + FBA Orders. Vendor Units never added.
- Quantity: same row scope as Orders, FBM/FBA; Total Quantity = FBM + FBA + Vendor Units. Vendor Orders = N/A throughout.
- Vendor: `ordered_revenue`/`ordered_units`, corrected half-open overlap test (a period ending exactly at the next period's start is not double-counted), ASIN-level only, never duplicated across SKU rows.

## 9. Output Grain

| Check | Result |
|---|---|
| Assigned ASINs represented | **1,723** |
| Total output rows | **2,575** (2,138 ASIN+SKU rows + 105 no-SKU rows + 332 Vendor rows) |
| Duplicate ASIN–SKU pairs | **0** |
| Rows containing multiple (comma-joined) SKUs | **0** |
| Vendor rows | ASIN-level only, one dedicated row per ASIN with Vendor data, never duplicated across SKU rows |

## 10. New Output

| | |
|---|---|
| Path | `09_OUTPUTS\2026-07-14_utharsika_new_v002.html` |
| SHA-256 | `01d8986e0bbbd083eae4bf1e70e56799d6bb6c30c99922c8ff10f3884d190b8e` |
| Size | 5,427,582 bytes |
| Embedded history | 2025-01-01 → 2026-07-13 (confirmed via embedded `HISTORY_START`/`HISTORY_END`/`SELECTABLE_END`/`LATEST_COMPLETED` markers, all present in the file) |

This is a genuinely fresh build (new PostgreSQL extraction under a new identity, not a copy of the existing v002's embedded JSON) that happens to produce figures **identical** to the immediately-prior seven-status validation — this is the expected, correct outcome, since both builds query the same underlying database, minutes apart, using the same approved rule, and confirms reproducibility rather than indicating anything was skipped.

## 11. Date Filter Modes

| Mode | Result |
|---|---|
| Daily | ✅ resolves correctly (tested 2026-06-15) |
| Weekly | ✅ (tested week of 2026-06-15) |
| Month | ✅ (tested 2026-06 and 2026-01; both resolve, with correct previous-year mapping to 2025-01/2025-06) |
| MTD | ✅ resolves to 2026-07-01 → **2026-07-13** (confirming the maximum selectable date is 2026-07-13, as required) |
| Custom | ✅ (tested 2026-07-01 → 2026-07-13) |
| Out-of-range guard | ✅ confirmed — selecting 2025-01-01 as a *current*-period Daily date correctly errors ("outside the selectable current-period range"), since the selectable current-period window is 2026-01-01→2026-07-13; 2025-01-01 remains reachable only as a *previous-year comparison* date (confirmed via the January 2026 Month-mode test, which correctly resolves its PY period to 2025-01-01→2025-01-31) |

**Maximum selectable date confirmed: 2026-07-13.**

## 12. Complete Monthly Reconciliation

Full detail: `07_EVIDENCE\generated_data\2026-07-14_utharsika_new_v002_all_months_reconciliation.csv`.

**All 19 months (2025-01 through 2026-07, capped at the 13th) reconcile to exactly £0.00 Sales difference, 0 Orders difference, 0 Quantity difference** between a fresh direct PostgreSQL query and the new_v002 HTML's own embedded engine/data (dashboard-computed and CSV totals are identical to the HTML total by construction — same `computeTotalV4` object feeds all three).

**Full-period total** (single continuous 2025-01-01→2026-07-13 query): Amazon Sales £671,202.03, Vendor Sales £46,792.53, Total Sales £717,994.56, Total Orders 34,413, Total Quantity 47,117 — PostgreSQL and HTML agree exactly on every figure.

**Row-level integrity:** missing `order_item_info` = 0; extra `order_item_info` = 0; duplicate `order_item_info` = 0 (re-confirmed via the same duplicate-check query used in the prior task, re-run fresh against this task's own extraction).

## 13. Reference CSV (validation only, not a scope restriction)

`02_SOURCE\user_provided\2026-07-14_utharsika_june_kpi_reference_b02.csv` (7 rows) was used **only** to validate June 2025/2026 values after the complete 1,723-ASIN, full-date-range dataset was built — the generated dataset was never restricted to these 7 rows. Full detail: `07_EVIDENCE\generated_data\2026-07-14_utharsika_new_v002_reference_reconciliation.csv`.

**Result: identical to the prior validation** — 6 of 7 rows PASS exactly; row 2 (`B0GY3G4S1F`) remains `MAPPED_SKU_MATCH_ONLY` (supplied SKU has zero transactions system-wide; the Mapped SKU `LSGL1275CL3PK+RPM40WH3PK` carries the reference's June 2026 value exactly).

## 14. Exact ASIN Validation — B0FX2QT3B1, June 2026 (fresh extraction)

| Metric | Value |
|---|---|
| Sales | **£726.65** |
| Orders | **23** |
| Quantity | **27** |

**Status contribution:** Completed (AMAZON, exact-pair SKU) = £699.76 / 21 orders / 24 quantity. Refunded (AMAZON, exact-pair SKU, `order_item_info=1178915`) = £26.89 Sales (already included under both rules) **and, under this rule, +1 Order / +1 Quantity** (newly counted, since Refunded is one of the seven approved statuses for Orders). Completed (REPLACEMENT, `RPR44WH` SKU) = £0.00 Sales / 1 order / 2 quantity. No Deleted/New/Pending/Inprogress/Hold rows exist for this ASIN in June 2026. **These values are reported as-is from the fresh extraction, not forced to match any earlier figure** — they are identical to the immediately-prior seven-status task's result, confirming consistency between the two independent builds.

## 15. No Publication — Confirmed

| Check | Before this task | After this task |
|---|---|---|
| `ph_task` id=157 hash | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` | **unchanged** |
| `ph_task` id=157 `updated_at` | 2026-07-14 15:06:09.792767+05:30 | **unchanged** |
| `ph_task` id=237 hash | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` | **unchanged** |
| `ph_task` id=237 `updated_at` | 2026-07-14 15:54:10.089775+05:30 | **unchanged** |
| `ph_task` writes performed | — | **0** |
| New row inserted | — | **NO** |
| `version_level` changed | — | **NO** |
| Scheduler touched | — | **NO** |

## Existing Files — Confirmed Unchanged

| File | SHA-256 |
|---|---|
| `09_OUTPUTS\2026-07-10_utharsika_v001.html` | `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` (unchanged) |
| `09_OUTPUTS\2026-07-10_utharsika_v002.html` | `0a7c304ba88cd6acedf26294b1f58d1dc4fe727aff1e93466aa0cb307321ca72` (unchanged) |

## Evidence Outputs

| File | Purpose |
|---|---|
| `07_EVIDENCE\2026-07-14_utharsika_new_v002_COMPLETE_HISTORICAL_REBUILD_VALIDATION.md` | This file |
| `07_EVIDENCE\generated_data\2026-07-14_utharsika_new_v002_all_months_reconciliation.csv` | 19-month + full-period PG/HTML reconciliation, row-level integrity |
| `07_EVIDENCE\generated_data\2026-07-14_utharsika_new_v002_reference_reconciliation.csv` | 7-row reference CSV validation (validation-only, not a scope restriction) |

## Final Verdict: **PASS**

Fresh PostgreSQL extraction covers the full 2025-01-01→2026-07-13 range, not restricted to June or the 7 reference ASINs; all 1,723 assigned ASINs represented; all seven approved statuses included, both cancellation statuses excluded; all 19 monthly periods (plus the full-period total) reconcile exactly with zero Sales/Orders/Quantity difference; missing/extra/duplicate order items are all zero; `v001` and the existing `v002` remain byte-for-byte unchanged; and zero `ph_task` writes occurred (confirmed by hash and `updated_at` comparison before and after).
