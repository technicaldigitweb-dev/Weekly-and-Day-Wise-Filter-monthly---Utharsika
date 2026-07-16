# UAWSO — Fresh 2026-07-16_utharsika_v001 Report (AMAZON-Only Orders Business-Rule Update)

**Target (new file, never existed before):** `09_OUTPUTS\2026-07-16_utharsika_v001.html`
**Business-rule update:** `01_REQUIREMENTS\Requirement Updates\2026-07-16_satheskanth_REQ-UAWSO_REQ-02-D01_amazon_only_orders_update.md`
**Execution date:** 2026-07-16
**Publication:** Not performed — `ph_task` was not accessed or modified in this task, per explicit instruction.

---

## 1. Protected Assets

| Item | Hash | Confirmed unchanged at end of task |
| ----- | ----- | ----- |
| `01_REQUIREMENTS\Requirement\2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md` | `f652d51fb6c77e3b1512a8078c86afe6e1726a86f7c43f5ca58259d2dfb14ea5` | YES |
| `09_OUTPUTS\2026-07-15_utharsika_v004.html` | `d8ab5b255619bf188acfa7044679e7c60bff0cef4d8d52717483e49ef1f4999d` | YES |
| `09_OUTPUTS\2026-07-09_utharsika_v001.html` | `52667eebadb04234f098af67d48d6005402f36e9f4e7b9e7ecdeb0cdc736aa9b` | YES |
| `09_OUTPUTS\2026-07-10_utharsika_v001.html` | `335e65f8e922a052a7cb96def3f63172e21d8b8cb39f4c2a85abdf43a3c4e1c4` | YES |
| `09_OUTPUTS\2026-07-10_utharsika_v002.html` | `0a7c304ba88cd6acedf26294b1f58d1dc4fe727aff1e93466aa0cb307321ca72` | YES |
| `09_OUTPUTS\2026-07-14_utharsika_v002.html` | `16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684` | YES |

