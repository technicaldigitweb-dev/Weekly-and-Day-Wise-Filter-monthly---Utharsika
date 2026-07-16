# SKILL FILE — DAILY KNOWLEDGE EXTRACTION TEMPLATE
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## ── METADATA BLOCK ──────────────────────────────────────────────────────────

date:                   2026-07-10
developer:              satheskanth
project:                Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report
project_code:           UAWSO
phase:                  DEPLOY
requirement_id:         REQ-01
deliverable_id:         REQ-01-D01
status:                 COMPLETE
evidence_location:      07_EVIDENCE\2026-07-10_utharsika_v001_PH_TASK_REPLACEMENT.md ; 07_EVIDENCE\2026-07-10_utharsika_v001_ASIN_SKU_GRAIN_AND_JUNE_RECONCILIATION.md ; 07_EVIDENCE\2026-07-10_utharsika_VENDOR_SALES_VALIDATION.md ; 07_EVIDENCE\2026-07-10_utharsika_ASIN_SCOPE_VALIDATION.md ; 09_OUTPUTS\2026-07-10_utharsika_v001.html
blos_keys_used:         NONE — no formal BLOS-key registry exists in this project yet; the business rules that would normally be BLOS-governed (130% achievement target, Amazon UK Completed-order scope, one-row-per-ASIN-SKU grain) are documented in plain language in this file instead.
hardcoded_thresholds:   ACHIEVEMENT_TARGET_MULTIPLIER = 1.30 (130% year-over-year Sales/Orders target), defined in src/calculations.py and mirrored in src/uawso_client_engine.js — not yet BLOS-governed.
three_am_standard:      PASS
llm_queryable:          YES
company_knowledge_candidate: YES
domain:                 E-commerce Operations — Amazon Marketplace — UK Sales & Orders
User:                   Utharsika
Benefit status:         PASS

## File path (fill after saving):
# 2026-07-10__satheskanth__uawso__REQ-01-D01.md

---

## 1. SYSTEM STATE

- **Current system state (before today):** UAWSO v001 dashboard was already published (row `id=157` in `tech_team_outputs.ph_task`), but the product master was built by starting from `order_transaction` history, not the assigned-product catalog. Result: only 1,610 of Utharsika's 1,723 assigned ASINs appeared — 113 ASINs with no Completed Amazon UK transaction were invisible. Multiple SKUs belonging to the same ASIN were merged into a single comma-joined string cell.
- **What was working:** Daily/Weekly/Month/MTD comparison engine, 130% achievement calculation, Sales-based Trend logic, searchable filter UI, FBM+FBA sales inclusion, the `ph_task` publication pipeline.
- **What was broken / missing:** ASIN coverage incomplete (113 ASINs silently absent); row grain incorrect (SKU arrays merged into one cell instead of one row per SKU); `public.vendor_sales` (Amazon Vendor Central channel, ~£46,642.46 of real revenue) was completely unqueried and absent from every total.
- **Your starting point:** An already-live v001 HTML needed an in-place content correction (same task_id, same version) — not a new report version, not a new `ph_task` row.

---

## 2. WHAT CHANGED TODAY

