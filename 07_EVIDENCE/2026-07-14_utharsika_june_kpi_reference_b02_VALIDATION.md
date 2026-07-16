# UAWSO v002 — June KPI Reference CSV (b02) Validation

**Purpose:** Read-only validation of the user-supplied reference file `2026-07-14_utharsika_june_kpi_reference_b02.csv` (7 ASIN/SKU rows, June 2025 and June 2026 Sales/Orders) against PostgreSQL, the published `v002.html`, and the stored `ph_task` row — without modifying any source, output, or published asset.

**Owner:** Satheskanth
**Status:** **PASS** (6 of 7 rows exact-match; 1 row is a documented `MAPPED_SKU_MATCH_ONLY` case, not a failure of the system)

---

## 1. Source CSV

| Field | Value |
|---|---|
| Path | `02_SOURCE\user_provided\2026-07-14_utharsika_june_kpi_reference_b02.csv` |
| SHA-256 | `3e9970b0f6967f6deceee967ccdccfc1de19978e0c0c097cb89725101686e5c2` |
| Encoding | ASCII |
| Delimiter | comma |
| Row count | **7** data rows (confirmed) |
| Columns | `ASIN, ACCOUNT, SKU, Mapped SKU, 2025 - Sales, 2025 - Order, 2026 - sales, 2026 - order` (exact match to expected) |
| Duplicate rows | 0 |
| Duplicate ASIN–SKU pairs | 0 (all 7 ASINs distinct) |
| Blank ASIN values | 0 |
| Blank SKU values | 0 |
| Blank Mapped SKU values | 4 of 7 (rows 3, 4, 5, 6) |
| Numeric-column parsing | Clean — plain integers/decimals, no currency symbols, no thousands separators |
| Leading/trailing whitespace | None found |
| Invalid ASIN/SKU formatting | None — all ASINs are standard 10-char Amazon identifiers; all SKUs follow the project's established `<product>+<accessory>` bundle-string convention |

The CSV was read only; not altered.

## 2. Reference Periods

| Column | Interpreted as |
|---|---|
| `2025 - Sales` | June 2025 Ordered Product Sales (`order_date::date >= '2025-06-01' AND < '2025-07-01'`) |
| `2025 - Order` | June 2025 Total Orders |
| `2026 - sales` | June 2026 Ordered Product Sales (`order_date::date >= '2026-06-01' AND < '2026-07-01'`) |
| `2026 - order` | June 2026 Total Orders |

No year-to-date, January-to-June, or full-year comparison was performed.

## 3. Assigned Scope

All 7 reference ASINs confirmed assigned to Utharsika via `public.user` → `public.ph_categories` → `public.ph_cate_products` (`which_channel=1`):

| ASIN | Assigned | Category count | Distinct assigned-user count | Shared |
|---|---|---|---|---|
| B084RC5DQG | YES | 1 | 1 | NO |
| B0GY3G4S1F | YES | 1 | 1 | NO |
| B0GY423LQJ | YES | 1 | 1 | NO |
| B0H38YJTN8 | YES | 1 | 1 | NO |
| B0H393YSKV | YES | 1 | 1 | NO |
| B0H3918NPV | YES | 1 | 1 | NO |
| B0D9Q142ZZ | YES | 1 | 1 | NO |

**0 rows out of scope.** No other user's records were included.

## 4. Approved v002 Metric Definitions (applied verbatim, unchanged)

- **Ordered Product Sales** = `SUM(item_price × quantity)`, `source_name='AMAZON'`, `order_status IN ('Completed','Refunded')`. A refund does not remove Sales from the original order month.
- **Total Orders** = `COUNT(DISTINCT order_item_info)`, `order_status='Completed'`, `source_name IN ('AMAZON','REPLACEMENT')`. Vendor Units are never counted as Orders; no Vendor Orders value was invented (`N/A` throughout, consistent with all prior evidence).
- **Quantity** was calculated only as supporting evidence (see Section 7 detail), never substituted for a reference comparison field (the reference CSV has no Quantity column).

## 5. Account Matching

**Normalization rule applied:** trim whitespace, case-insensitive comparison, strip the literal `"amazon "` prefix used in `ss_name` — no other transformation. Under this rule, `ss_name` values found in the database for these 7 ASINs:

| ss_name (raw) | Normalizes to | Source | Status |
|---|---|---|---|
| `amazon Ledsone` | Ledsone | AMAZON | (used by rows 1, 7) |
| `amazon Dcvoltage` | Dcvoltage | AMAZON | (used by rows 2–6) |
| `amazon Dcvoltage_amazon` | **does not normalize to "Dcvoltage" under the applied rule** | REPLACEMENT | alternate record (row 4 only) |

