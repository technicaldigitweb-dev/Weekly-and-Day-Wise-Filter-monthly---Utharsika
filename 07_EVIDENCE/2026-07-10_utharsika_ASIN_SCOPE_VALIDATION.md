# UAWSO ASIN and Sales Scope Validation — 2026-07-10 (Read-Only)

**What this asset is:** A discovery/validation report answering whether all Utharsika-assigned ASINs are correctly available and whether Sales includes all required Amazon UK fulfilment channels (FBM/FBA/Vendor).

**Why it exists:** To independently verify the already-published HTML's known limitation (113 missing ASINs) and to check a previously unexamined question (fulfilment-channel coverage) before deciding whether a correction is needed.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Complete. Read-only throughout — no HTML, template, calculation, or database write of any kind occurred.
**Known limits:** None outstanding for this validation itself — all questions in the request were answered with live data.
**Pass/fail rule:** N/A (discovery report, not a pass/fail gate).
**Next action:** User decides whether/how to address the two findings below (ASIN-without-SKU gap; SKU-sourced-from-transactions-only design limitation). No action taken automatically.

---

## Step 1 — Assigned ASIN Count Validation

| Metric | Value |
|---|---|
| Total distinct assigned ASIN count | **1723** (confirmed live, matches every prior session) |
| Utharsika's `user` id | 109 (2 identical duplicate rows in `public.user` for `user_name='utharsika'` — see Duplicate Data Anomaly below) |
| Categories | 2: `Lampshade` (id 66), `Wall plug` (id 67) — each has 2 duplicate rows in `public.ph_categories` |

### Duplicate Data Anomaly Found (genuine, at the raw-row level — does NOT affect the 1723 count)

A real, systematic data-quality issue exists across **three layers** of the assignment chain, discovered while investigating "duplicate assigned ASIN count":

| Layer | Duplication factor | Detail |
|---|---|---|
| `public.user` | 2x | Exactly 2 identical rows for `user=109, user_name='utharsika'` |
| `public.ph_categories` | 2x per category | Exactly 2 identical rows each for category 66 and category 67 |
| `public.ph_cate_products` | 2x per (category, ASIN) pair | **Verified for all 1723 pairs**: every single (ass_cate_id, ref_id) combination has exactly 2 rows — uniform, not random (consistent with a sync/load job that ran twice) |

**Duplicate assigned ASIN count (raw row-level duplication): every one of the 1723 assigned ASINs is affected** — but this is duplication of *rows*, not of *distinct ASIN values*. Because every resolution query used in this project (`sql/01_resolve_assigned_asins.sql`, `src/sku_resolver.py`, and the live extraction script) uses `SELECT DISTINCT`, the final resolved ASIN set has always been exactly 1723 — **correct and unaffected** by this underlying duplication. This is reported as a data-quality finding for awareness, not a defect in any UAWSO deliverable.

A naive `COUNT(*)` (no `DISTINCT`) through the full join chain would incorrectly report up to 13,784 "assignment rows" (1723 × 2 user-dup × 2 category-dup × 2 product-dup, compounding depending on join style) — this was reproduced and diagnosed during this validation, not present in any published artifact.

## Step 2 — Assigned ASINs vs. Current HTML Product Master

Compared `07_EVIDENCE\generated_data\2026-07-10_utharsika_v001_assigned_asins.json` (source of truth) against `07_EVIDENCE\generated_data\2026-07-10_utharsika_v001_product_master.json` (embedded in the published HTML).

| Metric | Value |
|---|---|
| Assigned ASIN count | 1723 |
| HTML represented ASIN count | 1610 |
| Missing ASIN count | **113** |
| Extra ASIN count | **0** (no ASIN in the product master falls outside the assigned set — isolation confirmed) |

### Missing ASIN Investigation (all 113, checked individually against live data)

| Check | Result for all 113 |
|---|---|
| 1. Assigned to Utharsika? | YES (all 113, by construction — they are in the assigned-ASIN source list) |
| 2. Matching SKU exists (in product master)? | NO (that is the definition of "missing") |
| 3. Amazon UK Completed transaction exists (any date)? | **NO for all 113** — confirmed by re-querying `order_transaction` directly for these exact 113 ASINs with no filters at all |
| 4. Sales exists (under required scope)? | NO |
| 5. Orders exist (under required scope)? | NO |

**Deeper breakdown of the 113** (checked against `order_transaction` with zero filters, any source/marketplace/status):
- **102 ASINs** have **zero transaction rows of any kind, ever** — no Amazon, no eBay, no Shopify, nothing. These are assigned products with no sales history in the system at all.
- **11 ASINs** have **some** transaction rows, but none are Amazon+UK+Completed. Verified row-by-row: their actual rows are Amazon **non-UK** marketplaces (Germany, Ireland, France, US) or Amazon **UK but not Completed** (`Refunded`, `Cancelled`). Not one of these 11 has a UK+Completed combination.

