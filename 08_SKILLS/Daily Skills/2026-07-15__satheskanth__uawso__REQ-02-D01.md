# SKILL FILE — DAILY KNOWLEDGE EXTRACTION TEMPLATE
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## ── METADATA BLOCK ──────────────────────────────────────────────────────────

date:                   2026-07-15
author:                 Satheskanth
developer:              satheskanth
project:                Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report
project_code:           UAWSO
phase:                  DEPLOY
requirement_id:         REQ-02
deliverable_id:         REQ-02-D01
status:                 COMPLETE
evidence_location:      07_EVIDENCE\2026-07-15_utharsika_REQ-02-D01_complete_real_data_html_validation.md ; 07_EVIDENCE\2026-07-15_utharsika_v004_local_business_rule_data_validation.md ; 07_EVIDENCE\2026-07-15_utharsika_v004_sticky_columns_export_and_definitions_validation.md ; 07_EVIDENCE\2026-07-15_utharsika_v004_sticky_pagination_validation.md ; 07_EVIDENCE\2026-07-15_utharsika_v004_ph_task_publication.md ; 07_EVIDENCE\2026-07-15_utharsika_v004_15_row_view_and_row_256_replacement.md ; 09_OUTPUTS\2026-07-15_utharsika_v004.html
blos_keys_used:         NONE — no formal BLOS-key registry exists in this project yet.
hardcoded_thresholds:   ACHIEVEMENT_TARGET_MULTIPLIER = 1.30 — used inside `computeRowsV5`/`computeTotalV5` (`uawso_client_engine.js`) to calculate the "Achievement %" column shown in today's report; unchanged from REQ-01, still not BLOS-governed. Cancelled/Canceled are NOT classified as a threshold — they are the status-exclusion rule, documented in Section 5 below.
three_am_standard:      PASS
llm_queryable:          YES
company_knowledge_candidate: YES
domain:                 E-commerce Operations — Amazon Marketplace — UK Sales and Orders
User:                   Utharsika
Benefit status:         ACHIEVED

## File path (fill after saving):
# 2026-07-15__satheskanth__uawso__REQ-02-D01.md

---

## 1. SYSTEM STATE

- **Current system state (before today):** UAWSO v002 (`09_OUTPUTS\2026-07-14_utharsika_v002.html`, `ph_task` row `id=237`) was the latest published report. Its row grain was one row per ASIN+SKU pair (plus a separate "no-SKU" and "Vendor" row type), with a visible SKU column, no product image, and Orders calculated by grouping at `(date, ASIN, SKU)` and summing up to the ASIN.
- **What was working:** The dynamic order-status exclusion rule (Cancelled/Canceled only), Sales/Orders/Quantity calculations, and the FBM/FBA/Vendor split — all carried over unchanged from REQ-01-D02.
- **What was broken / missing:** No product image existed anywhere in the report. The SKU column was still visible, which a prior discovery task (`03_DISCOVERY\2026-07-15_uawso_REQ-01-D03_image_and_asin_orders_discovery.md`) had flagged as a structural double-count risk for Orders — summing `(date, ASIN, SKU)` partitions up to the ASIN is not mathematically equivalent to grouping directly at `(date, ASIN)`, because the same `order_item_info` can appear under more than one SKU row for the same ASIN and date.
- **Your starting point:** A validated v002 report at ASIN+SKU grain; today's requirement (REQ-02-D01) was to replace it with a true ASIN-level report, add a product image, close the Orders double-count risk at the SQL layer, and improve table usability.

---

## 2. WHAT CHANGED TODAY

