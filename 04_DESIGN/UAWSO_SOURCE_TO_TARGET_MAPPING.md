# UAWSO Source-to-Target Mapping

**What this asset is:** A field-by-field map from every report output to its exact source, join, filter, and formula.

**Why it exists:** So implementation SQL can be written directly from this table without re-deriving logic, and so validation can check each field independently.

**Business question supported:** "Where does each number on the report actually come from?"

**Source or evidence used:** `08_SKILLS\database_skills\skills_minimal_pack 2 (2).zip → TABLE_order_transaction.md`; live read-only schema checks of `public.user`, `public.ph_categories`, `public.ph_cate_products`, `tech_team_outputs.ph_task`; `01_REQUIREMENTS\UAWSO_REQUIREMENT_RECORD.md`.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Design complete, not implemented.
**Known limits:** Not yet validated against a live run (no SQL executed this stage).
**Pass/fail rule:** A field mapping passes review when its source, join, filter, and formula are all traceable to a cited source with no invented logic.
**Next action:** Use this mapping as the direct input to `04_DESIGN\UAWSO_SQL_DESIGN.sql.md`.

---

## 0. Assigned-SKU Resolution (prerequisite to every report field)

| Step | Source table | Column | Filter | Notes |
|---|---|---|---|---|
| Resolve Utharsika's user id | `public.user` | `user`, `user_firstname`, `user_name` | `LOWER(user_name) = 'utharsika'` | Confirmed: `user=109` |
| Resolve her categories | `public.ph_categories` | `id`, `user_id` | `user_id = 109` | Confirmed: 2 categories (`Lampshade`=66, `Wall plug`=67) |
| Resolve assigned Amazon ASINs | `public.ph_cate_products` | `ref_id`, `ass_cate_id`, `which_channel` | `ass_cate_id IN (categories above)` AND `which_channel = 1` (Amazon) | `ref_id` holds the **ASIN**, confirmed by sample data (`B0CGDZ76D8` format) |
| De-duplicate | — | `DISTINCT ref_id` | — | Defensive step; 0 duplicates found for Utharsika currently, but the design must not assume this holds forever |

Output of this step: one distinct set of ASINs assigned to `utharsika`. This set is joined to `order_transaction`, never the reverse (never filter transactions first by `user_name` on `order_transaction`, per Section 5 of the stage instructions).

## 1. Field Mapping