- **Change 1:** Built `05_IMPLEMENTATION\src\extract_uawso_full_coverage.py` — new read-only extraction that produces the FULL 1,723-ASIN assigned master, `LEFT JOIN`ed to `order_transaction` (for SKU + FBM/FBA split by `fba_sales`) and `LEFT JOIN`ed to `public.vendor_sales` (for Vendor revenue) — replacing the old transaction-first product master.
- **Change 2:** Added v3 functions to `05_IMPLEMENTATION\src\uawso_client_engine.js` (`buildCanonicalRows`, `sumRangeSplitByAsinSku`, `computeRowsV3`, `computeTotalV3`). These enforce the correct row grain: exactly one row per `(ASIN, SKU)` pair, plus exactly one dedicated blank "Vendor" row per ASIN that carries Vendor data (never duplicated across that ASIN's SKU rows).
- **Change 3:** Rewrote `05_IMPLEMENTATION\templates\uawso_report_template.html` — new 14-column table (ASIN, SKU, Row Type, FBM Sales/Orders, FBA Sales/Orders, Vendor Sales/Units, PY/CY Sales, Sales Change, Trend, Achievement %), searchable multi-select ASIN/SKU dropdowns with dependency filtering (selecting an ASIN narrows SKU options and vice versa), CSV export of the full filtered row set (computed before pagination), and a "Data Coverage Notes" section disclosing the Vendor period-overlap limitation.
- **Change 4:** Replaced the stored `html_content` on the existing `ph_task` row (`id=157`) via a guarded single-row `UPDATE` — pre-checked the row was uniquely identified, verified `rowcount == 1` before commit, captured before/after SHA-256. `task_id`, `assigned_user`, `assigned_user_team`, `version_level` all left untouched.

**Evidence reference:** Final HTML SHA-256 `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3`; `ph_task` row `id=157`; full before/after hash trail in `07_EVIDENCE\2026-07-10_utharsika_v001_PH_TASK_REPLACEMENT.md`.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

**Table(s) involved:** `public.vendor_sales`, `public.order_transaction`, `public.ph_cate_products`, `public.ph_categories`, `public.user`, `tech_team_outputs.ph_task`

**Finding:** `public.vendor_sales` has **no `sku` column and no order-level identifier** — only `asin`, `ordered_revenue`, `ordered_units`, and a `start_time`/`end_time` **period** (not a single date). It also mixes granularity: most rows are ~1-hour "daily" markers, but some rows span a full calendar month. This table was completely unqueried by any UAWSO script before today.

**SQL logic or pattern discovered:** Because `vendor_sales` carries no SKU, its revenue must be attributed to exactly **one** row per ASIN — either that ASIN's existing no-SKU row, or one dedicated new blank "Vendor" row. It must never be joined onto every SKU row belonging to that ASIN, or the revenue gets multiplied by the SKU count.

**Operational meaning:** `public.ph_cate_products` / `ph_categories` / `user` all contain a confirmed uniform 2x raw-row duplication (every assignment row exists exactly twice). `DISTINCT` must always be applied when resolving the assigned-ASIN master, or counts will be silently inflated (e.g. 1,723 real ASINs can appear as up to 13,784 raw rows through the naive join).

---

## 4. GAP FOUND

**Gap description:** A user-provided reference value for June 2025 previous-year Sales (**£42,086.96**) could not be reproduced from source data. The database-calculated, independently reconciled value is **£41,146.84** (difference: **£940.12**). Eight calculation variants were tested — full-month vs. partial-day range, FBM+FBA-only vs. +Vendor, Vendor overlap-vs-strict-containment allocation, a timezone-shift hypothesis, and live-vs-cached data comparison — and none reproduced the reference figure or isolated the gap to a specific row, date, or channel.

**Impact if unresolved:** The dashboard's June figure may not match a business stakeholder's own manual calculation, creating a trust/traceability question even though the shown figure is fully source-backed.

**Recommended action:** Whoever produced the £42,086.96 reference should specify the exact date range, whether Vendor was included, and any manual adjustment used to derive it, so the two figures can be compared line-by-line.

**Owner (if known):** Satheesvaran (business validator) / whoever supplied the original reference figure.

---

## 5. VALIDATION RULE ADDED OR CHANGED

**Rule name / ID:** UAWSO Row-Grain Rule (v3)
**Condition checked:** IF an assigned ASIN has one or more matching SKUs (from Completed Amazon UK transaction history) THEN create one row per `(ASIN, SKU)` pair. ELSE create exactly one row with `SKU = blank`, `mapping_status = NO_SKU_MAPPING`.
**What it prevents:** Comma-joined multi-SKU values in a single cell (unfilterable, ambiguous data); assigned ASINs silently disappearing from the report because they lack a SKU.
**Where implemented:** `src/uawso_client_engine.js :: buildCanonicalRows()`, `computeRowsV3()`
**BLOS reference:** None — no formal BLOS-key registry exists in this project for this rule; documented here as the source of truth.

**Rule name / ID:** Vendor Non-Duplication Rule
**Condition checked:** IF an ASIN has Vendor data AND has SKU rows, THEN attach Vendor Sales/Units to exactly one new blank row (`rowType = VENDOR_ASIN_LEVEL`). IF an ASIN has Vendor data AND has no SKU at all, THEN reuse its single existing blank no-SKU row (`rowType = NO_SKU_MAPPING_VENDOR`) rather than creating a second blank row.
**What it prevents:** Vendor revenue being multiplied across every SKU row belonging to the same ASIN.
**Where implemented:** `src/uawso_client_engine.js :: buildCanonicalRows()`, `computeRowsV3()` (gated by an `isVendorRow` boolean flag)
**BLOS reference:** None.

---

## 6. FAILURE MODE OR EDGE CASE

**Failure scenario:** An ASIN that has Vendor sales data but zero Amazon UK Completed transactions ever (no SKU mapping at all) could end up either omitted entirely or duplicated into two blank rows.
**How it is triggered:** ASIN `B0DTKCSD1R` is the one real example in production data — it has Vendor sales but no SKU mapping.
**How it is detected:** A dedicated automated test (`tests/test_uawso_client_engine_v3.js`) explicitly asserts this exact ASIN produces exactly 1 row, never 0 or 2.
**Recovery procedure:** `buildCanonicalRows()` checks whether the ASIN already has Vendor data before deciding whether its no-SKU row needs a separate Vendor row or can reuse the existing blank row — verified by automated test, not manual review.
**Risk level:** MEDIUM (only 1 ASIN affected today, but the same pattern could recur for any future ASIN with Vendor-but-no-Amazon-UK-history).

---

## 7. DECISIONS MADE TODAY

**Decision:** Attribute a Vendor sales period to any date range it overlaps in full (no proration), rather than splitting a monthly Vendor period proportionally across the days/weeks it spans.
**Alternatives considered:** Prorate a monthly Vendor period evenly across its days; require exact period-to-range containment before counting it at all.
**Reason for choice:** `vendor_sales` has no daily granularity for its monthly-bucketed rows, so proration would be an invented approximation, not a real number. Overlap-inclusion is the simplest rule that doesn't silently drop real revenue.
**Trade-off accepted:** Vendor figures can be over- or under-attributed at month-boundary edges when a monthly Vendor period is compared against a shorter (daily/weekly) selection — disclosed transparently in the HTML's own "Data Coverage Notes" section rather than hidden.
**Who approved:** Not yet formally reviewed — flagged for the assigned technical reviewer.

**Decision:** Do not force the HTML's June PY Sales value to match the user-provided £42,086.96 reference.
**Alternatives considered:** Silently overwrite the calculated value with the reference figure.
**Reason for choice:** The reference figure could not be reproduced from any tested source-data variant; forcing it would hide a real discrepancy rather than resolve it.
**Trade-off accepted:** The published dashboard may look "wrong" to someone expecting £42,086.96 until the reference is reconciled — accepted as the honest state over a fabricated fix.
**Who approved:** Instructed explicitly by the task owner this session.

---

## 8. COMPANY KNOWLEDGE EXTRACT

### Business Rule:
When a reporting dashboard must show a business's full assigned inventory (not just what has transaction history), the report's row universe must be built by starting from the complete assignment/catalog master and `LEFT JOIN`ing transaction data onto it — never starting from the transaction table and treating "products that never sold" as out of scope.

### Operational Assumption:
Any table storing an ASIN without an accompanying SKU column (like `vendor_sales`) cannot be safely joined 1:1 onto a SKU-level report — its metric must be attributed at the ASIN level to exactly one row, never fanned out across that ASIN's SKU rows.

### Reusable Logic / Formula:
**Coarse-Grain Attribution Pattern:** when a metric source's grain is coarser than the report's row grain (ASIN-only data feeding an ASIN+SKU report), pick exactly one "carrier" row per coarse-grain key (reuse an existing blank/placeholder row if one exists; otherwise create exactly one new one) and gate the metric's inclusion on an explicit boolean flag (e.g. `isVendorRow`) rather than attaching it unconditionally to every matching row.

### Canonical Vocabulary:
FBM = Fulfilled by Merchant; FBA = Fulfilled by Amazon (both derived from `order_transaction.fba_sales`); Vendor = Amazon Vendor Central sales (from `vendor_sales`, ASIN-only, no SKU, no order-level key — always "Units", never "Orders"); Row Type = `ASIN_SKU` | `VENDOR_ASIN_LEVEL` | `NO_SKU_MAPPING` | `NO_SKU_MAPPING_VENDOR`.

### Cross-Project Applicability:
YES. The Coarse-Grain Attribution Pattern above applies to any project combining a per-SKU/per-item report with a secondary data source that only has parent-level (ASIN/product/category) granularity — e.g. a future eBay or Shopify Vendor-style channel, or supplier-level cost/rebate data joined onto a SKU-level P&L. Flagged as a parent-AIOS candidate below.

---

## 9. LLM STANDARD CHECK

| Check | YES / NO |
|---|---|
| Could an unknown developer continue from this file without reading source code? | YES |
| Is every business threshold visible (not buried in code)? | YES |
| Is the GAP section completed or marked NONE? | YES (completed) |
| Is the COMPANY KNOWLEDGE EXTRACT section substantive? | YES |
| Are evidence locations referenced? | YES |
| Is metadata complete? | YES |
| Is this extracting knowledge — not just logging activity? | YES |

**Three-AM Standard self-assessment:**
> A developer with no context could locate the exact ASIN+SKU-vs-Vendor duplication bug, understand why `vendor_sales` cannot be joined like a normal SKU table, and safely extend this pattern to a new fulfilment channel — using only this file and the referenced evidence, without reading the JS/Python source first.

---

## ── PARENT-AIOS CANDIDATE ─────────────────────────────────────────────────

*(Addendum — not deleted or promoted; recorded for future company-knowledge review, per `company_knowledge_candidate: YES` above.)*

- **Candidate title:** Safe handling of ASIN-level metrics when the main reporting grain is ASIN-SKU (Coarse-Grain Attribution Pattern)
- **Source subfolder:** `05_IMPLEMENTATION\src\uawso_client_engine.js` (`buildCanonicalRows`, `computeRowsV3`)
- **Problem solved:** Prevents a coarser-grain data source (ASIN-only, e.g. Vendor sales) from being duplicated across every finer-grain row (ASIN+SKU) it would naively join to.
- **Evidence path:** `07_EVIDENCE\2026-07-10_utharsika_v001_ASIN_SKU_GRAIN_AND_JUNE_RECONCILIATION.md` (Part 4 — Vendor duplication check, 0 leaked rows across all 1,723 ASINs)
- **Reuse reason:** Any future project joining a parent-level metric (supplier rebates, category-level costs, a new sales channel without item-level detail) onto an item-level report faces the identical duplication risk.
- **KPI or proxy KPI:** 0 duplicate-attributed rows / 0 revenue leakage onto sibling rows (verified programmatically, repeatable as a standard test).
- **Owner/reviewer:** Satheskanth (owner) / assigned technical reviewer (not yet confirmed).
- **Duplicate-risk check:** No equivalent pattern found documented elsewhere in this project's `08_SKILLS\` folder as of this date (first skill file for UAWSO).
- **Recommended next action:** If a second project encounters the same coarse-to-fine join problem, extract this pattern into a shared skill/company-knowledge entry rather than re-deriving it.

---

## ── SUBMISSION CHECKLIST ─────────────────────────────────────────────────────

- [x] File named correctly: `2026-07-10__satheskanth__uawso__REQ-01-D01.md`
- [x] All metadata fields filled
- [x] Sections 1–9 completed (or explicitly marked NONE)
- [x] No credentials, passwords, or API keys included
- [x] LLM Standard Check table completed
- [x] Three-Am Standard self-assessment written
- [x] Evidence location referenced

---
*DIGITWEB LK LTD — Daily Skill Increment System — v3.0 — May 2026*
*Filed by: Satheskanth*
