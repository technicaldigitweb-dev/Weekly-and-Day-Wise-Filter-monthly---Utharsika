# UAWSO REQ-02-D01 — Complete Real-Data ASIN-Level HTML: Build & Validation

**Requirement ID:** REQ-02
**Deliverable ID:** REQ-02-D01
**Execution timestamp:** 2026-07-15 14:09:59 (Asia/Colombo)
**Status:** New HTML created and validated. **Not published to `ph_task`** — publication requires a separate user approval (Section 18 of the governing task).

---

## 1. Source Date Range

| Item | Value |
| ----- | ----- |
| Source maximum `order_date` at execution time | 2026-07-15 (today — a partial/incomplete day) |
| Selected safe end date | **2026-07-14** |
| Reason considered complete | Current (2026-07-15) is always excluded per the standing "current incomplete day excluded" rule — 2026-07-14 is the latest calendar day with a full day already elapsed |
| Start date | 2025-01-01 |
| Reporting days | 560 |
| Reporting months | 19 |
| Selectable current-period range | 2026-01-01 → 2026-07-14 |

## 2. Assigned ASIN Scope

| Item | Value |
| ----- | ----- |
| Current assigned ASIN count | 1,723 |
| Previous baseline (same day, REQ-01-D03/REQ-02-D01 discovery) | 1,723 |
| Added | 0 |
| Removed | 0 |
| ASINs with duplicate assignment rows | 0 |
| Duplicate `order_item_info` caused by assignment joins | 0 |

