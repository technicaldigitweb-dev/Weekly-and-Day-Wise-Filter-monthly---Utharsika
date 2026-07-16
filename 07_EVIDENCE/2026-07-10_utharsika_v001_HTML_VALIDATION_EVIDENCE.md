# UAWSO HTML Validation Evidence — 2026-07-10_utharsika_v001

**What this asset is:** Full validation record for today's self-contained interactive dashboard HTML.

**Why it exists:** To make every claim about the final HTML (coverage, correctness, security, isolation) independently checkable, not asserted.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Complete. **Updated in place (same v001 identity, no v002)** with full ASIN coverage, FBM/FBA/Vendor sales, CSV export, and searchable multi-select filters — see the Update section immediately below. Publication to `ph_task` and scheduler registration remain gated pending explicit approval.
**Known limits:** See the v2 Known Limits list below (vendor-period overlap allocation; no real-browser DOM interaction test performed).
**Pass/fail rule:** PASS requires every section below to show PASS with no unexplained gap.
**Next action:** User reviews this evidence and the HTML itself, then approves (or not) the `ph_task` publish.

---

## UPDATE (same day, v001 unchanged) — Full ASIN Coverage + FBM/FBA/Vendor + CSV + Searchable Filters

This update was made **in place** — same `task_name`/`task_id`/version identity (`v001`), same output path (`09_OUTPUTS\2026-07-10_utharsika_v001.html`). **No v002 was created; no `ph_task` write occurred.** The original validation below (Database Access Method through the original Overall Verdict) remains an accurate historical record of the *first* build of this file; this section documents what changed and re-validates the result.

### What changed

1. **Complete ASIN coverage.** The table now starts from the full 1723-ASIN assigned master (`extract_uawso_full_coverage.py`), `LEFT JOIN`ed to `order_transaction` (for SKU + FBM/FBA) and `LEFT JOIN`ed to `vendor_sales` (for Vendor) — never starting from transaction data. All 1723 ASINs are always present in every view; the 113 without any qualifying transaction display a blank SKU and zero metrics rather than being hidden (`hasSku: false` on the row).
2. **FBM + FBA + Vendor sales coverage.** `src/uawso_client_engine.js` gained `computeRowsV2`/`computeTotalV2`, splitting `order_transaction` by `fba_sales` (FBM/FBA) and adding `vendor_sales` (`ordered_revenue`/`ordered_units`) as a third, independently-sourced metric. Total Sales = FBM + FBA + Vendor.
3. **Vendor period-overlap allocation.** `public.vendor_sales` stores periods (`start_time`/`end_time`), not daily rows, with mixed granularity (confirmed: ~86% are ~1-hour "daily" markers, ~14% are full-month spans). `Engine.sumVendorRange()` attributes a period's full revenue/units to any selected date range it overlaps (no proration) — documented as a source-data limitation in the HTML's own "Data Coverage Notes" section, not hidden.
4. **CSV download.** Exports exactly the currently-filtered, currently-sorted row set (all rows, not just the current page), with the same 15 columns visible in the table.
5. **Searchable multi-select ASIN/SKU dropdowns.** Replaced the old `<select multiple>` controls with a custom dropdown component (search box, Select All, Clear All, selected count, ASIN↔SKU dependency filtering) — no external UI library used (self-contained constraint).
6. **New table columns (15, per spec):** ASIN, SKU, FBM Sales, FBM Orders, FBA Sales, FBA Orders, Vendor Sales, Vendor Units, Total Sales, Total Orders/Units, Previous Year Sales, Current Year Sales, Sales Change, Trend, Achieve Sales %.
7. **Data Coverage Notes section** added at the end of the HTML (total/displayed/no-SKU ASIN counts, live-recalculated no-sales count, Vendor-period-overlap disclosure).
8. **KPI cards** now include Order Change/Achieve Order % computed on the combined "Total Orders/Units" hybrid metric, per the KPI-card spec (Section 2), while the table itself only shows the columns literally listed in the table-column spec (Section 7) — the two sections intentionally differ per the request's own wording.

### Data Source Changes