- **Change 1:** Rebuilt the report grain — one row per assigned ASIN, with `public.order_transaction` grouped directly by `(date, ASIN)` at the SQL layer (`extract_uawso_v5_asin_level.py`), never by `(date, ASIN, SKU)` then summed. SKU was removed entirely from the SQL `GROUP BY`, the JSON data model, the visible table, sorting, filtering, search, and the CSV — not hidden with CSS.
- **Change 2:** Added a product-image column sourced from `public.listing_data` (`ref_id = ASIN`, `which_channel=1`, `market_place='UK'`, `wrong_sku=0`), with a deterministic tie-break (lowest `listing_data.id`) when more than one valid image row exists for an ASIN — business-confirmed by Utharsika as a pure technical stability mechanism, not a quality judgment.
- **Change 3:** Ran a full, independent local business-rule validation against the live PostgreSQL source (read-only), re-deriving Sales, Orders, Quantity, Vendor Sales/Units, and image selection for all 1,723 ASINs from scratch and comparing against the shipped HTML — zero difference on every metric.
- **Change 4:** Added sticky header, frozen ASIN and Image columns, a sticky pagination bar with Previous/Next/direct-page-navigation, removed the Row Type column, kept a single "download all filtered rows" CSV action, and added a Column Definitions panel.
- **Change 5:** Corrected the table viewport, which had been sized as `70vh` (a window-height-relative guess that showed far fewer rows than intended on typical windows), to an absolute pixel height computed from real, headless-browser-measured dimensions (header + 15 body rows + pagination bar), so exactly 15 complete rows are visible regardless of the viewer's window size. Page size stayed at 50 — page size and visible-viewport row count are two different controls.
- **Change 6:** Published the verified HTML to a new `ph_task` row (`id=256`, `task_id=UAWSO-2026-07-15-utharsika-v004`), then, after explicit separate user approval, updated that same row in place with the viewport-corrected HTML (no new row, no new file version) — with reversible local and database backups taken first.
- **Change 7:** Recorded today's closure in `daily_task.tbl_uawso_satheskanth` (row `id=3`) via the MCP PostgreSQL connection.

**Evidence reference:** Final HTML SHA-256 `51865bbb45a5b49c15c74156723efa12d8ec6211f397487e9dec12f288587b24` (after the viewport correction; the original published SHA-256 was `8751b4d373772d4bc38c5e424000f846b842b61b73a9bb40368ba71df57d6f1e`); `ph_task` row `id=256`; full detail across the six evidence files listed in the metadata block above.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

**Table(s) involved:** `public.order_transaction`, `public.listing_data`, `public.vendor_sales`, `public.ph_cate_products`, `public.ph_categories`, `public.user`, `tech_team_outputs.ph_task`, `daily_task.tbl_uawso_satheskanth`

**Finding:** The production extraction script filters `source_name IN ('AMAZON', 'REPLACEMENT')` for Orders and Quantity, but `source_name = 'AMAZON'` only for Sales. During today's independent local validation, an initial re-check using `AMAZON` only for Orders produced 34,205 — 249 short of the approved 34,454. Adding the `REPLACEMENT` source closed the gap exactly. This was not a new rule invented today — it was already the extraction script's documented behaviour — but it was not obvious from the requirement document's own abbreviated Filter Conditions block, which only lists `source_name='AMAZON'`.

**SQL logic or pattern discovered:** `public.listing_data` has no schema-level restriction preventing more than one valid image row per ASIN (up to 6 candidate rows and 3 distinct images were found for some ASINs). A deterministic tie-break (`ROW_NUMBER() OVER (PARTITION BY ref_id ORDER BY id ASC) = 1`) is required — an unordered `LIMIT 1` would make the selected image vary between runs even with unchanged data.

**Operational meaning:** Two credential mechanisms exist for this project and must never be mixed: the approved `temp_user` credential (via `05_IMPLEMENTATION\config\.env`) is scoped to `tech_team_outputs` only — it has no access to the `daily_task` schema (`InsufficientPrivilege: permission denied for schema daily_task`, confirmed directly). The MCP PostgreSQL connection is the only path with `daily_task` access. Every future daily-task write must use MCP, not the `.env`/`temp_user` mechanism, and every `ph_task` HTML publication must use the `.env`/`temp_user` mechanism, not MCP.

---

## 4. GAP FOUND