| Target field | Source table | Source column | Assignment source | Join key | Mandatory filters | Aggregation | Date period | Formula | Null handling | Zero handling | Validation method | Unresolved |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ASIN | `order_transaction` | `asin` | Assigned-SKU set (§0) | assigned `ref_id` = `ot.asin` | `source_name='AMAZON'`, `market_place='UK'`, `order_status='Completed'` | `GROUP BY asin, sku` | N/A (identity) | — | N/A | N/A | Must appear in assigned-SKU set | None |
| SKU | `order_transaction` | `sku` | Resolved via ASIN join (assignment is by ASIN, not SKU) | same as above | same as above | `GROUP BY asin, sku` | N/A (identity) | — | N/A | N/A | Confirmed one ASIN can map to multiple SKUs (bundle pattern seen in sample data) | None |
| Previous Year Sales | `order_transaction` | `order_total` | — | — | same as above + prior-year date window | `SUM(COALESCE(order_total,0))` | Prior-year equivalent window (see §Date Boundaries below) | — | `COALESCE(order_total,0)` | 0 is a valid value, not an error | Recompute independently, ±0.01 tolerance | None |
| Previous Year Orders | `order_transaction` | `order_item_info` | — | — | same as above + prior-year date window | `COUNT(DISTINCT order_item_info)` | Prior-year equivalent window | — | N/A (PK, never null) | 0 is valid | Recompute independently | None |
| This Year Sales | `order_transaction` | `order_total` | — | — | same as above + current-year date window | `SUM(COALESCE(order_total,0))` | Current-year window (Daily/Weekly/MTD) | — | `COALESCE(order_total,0)` | 0 is valid | Recompute independently | None |
| This Year Orders | `order_transaction` | `order_item_info` | — | — | same as above + current-year date window | `COUNT(DISTINCT order_item_info)` | Current-year window | — | N/A | 0 is valid | Recompute independently | None |
| Sales Change | derived | — | — | — | — | row-level | matches report period | `(This Year Sales − Previous Year Sales) ÷ Previous Year Sales` (confirmed by matching 2 independent sample rows in the source worksheet) | `NULLIF(Previous Year Sales,0)` denominator | Previous=0 → NULL/undefined, see §Zero-Value Rule | Recompute from Sales fields | **Previous=0, Current>0 case — open, see business rules spec** |
| Order Change | derived | — | — | — | — | row-level | matches report period | `(This Year Orders − Previous Year Orders) ÷ Previous Year Orders` | `NULLIF(Previous Year Orders,0)` | Same as Sales Change | Recompute from Orders fields | Same open item |
| Trend | derived | — | — | — | — | row-level | matches report period | Sales-only: `UP` if This>Prev, `DOWN` if This<Prev, `NO CHANGE` if equal (includes both-zero case) | N/A | Both zero → `NO CHANGE` (per confirmed zero-value rule) | Check against Sales fields only, never Orders | None |
| Achieve Sales % | derived | — | — | — | — | row-level | matches report period | `(This Year Sales ÷ (Previous Year Sales × 1.30)) × 100` | `NULLIF(Previous Year Sales × 1.30, 0)` | Both zero → display `NOT IMPROVED`; Previous=0,Current>0 → open question | Recompute from Sales fields | **Previous=0, Current>0 case — open** |
| Achieve Order % | derived | — | — | — | — | row-level | matches report period | `(This Year Orders ÷ (Previous Year Orders × 1.30)) × 100` | `NULLIF(Previous Year Orders × 1.30, 0)` | Same as Achieve Sales % | Recompute from Orders fields | Same open item |
| Total row (Sales/Orders) | derived | — | — | — | — | `SUM()` across all rows in the period | matches report period | Plain sum of already-aggregated per-ASIN/SKU values | N/A | N/A | Recompute totals independently from row-level sums | None |
| Total Achieve Sales %/Order % | derived | — | — | — | — | aggregate-of-aggregate | matches report period | `Total This Year Sales ÷ (Total Previous Year Sales × 1.30) × 100` — **never** an average of row-level percentages | `NULLIF` on denominator | Same zero rule as row-level | Recompute from totals, confirm ≠ `AVG(row percentages)` | None |
| report_date | system-derived | — | — | — | Asia/Colombo calendar | — | — | `report_date = (current Sri Lanka date) − 1 day` | N/A | N/A | Confirm against `NOW() AT TIME ZONE 'Asia/Colombo'` | Exact automation run time not specified — see handover |
| project_code | constant | — | — | — | — | — | — | `'UAWSO'` | N/A | N/A | Exact string match | None |
| task_id | derived | — | — | — | — | — | — | `'UAWSO-' \|\| to_char(report_date,'YYYY-MM-DD')`, suffixed `-v{version_level}` for same-date corrections after v1 | N/A | N/A | Must satisfy live `ph_task_task_id_unique` constraint | None (constraint confirmed live) |
| assigned_user | constant, verified | `public.user.user_name` | Assigned-user standard | — | — | — | — | `'utharsika'` copied verbatim | N/A | N/A | Exact string match, case-sensitive | None |
| assigned_user_team | constant | — | — | — | — | — | — | `'ph_priors'` | N/A | N/A | Exact string match | None |
| daily version identity | derived | `tech_team_outputs.ph_task.version_level` / `.version_status` | — | — | — | — | — | New row per report_date at `version_level=1`; corrections increment `version_level` and reject the prior same-date row | N/A | N/A | One active (`released`, non-`rejected`) row per report_date | None |

## Date Boundaries (referenced above, defined fully in the business rules spec)

See `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §Reporting Period Rules for the full Daily/Weekly/MTD boundary definitions including the previous-year equivalent-period logic and leap-year handling.
