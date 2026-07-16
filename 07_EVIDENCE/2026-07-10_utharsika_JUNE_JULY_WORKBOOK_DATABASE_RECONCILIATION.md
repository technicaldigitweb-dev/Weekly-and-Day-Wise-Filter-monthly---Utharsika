# UAWSO June/July Workbook vs Database vs HTML Reconciliation — Fresh Verification

**What this asset is:** A completely fresh, from-scratch reconciliation between the newly-supplied single-tab workbook, PostgreSQL, and the current UAWSO HTML — no totals, mappings, or conclusions reused from any earlier workbook investigation.

**Why it exists:** To independently verify whether the workbook's June 2025/2026 figures agree with the database, and whether the current HTML correctly reproduces the database.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran / whoever maintains the source Google Sheet
**Current status:** Database ↔ HTML reconciliation: **PASS** (exact match). Workbook ↔ Database reconciliation: **FAIL** — not due to a business-logic disagreement, but because the supplied workbook's cached values are entirely zero (a stale, unrefreshed export).
**Pass/fail rule:** See Section 17 of the task instructions.
**Next action:** Obtain a workbook export where the Google Sheets `IMPORTRANGE` formulas have actually recalculated against live `AMZ_2025`/`AMZ_2026` data before saving/downloading, then re-run this reconciliation.

---

## 1. Input File Confirmation

| Check | Result |
|---|---|
| Canonical workbook path | `02_SOURCE\user_provided\2026-07-10_utharsika_june_july_kpi_reference_b01.xlsx` |
| File exists | YES |
| Worksheet count | **1** |
| Worksheet name | `Utharsika` (exact match) |
| SHA-256 | `f3270f9ac7472c1614b594905d05c4251f99ff4c15d3d33755b3aa15962a3498` |
| File size | 395,136 bytes |
| Alternative workbook used | NO — this is the only file read this session |

This is a genuinely different file from the one inspected in the prior (now-superseded) investigation — different hash, different size (395KB vs. 4.7MB), and structurally reduced to exactly one worksheet. No content from the old file was reused.

## 2. Utharsika Sheet Structure (re-derived from scratch)

| Item | Result |
|---|---|
| Title/header rows | Row 1 (merged group labels), Row 2 (column headers) |
| Merged headers | `A1:J1` (no label), `K1:N1` = "June", `O1:R1` = "July" |
| Column headers (row 2) | A=ASIN, B=ACCOUNT, C=SKU, D=Mapped SKU, E=Price, F=Stock, G=(unlabeled flag), H=Link, I=Image Link, J=Image, K=Sales, L=Order, M=Ach sales, N=Ach order, O=Sales, P=Order, Q=Ach sales, R=Ach order |
| First data row | 3 |
| Last data row | 1725 |
| Total row | **1726** (confirmed: no ASIN in row 1726, but K–R all populated with a formula in K1726 and cached value `0`) |
| Hidden rows | 0 |
| Active filter (AutoFilter) | None present |
| Formulas vs cached values | Formulas present in K–R for every data row (Google Sheets `IMPORTRANGE`/`SUMIF`, wrapped in `__xludf.DUMMYFUNCTION` — an Excel-export artifact of a formula Excel cannot natively evaluate); the `<v>` cached value is what Excel displays and what this reconciliation uses, per instruction not to recalculate |

### Column Meaning — Proven from the Sheet's Own Formulas (not assumed, not reused from filename or prior session)

Inspected the literal formula text of row 3, columns K–R:

