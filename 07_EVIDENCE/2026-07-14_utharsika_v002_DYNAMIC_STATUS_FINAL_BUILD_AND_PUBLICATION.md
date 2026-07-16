# UAWSO — Final Dynamic-Status Build and Publication (`2026-07-14_utharsika_v002.html`)

**What this asset is:** The final business rule (include every non-null, non-blank order status except the two cancellation variants, with no hardcoded include-list) implemented in code, freshly extracted, built to `09_OUTPUTS\2026-07-14_utharsika_v002.html`, fully validated, and published to the existing `ph_task` row (id=237).

**Owner:** Satheskanth
**Status:** **PASS** — built, validated, published.

---

## 1. Status Discovery (fresh, this task)

```sql
SELECT status, COUNT(*), COUNT(DISTINCT order_item_info), SUM(COALESCE(quantity,0)),
       SUM(COALESCE(item_price,0)*COALESCE(quantity,0))
FROM public.order_transaction GROUP BY status ORDER BY status;
```

| Status | Row count | Distinct order items | Quantity | Sales |
|---|---|---|---|---|
| Canceled | 1,395 | 1,395 | 270 | £88.47 |
| Cancelled | 10,632 | 10,632 | 5,452 | £101,849.51 |
| Completed | 1,198,909 | 1,198,909 | 1,945,069 | £25,172,631.08 |
| Deleted | 1,615 | 1,615 | 3,843 | £41,341.57 |
| Hold | 3 | 3 | 7 | £145.03 |
| Inprogress | 9 | 9 | 10 | £400.72 |
| New | 416 | 416 | 692 | £10,010.35 |
| Pending | 58 | 58 | 83 | £898.49 |
| Refunded | 20,108 | 20,108 | 36,770 | £557,308.41 |

**Null status count: 0. Blank status count: 0.** **9 total distinct statuses — no status beyond the previously-known 9 was discovered.** No status was omitted for any reason other than being a cancellation variant or null/blank (there were none of the latter to omit).

## 2. Dynamic Status Rule

```sql
status IS NOT NULL
AND BTRIM(status) <> ''
AND BTRIM(status) NOT IN ('Cancelled', 'Canceled')
```

**Included (7, discovered automatically, not hardcoded):** Completed, Refunded, Deleted, New, Pending, Inprogress, Hold
**Excluded (2, the only hardcoded values in the system):** Cancelled, Canceled

## 3. Implementation Files Changed

| File | Change |
|---|---|
| `05_IMPLEMENTATION/src/extract_uawso_v4_ordered_sales.py` | Replaced the fixed `APPROVED_STATUSES` tuple and `order_status IN %(statuses)s` clauses with `EXCLUDED_ORDER_STATUSES = {"Cancelled", "Canceled"}`, an `is_included_order_status()` Python helper, and a single shared `STATUS_FILTER_SQL` fragment (`status IS NOT NULL AND BTRIM(status) <> '' AND BTRIM(status) NOT IN ('Cancelled','Canceled')`) used identically in both the product-master SKU-discovery query and the daily-aggregates query — no second, independently-maintained status rule exists anywhere in this file. |
| `05_IMPLEMENTATION/src/uawso_client_engine.js` | Added `EXCLUDED_ORDER_STATUSES` (a `Set`) and `isIncludedOrderStatus(value)`, exported from the engine's returned object. This mirrors the SQL-side rule exactly. It is not on the current hot path (status filtering already happens server-side in SQL before the daily-aggregates JSON is embedded), but is exposed for any future client-side status filter so it would reuse the exact same rule rather than a second list. |

No other file required changes (`templates/uawso_report_template_v4.html`, `dashboard_renderer.py`, and the generator driver all operate on whatever the extraction produces).

## 4. Data Range and Scope

| Check | Result |
|---|---|
| Data range | **2025-01-01 → 2026-07-13 inclusive** |
| Minimum embedded date | 2025-01-01 |
| Maximum embedded date | 2026-07-13 |
| Distinct months | **19** |
| Assigned ASIN count | **1,723** |
| Raw vs distinct assignment count | 1,723 = 1,723 (0 duplicates) |
| `order_transaction` source rows (qualifying, Utharsika scope) | 34,413 |
| `vendor_sales` source rows (Utharsika scope, all time) | 960 |
| Duplicate `order_item_info` after scope join | **0** |
| Other-user ASINs included | **0** |

## 5-10. Sales / Orders / Quantity / Vendor Rules

Unchanged in substance from the prior fixed-list build (Sales = `item_price × quantity` for AMAZON rows with an included status; Orders = `COUNT(DISTINCT order_item_info)` for AMAZON/REPLACEMENT rows with an included status; Quantity = same scope as Orders + Vendor Units; Vendor Orders = N/A; the `periodsOverlapV4`/`sumVendorRangeV4` boundary fix remains active and unmodified) — only the **status-selection mechanism** changed, from a fixed list to dynamic exclusion.

## 11. Final Output

| | |
|---|---|
| Path | `09_OUTPUTS\2026-07-14_utharsika_v002.html` |
| Pre-existing hash at this path before this task | **none — file did not exist** |
| SHA-256 (after generation) | `16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684` |
| Size | 5,428,696 bytes |
| Contains `2026-07-13` marker | YES |
| Temporary `2026-07-14_utharsika_new_v002.html` removed | **YES**, after all validation passed |

## 12. Output Grain

