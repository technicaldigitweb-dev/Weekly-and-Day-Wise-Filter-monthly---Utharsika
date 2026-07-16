# UAWSO v001 — ASIN–SKU Grain Correction & June PY Reconciliation

**What this asset is:** Evidence for two corrections to the existing `2026-07-10_utharsika_v001.html`: (1) the table row grain, (2) an investigation into a reported June previous-year Sales discrepancy.

**Why it exists:** To make both the fix and the (partial) non-fix independently checkable — Issue 1 is resolved and verified; Issue 2 is honestly reported as unresolved, per explicit instruction not to force a number.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Issue 1 (grain) — **RESOLVED, verified.** Issue 2 (June £940.12 gap) — **NOT resolved; source data cannot reproduce the user-provided value.** See Part 5 below.
**Known limits:** See Issue 2's conclusion — the exact cause of the £940.12 difference could not be identified from any tested query variant, live or cached.
**Pass/fail rule:** Per the stage's explicit stop condition, the overall verdict is **FAIL** while the June discrepancy remains unexplained, even though every other requirement (grain, reconciliation, security, row structure) passed its own checks.
**Next action:** Route the June figure to whoever provided the £42,086.96 reference value (e.g. Satheesvaran) for clarification — see Part 5's exact open question.

---

## Part 1 — Existing Grain Inspected (before any change)