**Disclosure:** an earlier turn in this same session (before this task's explicit "do not modify the approved requirement" correction) briefly inserted a Section 3.3 amendment directly into `2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md`. That edit was fully reverted (exact-text removal, restoring the file to its prior content) **before** this task's baseline hash above was captured — the hash shown is the file's correct, restored, protected state, and it has not been touched again since.

## 2. Business-Rule Update File

Created (new folder, since no existing requirement-changes/addenda folder was found under `01_REQUIREMENTS\`): `01_REQUIREMENTS\Requirement Updates\2026-07-16_satheskanth_REQ-UAWSO_REQ-02-D01_amazon_only_orders_update.md`. Full content: reason for change, prior rule, new rule, evidence paths, impacted files, validation rule, known limits, next step — per the required structure.

## 3. Old Rule vs New Rule

| | Old | New |
| ----- | ----- | ----- |
| FBM/FBA Orders source | `source_name IN ('AMAZON', 'REPLACEMENT')` | `source_name = 'AMAZON'` only |
| Cancellation exclusion | `BTRIM(order_status) NOT IN ('Cancelled','Canceled')` | Unchanged |
| Vendor Orders | `= public.vendor_sales.ordered_units` | Unchanged |
| Total Orders | FBM + FBA + Vendor Orders | Unchanged formula, corrected inputs |
| Sales source | `source_name = 'AMAZON'` | Unchanged |

## 4. Changed Active Source Files

| File | Change |
| ----- | ----- |
| `05_IMPLEMENTATION\src\extract_uawso_v5_asin_level.py` | The daily-aggregates query's `WHERE` clause changed from `ot.source_name IN ('AMAZON', 'REPLACEMENT')` to `ot.source_name = 'AMAZON'`. This is the single query that produces `fbm_orders`/`fba_orders` for every downstream stage (Sales' own inner `source_name='AMAZON'` filter was already correct and unaffected). Docstring updated to document the new rule and reference the update file. |
| `05_IMPLEMENTATION\templates\uawso_report_template_v5_asin_level.html` | Two methodology notes (Data Coverage Notes "Total Orders rule", footer "FBM/FBA Orders" bullet) updated to state `source_name='AMAZON'` only, referencing the 2026-07-16 update. |
| `05_IMPLEMENTATION\src\uawso_client_engine.js` | **Not changed** — the client engine has no `source_name` logic of its own; it only sums whatever `fbm_orders`/`fba_orders` values are already present in the embedded JSON (already-corrected by the extraction script). |

**Not changed (correctly, per instruction to only touch active v5 logic, not archived/historical scripts):** `05_IMPLEMENTATION\templates\uawso_report_template.html` (the old v4 template baked into the frozen v002 HTML files), `05_IMPLEMENTATION\src\extract_uawso_v4_ordered_sales.py` (v4 extraction, used only by the frozen v002 reports), and one-off historical diagnostic scripts under `05_IMPLEMENTATION\tests\validate_*.py` (`validate_kpi_reference_b02.py`, `validate_seven_status_refresh.py`, `validate_phase3_8.py` — prior investigative artifacts, not part of the active regression suite).

## 5. B0FX2XDLT5 June 2026 Reconciliation

| Metric | Value |
| ----- | ----- |
| Raw AMAZON-source distinct order items | 17 |
| Cancelled (excluded) | 1 |
| Valid FBM Orders | 14 |
| Valid FBA Orders | 2 |
| **Valid Amazon Orders** | **16** |
| REPLACEMENT-source rows contributing to the count | **0** |

Verified twice independently: once via a direct, focused SQL query (`05_IMPLEMENTATION\src\regression_check_B0FX2XDLT5_amazon_only.py`) before extraction, and once by reading the actual embedded `daily_aggregates_asin` JSON from the newly-generated report itself. Both agree exactly: 14 + 2 = 16, and `order_item_info=1177733` (the REPLACEMENT row) does not appear in the AMAZON-only result set.

## 6. REPLACEMENT / Cancellation Exclusion Confirmation

- REPLACEMENT-source rows contributing to any Order count: **0** (confirmed structurally — the Orders query's `WHERE` clause no longer includes `REPLACEMENT` at all — and confirmed numerically for B0FX2XDLT5).
- Cancellation exclusion: **unchanged and confirmed still active** — `STATUS_FILTER_SQL` (`NOT IN ('Cancelled', 'Canceled')`) was not modified; the same shared fragment is reused by the corrected query.

## 7. Fresh Data Extraction

| Item | Value |
| ----- | ----- |
| Extraction timestamp | 2026-07-16 14:26:07 (Asia/Colombo) |
| Source maximum available `order_date` (AMAZON, UK) at extraction time | 2026-07-16 00:57:47 (today, partial — 6 order items so far) |
| Report start date | 2025-01-01 |
| Report end date | **2026-07-15** (latest complete business day — today, 2026-07-16, is still in progress and excluded, per the project's standing "current incomplete day excluded" convention) |
| Assigned ASIN count | 1,723 |
| Product master rows | 1,723 (1,700 with a usable image, 23 without — image coverage naturally differs slightly from 2026-07-15's snapshot, since this is genuinely fresh, current listing data, not a re-render of the old snapshot) |
| Daily ASIN-grain aggregate rows | 29,240 |
| Vendor period rows | 961 (333 ASINs with Vendor data) |
| Multi-image ASINs (freshly recomputed) | 229 |

**This extraction did not reuse the 2026-07-15_utharsika_v004 embedded snapshot** — every figure below was produced from a brand-new live query against `public.order_transaction`, `public.listing_data`, and `public.vendor_sales`, run today.

## 8. Report Totals (this report, AMAZON-only Orders)

| Metric | Value |
| ----- | ----- |
| FBM Sales | £487,957.12 |
| FBA Sales | £184,681.80 |
| Vendor Sales | £46,814.94 |
| **Total Sales** | **£719,453.86** |
| FBM Orders | 26,271 |
| FBA Orders | 7,975 |
| Vendor Orders | 4,748 |
| **Total Orders** | **38,994** (= 26,271 + 7,975 + 4,748) |
| ASIN rows | 1,723 |

## 9. Source-vs-HTML Independent Reconciliation

A **second, independently-written SQL query** (`05_IMPLEMENTATION\src\independent_reconciliation_2026_07_16.py`) — deliberately not reusing the extraction script's own query text — re-derived every total from the live database and compared against the generated report:

| Metric | Independent re-derivation | Report (HTML/engine) | Difference |
| ----- | ----- | ----- | ----- |
| Assigned ASIN scope | 1,723 (missing=0, extra=0) | 1,723 | 0 |
| FBM Sales | £487,957.12 | £487,957.12 | £0.00 |
| FBA Sales | £184,681.80 | £184,681.80 | £0.00 |
| Vendor Sales | £46,814.94 | £46,814.94 | £0.00 |
| Total Sales | £719,453.86 | £719,453.86 | £0.00 |
| FBM Orders | 26,271 | 26,271 | 0 |
| FBA Orders | 7,975 | 7,975 | 0 |
| Vendor Orders | 4,748 | 4,748 | 0 |
| Total Orders | 38,994 | 38,994 | 0 |

Image selection was also independently re-verified for all 1,723 ASINs (`05_IMPLEMENTATION\src\independent_image_check_2026_07_16.py`, separate `ROW_NUMBER()`-based query): **0 mismatches**.

## 10. Quantity Absence

Confirmed structurally (no `data-field` for any Quantity column, no Quantity CSV header, no Quantity Column Definitions entry, no Quantity KPI card) and functionally (real headless-Chromium rendering: KPI label list captured, contains no "QUANTITY" entry; `total.totalQuantity`/`row.fbmQuantity` are `undefined` on every computed object). **Quantity output fields remaining: 0.**

## 11. UI Regression (real browser, Playwright/Chromium)

| Check | Result |
| ----- | ----- |
| One row per ASIN | YES (1,723 rows, 1,723 distinct ASINs) |
| 15 complete rows visible | YES |
| Page size | 50 |
| Sticky header | YES |
| Sticky ASIN column | YES |
| Sticky Image column | YES |
| Sticky pagination | YES |
| Previous / Next / direct-page navigation | YES (all exercised: Next → Page 2, Go to 5 → Page 5) |
| Full filtered-data download | YES (real triggered download: 1 header + 1,723 rows = 1,724 lines) |
| Image column present | YES |
| Column Definitions present | YES |

## 12. Tests

New dedicated suite `05_IMPLEMENTATION\tests\test_uawso_2026_07_16_amazon_only_orders_v001.js` — **22/22 checks passed**, covering: AMAZON-only Orders query confirmed (structural), REPLACEMENT exclusion confirmed (structural + numeric), cancellation exclusion unchanged, B0FX2XDLT5 June = 16, FBM/FBA/Vendor/Total Orders formula, Quantity absence (KPI/table/CSV/definitions/computed objects), Sales logic unchanged, one row per ASIN, and full historical-file hash protection (original requirement + all 5 prior HTML outputs). Full pre-existing regression suite re-run and unaffected: `test_uawso_client_engine.js` 42/42, `_v2` 19/19, `_v3` 21/21, `_v5` 25/25, `test_uawso_sticky_columns_and_export_v5.js` 21/21, `test_uawso_pagination_v5.js` 40/40, `test_uawso_15row_viewport_v5.py` 28/28 (all still validating `2026-07-15_utharsika_v004.html`, which is untouched and correctly still shows its own frozen figures, e.g. Total Orders 39,202 under the pre-2026-07-16 rule — this is expected and correct, not a regression). **Total: 218/218 across all suites.**

## 13. Browser Validation

Full — genuine headless Chromium (Playwright) rendering and interaction was used throughout (Section 11), not static source inspection.

## 14. Staging and Final Paths

| Item | Value |
| ----- | ----- |
| Staging path | `09_OUTPUTS\staging\2026-07-16_utharsika_v001.staging.html` |
| Staging SHA-256 | `b0a781f4d79e5be64fe446bdbe93dd789f4c61f92dfa0dac3e90eb0fdecea2bf` |
| Promotion method | `promote_uawso_2026_07_16_v001.py` — refused to run if the target already existed (`OUTPUT_VERSION_ALREADY_EXISTS` guard), verified via `os.rename` (fails on Windows if the target exists — a second, structural safety layer), re-read and re-hashed after |
| Final path | `09_OUTPUTS\2026-07-16_utharsika_v001.html` |
| Final SHA-256 | `b0a781f4d79e5be64fe446bdbe93dd789f4c61f92dfa0dac3e90eb0fdecea2bf` (matches staging exactly) |
| Final byte size | 5,011,392 bytes |

## 15. ph_task

**Not accessed, not modified.** No connection to `tech_team_outputs.ph_task` was made at any point in this task. Publication rules for a later, separate task are documented (not executed) in the governing task's Section 14: one active final output per user per report date; a new report date creates a new `ph_task` row; never replace a previous date's row; only the final approved version remains active per date; `assigned_user`/`assigned_user_team`/`version_level` must be set correctly for board visibility; same-day replacement requires explicit approval at publication time.

## 16. Final PASS/FAIL

```
- original requirement unchanged                                    YES
- new business-rule update file created                              YES
- AMAZON-only Orders applied                                         YES
- REPLACEMENT Orders excluded                                        YES (0 contributing)
- B0FX2XDLT5 June Amazon Orders = 16                                  YES
- cancellation logic remains correct                                 YES (unchanged, re-verified)
- Vendor Orders equal ordered_units                                  YES (4,748 = 4,748)
- Quantity output fields = 0                                         YES
- fresh data fetched (not reused snapshot)                           YES
- exact new filename created (09_OUTPUTS\2026-07-16_utharsika_v001.html)  YES
- prior HTML files unchanged                                         YES (all 5, hash-verified)
- ph_task unchanged                                                  YES (not accessed)
- all tests pass                                                     YES (218/218)
```

**FINAL STATUS: PASS.** `09_OUTPUTS\2026-07-16_utharsika_v001.html` is a freshly-extracted, fully-validated report applying the corrected AMAZON-only Orders business rule, with zero difference against two independently-derived source reconciliations, zero image mismatches, zero Quantity output fields, and full UI feature parity — ready for review before a separate, later `ph_task` publication task.
