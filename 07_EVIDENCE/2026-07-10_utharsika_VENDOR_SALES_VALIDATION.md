# UAWSO Vendor Sales Table Validation — 2026-07-10 (Read-Only)

**What this asset is:** A discovery/validation report determining whether a dedicated Vendor sales table exists, whether it contains data for Utharsika's assigned products, and whether it should be included in UAWSO reporting.

**Why it exists:** The prior validation session (`2026-07-10_utharsika_ASIN_SCOPE_VALIDATION.md`) checked for a `ss_name='vendor'` sub-source *inside* `order_transaction` and found it dormant (2 legacy rows, no ASIN linkage). This session checks a different, previously-unexamined table entirely and finds a materially different answer.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Complete. Read-only throughout — no HTML, template, calculation, database write, or new table was created.
**Known limits:** `vendor_sales` has no explicit `market_place` column, so "UK only" is inferred from currency (see Step 4), not directly proven by a labeled field. `vendor_sales` has no `sku` column at all — only `asin`.
**Pass/fail rule:** N/A (discovery report).
**Next action:** User decides whether to incorporate `vendor_sales` into the UAWSO pipeline. **No changes have been made to any UAWSO deliverable.**

---

## Step 1 — Locate Vendor Sales Table

Searched `information_schema.tables` across **all** schemas for any table name containing "vendor" (not assumed — searched broadly first).

| Field | Value |
|---|---|
| Table found | **YES** |
| Schema | `public` |
| Table name | `vendor_sales` |
| Row count (system-wide, all users) | **5,026** |
| Distinct ASINs (system-wide) | 1,897 |
| Date columns | `start_time`, `end_time` (both `timestamp without time zone` — no single "order_date" column; each row represents a period, not a single transaction) |
| ASIN/SKU columns | **`asin` (text) only — no `sku` column exists in this table** |
| Sales columns | `ordered_revenue` (double precision), `currency_code` (text) |
| Order/quantity columns | `ordered_units` (bigint) — **no `order_item_info`-equivalent distinct-order identifier**; `ordered_units` is a unit/quantity count, not an order count |
| Marketplace columns | **None** — no `market_place`/`source_name`/`ss_name` column exists |
| User/account columns | `user_id` (bigint), `user_name` (text) — direct PH-holder attribution, same pattern as `order_transaction` |
| Other columns | `id`, `created_at`, `updated_at`, `category_id`, `category_name` |

This table was **not referenced anywhere** in any prior UAWSO session, script, or design document — confirmed by searching the project's skills packs (`08_SKILLS\database_skills\`) for any documentation of it: none exists in either the newer or older skill pack.

## Step 2 — Utharsika Product Scope Check

Used the same approved assignment chain (`public.user` → `public.ph_categories` → `public.ph_cate_products`, `which_channel=1`) as every prior session — resolved the same 1723 assigned ASINs (unchanged, re-verified).

| Check | Result |
|---|---|
| `vendor_sales` contains any of the 1723 assigned ASINs | **YES — 329 ASINs** |
| Cross-check: direct `user_name='utharsika'` filter on `vendor_sales` itself | **Also exactly 329 ASINs — 100% identical set**, zero discrepancy either direction. The table's own direct user attribution and the standard assignment-chain join agree perfectly. |
| `vendor_sales` contains any of the 1610 "transactional" ASINs (current HTML product master) | **328 of the 329** vendor ASINs are already represented in the current HTML (they have both `order_transaction` sales AND `vendor_sales` sales) |
| `vendor_sales` contains any of the 113 "missing" ASINs from the prior validation | **Only 1 of the 329** — Vendor data would resolve just 1 of the 113 gaps, not the majority |
| Matching SKUs | **Not applicable — `vendor_sales` has no SKU column.** SKU cannot be determined from this table; would need to be resolved via a join to `order_transaction` on ASIN (imperfect, since not every vendor ASIN necessarily has a matching order_transaction SKU) or left blank/aggregated at ASIN level only. |

## Step 3 — Vendor Sales Coverage (Utharsika-assigned products, 2025-01-01 to 2026-07-09)

| Metric | Value |
|---|---|
| Vendor ASIN count | **329** |
| Vendor SKU count | **N/A — no SKU column exists in this table** |
| Vendor sales total (`ordered_revenue`) | **£46,642.46** |
| Vendor units total (`ordered_units`) | **4,738** |
| Earliest Vendor date | 2025-06-01 |
| Latest Vendor date | 2026-07-06 |
| Vendor row count (matched) | 951 |

Note: `ordered_units` is a **unit/quantity** count, not an order count in the `COUNT(DISTINCT order_item_info)` sense used elsewhere in UAWSO — there is no equivalent unique-order identifier in this table, so it cannot be summed into "Orders" using the same method as `order_transaction` without a business decision on how to define "an order" for Vendor data (e.g., row count, or units, or something else).