No scope drift; no multiplication risk. Full detail: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_asin_scope_comparison.csv`.

## 3. Order Status Rule

Dynamic exclusion rule unchanged: `order_status IS NOT NULL AND BTRIM(order_status) <> '' AND BTRIM(order_status) NOT IN ('Cancelled','Canceled')`.

Discovered statuses in the assigned/UK/AMAZON+REPLACEMENT scope, full date range: Canceled (excluded), Cancelled (excluded), Completed, Deleted, New, Pending, Refunded (all included). `Inprogress`/`Hold` exist elsewhere in the database but contribute zero rows in this exact scope today — the rule remains dynamic, not a hardcoded list. Full per-status Sales/Orders/Quantity contribution: `07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_status_contribution.csv`.

## 4. Final Report Grain

**One row per assigned ASIN.** SKU is not part of the SQL `GROUP BY`, the Python/JSON data model, the HTML table, sorting, filtering, search, CSV headers, CSV rows, or totals — it was removed at the extraction layer (`extract_uawso_v5_asin_level.py` groups directly by `(date, asin)`, never by `(date, asin, sku)`), not hidden with CSS. Verified: 1,723 canonical rows for 1,723 assigned ASINs, zero duplicates.

## 5. Image Source and Coverage

| Item | Value |
| ----- | ----- |
| Source | `public.listing_data.main_image_url` |
| Join | `ref_id = ASIN`, `which_channel=1`, `market_place='UK'`, `wrong_sku=0` |
| Assigned ASINs | 1,723 |
| Image-covered ASINs | 1,699 |
| No-image ASINs | 24 (17 no valid listing row + 7 all-blank image) |
| Multi-image ASINs | 227 (max 3 distinct images, max 6 candidate rows) |
| Selection rule | Lowest `listing_data.id` among valid rows (`ROW_NUMBER() OVER (PARTITION BY ref_id ORDER BY id ASC) = 1`) — never an unordered `LIMIT 1` |
| Business status | `BUSINESS-CONFIRMED` (Utharsika, REQ-02-D01 Section 5) — any valid image is acceptable; lowest-id exists only for run-to-run stability |

Evidence: `2026-07-15_utharsika_v004_image_coverage` (see `2026-07-15_uawso_image_field_coverage.csv`), `2026-07-15_utharsika_v004_multi_image_selection.csv`, `2026-07-15_utharsika_v004_no_image_report.csv`.

## 6. ASIN-Level KPI Reconciliation (full range, 2025-01-01 → 2026-07-14)

| Metric | PostgreSQL (direct SQL) | HTML-embedded engine (Node.js, actual shipped data) | Match |
| ----- | ----- | ----- | ----- |
| Amazon Sales (FBM+FBA) | £672,020.97 | £672,020.97 | YES |
| Vendor Sales | £46,814.94 | £46,814.94 | YES |
| Total Sales | £718,835.91 | £718,835.91 | YES |
| Total Orders | 34,454 | 34,454 | YES |
| FBM+FBA Quantity | 42,418 | 42,418 | YES |
| Vendor Units | 4,748 | 4,748 | YES |
| Total Quantity | 47,166 | 47,166 | YES |
| Row count | 1,723 | 1,723 | YES |
| Duplicate ASIN rows | 0 | 0 | YES |

The "HTML-embedded engine" figures were produced by extracting the actual `product_master`/`daily_aggregates_asin`/`vendor_periods` JSON payloads out of the real, promoted `09_OUTPUTS\2026-07-15_utharsika_v004.html`, loading `src/uawso_client_engine.js` (the identical file injected into the HTML) in Node.js, and calling the exact same functions the browser calls (`buildCanonicalRowsV5`, `sumRangeByAsinV5`, `computeRowsV5`, `computeTotalV5`) — not a hand re-derivation. Full detail: `2026-07-15_utharsika_v004_asin_level_kpi_reconciliation.csv`.

## 7. Source-to-Output Order-Item Reconciliation

| Metric | Value |
| ----- | ----- |
| Source distinct `order_item_info` (flat, no grouping) | 34,454 |
| Output distinct `order_item_info` (grouped by date+ASIN, summed) | 34,454 |
| Missing order items | 0 |
| Extra order items | 0 |
| Duplicate order items | 0 |

Flat vs. grouped-and-summed agreement is the formal proof that no `order_item_info` spans multiple ASINs or multiple date/ASIN partitions in the shipped output. Full detail: `2026-07-15_utharsika_v004_order_item_reconciliation.csv`.

## 8. CSV Reconciliation

CSV export and the visible HTML table/KPI cards derive from the identical `computeRowsV5`/`computeTotalV5` output (no separate CSV computation path). Independently re-simulated in Node.js: Total Sales, Total Orders, and Total Quantity all match exactly (£718,835.91 / 34,454 / 47,166). CSV headers contain no `SKU` column; contain `Image URL` (plain text, blank convention not needed since every row always has a value — either a URL or is omitted per the no-image state on the visible table; CSV writes the literal string when no URL exists, see `downloadCsv`). Full detail: `2026-07-15_utharsika_v004_csv_reconciliation.csv`.

## 9. Tests

23/23 checks passed in `05_IMPLEMENTATION\tests\test_uawso_client_engine_v5.js`, covering all 17 required items (row grain, SKU-aggregation-under-ASIN, distinct-Orders-once, multi-SKU non-duplication, SKU absence from HTML/CSV, Image column presence, valid image selection, deterministic lowest-id tie-break, no-image/image-loading-issue states, Vendor counted once, status exclusions, date boundary, filename-overwrite guard, ph_task-write absence). Pre-existing v1/v2/v3 engine test suites re-run and still 100% pass (42/42, 19/19, 21/21) — confirms the additive-only nature of the engine changes caused zero regression.

## 10. Historical Output Protection

All 4 pre-existing `09_OUTPUTS\*.html` files re-hashed identical to their pre-task baseline. `ph_task` rows 157 and 237 re-queried: content unchanged (row 237 byte-identical MD5 to its local file; row 157 remains in its already-documented pre-existing incident state, unrelated to this task), `updated_at` unchanged from the value observed at the start of this task. No database write occurred. Full detail: `2026-07-15_utharsika_v004_protected_html_hashes.csv`, `2026-07-15_utharsika_v004_protected_ph_task_hashes.csv`.

## 11. Staging → Final Promotion

| Item | Value |
| ----- | ----- |
| Staging path | `09_OUTPUTS\staging\2026-07-15_utharsika_v004.staging.html` |
| Staging SHA-256 | `aa4ea555338e0455d65f3c14441c37bddff012783b7c0602e4598bd04a0dd94a` |
| Final path | `09_OUTPUTS\2026-07-15_utharsika_v004.html` |
| Final SHA-256 (re-read after promotion) | `aa4ea555338e0455d65f3c14441c37bddff012783b7c0602e4598bd04a0dd94a` (matches staging exactly) |
| Final byte size | 5,112,262 |
| Promotion method | temp-file write → hash verify → target-does-not-exist re-check → `os.rename` (atomic, fails on Windows if target exists) → re-read and re-hash |
| Version selection | v004 — v001/v002 already used in `09_OUTPUTS`; v003 was skipped because it is already claimed (as a dry-run artifact, never published) by the paused automation runner's evidence trail (`07_EVIDENCE\automation\runs\2026-07-15\2026-07-15_utharsika_v003_validation.md`) — using v004 avoids any ambiguity with that unrelated, unpublished dry run |

## 12. Extraction Method Disclosure

`05_IMPLEMENTATION\src\extract_uawso_v5_asin_level.py` is the production-ready, standalone extraction script (matching the project's established `psycopg2` + `config.py` pattern) and is the source of truth for the SQL logic used. This session's Bash/PowerShell tool environment has no interactive PostgreSQL credentials available (`PGHOST`/`PGPASSWORD` etc. are unset, consistent with the project's standing decision never to persist a `.env.local`), so the actual live data for this run was obtained by executing the equivalent, identical SQL through the already-connected read-only `postgres` MCP tool, then converting its output into the same JSON file shapes the script itself would produce (`07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_*.json`). This is disclosed transparently rather than silently: the query logic, filters, and grouping used via the MCP tool are byte-identical to what is written in the script, and every resulting figure was independently cross-checked against a second, differently-shaped query (flat vs. grouped) as shown in Sections 6–7 above.

## 13. Final PASS/FAIL

```
PASS:
- complete current real data fetched (2025-01-01 to 2026-07-14, 1,723 ASINs)     YES
- one row per ASIN generated                                                     YES
- all SKU activity aggregated under its ASIN                                     YES
- SKU absent from HTML and CSV                                                   YES
- one image selected per ASIN (deterministic, business-confirmed)                YES
- no-image and loading-failure behavior implemented, distinct states             YES
- Sales, Orders, Quantity reconcile to the current live source snapshot          YES (0 difference)
- duplicate order items = 0 / missing = 0 / extra = 0                            YES
- all tests pass (23/23 new + 82/82 pre-existing)                                YES
- new final HTML created under a new unused version (v004)                       YES
- previous HTML files unchanged                                                  YES
- existing ph_task rows unchanged                                                YES
- no database write occurred                                                     YES
```

**FINAL STATUS: PASS**

Not published to `ph_task`. Awaiting user review and separate publication approval per Section 18.