**Conclusion: the 113-ASIN gap is not a query bug.** The mandatory filters (`source_name='AMAZON' AND market_place='UK' AND order_status='Completed'`) are being applied correctly and consistently everywhere; these 113 ASINs simply have no Completed Amazon UK sales to report, ever. The underlying structural cause is documented below.

### Root Cause (structural, not a bug)

The product master is built as `SELECT DISTINCT asin, sku FROM order_transaction WHERE asin = ANY(assigned) AND <mandatory filters>` — i.e., **SKU is sourced only from transaction history**, not from a separate product/ASIN catalog table. No canonical ASIN→SKU catalog table (independent of sales history) was identified in this schema during this or prior sessions. Consequently, an assigned ASIN that has never had a single qualifying transaction has no SKU to pair with, and cannot be given a display row (SKU is a required visible column). This is why "assigned but zero-ever-sold" ASINs cannot currently appear in the dashboard even as a zero-value row — a real design limitation, not an oversight in the filter logic.

## Step 3 — SKU Mapping Validation (all 1723 assigned ASINs)

| Classification | Count |
|---|---|
| **A.** ASIN with SKU and sales (in the 2025-01-01→2026-07-09 embedded window) | **1516** |
| **B.** ASIN with SKU (has sold at some point, per product master) but zero sales in the embedded 2025-2026 window specifically | **94** |
| **C.** ASIN without SKU (no Completed Amazon UK transaction ever, at any date) | **113** |
| **D.** Duplicate SKU mapping — one SKU shared across more than one ASIN (bundle/multi-ASIN SKU pattern) | **400 SKUs** affected |

Sanity check: A + B + C = 1516 + 94 + 113 = **1723** ✓ (matches the assigned total exactly)

SKU-count distribution across the 1610 represented ASINs: 1370 ASINs have exactly 1 SKU; 240 ASINs have 2 or more (max observed: 8 SKUs for a single ASIN) — consistent with the bundle pattern already documented in the `order_transaction` reusable schema reference from the design stage.

**Note on Classification D:** a SKU mapping to multiple ASINs is an expected, previously-documented pattern (bundle SKUs sold under more than one parent ASIN listing), not itself an error — flagged here only because it was explicitly requested, not because it requires correction.

## Step 4 — Order Source / Fulfilment Coverage Investigation

Live schema of `public.order_transaction` re-confirmed (20 columns, queried fresh — not assumed from documentation):

```
order_item_info, order_id, item_id, asin, product_id, sku, item_price, quantity,
order_status, order_date, order_total, order_sub_source, ss_name, source,
source_name, market_place, fba_sales, category_id, category_name, user_id, user_name
```

**No dedicated `fulfilment_channel`/`fulfillment_channel`/`order_type`/`vendor_type` column exists.** The two columns that carry fulfilment-relevant information are:
- **`fba_sales`** (boolean) — `TRUE` = FBA, `FALSE`/`NULL` = FBM. Documented as "Amazon only" in the reusable schema reference and confirmed live.
- **`ss_name`** (text, sub-source/store name) — one specific value, `'vendor'`, exists in the live data (see Step 5).

## Step 5 — FBM / FBA / Vendor Coverage (live, for Utharsika's assigned ASINs, 2025-01-01→2026-07-09, Amazon UK Completed)

| Channel | Available? | ASIN count | SKU count | Sales | Orders |
|---|---|---|---|---|---|
| **FBM** (`fba_sales = FALSE`) | **YES** | 801 (distinct across `amazon Dcvoltage` + `amazon Ledsone` + `amazon SRM Amazon` sub-sources) | ~485 | **£507,631.04** | **25,448** |
| **FBA** (`fba_sales = TRUE`) | **YES** | 267 (across `amazon Dcvoltage` + `amazon Ledsone`) | ~278 | **£170,330.29** | **7,886** |
| **Vendor** (`ss_name = 'vendor'`) | **Present in schema, but not applicable to Utharsika** | 0 | 0 | £0.00 | 0 |

Raw breakdown by `ss_name` × `fba_sales` (Utharsika-assigned ASINs, Amazon UK Completed, 2025-2026):

| ss_name | fba_sales | Orders | Sales |
|---|---|---|---|
| amazon Dcvoltage | FALSE (FBM) | 13,658 | £264,723.00 |
| amazon Ledsone | FALSE (FBM) | 11,729 | £241,864.59 |
| amazon Dcvoltage | TRUE (FBA) | 4,948 | £104,804.77 |
| amazon Ledsone | TRUE (FBA) | 2,938 | £65,525.52 |
| amazon SRM Amazon | FALSE (FBM) | 61 | £1,043.45 |