## Step 4 — Marketplace Scope

| Question | Answer |
|---|---|
| Is Vendor data UK only? | **Strongly indicated, not directly proven.** No `market_place` column exists in this table at all. System-wide (all 5,026 rows, all users, not just Utharsika), **`currency_code` has exactly one distinct value: `GBP`**. GBP is virtually always UK-specific in this kind of e-commerce data, but this is an inference from currency, not a labeled marketplace field — reported honestly as such, per the instruction not to assume. |
| Is marketplace available? | **NO** — no column carries this information directly |
| Is account information available? | **Partially.** No `ss_name`/storefront/account column exists. `user_id`/`user_name` (PH holder) and `category_id`/`category_name` are available — the same attribution pattern as `order_transaction`, but no sub-account/storefront breakdown. |
| Is it already included somewhere else? | **NO.** Confirmed by exact reconciliation in the prior validation session: the currently published HTML's total (£677,961.33) exactly equals the sum of `order_transaction`'s FBM+FBA totals alone, with zero contribution from `vendor_sales` (a completely separate table, never joined or queried by any UAWSO script to date). |
| Do not assume Vendor = Amazon Vendor | Acknowledged. The table's *name* (`vendor_sales`) and the fact that 328 of its 329 Utharsika-matched ASINs are also confirmed Amazon-sold products (via `order_transaction.source_name='AMAZON'`) is suggestive of Amazon Vendor Central, but **this table contains no `source_name`/platform column of its own** — it cannot be definitively proven from this table alone which platform's "vendor" program it represents. Reported as an open question, not resolved by assumption. |

## Step 5 — Compare Against Current HTML Scope

**Current HTML includes:** FBM + FBA (from `order_transaction`, confirmed via exact reconciliation in the prior validation session).

**`vendor_sales` contains additional business-required sales:** **YES.** £46,642.46 across 329 ASINs (951 rows) that is entirely absent from the current published report and from every prior UAWSO calculation, because `vendor_sales` was never queried by any script built in this project until this validation session.

This is **new revenue currently unreported**, not a duplicate of existing FBM/FBA data — `order_transaction` and `vendor_sales` are structurally separate tables with no overlapping row identity (`order_transaction` is line-item/order-level with `order_item_info` as a distinct-order key; `vendor_sales` is period-aggregated per ASIN with no equivalent order-level key).

---

## Required Output

**A.** `vendor_sales` table exists: **YES**
**B.** Schema name: `public`
**C.** Row count: **5,026** (system-wide); **951** rows matched to Utharsika's 1723 assigned ASINs
**D.** Date coverage: `2025-06-01` to `2026-07-08` (system-wide); `2025-06-01` to `2026-07-06` for Utharsika's matched rows — both within the current embedded history window (`2025-01-01`→`2026-07-09`), though the table itself has no data before June 2025
**E.** ASIN column: `asin` (text)
**F.** SKU column: **none exists**
**G.** Sales column: `ordered_revenue` (double precision)
**H.** Order/quantity column: `ordered_units` (bigint) — a unit count, not a distinct-order count; no direct equivalent to `order_item_info`
**I.** Utharsika Vendor ASIN count: **329**
**J.** Utharsika Vendor SKU count: **N/A (no SKU column)**
**K.** Vendor sales total: **£46,642.46**
**L.** Vendor quantity/orders total: **4,738 units** (951 rows; no distinct-order concept available)
**M.** Vendor UK scope confirmed: **Indicated by single currency (GBP, system-wide) but not directly confirmed — no marketplace column exists**
**N.** Vendor data already included in current HTML: **NO**
**O.** Additional HTML update required: **Advisory — YES, if the business wants Vendor revenue included.** Not automatically triggered by this validation (no change was made). Adding it would require: (1) a business decision on how to define "Orders" for Vendor data (no order-level key exists, only unit counts), (2) a decision on how to display SKU (no SKU column — would need an ASIN-level-only row, or a best-effort join to `order_transaction` for a representative SKU), and (3) a business decision on marketplace scope given no explicit UK flag exists on this table.
**P.** Evidence path: `07_EVIDENCE\2026-07-10_utharsika_VENDOR_SALES_VALIDATION.md`

## Isolation Confirmation

All queries this session were scoped to Utharsika (`user_name='utharsika'`/`user_id=109`) or were system-wide schema/aggregate checks that touched no other user's row-level report content. **Other users' `ph_task` content inspected or reused: NO.**

## Files Changed

**NONE** in the HTML/template/calculation surface, and **no new database table was created**. This evidence file and two small local intermediate files (`05_IMPLEMENTATION\state\vendor_matched_asins.json`) were created for this validation only.

**Database writes: NONE.**