| Check | Result |
|---|---|
| Assigned ASINs represented | 1,723 |
| Total output rows | 2,575 (2,138 ASIN+SKU + 105 no-SKU + 332 Vendor) |
| Duplicate ASIN–SKU pairs | **0** |
| Rows with concatenated SKUs | **0** |
| Missing order items | **0** |
| Extra order items | **0** |
| Duplicate order items | **0** |
| Vendor values counted once | YES (ASIN-level, `isVendorRow` gating unchanged) |

## 13. Report Features

Daily, Weekly, Month, MTD, Custom modes; ASIN/SKU multi-select with search/select-all/clear-all; pagination; KPI cards; table footer; filtered CSV; full-dataset CSV — all unchanged from the validated v4 template, all confirmed operating on the same `computeTotalV4`/row objects (Section 13 below).

## 14. All-19-Month Reconciliation

Full detail: `07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_dynamic_status_monthly_reconciliation.csv`.

**Every one of the 19 months reconciles to exactly £0.00 Sales difference, 0 Orders difference, 0 Quantity difference** between a fresh PostgreSQL query and the final HTML's embedded engine/data (dashboard and CSV totals are identical to the HTML total by construction).

**Full-period total** (single continuous query): Amazon Sales £671,202.03, Vendor Sales £46,792.53, Total Sales £717,994.56, Total Orders 34,413, Total Quantity 47,117 — PostgreSQL and HTML agree exactly. (As previously documented, this figure is not the sum of the 19 monthly Vendor columns, due to the well-understood month-boundary-crossing Vendor period behavior — not a defect.)

## 15. Reference Validation (validation only)

`02_SOURCE\user_provided\2026-07-14_utharsika_june_kpi_reference_b02.csv` — full detail: `07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_dynamic_status_reference_reconciliation.csv`. **6 of 7 rows PASS exactly; row 2 (`B0GY3G4S1F`) remains `MAPPED_SKU_MATCH_ONLY`**, unchanged from every prior validation of this reference file. The generated dataset was never restricted to these 7 rows.

## 16. Exact ASIN Check — B0FX2QT3B1, June 2026

| Metric | Value |
|---|---|
| Sales | £726.65 |
| Orders | 23 |
| Quantity | 27 |

**Status contribution:** Completed (AMAZON, exact-pair SKU) = £699.76 / 21 orders / 24 quantity. Refunded (AMAZON, exact-pair SKU) = £26.89 Sales + 1 Order + 1 Quantity (newly counted as an Order under the current rule, since Refunded is an included status). Completed (REPLACEMENT, `RPR44WH` SKU) = £0.00 / 1 order / 2 quantity. No Deleted/New/Pending/Inprogress/Hold activity exists for this ASIN in June 2026. **Not forced to any previous value** — identical to the immediately-prior two builds, confirming consistency.

## 17. Publication

Updated the **existing** `ph_task` row (id=237, task_id=`UAWSO-2026-07-14-utharsika-v002`) inside an explicit transaction. Only `html_content` and `updated_at` were changed.

| Field | Before | After |
|---|---|---|
| id | 237 | 237 (unchanged) |
| task_id | UAWSO-2026-07-14-utharsika-v002 | unchanged |
| project_code | UAWSO | unchanged |
| assigned_user | utharsika | unchanged |
| assigned_user_team | ph_priors | unchanged |
| version_level | 2 | **2 (unchanged)** |
| html SHA-256 | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` | **`16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684`** |
| updated_at | 2026-07-14 15:54:10.089775+05:30 | **2026-07-14 18:01:26.353217+05:30** |

**Pre-commit checks (all 8 passed):** hash matches local; `assigned_user`/`project_code`/`version_level` correct; `2026-07-13` marker present; row 157's `task_id`, hash, and `updated_at` all confirmed unchanged **within the same transaction**, before commit.

**Row 157 (untouched, confirmed both before and after commit):**

| Field | Value |
|---|---|
| task_id | UAWSO-2026-07-10-utharsika-v001 (unchanged) |
| html SHA-256 | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` (unchanged) |
| updated_at | 2026-07-14 15:06:09.792767+05:30 (unchanged) |

**No new row was inserted.** Total UAWSO rows after commit: **2** (157 + 237, unchanged count).

## v001 / Frozen v002 — Confirmed Unchanged

| File | SHA-256 |
|---|---|
| `09_OUTPUTS\2026-07-10_utharsika_v001.html` | `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` |
| `09_OUTPUTS\2026-07-10_utharsika_v002.html` | `0a7c304ba88cd6acedf26294b1f58d1dc4fe727aff1e93466aa0cb307321ca72` |

## Evidence Outputs

| File | Purpose |
|---|---|
| `07_EVIDENCE\2026-07-14_utharsika_v002_DYNAMIC_STATUS_FINAL_BUILD_AND_PUBLICATION.md` | This file |
| `07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_dynamic_status_monthly_reconciliation.csv` | 19-month + full-period reconciliation |
| `07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_dynamic_status_reference_reconciliation.csv` | 7-row reference validation |

## Final Verdict: **PASS**

Every non-blank status except Cancelled/Canceled is included, via dynamic exclusion logic (not a hardcoded list); no status was omitted for any other reason; the full 2025-01-01→2026-07-13 range is covered; 1,723 assigned ASINs represented; all 19 months reconcile exactly; missing/extra/duplicate order items are all zero; the final file was written to the correct designated path; the temporary candidate was removed after validation; the existing row 237 was updated in place (html_content/updated_at only); no new row was inserted; row 157 is confirmed unchanged; and stored/local hashes match exactly.