**Vendor investigation:** searched the entire `order_transaction` table (not scoped to Utharsika) for `ss_name ILIKE '%vendor%'`. Found exactly **2 rows system-wide**, both `source_name='AMAZON', ss_name='vendor'`, both dated **2023-05-22** (well before the embedded history window), and both with **no ASIN value** (`asin_count: 0` when grouped — the ASIN field is empty/null on these rows). Vendor is effectively a **dormant, legacy channel** in this database: present in the schema/data as a concept, but with no active product-level data, nothing for Utharsika, and nothing within the 2025-2026 reporting window at all.

## Step 6 — Sales Completeness Check

Cross-validated the FBM+FBA breakdown above against the actual embedded dataset already published in `09_OUTPUTS\2026-07-10_utharsika_v001.html`:

```
Manual FBM + FBA sum:        £507,631.04 + £170,330.29 = £677,961.33  |  25,448 + 7,886 = 33,334 orders
Embedded dataset total:      £677,961.33                              |  33,334 orders
```

**Exact match.** This confirms the currently published dataset **already includes both FBM and FBA in full** — the existing extraction query (`sql/02_report_query.sql` / `extract_uawso_daily_aggregates.py`) never filters on `fba_sales` or `ss_name`, so both fulfilment types were captured correctly from the start, without needing any change.

```
Current HTML scope:
Included fulfilment types:   FBM, FBA (both included by construction — no fba_sales filter exists anywhere in the pipeline)
Missing fulfilment types:    Vendor — but only because Vendor has zero data for Utharsika's products in this window (2 dormant, ASIN-less, pre-2025 rows exist system-wide; none would be excluded by the current query even if they did apply, since there is no ss_name filter either)
```

## Required Output

**A.** Source assigned ASIN count: **1723**
**B.** Duplicate assigned ASIN count: **0 distinct-ASIN duplicates** (the resolved set is clean); **but all 1723 have duplicate underlying rows** at the `ph_cate_products`/`ph_categories`/`user` table level (2x each, uniform) — see Duplicate Data Anomaly
**C.** HTML represented ASIN count: **1610**
**D.** Missing ASIN count: **113**
**E.** Missing ASIN reasons: 102 have zero transaction history of any kind; 11 have transaction history but never Amazon+UK+Completed (either wrong marketplace or wrong status) — no query bug, confirmed row-by-row
**F.** ASIN with SKU count: **1610** (of which 1516 also have 2025-2026 sales, 94 have historical-only sales)
**G.** ASIN without SKU count: **113**
**H.** Duplicate SKU mapping count: **400 SKUs** map to more than one ASIN (expected bundle pattern, not an error)
**I.** Order table fulfilment columns found: **`fba_sales`** (boolean, FBA/FBM) and **`ss_name`** (text, includes a dormant `'vendor'` value) — no dedicated fulfilment-type column exists
**J.** FBM available: **YES**
**K.** FBA available: **YES**
**L.** Vendor available: **Present in schema; zero applicable data for Utharsika / zero data in the reporting window** — effectively NO for this scope
**M.** FBM sales: **£507,631.04**
**N.** FBA sales: **£170,330.29**
**O.** Vendor sales: **£0.00**
**P.** FBM orders: **25,448**
**Q.** FBA orders: **7,886**
**R.** Vendor orders: **0**
**S.** Total Amazon UK sales (assigned scope, 2025-2026): **£677,961.33**
**T.** Total Amazon UK orders (assigned scope, 2025-2026): **33,334**
**U.** Current HTML fulfilment coverage: **FBM + FBA fully included** (verified by exact reconciliation against the published dataset)
**V.** Missing business requirement coverage: **None for FBM/FBA/Vendor** (Vendor has no data to miss). **The 113-ASIN gap remains the one open item**, already recorded as `PENDING_CORRECTION` in the published `ph_task` row — root cause now further clarified as a structural SKU-sourced-from-transactions-only limitation, not a filter bug.
**W.** Recommended correction required: **NO for fulfilment-channel coverage** (already complete). **Advisory only, not urgent, for the ASIN-without-SKU gap** — would require either (a) accepting that never-sold ASINs cannot display a SKU and are correctly absent, or (b) sourcing SKU from a separate product-catalog table (not yet identified in this schema) if the business wants every assigned ASIN visible regardless of sales history.

## Isolation Confirmation

Every query this session was scoped to Utharsika (`user_name='utharsika'`, `user=109`) or was a schema-only/system-wide aggregate check that touched no other user's row-level report content. **Other users' `ph_task` content inspected or reused: NO.**

## Files Changed

**NONE** in the HTML/template/calculation surface. This evidence file and two small local intermediate files (`05_IMPLEMENTATION\state\missing_asins.json`) were created for this validation only.

**Database writes: NONE.**
