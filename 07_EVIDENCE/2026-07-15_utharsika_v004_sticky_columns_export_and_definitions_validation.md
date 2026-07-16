# UAWSO v004 (Unpublished) — Sticky Header/Columns, Single Download, Row Type Removal, Column Definitions

**Target file:** `09_OUTPUTS\2026-07-15_utharsika_v004.html` (still unpublished — no `ph_task` row references this identity)
**Execution date:** 2026-07-15

---

## 1. Backup

| Item | Value |
| ----- | ----- |
| Previous v004 SHA-256 | `aa4ea555338e0455d65f3c14441c37bddff012783b7c0602e4598bd04a0dd94a` |
| Previous v004 byte size | 5,112,262 |
| Backup path | `09_OUTPUTS\staging\2026-07-15_utharsika_v004_before_sticky_and_export_update.html` |
| Backup hash matches previous v004 | YES (confirmed identical before any edit was made) |
| Backup modified | NO |

## 2. Visible Column Identification (before implementing sticky positioning)

Read directly from the live pre-edit `09_OUTPUTS\2026-07-15_utharsika_v004.html` `<thead>`:

```
Column 1: ASIN
Column 2: Image
```

No width was assumed. Column 1's width is measured at render time via `getBoundingClientRect().width` on the actual header cell and written to a `--uawso-col1-width` CSS custom property, which column 2's `left` offset reads — the offset is never a hardcoded guess.

## 3. Sticky Header and Sticky Columns

| Item | Result |
| ----- | ----- |
| Header frozen (vertical scroll) | YES — `table.uawso-table thead th { position: sticky; top: 0; z-index: 3; background: var(--accent-bg); }` |
| Column 1 (ASIN) frozen (horizontal scroll) | YES — `left: 0; z-index: 2; background: var(--card);` |
| Column 2 (Image) frozen (horizontal scroll) | YES — `left: var(--uawso-col1-width, 90px); z-index: 2; background: var(--card);` |
| Top-left frozen-cell layering | `thead th:nth-child(1)`/`(2)` set to `z-index: 4`, above both the plain sticky header (`z-index: 3`) and the frozen body columns (`z-index: 2`) |
| Overlap issues found | 0 |
| Scroll container | `.uawso-table-wrap { overflow: auto; max-height: 70vh; }` — the standard, cross-browser-robust pattern for combined sticky-header + frozen-column tables (a bounded-height scroll box, rather than relying on ambiguous window-scroll sticky behavior) |
| Total-row (footer) sticky columns | Column 1/2 of the total row keep the `--accent-bg` background (not the generic `--card`), so the frozen cells don't look visually broken against the shaded total row |

## 4. Single Download Action

| Item | Before | After |
| ----- | ----- | ----- |
| Download buttons | 2 (`btn-csv` "Download CSV (filtered)", `btn-csv-full` "Download CSV (full dataset, no filters)") | 1 (`btn-csv`, relabelled "Download Filtered Full Data") |
| Exports complete filtered dataset (not just visible page) | YES — `downloadCsv(state.lastFilteredRows, "filtered")`; `state.lastFilteredRows` is assigned the full sorted (unpaginated) filtered array at the end of `renderTable`, not the paginated `pageRows` slice |
| Respects date range / search / other filters | YES — unchanged filter pipeline (`applyFilters`) feeds the same rows used for the table and the download |
| One row per ASIN, Image URL as text, no SKU, no Row Type | YES (all four confirmed in the CSV header/row-building code) |

Dead code removed after confirming no remaining dependency: the `btn-csv-full` handler, `state.lastAllRows` (only consumer was the removed handler), and `rowTypeLabel()` (only consumers were the removed table-cell and CSV-cell usages).

## 5. Row Type Removal

Removed from: table header (`<th data-field="rowType">`), table body cell, table footer leading cells (now 2, not 3), CSV header array, CSV row-value array, empty-state `colspan` (25 → 24, confirmed 24 actual `<th>` elements). Not present in sorting controls, filter controls, or search labels (it was never wired into any of those in the v5 template). The internal `rowType` field remains in the engine's row objects (`buildCanonicalRowsV5`/`computeRowsV5` output, always `"ASIN"`) since it costs nothing to leave and the requirement explicitly permits retaining it as a non-visible internal field — it is simply never read by the template anymore.

**Confirmed unchanged by this removal:** Sales, Orders, Quantity, image selection, date filtering, fulfilment calculations, and Vendor handling are computed entirely by `uawso_client_engine.js`, which was not modified in this task (verified: `buildCanonicalRowsV5`/`computeRowsV5`/`computeTotalV5` function signatures unchanged; full KPI reconciliation in Section 7 below is byte-identical to the pre-update figures).

## 6. Column Definitions Section

Added as a new `<div class="uawso-panel" id="uawso-column-definitions">` with `<h2>Column Definitions</h2>`, placed after the Methodology footer and before the embedded JSON `<script>` blocks (so it is never mistaken for exportable data — it is DOM-only markup, never read by `downloadCsv`, which only ever touches the in-memory row objects). All 24 visible columns (ASIN, Image, FBM Sales, FBM Orders, FBM Quantity, FBA Sales, FBA Orders, FBA Quantity, Vendor Sales, Vendor Units, Total Sales, Total Orders, Total Quantity, PY Sales, CY Sales, PY Orders, CY Orders, PY Quantity, CY Quantity, Sales Change %, Order Change %, Quantity Change %, Trend, Achievement %) are explained in plain English. No "Product Name" definition was added, since the report has no visible Product Name column (product title is search-only metadata) — matching the requirement's "where applicable" qualifier rather than describing a column that doesn't exist.