**Gap description:** The report displays two columns — "Order Change %" and "Quantity Change %" — computed with the same formula pattern as the approved "Sales Change %", but REQ-02-D01's written business rules (Section 5 of the requirement) only define a Change formula for Sales. No written business rule for Order Change % or Quantity Change % exists in the currently-approved requirement document.
**Impact if unresolved:** The two columns display a number the code computes consistently, but no one has formally confirmed that percentage-change reporting is the intended, approved way to present period-over-period Orders/Quantity movement.
**Recommended action:** A future requirement update should either formally define the Order Change % / Quantity Change % formula (most likely: mirror the Sales Change % pattern) or state that these columns should be removed/relabelled.
**Owner (if known):** Satheskanth (owner) / business validator (Utharsika) for sign-off on the intended formula.

**Second gap (non-blocking):** Two of the 1,723 ASINs (`B0DPMQZ1WP`, `B0DPMRVHHR`) have overlapping/nested `vendor_sales` reporting windows for the same ASIN. The existing "sum every overlapping period, no proration" Vendor rule (unchanged since an earlier deliverable) sums both windows, which appears to double-count the nested portion — a combined £24.07 / 2-unit impact against a Vendor Sales total of £46,814.94 (0.05%) and a report Total Sales of £718,835.91 (0.003%). Immaterial to today's headline figures, not introduced today, but not previously documented either.

---

## 5. VALIDATION RULE ADDED OR CHANGED

**Rule name / ID:** ASIN-Level Grain Rule
**Condition checked:** One canonical row exists per assigned ASIN. `public.order_transaction` is grouped directly by `(date, ASIN)` at the SQL layer; SKU never appears in the grouping, the JSON payload, the visible table, or the CSV.
**What it prevents:** A structural Orders double-count that would occur if `(date, ASIN, SKU)` partitions were summed up to the ASIN instead of grouped directly at the ASIN.
**Where implemented:** `05_IMPLEMENTATION\src\extract_uawso_v5_asin_level.py`; `05_IMPLEMENTATION\src\uawso_client_engine.js :: buildCanonicalRowsV5, computeRowsV5, computeTotalV5`.
**BLOS reference:** None — no formal BLOS-key registry exists in this project.

**Rule name / ID:** Deterministic Image Selection Rule
**Condition checked:** `public.listing_data` filtered to `which_channel=1`, `market_place='UK'`, `wrong_sku=0`, non-blank `main_image_url`; when more than one valid row exists for an ASIN, select the row with the lowest `listing_data.id`.
**What it prevents:** The displayed product image changing between report runs for the same ASIN and the same underlying data.
**Where implemented:** `extract_uawso_v5_asin_level.py`; business-confirmed in `01_REQUIREMENTS\Requirement\2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md` Section 5.
**BLOS reference:** None.

---

## 6. FAILURE MODE OR EDGE CASE

**Failure scenario:** The table viewport was previously sized with `max-height: 70vh` — a fraction of whatever browser window height happened to be open. On a smaller or more typically-sized window, this showed far fewer complete rows than intended, with no indication to the user that more rows existed above the fold.
**How it is triggered:** Any window height below roughly 1300px (70vh needs to exceed header + 15 rows + pagination in absolute pixels for 15 rows to show; on a 900px-tall window, 70vh is only 630px).
**How it is detected:** User-reported ("the page size is 50, but the bounded table viewport currently displays only about five complete rows").
**Recovery procedure:** Replaced the viewport-relative CSS rule with an absolute pixel height, computed from real, headless-Chromium-measured dimensions (`--uawso-header-height`, `--uawso-row-height`, `--uawso-pagination-height`, `--uawso-visible-row-count: 15`, plus a small measured border-compensation buffer). Verified with a real browser at three different window sizes (1440×900, 1366×768, 1920×1080) — all three now show exactly 15 complete rows.
**Risk level:** LOW (now fixed and verified) — was MEDIUM before the fix, since it directly affected the end user's ability to see the data without excessive scrolling.

---

## 7. DECISIONS MADE TODAY