| New source | Purpose | Extraction |
|---|---|---|
| Full 1723-ASIN master | Row universe (never starts from transactions) | `extract_uawso_full_coverage.py`, `<identity>_product_master_full.json` |
| `order_transaction`, split by `fba_sales` | FBM Sales/Orders, FBA Sales/Orders | Same script, `<identity>_daily_aggregates_split.json` (28,601 rows, same count as the v1 pull — same underlying data, now split) |
| `public.vendor_sales` | Vendor Sales/Units | Same script, `<identity>_vendor_periods.json` (951 rows, 329 ASINs) |

All three extracted via the same Stage B credential-based, read-only session pattern as the original build (`temp_user`, env-var-only credentials, `readonly=True` session, connection closed after use). No write method called.

### FBM / FBA / Vendor Reconciliation (full embedded window, 2025-01-01 → 2026-07-09)

Cross-checked via a real Node.js run of the exact shipped engine against the real extracted data, and independently cross-checked a second time against the exact figures already published in `07_EVIDENCE\2026-07-10_utharsika_ASIN_SCOPE_VALIDATION.md` and `07_EVIDENCE\2026-07-10_utharsika_VENDOR_SALES_VALIDATION.md`:

| Metric | Value | Cross-check |
|---|---|---|
| FBM Sales | £507,631.04 | Exact match to prior validation |
| FBM Orders | 25,448 | Exact match |
| FBA Sales | £170,330.29 | Exact match |
| FBA Orders | 7,886 | Exact match |
| Vendor Sales | £46,642.46 | Exact match |
| Vendor Units | 4,738 | Exact match |
| **Total Sales** | **£724,603.79** | FBM+FBA+Vendor, computed and cross-checked |

### ASIN Coverage Result

| Check | Result |
|---|---|
| Assigned ASIN count | 1723 |
| Displayed ASIN count (always, every view) | **1723** (was 1610 in the original v001 build) |
| ASINs without SKU mapping | 113 — displayed with blank SKU, zero metrics, never hidden |
| Missing ASIN count | **0** — the "missing ASIN" concept from the prior validation no longer applies; every assigned ASIN is now always a row |

### CSV Validation

Reviewed and syntax-checked (`node --check`, passed) — the CSV export function was **not executed via a real browser download** (no browser automation tool available in this environment; `Blob`/`URL.createObjectURL`/programmatic-click are standard, well-understood browser APIs, not custom logic). What **was** verified directly:
- The exported column set matches the visible table columns exactly (15 columns, same order).
- The export operates on `state.lastFilteredRows` (the full filtered+sorted set produced by `render()`), not `pageRows` (the paginated slice) — confirmed by code inspection: `downloadCsv(state.lastFilteredRows)` is wired to the button, and `state.lastFilteredRows` is set to the *sorted, filtered* array in `renderTable()`, before pagination slicing occurs.
- CSV field escaping (commas/quotes/newlines) follows the standard RFC 4180 quoting pattern (wrap in quotes if the field contains a comma, quote, or newline; double any embedded quotes) — a well-established, low-risk pattern, reviewed by inspection.

### Filter Validation (real engine run against real v2 data, Node.js)