## 7. KPI and Data Protection

| Metric | Before | After | Difference |
| ----- | ----- | ----- | ----- |
| Data range | 2025-01-01 → 2026-07-14 | 2025-01-01 → 2026-07-14 | none |
| ASIN rows | 1,723 | 1,723 | 0 |
| Sales | £718,835.91 | £718,835.91 | 0 |
| Orders | 34,454 | 34,454 | 0 |
| Quantity | 47,166 | 47,166 | 0 |
| Image-covered ASINs | 1,699 | 1,699 | 0 |
| No-image ASINs | 24 | 24 | 0 |

Figures reconfirmed by loading the actual `<script type="application/json">` payloads out of the updated, promoted `09_OUTPUTS\2026-07-15_utharsika_v004.html` into Node.js and running the unmodified `uawso_client_engine.js` functions — not a hand re-derivation. The generation script (`generate_uawso_v5_2026_07_15_sticky_update_staging.py`) reused the exact same embedded-data JSON files from the original v004 build (`07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_*.json`) and additionally hard-asserts the snapshot still equals the approved baseline (1,723 / 1,699 / 24) before rendering, refusing to run otherwise — no live data was re-queried.

## 8. Tests

`05_IMPLEMENTATION\tests\test_uawso_sticky_columns_and_export_v5.js`: **21/21 checks passed**, covering all 17 required items (sticky header, sticky column 1, sticky column 2, measured (not hardcoded) column-2 offset, z-index layering, single download, filtered-full export, Row Type absent from HTML/CSV, Image URL retained, one-row-per-ASIN/KPI-logic untouched, Column Definitions present and complete, Sales/Orders/Quantity/row-count unchanged, historical HTML unchanged, no `ph_task` writes).

Pre-existing engine suites re-run for regression: `test_uawso_client_engine.js` 42/42, `test_uawso_client_engine_v2.js` 19/19, `test_uawso_client_engine_v3.js` 21/21, `test_uawso_client_engine_v5.js` 23/23 — all still 100% pass, confirming this UI-only change did not affect KPI logic.

## 9. Browser Validation — Disclosed Limitation

**No browser-automation tool (Playwright/Puppeteer) or DOM environment (jsdom) is available in this session.** True interactive verification — actually scrolling vertically and horizontally together, hovering rows, clicking sort/search/filter controls, clicking the download button and inspecting the resulting file, and visually confirming no pixel-level overlap — **could not be performed** and is not claimed to have been performed. This is disclosed here rather than silently omitted.

What **was** verified, as the strongest feasible substitute:
- The exact CSS sticky pattern used (bounded-height scroll container + `position: sticky` on `th`/`td`, offsets via a measured custom property) is the standard, well-documented, cross-browser-correct technique for this exact requirement (sticky header + frozen leading columns together) — not an experimental or unusual approach.
- Every structural piece (CSS rules, z-index ordering, JS measurement/assignment code, single button, absent Row Type, present Column Definitions, CSV header/row content) was confirmed present and internally consistent via direct source inspection and the automated test suite above.
- The KPI data itself was verified by actually executing the real, unmodified calculation engine against the real, embedded data (Section 7) — this is a genuine functional test, not a structural one.

**Recommendation:** before this file is published, a human (or a session with browser-automation access) should open it locally and confirm the items in the governing task's Section 11 visually, particularly the combined vertical+horizontal scroll behavior and hover readability on the sticky columns.

## 10. Historical Output Protection

All 4 other `09_OUTPUTS\*.html` files re-hashed identical to their long-standing baseline (unchanged by this task). `tech_team_outputs.ph_task` rows 157 and 237 re-queried: `updated_at` and `html_content` MD5 both unchanged from the value observed immediately before this task began. No `ph_task` row was created, updated, or referenced. No database write occurred.

## 11. Final PASS/FAIL

```
PASS:
- header remains visible during vertical scrolling (sticky rule present, correct scroll container)  YES
- columns 1 and 2 sticky during horizontal scrolling (measured offset, no overlap in source)         YES
- sticky cells do not overlap (z-index ordering verified: 2 < 3 < 4)                                 YES
- exactly one download option exists                                                                 YES
- download contains the complete filtered dataset (not a page slice)                                 YES
- Row Type absent from visible table and CSV                                                         YES
- column definitions shown at the bottom, all visible columns explained                              YES
- KPI values unchanged (0 difference across Sales/Orders/Quantity/rows/image-coverage)                YES
- ASIN row count remains 1,723                                                                       YES
- older HTML files remain unchanged                                                                  YES
- ph_task rows remain unchanged                                                                      YES
- updated v004 opens as valid HTML (well-formed, no unresolved placeholders, verified by the renderer's own placeholder check)  YES
```

**FINAL STATUS: PASS**, with the browser-interactive-validation limitation disclosed in Section 9. Not published to `ph_task`. Automation/scheduler not touched.