**Decision:** Group Orders directly at `(date, ASIN)` in the SQL layer, not by summing `(date, ASIN, SKU)` partitions up to the ASIN.
**Alternatives considered:** Keep the existing `(date, ASIN, SKU)` grouping and simply hide the SKU column with CSS.
**Reason for choice:** Hiding SKU with CSS would not close the structural double-count risk already flagged by an earlier discovery task — the same `order_item_info` could still be double-counted across SKU partitions under the hood.
**Trade-off accepted:** None material — the SQL change is a strict correctness improvement with no loss of information the report needs.
**Who approved:** Instructed explicitly in the approved REQ-02-D01 requirement document.

**Decision:** Size the table viewport in absolute pixels (measured), not `vh` (viewport-relative).
**Alternatives considered:** Increase the `vh` percentage; leave sizing device-relative.
**Reason for choice:** A `vh`-based height makes the number of visible rows vary by the viewer's window size — the actual reported symptom. An absolute pixel sum of real, measured header/row/pagination heights guarantees the same 15-row result on any window size.
**Trade-off accepted:** The fixed height assumes the row height driven by the 48px product image; the 24 ASINs without an image render a shorter row, so on rare occasions slightly more than 15 rows may be visible — never fewer.
**Who approved:** Instructed explicitly by the task owner this session.

**Decision:** Update the existing `ph_task` row 256 in place for the viewport correction, rather than publish a new `v005` file and a new row.
**Alternatives considered:** Publish a new version.
**Reason for choice:** Explicit user approval scoped the change as a correction to the existing v004 output, not a new deliverable version.
**Trade-off accepted:** None — reversible local and database backups were taken first, and both were verified byte-identical before any change was made.
**Who approved:** Instructed explicitly by the task owner this session.

---

## 8. COMPANY KNOWLEDGE EXTRACT

### Business Rule:
When a single business "product" (ASIN) can have more than one internal SKU, product-level reporting should use one row per product, with all qualifying SKU-level activity aggregated under it — not one row per SKU with the product identity duplicated across rows.

### Operational Assumption:
The system assumes an ASIN can have zero, one, or multiple valid product-image candidates in `public.listing_data`, and that Amazon Vendor Central (`public.vendor_sales`) reporting windows for the same ASIN may occasionally overlap in the source data — both must be handled deterministically rather than assumed to be clean.

### Reusable Logic / Formula:
**Direct-at-grain aggregation:** when a report's row key changes (e.g. from ASIN+SKU to ASIN-only), any COUNT(DISTINCT ...)-based metric must be re-grouped directly at the new grain in SQL — summing the old grain's pre-computed partitions up to the new grain is not equivalent and can silently double-count.
**Deterministic tie-break:** `ROW_NUMBER() OVER (PARTITION BY <entity> ORDER BY <stable id> ASC) = 1`, never an unordered `LIMIT 1`, whenever more than one valid candidate row can exist per entity.
**Viewport sizing:** table pagination page size (how many rows a "page" of data contains) and table viewport row count (how many rows are visible without scrolling) are two independent controls — a bounded scroll container's height should be computed from real, measured header/row/footer dimensions in absolute units, not a device-relative percentage.

### Canonical Vocabulary:
Same as REQ-01-D02 (FBM, FBA, Vendor, dynamic exclusion rule), plus: **ASIN-level grain** = one canonical row per ASIN, SKU entirely removed from the data model (not merely hidden); **Deterministic image tie-break** = lowest `listing_data.id`, a technical stability mechanism, not a business quality judgment; **Viewport row count** ≠ **page size** — distinct UI controls.

### Cross-Project Applicability:
YES. The direct-at-grain aggregation rule and the deterministic-tie-break pattern apply to any report where the row grain changes or where more than one valid "current" record can exist per entity. The viewport-sizing lesson applies to any paginated table UI in any project.

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
> A developer with no context could locate the ASIN-level grain rule, understand why SKU had to be removed from the SQL grouping (not just the UI), identify the exact image-selection tie-break and the AMAZON+REPLACEMENT Orders source nuance, and safely continue or extend today's work — using only this file and the referenced evidence, without reading the Python/JS source first.