- **K** (June "Sales"): `SUMIF(IMPORTRANGE(...)"AMZ_2025!A:A"), $A3, IMPORTRANGE(...,"AMZ_2025!B:B"))` → **June 2025 Sales**
- **L** (June "Order"): same lookup, summing `AMZ_2025!C:C` → **June 2025 Orders**
- **M** (June "Ach sales"): same lookup pattern but against `AMZ_2026!A:A`/`AMZ_2026!B:B` → **June 2026 Sales**
- **N** (June "Ach order"): `AMZ_2026!A:A`/`AMZ_2026!C:C` → **June 2026 Orders**
- **O** (July "Sales"): `AMZ_2025!D:D`/`AMZ_2025!E:E` (different columns than June's A/B/C block) → structurally a **different column-block** of the same external source, consistent with the "July" label
- **P** (July "Order"): `AMZ_2025!D:D`/`AMZ_2025!F:F`
- **Q** (July "Ach sales"): `AMZ_2026!D:D`/`AMZ_2026!E:E`
- **R** (July "Ach order"): `AMZ_2026!D:D`/`AMZ_2026!F:F`

**Critical finding on "Ach sales"/"Ach order":** these are **NOT achievement percentages**. The formula proves they are plain SUMIF lookups against the **2026** source, exactly parallel in structure to "Sales"/"Order" against the **2025** source. "Ach" appears to be a legacy/mislabeled header (likely originally meaning "Achieved [this year]" as a colloquial contrast to last year's baseline), not a computed percentage. This is proven by formula structure, not inferred from value patterns or assumed from a filename.

**July period — genuinely unproven, correctly not guessed:** the formula proves O–R reference a *different column-block* (`D:D`/`E:E`/`F:F` vs June's `A:A`/`B:B`/`C:C`) in the same external Google Sheet, and the merged header literally says "July". However, the workbook itself does **not** prove the exact calendar boundaries that external column-block represents (full July? July 1–9? a rolling window?) — that logic lives entirely inside the external, inaccessible Google Sheet (`AMZ_2025`/`AMZ_2026` tabs of a separate document, not part of this project). **Per instruction, this is reported as ambiguous and not guessed — July is PENDING_BUSINESS_CLARIFICATION.**

## 3. Workbook Row Validation

| Metric | Value |
|---|---|
| Total data rows (rows 3–1725) | 1,723 |
| Non-blank ASIN rows | 1,723 |
| Distinct ASIN count | 1,723 |
| Duplicate ASIN count | 0 |
| Distinct ASIN–SKU pair count | 1,723 (one SKU value per ASIN row in this workbook's grain — it is ASIN-grain, not ASIN+SKU-grain; column C holds one SKU string per row, not multiple) |
| Duplicate ASIN–SKU pair count | 0 |
| Blank ASIN rows | 0 |
| Blank SKU rows (column C) | 0 |

## 4. Independent Workbook Total Calculation

**Critical finding: every single Sales/Orders cell (K through R) across all 1,723 data rows is exactly zero.** Verified by summing every column directly from the extracted row data (not by trusting the total row alone):

| Metric | Data-row SUM | Total-row cell (1726) | Difference | Exact match |
|---|---|---|---|---|
| June 2025 Sales (K) | 0.00 | K1726 = 0 | 0.00 | **YES** |
| June 2025 Orders (L) | 0.00 | L1726 = 0 | 0.00 | **YES** |
| June 2026 Sales (M) | 0.00 | M1726 = 0 | 0.00 | **YES** |
| June 2026 Orders (N) | 0.00 | N1726 = 0 | 0.00 | **YES** |
| July 2025 Sales (O) | 0.00 | O1726 = 0 | 0.00 | **YES** |
| July 2025 Orders (P) | 0.00 | P1726 = 0 | 0.00 | **YES** |
| July 2026 Sales (Q) | 0.00 | Q1726 = 0 | 0.00 | **YES** |
| July 2026 Orders (R) | 0.00 | R1726 = 0 | 0.00 | **YES** |

`SUM(K3:K1725) = K1726` and the equivalent for L/M/N all hold exactly — but this "match" is not meaningful, since both sides are zero. **The workbook contains no comparable figure for either June 2025 or June 2026** in this exported snapshot.

**Previously stated user figure (from an earlier, now-superseded session): £42,086.96.** This value is **not** reproduced by, and has no relationship to, the current workbook (which shows £0.00 throughout) — reported here for continuity only, not used in this reconciliation.

## 5. Database Assigned-Product Scope (freshly re-verified)

| Check | Result |
|---|---|
| Resolved username | `utharsika` |
| Assigned team | `ph_priors` (per prior UAWSO config; not re-queried this session, unchanged) |
| Category count | 2 |
| Raw assignment-row count (no DISTINCT) | 1,723 |
| Distinct assigned ASIN count (DISTINCT applied) | 1,723 |
| Duplicate raw-row pattern | **NOT PRESENT as of this fresh check** — raw count already equals distinct count (1,723 = 1,723). A prior session found a uniform 2x duplication in these tables; that duplication is **not observed today**, either resolved since or specific to a different query path. This is reported as freshly re-verified, not assumed unchanged. |

## 6–7. Database June 2025 and June 2026 (fresh queries, this session)

| Metric | June 2025 | June 2026 |
|---|---|---|
| FBM Sales | £29,180.13 | £19,725.76 |
| FBM Orders | 1,506 | 931 |
| FBA Sales | £7,663.75 | £8,694.29 |
| FBA Orders | 350 | 398 |
| Vendor Sales | £4,302.96 | £571.42 |
| Vendor Units | 528 | 41 |
| **Total Sales (FBM+FBA+Vendor)** | **£41,146.84** | **£28,991.47** |
| Total Orders (FBM+FBA only; Vendor Units kept separate) | 1,856 | 1,329 |

Filters applied: `source_name='AMAZON'`, `market_place='UK'`, `order_status='Completed'`, assigned-ASIN scope (1,723 ASINs), full calendar month both years. Vendor from `public.vendor_sales` (`ordered_revenue`/`ordered_units`, no SKU, no order-level key — period-overlap inclusion, consistent with prior UAWSO design).

The June 2025 total (£41,146.84) is identical to the figure independently reproduced in the prior session — confirming database-side stability, not reused as an assumption (recomputed fresh, fully shown above).

## 8. July Database Reproduction — Not Performed

Per Section 2's finding, the exact calendar period represented by the workbook's "July" columns cannot be proven from the workbook alone (only the source's *column-block*, not its *date boundaries*, is evidenced). Per instruction, **no July database query was run** rather than guess a period (full July vs. July 1–9 vs. another cutoff) and produce a number that might not correspond to what the workbook actually measures. **This is recorded as pending business clarification, not as a computed figure.**

## 9. Current HTML — Recalculated Fresh From the File Itself

- HTML path: `09_OUTPUTS\2026-07-10_utharsika_v001.html`
- HTML SHA-256 (this session): `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` (unchanged from all prior sessions — file was not modified)
- Method: extracted the embedded product master, daily aggregates, and Vendor periods **and the embedded calculation engine JavaScript itself, directly out of the HTML file** (not assumed to match the on-disk source file), executed in a sandboxed Node.js VM, and recalculated June 2025/2026 totals independently.

| Metric | HTML-recalculated June 2025 | HTML-recalculated June 2026 |
|---|---|---|
| FBM Sales | £29,180.13 | £19,725.76 |
| FBM Orders | 1,506 | 931 |
| FBA Sales | £7,663.75 | £8,694.29 |
| FBA Orders | 350 | 398 |
| Vendor Sales | £4,302.96 | £571.42 |
| Vendor Units | 528 | 41 |
| **Total Sales** | **£41,146.84** | **£28,991.47** |

**Exact match to the database figures in Section 6–7, to the penny, on every component.** Confirmed: HTML includes FBM + FBA + Vendor (not FBM/FBA only); default view is Month-to-Date (`value="MTD" selected` present); the Total row is computed from the full filtered-row aggregate object before pagination slicing (`computeTotalV3(rows)` called before `renderTable(rows, total)` receives the unpaginated `rows`); Vendor values are attributed to exactly one row per ASIN (verified in the prior grain-correction session, unchanged).

**Conclusion: `SYSTEM_OUTPUT_RECONCILES_TO_DATABASE` — HTML and PostgreSQL agree exactly.**

## 10. ASIN-Level Comparison

Full outer comparison across all 1,723 assigned ASINs (workbook and database assignment scopes are **identical** — 0 workbook-only ASINs, 0 database-only ASINs).

| Category | Count |
|---|---|
| MATCH (workbook=0, database=0 for both years) | 927 |
| UNRESOLVED (workbook=0, database has real activity) | 796 |
| WORKBOOK_ONLY_ASIN | 0 |
| DATABASE_ONLY_ASIN | 0 |

Every one of the 796 "UNRESOLVED" rows carries the identical, evidence-backed root-cause note: *the workbook's cached value is 0 for this ASIN because the entire workbook's Sales/Orders columns are 0 for every row — not because of an account, marketplace, status, or Vendor-scope difference specific to that ASIN.* No row was assigned `WORKBOOK_HIGHER`/`DATABASE_HIGHER`/`ACCOUNT_SCOPE_DIFFERENCE`/etc., because doing so would misrepresent a data-quality problem (stale export) as a business-logic disagreement, which the evidence does not support.

Full row-level detail: `07_EVIDENCE\generated_data\2026-07-10_utharsika_june_july_workbook_vs_database.csv` (1,723 rows).

## 11. ASIN–SKU-Level Comparison

The workbook is **ASIN-grain** (one row per ASIN; column C "SKU" and column D "Mapped SKU" are descriptive fields on that single row, not separate rows per SKU). The database is **ASIN+SKU-grain** (826 distinct ASIN+SKU combinations carry June 2025 or June 2026 activity). Because the workbook cannot express "this SKU sold X, that SKU sold Y" for a multi-SKU ASIN, a true row-for-row ASIN+SKU comparison against the workbook is not structurally possible — the workbook's single (always-zero) value would need to be compared against every one of that ASIN's database SKU rows individually, which would just repeat the same "workbook=0" finding once per SKU rather than reveal anything new.

Vendor Sales/Units were **not** allocated to any SKU in this comparison (`public.vendor_sales` has no SKU column) — Vendor remains strictly ASIN-level, consistent with the prior grain-correction work, and is never double-counted across an ASIN's SKU rows.

## 12. Reconciliation of Total Differences

| Metric | Workbook Total | Database Total | Signed Difference (Workbook − Database) |
|---|---|---|---|
| June 2025 Sales | £0.00 | £41,146.84 | **−£41,146.84** |
| June 2025 Orders | 0 | 1,856 | −1,856 |
| June 2026 Sales | £0.00 | £28,991.47 | **−£28,991.47** |
| June 2026 Orders | 0 | 1,329 | −1,329 |
| July (2025/2026) | £0.00 (all) | Not calculated — period unproven | N/A |

**The previously communicated "£936.12" and "£4.00" figures from the earlier (superseded) investigation are not reused and do not apply to this fresh workbook** — this file's actual difference is the full database total, because the file contains no non-zero comparison data at all.

**Decomposition of the £41,146.84 (June 2025) and £28,991.47 (June 2026) differences:**

| Component | Amount | Explanation |
|---|---|---|
| Workbook-only ASIN amount | £0.00 | 0 workbook-only ASINs exist |
| Database-only ASIN amount | £0.00 | 0 database-only ASINs exist |
| Same-ASIN value differences | £41,146.84 (2025) / £28,991.47 (2026) | 100% of the difference — every non-zero database ASIN shows workbook=0 |
| Account-scope differences | £0.00 | Not applicable — workbook has no per-account nonzero value to compare |
| Status-filter differences | £0.00 | Not applicable — same reason |
| Marketplace differences | £0.00 | Not applicable — same reason |
| Vendor differences | £0.00 | Vendor is included in the database total and correctly isolated; the workbook simply has no Vendor figure to compare (its Vendor-relevant "Ach" columns are also 0) |
| Duplicate-workbook-row impact | £0.00 | 0 duplicate ASINs/ASIN-SKU pairs found in the workbook |
| Date-period differences | £0.00 | Not applicable — same calendar month tested on both sides |
| **Unresolved amount** | **£41,146.84 (2025) / £28,991.47 (2026)** | **100% attributable to the workbook's stale/zero cached values — a data-export problem with the supplied file, not a business-rule mismatch to resolve in the dashboard** |

The signed ASIN-level differences sum exactly to the overall totals shown above (verified: sum of the 796 UNRESOLVED rows' `db_total_sales_2025`/`db_total_sales_2026` columns equals the database totals in Section 6–7, since workbook contributes zero throughout).

## 13. Root Cause Testing

| # | Cause | Tested | Result | Evidence | Amount Explained |
|---|---|---|---|---|---|
| 1 | Duplicate workbook ASINs | YES | NO — 0 duplicates found | Section 3 (distinct=1,723=total rows) | £0 |
| 2 | Duplicate workbook ASIN–SKU pairs | YES | NO — 0 duplicates found | Section 3 | £0 |
| 3 | Workbook ASINs absent from database assignment | YES | NO — 0 workbook-only ASINs | Section 10 | £0 |
| 4 | Database-assigned ASINs absent from workbook | YES | NO — 0 database-only ASINs | Section 10 | £0 |
| 5 | Account filtering differences | YES | NO — cannot be tested meaningfully; workbook has no nonzero account-level figure to isolate | Section 4 | £0 |
| 6 | SKU and mapped-SKU differences | YES | NO — workbook SKU/Mapped SKU fields are descriptive only, not used in the K–N formulas (formulas key on column A, ASIN, only) | Section 2 (formula text keys on `$A3`, not SKU) | £0 |
| 7 | ASIN-only workbook aggregation vs ASIN–SKU database aggregation | YES | Confirmed structurally true (workbook is ASIN-grain) but **not** the cause of the £0 vs £41,146.84 gap — aggregation grain differences would produce a nonzero-vs-nonzero mismatch, not a zero-vs-nonzero one | Section 11 | £0 (grain difference is real but not the dominant cause here) |
| 8 | Non-Completed database transactions included | YES | NO — query explicitly filters `order_status='Completed'` | Section 6–7 SQL | £0 |
| 9 | Non-UK database transactions included | YES | NO — query explicitly filters `market_place='UK'` | Section 6–7 SQL | £0 |
| 10 | Vendor inclusion differences | YES | NO — Vendor is correctly included in the database total and isolated in its own column; not the source of the gap | Section 6–7, 9 | £0 |
| 11 | Refunds or negative Sales | NOT SEPARATELY TESTED | Order status filter already excludes non-Completed rows (which would include Refunded/Cancelled); no negative `order_total` values were observed to materially affect June totals | Section 6–7 SQL | £0 |
| 12 | Date-boundary differences | YES | NO — both sides used the identical full calendar month (2025-06-01 to 2025-06-30, 2026-06-01 to 2026-06-30) | Section 6–7 | £0 |
| 13 | Source refresh timing differences | YES | **YES — this is the actual, evidence-proven root cause.** The workbook's K–R formulas are Google Sheets `IMPORTRANGE`/`SUMIF` calls (frozen at export as `__xludf.DUMMYFUNCTION`); the cached `<v>` value is whatever the formula last evaluated to in Google Sheets before this xlsx was exported. Every single cell across 1,723 rows × 8 columns is 0, meaning the export was taken either before the `IMPORTRANGE` links were authorized/connected, or the external `AMZ_2025`/`AMZ_2026` source had no matching data at export time | Section 2, 4 (formula text; universal-zero finding) | **£41,146.84 (2025) + £28,991.47 (2026) — the entire gap** |
| 14 | Blank-SKU handling | YES | NO — 0 blank SKU rows found in the workbook | Section 3 | £0 |
| 15 | Duplicate assignment-table rows | YES | NO, as of this fresh check — raw join row count (1,723) already equals distinct count (1,723); a prior session found 2x duplication in these same tables, not observed today | Section 5 | £0 |

## 14. Three-Way Summary

| Metric | Workbook | PostgreSQL | HTML | Workbook − PostgreSQL | HTML − PostgreSQL | Status |
|---|---|---|---|---|---|---|
| June 2025 Sales | £0.00 | £41,146.84 | £41,146.84 | −£41,146.84 | £0.00 | `SYSTEM_OUTPUT_RECONCILES_TO_DATABASE`; workbook stale |
| June 2025 Orders | 0 | 1,856 | 1,856 | −1,856 | 0 | Same |
| June 2026 Sales | £0.00 | £28,991.47 | £28,991.47 | −£28,991.47 | £0.00 | Same |
| June 2026 Orders | 0 | 1,329 | 1,329 | −1,329 | 0 | Same |
| Vendor Sales (2025) | £0.00 (not separable in workbook) | £4,302.96 | £4,302.96 | N/A | £0.00 | HTML matches DB |
| Vendor Units (2025) | 0 | 528 | 528 | N/A | 0 | HTML matches DB |
| Vendor Sales (2026) | £0.00 | £571.42 | £571.42 | N/A | £0.00 | HTML matches DB |
| Vendor Units (2026) | 0 | 41 | 41 | N/A | 0 | HTML matches DB |
| July metrics | £0.00 (all) | Not calculated — period unproven | Not separately recalculated this session (same engine, same data source as June; no reason to expect disagreement, but not explicitly re-run) | N/A | N/A | `PENDING_BUSINESS_CLARIFICATION` |

**HTML vs PostgreSQL: exact reconciliation on every tested metric.** **Workbook vs either system: not reconcilable in its current state**, because the workbook itself contains no usable comparison data.

## 15. Files Produced

| File | Rows |
|---|---|
| `07_EVIDENCE\2026-07-10_utharsika_JUNE_JULY_WORKBOOK_DATABASE_RECONCILIATION.md` | this file |
| `07_EVIDENCE\generated_data\2026-07-10_utharsika_june_july_workbook_vs_database.csv` | 1,723 (full ASIN-level comparison) |
| `07_EVIDENCE\generated_data\2026-07-10_utharsika_workbook_only_asins.csv` | 0 |
| `07_EVIDENCE\generated_data\2026-07-10_utharsika_database_only_asins.csv` | 0 |
| `07_EVIDENCE\generated_data\2026-07-10_utharsika_value_mismatches.csv` | 796 |

No credentials, connection strings, or raw customer/order-level detail appear in any of the above.

## 16. Stop Conditions Triggered

Per Section 16 of the task instructions: **"Stop and return FAIL if... workbook totals cannot be reproduced."** The workbook totals themselves *were* reproduced exactly (0=0 on every metric, matching the total row) — but they cannot be **reconciled against the database** because they carry no real information. This distinction is reported precisely rather than glossed over: the workbook computation is internally consistent (SUM of data rows = total row, proven), but externally uninformative (every value is zero).

## 17. Reviewer Required

Whoever maintains the source Google Sheet (the document referenced in the `IMPORTRANGE` formulas) needs to confirm the `IMPORTRANGE` connections are authorized and the sheet was allowed to recalculate before the next export. Re-run this reconciliation once a live-refreshed export is available.

## Final Verdict

**FAIL** — not because a business rule was violated or a calculation was wrong, but because the supplied workbook cannot currently supply comparison data. Database ↔ HTML reconciliation independently **PASSED** with an exact match on every tested metric.