**Supplied account → matched database account:**

| Row | Supplied ACCOUNT | Matched ss_name | Result |
|---|---|---|---|
| 1 | Ledsone | `amazon Ledsone` | Exact match |
| 2–6 | DCvoltage | `amazon Dcvoltage` | Exact match (case-insensitive: "DCvoltage" vs "Dcvoltage") |
| 7 | Ledsone | `amazon Ledsone` | Exact match |

**Alternate account record found (row 4, B0H38YJTN8 only):** `amazon Dcvoltage_amazon` (REPLACEMENT source) — per instruction, this was **not** merged into "Dcvoltage" by similarity. It is reported separately as an alternate record. It carries a *different SKU* (`LSGL9015GY+RPM40WH`, no pack-size suffix) than the supplied SKU, so it does not affect this row's exact-SKU comparison regardless of the account question. Consistent with the pattern observed in prior sessions for other ASINs, this tag appears used specifically for REPLACEMENT-sourced records under the same physical seller account — but this is an observation, not a merge decision.

All final validation results use the supplied-account scope (`ss_name = 'amazon Ledsone'` or `'amazon Dcvoltage'` exactly, per row). An ASIN–SKU total across all accounts was calculated as a diagnostic only (see reconciliation CSV, `all_account_sales_2026`/`all_account_orders_2026` columns) — for every row it equals the account-specific result exactly, because none of these 7 ASINs have transactions under any other account.

## 6. SKU Matching Priority — Results

| Row | ASIN | Match level that reproduces the reference |
|---|---|---|
| 1 | B084RC5DQG | Match 1 (exact) — both years zero, correctly |
| 2 | B0GY3G4S1F | **Match 2 (Mapped SKU)** — Match 1 (exact supplied SKU) returns £0.00/0; the reference value is reproduced only via the Mapped SKU |
| 3 | B0GY423LQJ | Match 1 (exact) |
| 4 | B0H38YJTN8 | Match 1 (exact) |
| 5 | B0H393YSKV | Match 1 (exact) |
| 6 | B0H3918NPV | Match 1 (exact) |
| 7 | B0D9Q142ZZ | Match 1 (exact) — both years zero, correctly |

**Row 2 detail (the one Mapped-SKU case):** the supplied SKU `LSGL7512CL3PK+RPM40WH3PK` has **zero transactions anywhere in the database, under any account, at any time** (Match 4 all-account diagnostic = £0.00/0). The single June 2026 transaction for this ASIN (`order_item_info=1180841`, 2026-06-07, £21.89, qty 1) is recorded under the Mapped SKU `LSGL1275CL3PK+RPM40WH3PK`. Per instruction, the supplied SKU was **not** automatically replaced with the mapped SKU — both were evaluated independently and reported separately. The mapped SKU:
- **Exists in PostgreSQL:** YES (1 transaction)
- **Exists in the HTML:** YES (confirmed via the embedded product master and engine)
- **Carries the reference value:** YES, exactly (£21.89/1)
- **Relationship to supplied SKU:** appears to be an **alias/renamed SKU** for the same physical product bundle (the two SKU strings share the pattern `LSGL####CL3PK+RPM40WH3PK`, differing only in the numeric prefix — `7512` vs `1275` — consistent with a SKU renumbering rather than a different product)
- **Overlapping transactions with supplied SKU:** NO (supplied SKU has zero transactions to overlap with)

**Recommendation (not applied):** if the business intends the Mapped SKU to be the canonical, current SKU for this ASIN, the dashboard's product master should reflect that going forward — but this validation does **not** change the dashboard mapping, per instruction. This is a recommendation only.

## 7. Row-by-Row PostgreSQL Reconciliation

Full detail: `07_EVIDENCE\generated_data\2026-07-14_utharsika_june_kpi_reference_b02_reconciliation.csv`.

Transaction-level detail supporting every non-zero result (order IDs omitted from this summary per "do not expose customer-sensitive information unnecessarily" — order_item_info is retained as it is an internal system key, not customer data):