---

## ── QUERY REFERENCE (for LLM retrieval) ──────────────────────────────────────

*(Addendum — answers to the standard queryability questions, so this file is self-sufficient without verbal explanation.)*

- **Requirement:** Replace the SKU-based report layout with a true ASIN-level report — one row per ASIN, no SKU, one deterministic product image per ASIN, ASIN-wise Orders, complete validation, improved table usability.
- **Report grain:** One row per assigned ASIN. SKU is not part of the SQL `GROUP BY`, the data model, the visible table, or the CSV.
- **Sales/Orders/Quantity source:** `public.order_transaction`. Sales = `item_price × quantity`, `source_name='AMAZON'` only. Orders = `COUNT(DISTINCT order_item_info)` grouped directly by `(date, ASIN)`, `source_name IN ('AMAZON','REPLACEMENT')`. Quantity = FBM Quantity + FBA Quantity (same source scope as Orders) + Vendor Units.
- **Image source:** `public.listing_data.main_image_url`, joined `ref_id = ASIN`, filtered `which_channel=1`, `market_place='UK'`, `wrong_sku=0`; lowest `id` tie-break when multiple valid rows exist.
- **Vendor source:** `public.vendor_sales`. `ordered_revenue` → Vendor Sales, `ordered_units` → Vendor Units, summed once per ASIN over any reporting window overlapping the report's date range (no proration). Vendor Orders = N/A (no order-level key exists).
- **Excluded statuses:** Cancelled, Canceled — dynamic exclusion rule, not a fixed allow-list.
- **Data range:** 2025-01-01 through 2026-07-14.
- **Scale:** 1,723 assigned ASINs; 1,699 image-covered; 24 no-image (17 no valid listing row, 7 all-blank image); 227 multi-image ASINs.
- **Final metrics:** Sales £718,835.91; Orders 34,454; Quantity 47,166 — all independently re-derived from the live PostgreSQL source during today's local validation, with zero difference against the shipped HTML on every one of the 1,723 ASINs.
- **Validation proving completeness:** Assigned-scope missing/extra/duplicate ASINs = 0; Sales/Orders/Quantity/Vendor per-ASIN differences = 0 (all 1,723 ASINs); image mismatches = 0; date-boundary errors = 0; total-formula failures = 0 (structurally guaranteed by the engine's own arithmetic identities).
- **UI additions:** sticky header; frozen ASIN and Image columns; sticky pagination bar with Previous/Next/direct-page-navigation; Row Type column removed; single "download all filtered rows" CSV action retained; Column Definitions panel added; table viewport corrected to show exactly 15 complete rows (absolute pixel sizing, not window-relative) while page size remained 50.
- **Final HTML location:** `09_OUTPUTS\2026-07-15_utharsika_v004.html` (current SHA-256 `51865bbb45a5b49c15c74156723efa12d8ec6211f397487e9dec12f288587b24`, after the viewport correction).
- **Evidence location:** the six files listed in the metadata block above, plus supporting CSVs under `07_EVIDENCE\generated_data\`.
- **Published ph_task row:** `tech_team_outputs.ph_task.id = 256` (`task_id = UAWSO-2026-07-15-utharsika-v004`), stored-hash verified matching the local file both at first publication and again after the in-place viewport-correction update.
- **Daily work record:** `daily_task.tbl_uawso_satheskanth.id = 3`.
- **Limitations remaining:** "Order Change %" and "Quantity Change %" are displayed columns with no written business-rule definition in the approved requirement (Sales Change % is the only one formally defined) — flagged as `PENDING_BUSINESS_RULE`, not silently assumed correct. Two ASINs have an unresolved Vendor overlapping-reporting-window observation (immaterial in scale, documented for future review). Automation and Task Scheduler remain disabled by explicit instruction throughout today's work.
- **Next refresh action:** Resolve the Order Change % / Quantity Change % business-rule gap with the business validator before the next deliverable; separately decide when to resume and validate unattended daily automation.
- **Safe to reuse:** YES — the asset is hash-verified against the stored `ph_task` HTML both before and after the in-place correction, the ASIN-level grain and image-selection rules are centralized in one extraction script and one client engine (no second independently-maintained copy exists), and every KPI was independently re-derived from the live source today, not merely carried forward from a prior build.

---

## ── COMPANY-KNOWLEDGE CANDIDATE PACKET ────────────────────────────────────────

**Status: CANDIDATE ONLY. Not approved as parent/company truth. Requires separate review before promotion.**

- **Candidate title:** ASIN-Level Product Grain, Deterministic Multi-Image Selection, and Direct-at-Grain Order Counting for Multi-SKU Products.
- **Source subfolder:** `08_SKILLS\Daily Skills\2026-07-15__satheskanth__uawso__REQ-02-D01.md` (this file), project `08_SKILLS` (UAWSO).
- **Problem solved:** Reporting at the wrong grain (SKU instead of product/ASIN) both confuses end users viewing multi-SKU products as separate rows, and creates a structural risk of double-counting order-count metrics if the old grain's data is merely summed up rather than re-grouped directly at the new grain.
- **Evidence path:** `07_EVIDENCE\2026-07-15_utharsika_v004_local_business_rule_data_validation.md` (full per-ASIN reconciliation, 1,723/1,723 zero-difference); `07_EVIDENCE\2026-07-15_utharsika_REQ-02-D01_complete_real_data_html_validation.md` (grain-change build evidence).
- **Reuse reason:** Any project reporting on a "product" that can have multiple underlying SKUs, listings, or line-item records faces the same grain-choice and tie-break-determinism questions.
- **KPI or proxy KPI:** Zero-difference validation across all rows at the new grain (this project: 1,723/1,723 ASINs, 0 mismatches on Sales/Orders/Quantity/Vendor/Image).
- **Owner/reviewer:** Satheskanth (author); business validator Utharsika; technical reviewer role assigned per the REQ-02-D01 requirement document (Sajeesan or assigned senior developer).
- **Duplicate-risk check:** No existing skill file in `08_SKILLS\Daily Skills\` documents this exact grain-change/tie-break pattern; the closest prior related skill (`2026-07-14__satheskanth__uawso__REQ-01-D02.md`) covers the dynamic status-exclusion pattern, a different (though complementary) topic.
- **Recommended next action:** Review this candidate against other AIOS projects with multi-SKU-per-product reporting needs; if confirmed broadly reusable, promote the "direct-at-grain aggregation" and "deterministic tie-break" patterns into a shared, project-independent skill or BLOS-style governance reference.

---

## ── KNOWN LIMITATIONS ─────────────────────────────────────────────────────────

- Automation and Task Scheduler remained disabled throughout today's work — no unattended daily run was enabled or resumed.
- The local `.env` credential (`05_IMPLEMENTATION\config\.env`) is approved only for publishing HTML into `tech_team_outputs.ph_task` — it must never be committed to version control, exposed in logs, or reused for any other schema.
- `daily_task` schema writes require the MCP PostgreSQL connection specifically — the `.env`/`temp_user` credential has no access to it (confirmed via a direct `InsufficientPrivilege` error).
- The Vendor reporting-window overlap for 2 of 1,723 ASINs (Section 4) is documented for future business review, not resolved today — it was out of scope for a UI/grain correction task.
- A historical incident (row 157's content not matching its local v001 file) predates today's work and remains a separate, previously-documented issue — not something today's work caused or resolved.

---

## ── SUBMISSION CHECKLIST ─────────────────────────────────────────────────────

- [x] File named correctly: `2026-07-15__satheskanth__uawso__REQ-02-D01.md`
- [x] All metadata fields filled
- [x] Sections 1–9 completed (or explicitly marked NONE)
- [x] No credentials, passwords, or API keys included
- [x] LLM Standard Check table completed
- [x] Three-Am Standard self-assessment written
- [x] Evidence location referenced

---
*DIGITWEB LK LTD — Daily Skill Increment System — v3.0 — May 2026*
*Filed by: Satheskanth*