1. **Where ASIN-to-SKU mappings are created:** `05_IMPLEMENTATION\src\extract_uawso_full_coverage.py`, which produces `<identity>_product_master_full.json` — one entry per assigned ASIN with a `skus` array (built via `array_agg(DISTINCT ot.sku)`, so no duplicate SKUs within an ASIN's list).
2. **Were SKUs grouped into arrays/strings?** **YES — confirmed incorrect.** The prior `uawso_client_engine.js` (`computeRowsV2`) rendered `sku: p.skus.join(", ")` — a single comma-joined string per ASIN row. This directly violated the required "one row = one ASIN + one SKU" grain.
3. **Aggregation grain:** The underlying `daily_aggregates_split.json` was already correctly aggregated at **(date, ASIN, SKU)** grain (confirmed: 0 duplicate `(date,asin,sku)` keys across 28,601 rows). The bug was entirely in the **client-side row-computation step** (`computeRowsV2` collapsed to ASIN-only), not in the source SQL/extraction.
4. **Were multiple SKUs for the same ASIN being merged?** **YES** — via the `.join(", ")` call described above.
5. **Do duplicated assignment source rows affect mapping?** **NO.** `public.user`/`public.ph_categories`/`public.ph_cate_products` all contain a confirmed uniform 2x raw-row duplication (documented in `07_EVIDENCE\2026-07-10_utharsika_ASIN_SCOPE_VALIDATION.md`), but every extraction query uses `DISTINCT`/`array_agg(DISTINCT ...)`, so the resolved 1723-ASIN set and each ASIN's SKU list are unaffected.
6. **Did the previous table contain duplicate ASIN–SKU pairs?** No literal duplicates (each ASIN was one row), but the SKU *value* within that row was a merged multi-SKU string, which is the defect being corrected.

## Part 2 — Canonical ASIN–SKU Master (corrected)

Implemented in `src/uawso_client_engine.js::buildCanonicalRows()`, built once from the existing `product_master_full.json` (no new database extraction needed — the source SKU mapping was already correctly built via `DISTINCT`, only the row-rendering step needed fixing):

| Rule | Result |
|---|---|
| One row per distinct (ASIN, SKU) for ASINs with mappings | **1947 rows** |
| One row (blank SKU, `mapping_status=NO_SKU_MAPPING`) per ASIN with no mapping | **113 rows** |
| Duplicate (ASIN, normalized-blank-SKU) check: `COUNT(*) = COUNT(DISTINCT (asin, sku||rowType))` | **PASS** — 2388 total rows, 2388 distinct triples, 0 duplicates (verified programmatically) |
| Comma-joined SKU values | **0** (verified: no row's `sku` field contains a comma) |

## Part 3 — FBM/FBA at ASIN–SKU Grain

`daily_aggregates_split.json` (already `(date, asin, sku, fbm_sales, fbm_orders, fba_sales, fba_orders)` grain) is now summed via the new `Engine.sumRangeSplitByAsinSku()`, keyed by `"asin|sku"`, so FBM/FBA metrics attach to the correct individual SKU row — never repeating an ASIN-level total on every SKU row (each SKU row only receives the sum of the transaction rows that actually carry that exact SKU).

**Reconciliation (full embedded window, 2025-01-01 → 2026-07-09), verified via `tests/test_uawso_client_engine_v3.js` against real data:**

| Metric | Row-sum (this build) | Prior reference | Match |
|---|---|---|---|
| FBM Sales | £507,631.04 | £507,631.04 | ✅ exact |
| FBM Orders | 25,448 | 25,448 | ✅ exact |
| FBA Sales | £170,330.29 | £170,330.29 | ✅ exact |
| FBA Orders | 7,886 | 7,886 | ✅ exact |

No change from the prior validation — source data has not changed (also independently re-confirmed live via the approved read-only tool during this session, see Part 5).

## Part 4 — Vendor Data Without Duplication

Implemented exactly per the preferred safe rule:

1. All normal ASIN–SKU rows carry FBM/FBA only (`vendorSales`/`vendorUnits` are structurally `0` on every `ASIN_SKU` row — verified: `vendorOnSkuRows` summed across all `ASIN_SKU` rows = **0**, i.e. zero leakage).
2. For the **328** ASINs that have both SKU rows and Vendor data, exactly **one** additional row is created: `{asin, sku:"", rowType:"VENDOR_ASIN_LEVEL"}`.
3. For the **1** ASIN (`B0DTKCSD1R`) that has Vendor data but no SKU mapping at all, its single existing blank no-SKU row is reused and reclassified `NO_SKU_MAPPING_VENDOR` — **no second blank row is created for it** (verified: exactly 1 row for this ASIN).
4. Verified: **no ASIN has more than one Vendor-carrying row** (0 offenders across all 1723 ASINs).
5. Labeled in the HTML as `Vendor — SKU not provided by source` (Row Type column / CSV export).
6. Vendor Units are never called "Orders" anywhere in the UI, table headers, KPI cards, or CSV.

**Reconciliation (full embedded window):**

| Metric | Row-sum (this build) | Prior reference | Match |
|---|---|---|---|
| Vendor Sales | £46,642.46 | £46,642.46 | ✅ exact |
| Vendor Units | 4,738 | 4,738 | ✅ exact |

## Part 5 — June Previous-Year Sales Reconciliation

### What "currently shown" means

The current HTML's June PY figure (£41,146.84) is produced by: **Comparison mode = Month, Month = 2026-06 → resolved previous-year period = full calendar June 2025 (2025-06-01 to 2025-06-30) → FBM + FBA + Vendor.** This is the period-resolution logic's own output (`Engine.resolvePeriod("MONTH", {month:"2026-06"}, ...)` → `{cyStart:"2026-06-01", cyEnd:"2026-06-30", pyStart:"2025-06-01", pyEnd:"2025-06-30"}`), which is the same Month-mode logic already established and tested across every prior session — no special-case bug in the date resolution itself.

### Reconciliation Table (all variants actually run against real data, live-verified)

| # | Calculation variant | Date range (PY) | FBM | FBA | Vendor | Total | Difference from £42,086.96 |
|---|---|---|---|---|---|---|---|
| 1 | **Full June 2025, FBM+FBA+Vendor (= currently shown)** | 2025-06-01 → 2025-06-30 | £29,180.13 | £7,663.75 | £4,302.96 | **£41,146.84** | −£940.12 |
| 2 | Full June 2025, FBM+FBA only (no Vendor) | 2025-06-01 → 2025-06-30 | £29,180.13 | £7,663.75 | £0.00 | £36,843.88 | −£5,243.08 |
| 3 | Matched partial-day range (2025-06-01→2025-07-09, mislabeled as "June" under an MTD-style 39-day window) | 2025-06-01 → 2025-07-09 | £38,643.45 | £16,100.96 | £8,871.77 | £63,616.18 | +£21,529.22 |
| 4 | 2025-06-01 → 2025-07-01 (matches the Vendor period's own literal end-date field) | 2025-06-01 → 2025-07-01 | £30,214.45 | £7,818.27 | £8,871.77 | £46,904.49 | +£4,817.53 |
| 5 | Date boundary shifted by 1 day (2025-06-02 → 2025-06-30) | 2025-06-02 → 2025-06-30 | £27,997.54 | £7,346.85 | £4,302.96 | £39,647.35 | −£2,439.61 |
| 6 | Full June 2025, FBM+FBA with an Asia/Colombo (+5:30) timezone shift applied to `order_date` before bucketing | 2025-06-01 → 2025-06-30 (shifted) | £29,063.20* | (included in FBM figure — shift applied to combined FBM+FBA total: £36,726.81) | not recomputed with shift | ~£41,029.77† | ~−£1,057.19 |
| 7 | Live re-query (this session) vs cached extraction (prior session) | 2025-06-01 → 2025-06-30 | £29,180.13 | £7,663.75 | £4,302.96 | **£41,146.84** | −£940.12 (identical to #1 — confirms no stale-data issue) |
| 8 | Vendor allocated with **strict containment** (period must be fully *within* June, not just overlapping) instead of overlap-allocation | 2025-06-01 → 2025-06-30 | £29,180.13 | £7,663.75 | £0.00‡ | £36,843.88 | −£5,243.08 |

\* Timezone-shift test was run as a combined FBM+FBA figure (£36,726.81), not split by FBM/FBA individually — shown combined for transparency.
† Variant 6's total is FBM+FBA(shifted) + Vendor(unshifted, from variant 1) — an approximation to test direction of effect, not a fully independent variant.
‡ All 13 Vendor periods overlapping June 2025 are stored as `start_date=2025-06-01, end_date=2025-07-01` (an exclusive-end monthly bucket) — under a naive date-only "fully contained" test this incorrectly excludes them entirely, which is itself a boundary-representation nuance (documented as a separate, secondary finding below), not the source of the £940.12 gap.

### Exact explanation of the £940.12 difference

**Not identified.** None of the 8 tested variants — spanning date-range interpretation, FBM/FBA-only vs. FBM+FBA+Vendor, Vendor overlap-vs-strict-containment allocation, a timezone-shift hypothesis, and a live-vs-cached-data check — reproduce £42,086.96 or land on a £940.12 difference from a *different* baseline that would explain it as a specific, identifiable component (e.g., one specific ASIN, one specific channel, or one specific date range difference).

**Current source-backed value:** £41,146.84 (Full June 2025, FBM+FBA+Vendor — confirmed identically by both the cached extraction and a fresh live query run this session).
**User-provided value:** £42,086.96.
**Difference:** £940.12 (user-provided value is higher).
**Included/excluded channel:** FBM and FBA are included in both the current calculation and (presumably) the reference figure; Vendor's inclusion in the *reference* figure is unknown — variant #2 (excluding Vendor) is £5,243.08 short, ruling out "reference excludes Vendor" as a simple explanation on its own.
**Included/excluded dates:** Full calendar June (30 days) is the only period consistent with the "Month" comparison mode and with June being a fully-completed month; no tested alternate date range reproduces the target value either.
**Affected ASIN/SKU rows:** Not identified — £940.12 was not traceable to any specific row, ASIN, or SKU subset through the variants tested; a row-by-row diff against the reference figure was not possible because the reference value's own derivation (which rows/dates/channels it includes) was not available to compare against.
**Required business decision:** Whoever prepared the £42,086.96 reference figure needs to specify: (a) the exact date range they used, (b) whether Vendor was included, and (c) whether any additional data source beyond `order_transaction`/`vendor_sales` (e.g., a manual adjustment, a different snapshot of the ASIN assignment, or a currency conversion) contributed to their number. Without that, the gap cannot be closed from this side.

### Secondary finding (not the cause of the £940.12 gap, but worth fixing separately)

Vendor periods that represent a full calendar month are stored with an **inclusive-looking but effectively exclusive** end date (`start_date=2025-06-01, end_date=2025-07-01` for "June"). The current overlap-allocation logic (`periodsOverlap`, no proration) correctly includes these in full for any range touching June, which is why variant #1 (the current, correct behaviour) matches what's shown. A **strict "fully contained"** test (variant #8) would incorrectly exclude them due to the exclusive-end representation — this is flagged as a data-modeling nuance worth documenting precisely if `vendor_sales`' date semantics are ever formally specified by its source system, but it is **not** the explanation for the £940.12 gap, since the current (correct) overlap-based method already includes these periods in full.

### No hardcoded correction was applied

Per the explicit instruction, **the HTML was not modified to force £42,086.96.** The June PY figure shown remains £41,146.84 — the value the source data actually produces under the approved filters and the current Month-mode date resolution.

## Part 6 — Filter Behaviour (re-verified against the corrected grain)

- ASIN selection shows every row for that ASIN (SKU rows + its Vendor/no-mapping row, if any) — verified via the multi-SKU ASIN test (`B07WP51SL6`, 2 SKUs → both rows returned when the ASIN is selected).
- SKU selection shows only rows with that exact SKU value — verified.
- Combined ASIN+SKU filter uses intersection logic — verified (returns exactly the one matching row).
- Blank-SKU Vendor/no-mapping rows remain reachable when their ASIN is selected (the `applyFilters` logic explicitly allows a blank row through when its ASIN is in the selected set, even without a SKU-text match) — implemented and code-reviewed; not independently unit-tested this session due to time, flagged as a known limitation (browser-DOM-level filter interaction was not executed live — see Known Limits).
- No SKU dropdown option is a comma-joined list (dropdown options are built from `SKU_LIST`, a flat deduplicated list of individual SKU strings, never from a row's joined `sku` field).
- Dynamic cards (KPIs) are computed from `Engine.computeTotalV3(rows)` — a fresh aggregate-of-aggregate over the currently filtered row set, never double-counting (Vendor is structurally zero on every `ASIN_SKU` row, so summing all rows' `vendorSales` cannot double-count it).

## Part 7 — CSV Rules (re-verified)

- Each CSV row = one ASIN + zero-or-one SKU + one Row Type + row-level metrics — matches the corrected table grain exactly (same `computeRowsV3` output feeds both the table and the CSV).
- No SKU arrays or comma-joined SKU values in the CSV SKU column (verified by code inspection: `r.sku` is the single string field on each `ASIN_SKU`/blank row, never `r.skus.join(...)`— that array no longer exists on v3 rows at all).
- No-filter CSV exports the complete corrected 2388-row dataset (for the active period).
- Filtered CSV exports all matching rows via `state.lastFilteredRows` (the full filtered+sorted array, set before pagination slicing in `renderTable()`), not just the current page.
- CSV totals reconcile to the dynamic cards for the same filter state — both are computed from the identical `rows`/`total` objects produced by one `render()` call.

## Part 8 — Table Columns (implemented exactly as specified)

`ASIN | SKU | Row Type | FBM Sales | FBM Orders | FBA Sales | FBA Orders | Vendor Sales | Vendor Units | PY Sales | CY Sales | Sales Change | Trend | Achievement %`

No ambiguous combined "Total Orders/Units" column exists anywhere in the table, KPI cards, or CSV in this build — FBM Orders, FBA Orders, and Vendor Units are always three separate values.

## Part 9 — Validation Test Results

### Grain checks (`tests/test_uawso_client_engine_v3.js`, 21/21 PASS)

| Check | Result |
|---|---|
| 1,723 distinct assigned ASINs represented | PASS |
| Every populated SKU cell contains exactly one SKU | PASS (0 comma-joined values) |
| No duplicated ASIN–SKU pair | PASS (2388 rows, 2388 distinct triples) |
| Every no-SKU ASIN appears at least once | PASS (113/113) |
| Vendor data appears only once per ASIN | PASS (0 ASINs with >1 Vendor row) |
| No Vendor multiplication across SKU rows | PASS (0 leaked onto `ASIN_SKU` rows) |

### Reconciliation checks

| Check | Result |
|---|---|
| FBM row-sum = source FBM | PASS (exact) |
| FBA row-sum = source FBA | PASS (exact) |
| Vendor row-sum = source Vendor | PASS (exact) |
| CY Sales = FBM + FBA + Vendor | PASS |
| FBM/FBA Orders reconcile | PASS (exact) |
| Vendor Units reconcile | PASS (exact) |

### June checks

| Check | Result |
|---|---|
| Exact June PY period documented | PASS — 2025-06-01 → 2025-06-30 |
| HTML June PY Sales reconciled to source | PASS — £41,146.84 confirmed source-backed (live + cached agree) |
| Difference against £42,086.96 explained | **FAIL — not explained**, see Part 5 |
| No hardcoded correction | PASS — value was not forced |

### UI checks (structural/code-review; see Known Limits for what was not browser-tested)

| Check | Result |
|---|---|
| ASIN dropdown present, searchable, multi-select | PASS (structural) |
| SKU dropdown present, searchable, multi-select | PASS (structural) |
| Dependent options (ASIN↔SKU) | PASS (code-reviewed, logic unchanged from the prior session's tested version) |
| Dynamic cards | PASS (uses `computeTotalV3`, verified via engine tests) |
| No-filter CSV | PASS (code-reviewed) |
| Filtered CSV | PASS (code-reviewed, uses `state.lastFilteredRows`) |
| Pagination independence (totals unaffected by page) | PASS (totals computed from full `rows`, before `renderTable`'s pagination slice) |

## Part 10 — Output and Final SHA-256

| Field | Value |
|---|---|
| Output path | `09_OUTPUTS\2026-07-10_utharsika_v001.html` (same path, overwritten — no v002) |
| SHA-256 | `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` (independently re-verified via `sha256sum`, matches exactly) |
| Size | 4,307,156 bytes (4.11 MB) |
| Total table rows | 2388 (1947 ASIN+SKU rows + 113 no-SKU rows + 328 Vendor-only rows) |
| Embedded JSON integrity | `product_master_full`, `daily_aggregates_split`, `vendor_periods` all confirmed byte-identical to source-of-truth files; engine JS confirmed embedded verbatim |

## Known Limits

- **The June £940.12 discrepancy remains unresolved** — see Part 5. This is the primary reason the overall verdict is FAIL, per the stage's explicit stop condition.
- No real-browser DOM interaction test (dropdown clicks, CSV download click) was performed — no browser automation tool is available in this environment. JS syntax verified valid (`node --check`); all calculation/grain/reconciliation logic verified against real data via Node.js execution of the exact shipped engine code (61 v1/v2 checks + 21 v3 checks = 82 total engine checks pass).
- The Vendor period exclusive-end-date nuance (Part 5, Secondary Finding) is documented but not changed — the current overlap-based allocation already produces the correct (source-matching) result for the tested cases.

## Isolation Confirmation

All queries this session were scoped to Utharsika or were schema/system-wide checks touching no other user's row-level content. **Other users' `ph_task` content inspected or reused: NO.**

## Files Changed

- `05_IMPLEMENTATION\src\uawso_client_engine.js` (v3 functions added, additive — v1/v2 untouched)
- `05_IMPLEMENTATION\templates\uawso_report_template.html` (rewritten for the corrected grain and new column spec)
- `05_IMPLEMENTATION\src\dashboard_renderer.py` (new placeholders for row-count coverage stats)
- `05_IMPLEMENTATION\tests\test_uawso_client_engine_v3.js`, `tests\generate_final_dashboard_v3.py` (created)
- `09_OUTPUTS\2026-07-10_utharsika_v001.html` and its `staging\` copy (regenerated, same identity)

**Database writes: NONE.**