| ASIN | order_date | SKU | account | fulfilment | status | source | item_price | qty | Sales | In Sales? | In Orders? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B0GY3G4S1F | 2026-06-07 | LSGL1275CL3PK+RPM40WH3PK (mapped) | Dcvoltage | FBM | Completed | AMAZON | 21.89 | 1 | 21.89 | YES | YES |
| B0GY423LQJ | 2026-06-01 | LSGL9015CL2PK+RPM40WH2PK | Dcvoltage | FBM | Completed | AMAZON | 12.89 | 1 | 12.89 | YES | YES |
| B0GY423LQJ | 2026-06-22 | LSGL9015CL2PK+RPM40WH2PK | Dcvoltage | FBM | Completed | AMAZON | 12.89 | 1 | 12.89 | YES | YES |
| B0H38YJTN8 | 2026-06-03 | LSGL9015GY2PK+RPM40WH2PK | Dcvoltage | FBM | Completed | AMAZON | 18.89 | 1 | 18.89 | YES | YES |
| B0H38YJTN8 | 2026-06-08 | LSGL9015GY2PK+RPM40WH2PK | Dcvoltage | FBM | Completed | AMAZON | 18.89 | 1 | 18.89 | YES | YES |
| B0H38YJTN8 | 2026-06-08 | LSGL9015GY2PK+RPM40WH2PK | Dcvoltage | FBM | Completed | AMAZON | 18.89 | 1 | 18.89 | YES | YES |
| B0H38YJTN8 | 2026-06-11 | LSGL9015GY2PK+RPM40WH2PK | Dcvoltage | FBM | Completed | AMAZON | 18.89 | 2 | 37.78 | YES | YES |
| B0H38YJTN8 | 2026-06-11 | LSGL9015GY+RPM40WH (different SKU) | Dcvoltage_amazon | FBM | Completed | REPLACEMENT | 0.00 | 4 | 0.00 | excluded — different SKU (not this reference row) | excluded — different SKU |
| B0H393YSKV | 2026-06-01 | LSGL9015GY3PK+RPM40WH3PK | Dcvoltage | FBM | Completed | AMAZON | 28.89 | 1 | 28.89 | YES | YES |
| B0H393YSKV | 2026-06-02 | LSGL9015GY3PK+RPM40WH3PK | Dcvoltage | FBM | Completed | AMAZON | 28.89 | 1 | 28.89 | YES | YES |
| B0H3918NPV | 2026-06-02 | LSGL9015GY5PK+RPM40WH5PK | Dcvoltage | FBM | Completed | AMAZON | 45.89 | 1 | 45.89 | YES | YES |

No Refunded rows, no Cancelled/Canceled rows, and no additional Completed-REPLACEMENT rows matching any of these 7 exact supplied SKUs were found in either June window. `refunded_row_count = 0` and `cancelled_row_count = 0` for all 7 rows, both years.

## 8. Mapped-SKU Rows — Full Findings

Three rows carry a populated Mapped SKU (rows 1, 2, 7):

| Row | Supplied SKU independently valid? | Mapped SKU independently valid? | v002 uses | Same transactions? | Duplication risk if both counted | Recommendation |
|---|---|---|---|---|---|---|
| 1 (B084RC5DQG) | Valid string, 0 transactions | Valid string, 0 transactions | Neither has data — v002 shows this ASIN's one real SKU (`LSGLLF170AR+SCRN70YB`, outside June) | N/A | None — both are zero | Reference-only; neither SKU has real activity in the reporting window |
| 2 (B0GY3G4S1F) | Valid string, **0 transactions ever** | Valid string, **1 transaction (June 2026)** | v002's product master includes only the Mapped SKU (the supplied SKU never appears in any transaction) | No overlap — supplied SKU has nothing to overlap with | **None** — counting both would not duplicate anything, since the supplied SKU contributes zero | **Canonical SKU replacement** — the Mapped SKU appears to be the actual, current SKU in use |
| 7 (B0D9Q142ZZ) | Valid string but does not match the real historical SKU exactly (real SKU has a `+RPM40WH2PK` suffix the supplied SKU lacks) | Valid string, 0 transactions, unrelated bundle pattern | Neither — v002 uses the real SKU `LSGLBC150CO2PK+RPM40WH2PK` | N/A | None — all three SKU strings are zero or irrelevant to June | **Legacy/unrelated SKU** — the supplied SKU looks like a truncated version of the real SKU; the Mapped SKU appears to reference an unrelated product bundle entirely |

**No dashboard mapping was changed.** These are recommendations only, as instructed.

## 9. HTML Validation

Extracted the v002 HTML's own embedded product master, daily-aggregates-split, vendor periods, and engine code (Node `vm` sandbox execution of the file's actual embedded script, not the on-disk source file).

**Every HTML value matches the corresponding PostgreSQL value exactly** — for both the exact-supplied-SKU comparison and the Mapped-SKU diagnostic, at every row, both years. Full detail in the reconciliation CSV (`html_exact_2025_sales`, `html_exact_2026_sales`, etc. columns are identical to their `pg_exact_*` counterparts in every row).