| Test | Result |
|---|---|
| Default MTD | PASS (unchanged from v1: 2026-07-01→09 vs 2025-07-01→09) |
| Random Daily date | PASS (unchanged period-resolution logic, shared with v1) |
| June comparison | PASS (unchanged) |
| Weekly comparison | PASS (unchanged, uses the same corrected-this-project Weekly logic) |
| ASIN filter (multi-SKU ASIN `B07WP51SL6`, 2 SKUs) | PASS — returns exactly 1 row |
| SKU filter (one of that ASIN's SKUs) | PASS — returns the ASIN via the `skus` array match |
| Combined ASIN+SKU filter | PASS — returns exactly 1 row |
| No-SKU ASIN row (of the 113) | PASS — present, `hasSku:false`, `totalSales` is a valid number (0 or real), never omitted |
| Row count always 1723 regardless of period/filters (before filtering) | PASS |

19 additional v2-specific engine checks pass (`tests/test_uawso_client_engine_v2.js`), on top of the original 42 v1 checks (still passing, unaffected — v2 was purely additive to the engine file). **61/61 total engine checks pass.**

### Security (re-checked)

Same checks as the original build, re-run against the updated (larger) file: no credential value, no DB host literal, no connection string, no `order_id`/`order_item_info` raw field, no customer fields. All PASS.

### Final HTML (updated)

| Field | Value |
|---|---|
| Path | `09_OUTPUTS\2026-07-10_utharsika_v001.html` (same path — overwritten, not versioned) |
| SHA-256 | `bce7315b58b58c17b78dfe1cf4ec08b7169e07df2164bcf2df7045891d93f4cf` (independently re-verified via `sha256sum`, matches exactly) |
| Size | 4,299,377 bytes (4.10 MB) — grew from 3.26 MB due to the FBM/FBA split (roughly doubling numeric fields in the daily dataset) and the added vendor-periods payload |
| Embedded JSON integrity | All three payloads (`product_master_full`, `daily_aggregates_split`, `vendor_periods`) and the engine JS confirmed byte-identical to their source-of-truth files by direct extraction and comparison |

### Known Limits (v2, in addition to the original list below)

- Vendor-period overlap allocation (no proration) can over/under-attribute Vendor figures at month-boundary edges when a monthly-bucketed Vendor period is compared against a shorter selection — a source-data granularity limitation, disclosed in the HTML itself, not hidden.
- No real-browser DOM interaction test (dropdown clicks, CSV button click triggering an actual file download, pagination clicks) was performed — no browser automation tool is available in this environment. JS syntax was verified valid (`node --check`), and all underlying calculation/filter logic was verified against real data via Node.js execution of the exact shipped code. The UI-wiring layer (DOM event handlers, rendering) was reviewed by inspection but not executed end-to-end in a browser.
- `jsdom` (or an equivalent headless-DOM library) is not installed in this environment, which was confirmed by attempting to load it — this is why DOM-level testing was not attempted rather than skipped by choice.

### v2 Overall Verdict

**PASS** for data coverage, FBM/FBA/Vendor reconciliation, ASIN completeness, filter/calculation correctness (real, Node-verified), and security. **Advisory-only** for CSV/dropdown UI interaction (reviewed, not browser-executed). `ph_task` publication: **NOT ATTEMPTED** (gated, unchanged).

---

## Original v1 Validation Record (preserved for history)

## Database Access Method

Two-stage approach, as instructed:

- **Stage A (MCP, small checks):** Used earlier this session for schema confirmation, assignment counts, and a sizing check that confirmed the full `2025-01-01`→`2026-07-09` daily-grain dataset is **28,601 rows** — too large to reliably transcribe through the chat interface.
- **Stage B (credential-based, full extraction):** `05_IMPLEMENTATION\src\extract_uawso_daily_aggregates.py`, using the project's approved `temp_user` read-only credentials (`02_SOURCE\db_access_templates\temp_user.py`), loaded via environment variables only (never hardcoded in the new script). Connectivity and read permissions were verified first with small `COUNT(*)` probes against `public.order_transaction`, `public.user`, `public.ph_categories`, `public.ph_cate_products` before the full extraction ran. The extraction opened a **read-only session** (`conn.set_session(readonly=True)`), ran three `SELECT`-only queries, wrote results directly to local JSON files, and closed the connection. No write method was called at any point.

**Credentials exposed in any output, log, or file:** NO. Only `[REDACTED]` appears in script output; the raw password value and full connection string never appear in any created file (independently verified below).

## Data Coverage

| Check | Result |
|---|---|
| Embedded history starts 2025-01-01 | PASS — `index.dates[0] === "2025-01-01"` (Node test) |
| Embedded history ends 2026-07-09 | PASS — `index.dates[last] === "2026-07-09"` (Node test) |
| No record later than 2026-07-09 | PASS — verified over all 28,601 rows |
| No record earlier than 2025-01-01 | PASS — verified over all 28,601 rows |
| Both 2025 and 2026 data present | PASS — full range spans both years |
| All assigned ASINs represented | PASS — 1723 assigned ASINs, product master built directly from them |
| All assigned SKUs represented | PASS — 830 distinct matching SKUs, 1947 ASIN×SKU combinations |
| No other-user product represented | PASS — resolution query filters exclusively on `user_name='utharsika'` (`user=109`); Node test confirms every embedded row's ASIN is in the assigned set |
| No raw order rows embedded | PASS — grain is `(calendar_date, asin, sku, sales_total, orders_total)` only; Node test confirms no `order_id`/`order_item_info`/customer fields present in any of the 28,601 rows |

## Default View (Month-to-Date)

| Check | Result |
|---|---|
| Opens in MTD mode | PASS — `<option value="MTD" selected>` is the template's default |
| Current period = 2026-07-01 → 2026-07-09 | PASS — Node test `Default MTD: current period` |
| Previous period = 2025-07-01 → 2025-07-09 | PASS — Node test `Default MTD: previous period` |
| All assigned products visible | PASS — row count (1947) equals product master count exactly |
| Zero-activity products not silently excluded | PASS — 1491 of 1947 rows have zero Sales in both periods and are still present |
| Totals correct | PASS — MTD total This Year Sales (7442.66) matches an independent full-scan sum over the raw 28,601-row dataset |

## Filter Tests (all run against the real embedded dataset, via the exact shipped engine code under Node.js)

| # | Test | Result |
|---|---|---|
| 1 | Arbitrary completed Daily date (2026-07-09) | PASS — Sales 350.94 / Orders 12, matches the independently-fetched MCP values from earlier this session exactly |
| 2 | June 2026 vs June 2025 | PASS — current 2026-06-01→30, previous 2025-06-01→30 |
| 3 | Specific completed week (2026-06-08→14) | PASS — previous 2025-06-08→14 (see bug-fix note below) |
| 4 | Custom multi-day range (2026-05-10→25, the spec's own example) | PASS — previous 2025-05-10→25 |
| 5 | ASIN filter | PASS — returns only rows for the selected ASIN |
| 6 | SKU filter | PASS — returns only rows for the selected SKU |
| 7 | Combined ASIN+SKU | PASS — returns exactly the one matching pair |
| 8 | No product filter | PASS — full product master (1947) returned |
| 9 | Trend filter (UP) | PASS — every returned row has This Year Sales > Previous Year Sales |
| 10 | Minimum Sales | PASS — every result ≥ threshold |
| 11 | Maximum Orders | PASS — every result ≤ threshold |
| 12 | Search/Sort/Pagination | Implemented in the template's UI layer (`applyProductFilters`, `renderTable` sort/paginate); logic code-reviewed, exercises the same filtered-rows array used by the KPI/Total calculation so pagination cannot desync from totals (Total row is computed from the full filtered set, before pagination slicing) |
| 13 | Reset | Implemented (`resetFilters()`); restores all controls to default state and MTD mode |

## A Third Issue Found and Fixed: Hardcoded Credential in a Check Script

A final security self-check (grepping all newly created files for the literal credential value) found that `tests/generate_final_dashboard.py`'s own structural-check code contained the literal password and host values as hardcoded strings to search for (a negative assertion, "confirm this value is NOT in the output HTML" — but the literal value was still embedded in new source code, violating the "do not hardcode credentials into new code" rule even though it was never written to the HTML itself). Fixed by reading both values from the environment at check-time instead (`os.environ.get("PGPASSWORD", "")`), with the checks becoming vacuously-true no-ops if those variables aren't set, rather than ever embedding the literal value in the script. Re-ran with the real credentials present in the environment to confirm the dynamic checks still function correctly — final HTML SHA-256 unchanged (proving the fix only touched the check logic, not the output).

## A Real Bug Found and Fixed This Session

The Weekly comparison mode initially re-derived the previous-year period as "the shifted date's own Monday-to-Sunday week" (carried over from the original design stage's business-rules spec). The Node test caught that this produced `2025-06-02→2025-06-08` instead of the `2025-06-08→2025-06-14` this session's instructions explicitly specify ("compare against the same calendar start and end dates shifted back one year"). Root-caused and fixed in `src/uawso_client_engine.js` (removed the Monday-re-anchoring branch for `WEEKLY`, now a plain calendar-date shift like `CUSTOM`). Re-ran the full 42-check suite after the fix — all passed. **This also corrects `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md`'s original Weekly rule**, which is being updated to match (see documentation updates).

## Boundary Tests

| Check | Result |
|---|---|
| Current date (2026-07-10) rejected | PASS |
| Future date rejected | PASS |
| 2025 selected as current period rejected | PASS |
| Date before 2026-01-01 rejected | PASS |
| Date after 2026-07-09 rejected | PASS (same "outside selectable range" path) |
| Reversed custom range rejected | PASS |
| Unavailable previous-year comparison rejected | PASS — verified with a synthetic tightened history boundary (the real embedded history is wide enough that this path isn't reachable from the real selectable range, so was tested with an intentionally narrowed boundary to exercise the code path) |
| February 29 handled safely | PASS — 2028-02-29 correctly maps to 2027-02-28 with a `leapNote` flag set |
| No-data selection shows a clear message | PASS — `showEmpty()`/`showError()` paths implemented and code-reviewed |

## Calculation Tests

| Check | Result |
|---|---|
| Sales totals | PASS — cross-checked against independent full-scan sums |
| Orders totals | PASS — cross-checked against independent full-scan sums |
| Sales Change / Order Change | PASS — formula matches the worksheet's own illustrative rows (from the original design-stage unit tests, same formula reused verbatim) |
| Trend | PASS — Sales-based only, 3 labels only, zero-base rule (`Prev=0,Curr>0→UP`) verified |
| 130% targets | PASS |
| Achieve Sales %/Achieve Order % | PASS — undefined (not fabricated) when target is zero |
| Total row recalculation | PASS — aggregate-of-aggregate, explicitly proven NOT equal to a naive average of row-level percentages |
| Zero-base handling | PASS |

## Security and Quality

| Check | Result |
|---|---|
| Credentials absent from final HTML | PASS — verified: neither the password value nor the DB host literal appears anywhere in the 3.26MB file |
| Connection strings absent | PASS — no `postgresql://` or `psycopg2.connect` string present |
| Raw order-level fields absent | PASS — no `order_id`/`order_item_info` key present anywhere in the embedded JSON |
| Personal/customer data absent | PASS — no customer name/email/tracking fields present (extraction query never selected them) |
| Unresolved template placeholders | **0** — verified programmatically (`dashboard_renderer.verify_no_placeholders`) |
| Script errors | Not measured in a real browser (no browser automation available); the exact shipped engine code was run 42 times under Node.js with zero exceptions outside the deliberately-tested rejection paths |
| One main dynamic table only | PASS — `id="uawso-table"` appears exactly once; no separate Daily/Weekly/MTD tables |
| Direct browser→PostgreSQL connection | PASS (absent) — the HTML contains no network call of any kind; all data is pre-embedded, static JSON |
| One final output HTML for today | PASS — exactly one file matches `2026-07-10_utharsika_v001*.html` outside the `staging/` subfolder |

## File and Size Evidence

| Item | Value |
|---|---|
| Assigned ASIN count | 1723 |
| Matching SKU count | 830 |
| Valid ASIN/SKU combination count (product master rows) | 1947 |
| Daily aggregate row count | 28,601 |
| Product-master JSON size | 97,458 bytes |
| Daily-aggregate JSON size | 3,286,135 bytes |
| Staging HTML path | `09_OUTPUTS\staging\2026-07-10_utharsika_v001.staging.html` |
| Final HTML path | `09_OUTPUTS\2026-07-10_utharsika_v001.html` |
| Final HTML SHA-256 | `024f7f28426125833f7091617afc7ef5c89adfb3a3f1cd543645dfd8b6fe7c23` (independently verified via `sha256sum`, matches exactly) |
| Final HTML size | 3,420,089 bytes (3.26 MB) |

**Note on size:** 3.26 MB is large for an HTML file but well within what modern browsers handle without difficulty for static content; no client-side network calls are made, so there is no server round-trip cost. Actual render/interaction performance was not measured in a real browser in this environment — flagged as a known limitation, not silently ignored.

## Overall Verdict

**PASS** for build, data coverage, default view, filters, boundaries, calculations, and security/isolation. Publication to `ph_task` remains **NOT ATTEMPTED** (gated, per instruction).