**No SYSTEM_MISMATCH found.** No extraction omission, account-mapping error, SKU-mapping error, filter-logic error, date-range error, status/source-logic error, duplication, missing transaction, or stale-data issue was detected for any of the 7 rows.

## 10. ph_task Validation (read-only)

| Check | Result |
|---|---|
| Rows matching `project_code='UAWSO' AND assigned_user='utharsika'` | **1** (id=157) |
| Stored HTML SHA-256 (computed server-side via `sha256(convert_to(html_content,'UTF8'))`) | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` |
| Local `v002.html` SHA-256 | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` |
| Match | **YES** |
| `version_level` | 2 (unchanged) |

The stored HTML is confirmed identical to the locally validated HTML — no stale or different dataset is published. **The row was not updated.**

## 11-13. Exact Reference Comparison and Aggregate Totals

Full per-row detail: `07_EVIDENCE\generated_data\2026-07-14_utharsika_june_kpi_reference_b02_reconciliation.csv`.

| Period | Reference total Sales | PG exact-SKU total Sales | HTML exact-SKU total Sales | Reference total Orders | PG exact-SKU total Orders | HTML exact-SKU total Orders |
|---|---|---|---|---|---|---|
| June 2025 | £0.00 | £0.00 | £0.00 | 0 | 0 | 0 |
| June 2026 | £245.79 | £223.90 | £223.90 | 10 | 9 | 9 |

**June 2026 aggregate difference (£21.89 Sales / 1 Order) is entirely and exactly explained by row 2's `MAPPED_SKU_MATCH_ONLY` case** — not by any system defect. If row 2 is evaluated using its Mapped SKU (as documented, not substituted automatically), the totals reconcile exactly: £223.90 + £21.89 = £245.79 Sales; 9 + 1 = 10 Orders.

**Duplication risk:** none. Supplied-SKU and Mapped-SKU totals were never summed together for any row — each row contributes to the aggregate via exactly one match level (either its exact supplied SKU, when it has data, or reported as a separate mapped-SKU diagnostic when it does not). No row's transactions were counted twice.

## Limitations

- **Account normalization** relies on a `"amazon " + <name>` prefix convention observed consistently in this dataset; it is not a documented database constraint, so a future account name that doesn't follow this convention would need manual review.
- **The Mapped SKU column's exact intended semantics are not documented anywhere in the source system** — this validation classifies each mapped-SKU case based on transaction-pattern evidence only (Section 8), not a confirmed business specification.
- As previously documented (`07_EVIDENCE\2026-07-14_utharsika_v002_ORIGINAL_ORDER_MONTH_SALES_VALIDATION.md`), `order_date` is strongly supported as the original order date via price-tier consistency, order-sequence consistency, and selective-field-mutation evidence, but **absolute proof is unavailable** because the schema has no separate refund-date column. This limitation applies equally to the transactions reconciled in this validation.

## PASS/FAIL by Row

| Row | ASIN | Verdict |
|---|---|---|
| 1 | B084RC5DQG | PASS |
| 2 | B0GY3G4S1F | **MAPPED_SKU_MATCH_ONLY** (not a system defect — documented, not forced) |
| 3 | B0GY423LQJ | PASS |
| 4 | B0H38YJTN8 | PASS |
| 5 | B0H393YSKV | PASS |
| 6 | B0H3918NPV | PASS |
| 7 | B0D9Q142ZZ | PASS |

## Recommended Next Action

Confirm with the business whether `LSGL1275CL3PK+RPM40WH3PK` (row 2's Mapped SKU) should be treated as the canonical SKU for ASIN `B0GY3G4S1F` going forward, since it is the only SKU with any real transaction history for that ASIN. No dashboard or mapping change has been made pending that confirmation.

## Evidence Outputs

| File | Purpose |
|---|---|
| `07_EVIDENCE\2026-07-14_utharsika_june_kpi_reference_b02_VALIDATION.md` | This file |
| `07_EVIDENCE\generated_data\2026-07-14_utharsika_june_kpi_reference_b02_reconciliation.csv` | One row per reference row, all comparison fields |

## Final Verdict: **PASS**

All 7 rows were evaluated; every PostgreSQL/HTML pair matches exactly (no `SYSTEM_MISMATCH`); the one row-level mismatch against the reference (row 2) has a complete, evidence-backed root cause (`MAPPED_SKU_MATCH_ONLY`) rather than an unexplained discrepancy; no source, HTML, or `ph_task` asset was modified.
