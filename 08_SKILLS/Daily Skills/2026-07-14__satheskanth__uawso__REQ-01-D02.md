# SKILL FILE — DAILY KNOWLEDGE EXTRACTION TEMPLATE
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## ── METADATA BLOCK ──────────────────────────────────────────────────────────

date:                   2026-07-14
developer:              satheskanth
project:                Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report
project_code:           UAWSO
phase:                  DEPLOY
requirement_id:         REQ-01
deliverable_id:         REQ-01-D02
status:                 COMPLETE
evidence_location:      07_EVIDENCE\2026-07-14_utharsika_v002_DYNAMIC_STATUS_FINAL_BUILD_AND_PUBLICATION.md ; 07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_dynamic_status_monthly_reconciliation.csv ; 07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_dynamic_status_reference_reconciliation.csv ; 09_OUTPUTS\2026-07-14_utharsika_v002.html
blos_keys_used:         NONE — no formal BLOS-key registry exists in this project yet; the order-status inclusion rule (documented below) is the business-logic key that would normally be BLOS-governed.
hardcoded_thresholds:   NONE remaining for order-status inclusion — the prior fixed seven-status allow-list was replaced by a dynamic exclusion rule (only Cancelled and Canceled are hardcoded, as the exclusion side). ACHIEVEMENT_TARGET_MULTIPLIER = 1.30 remains unchanged from D01, still not BLOS-governed.
three_am_standard:      PASS
llm_queryable:          YES
company_knowledge_candidate: YES
domain:                 E-commerce Operations — Amazon Marketplace — UK Sales & Orders
User:                   Utharsika
Benefit status:         PASS

## File path (fill after saving):
# 2026-07-14__satheskanth__uawso__REQ-01-D02.md

---

## 1. SYSTEM STATE

- **Current system state (before today):** UAWSO v002 (`09_OUTPUTS\2026-07-10_utharsika_v002.html`, `ph_task` row `id=237`) used a **fixed seven-status allow-list** (`Completed, Refunded, Deleted, New, Pending, Inprogress, Hold`) for Sales/Orders/Quantity inclusion, hardcoded in both `extract_uawso_v4_ordered_sales.py` and mirrored implicitly in the client engine's pre-aggregated data. The list had been derived from a one-time status discovery and would silently miss any future new status.
- **What was working:** Ordered Product Sales (`item_price × quantity`), Total Orders (`COUNT(DISTINCT order_item_info)`), Total Quantity, the `periodsOverlapV4`/`sumVendorRangeV4` Vendor boundary fix, the full 1,723-ASIN/one-row-per-ASIN-SKU grain, and the ASIN-level Vendor non-duplication rule (all carried over unchanged from D01/the prior seven-status build).
- **What was broken / missing:** The status list was a fixed allow-list, not derived dynamically — a genuine mismatch risk, since a brand-new operational status appearing in `order_transaction` in the future would be silently excluded from Sales/Orders/Quantity until a developer manually noticed and updated the hardcoded list.
- **Your starting point:** A validated, but not-yet-dynamic, seven-status v002 build; the task for today was to make the status rule exclusion-based (future-proof) and re-publish under the correct final identity.

---

## 2. WHAT CHANGED TODAY

- **Change 1:** Ran a fresh, full-table status discovery against `public.order_transaction` (all users, all time) to confirm the complete, current set of distinct `order_status` values before changing any rule — found exactly the same 9 statuses as previously known (no new one), 0 null, 0 blank.
- **Change 2:** Rewrote `05_IMPLEMENTATION\src\extract_uawso_v4_ordered_sales.py` — replaced the fixed `APPROVED_STATUSES` tuple and every `order_status IN %(statuses)s` clause with `EXCLUDED_ORDER_STATUSES = {"Cancelled", "Canceled"}`, an `is_included_order_status()` Python helper, and one shared `STATUS_FILTER_SQL` fragment (`status IS NOT NULL AND BTRIM(status) <> '' AND BTRIM(status) NOT IN ('Cancelled','Canceled')`) reused identically in the product-master SKU-discovery query and the daily-aggregates query.
- **Change 3:** Added the client-side mirror to `05_IMPLEMENTATION\src\uawso_client_engine.js` — `EXCLUDED_ORDER_STATUSES` (a `Set`) and `isIncludedOrderStatus(value)`, exported from the engine. Not on the current hot path (filtering already happens server-side before the daily-aggregates JSON is embedded) but available for any future client-side status filter, so it can never drift from the SQL-side rule.
- **Change 4:** Freshly extracted the complete historical dataset (2025-01-01 → 2026-07-13, 1,723 assigned ASINs, 34,413 qualifying `order_transaction` rows, 960 `vendor_sales` rows) under the new dynamic rule and generated `09_OUTPUTS\2026-07-14_utharsika_v002.html` directly at its own dedicated final path (not overwriting the frozen `2026-07-10_utharsika_v002.html`, and not a `new_v002`/`v003` candidate file — that temporary file was deleted after validation passed).
- **Change 5:** Validated all 19 monthly reporting periods (2025-01 through 2026-07, capped at the 13th) — PostgreSQL vs. embedded HTML vs. dashboard vs. CSV all reconcile to exactly £0.00 Sales / 0 Orders / 0 Quantity difference; missing/extra/duplicate `order_item_info` all zero.
- **Change 6:** Published the verified HTML to the **existing** `ph_task` row `id=237` (`task_id=UAWSO-2026-07-14-utharsika-v002`) inside a transaction — updated only `html_content` and `updated_at`; did not touch `task_id`, `version_level`, or row `id=157`.

**Evidence reference:** Final HTML SHA-256 `16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684`; `ph_task` row `id=237`; full detail in `07_EVIDENCE\2026-07-14_utharsika_v002_DYNAMIC_STATUS_FINAL_BUILD_AND_PUBLICATION.md`.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

**Table(s) involved:** `public.order_transaction`, `public.vendor_sales`, `public.ph_cate_products`, `public.ph_categories`, `public.user`, `tech_team_outputs.ph_task`, `daily_task.tbl_uawso_satheskanth`

**Finding:** `public.order_transaction.order_status` contains exactly **9 distinct values**: `Canceled, Cancelled, Completed, Deleted, Hold, Inprogress, New, Pending, Refunded`. No `NULL` and no blank-string status exists anywhere in the table. `Cancelled` (double-L) and `Canceled` (single-L) are two genuinely distinct stored strings, not a casing variant of each other, and both must be excluded — a query filtering only one of the two would silently leak the other's rows into Sales/Orders.

**SQL logic or pattern discovered:** An exclusion-based filter (`status IS NOT NULL AND BTRIM(status) <> '' AND BTRIM(status) NOT IN ('Cancelled','Canceled')`) is strictly safer than an inclusion-based allow-list for a status column that is not schema-constrained (no `CHECK` constraint on `order_transaction.order_status` restricting its values) — new statuses can and do appear over time (`Hold` and `Inprogress` were both first observed within the current reporting window, dated 2026-07-12/13), and an allow-list silently drops them while an exclusion-list picks them up automatically.

**Operational meaning:** `daily_task.tbl_uawso_satheskanth` (used for today's own daily-work record) is only writable via the MCP PostgreSQL tool — the `temp_user` credential used for direct `psycopg2` connections does not have `daily_task` schema privileges (confirmed by repeated `InsufficientPrivilege` errors). `tech_team_outputs.ph_task`, by contrast, is writable via both paths. Any future daily-task push must use the MCP tool, not a direct credential connection.

---

## 4. GAP FOUND

**Gap description:** No `CHECK` constraint (or equivalent schema-level enumeration) exists on `public.order_transaction.order_status`, so the set of valid statuses is defined entirely by whatever values happen to be inserted by upstream systems — there is no authoritative, queryable list of "all statuses that will ever exist."
**Impact if unresolved:** A future new status is included automatically under the dynamic rule (correct default behaviour), but its business meaning (is it a valid sale, an operational placeholder, a new cancellation variant?) is not reviewed automatically — it could silently and materially affect Sales/Orders/Quantity if it turns out to represent something that should have been excluded.
**Recommended action:** Every future UAWSO refresh should re-run the status discovery query and explicitly report any status not seen in the previous refresh, with its row count and Sales contribution, before treating the new totals as final.
**Owner (if known):** Satheskanth (owner) / assigned technical reviewer for sign-off on any newly discovered status's business meaning.

---

## 5. VALIDATION RULE ADDED OR CHANGED

**Rule name / ID:** Dynamic Order-Status Inclusion Rule
**Condition checked:** Include a row when `order_status` is not null, `BTRIM(order_status) <> ''`, and `BTRIM(order_status) NOT IN ('Cancelled', 'Canceled')`. This is **exclusion-based**, not a fixed allow-list — any status satisfying the condition is included automatically, with no code change required when a new status appears.
**What it prevents:** A future new, valid order status being silently omitted from Sales/Orders/Quantity because a hardcoded include-list was never updated.
**Where implemented:** `src/extract_uawso_v4_ordered_sales.py :: STATUS_FILTER_SQL, is_included_order_status()`; `src/uawso_client_engine.js :: EXCLUDED_ORDER_STATUSES, isIncludedOrderStatus()`.
**BLOS reference:** None — no formal BLOS-key registry exists in this project; documented here as the source of truth.

---

## 6. FAILURE MODE OR EDGE CASE

**Failure scenario:** A future new order status could represent something that should logically be excluded (e.g. a new cancellation-family status, a fraud-hold status, a test/dummy status) but would be **included automatically** under the current dynamic rule, since only `Cancelled`/`Canceled` are excluded by name.
**How it is triggered:** Any new distinct value appearing in `order_transaction.order_status` that is not one of the two named exclusions.
**How it is detected:** Not automatically flagged by the current code — must be caught by re-running the status discovery query at the start of each future refresh and comparing the distinct-status list against the previous refresh's list.
**Recovery procedure:** If a newly discovered status should be excluded, add its exact string to `EXCLUDED_ORDER_STATUSES` in both `extract_uawso_v4_ordered_sales.py` and `uawso_client_engine.js` (kept in sync, per the single-source-of-truth pattern already established), then re-extract and re-validate.
**Risk level:** MEDIUM — low probability per refresh (only 2 new statuses, `Hold` and `Inprogress`, appeared across ~19 months of history and 34,413+ qualifying rows, both currently zero-impact on Utharsika's assigned scope), but the impact if a materially-different new status appeared unreviewed could be significant.

---

## 7. DECISIONS MADE TODAY

**Decision:** Use exclusion-based status filtering (`NOT IN ('Cancelled','Canceled')`) instead of continuing with a fixed seven-status allow-list.
**Alternatives considered:** Keep the fixed list and manually add to it whenever a new status is noticed.
**Reason for choice:** An allow-list requires a human to notice a new status before it's ever included — a silent-omission failure mode. An exclusion-list only requires a human to notice a new status if it needs to be *excluded* — the default (inclusion) is the safer one for a Sales/Orders reporting KPI, since under-reporting Sales is a worse failure than over-reporting a status that turns out to need exclusion later (which is still caught at the next refresh's discovery step).
**Trade-off accepted:** A future new status that should have been excluded will be included until a developer reviews and adds it to the exclusion set — mitigated by the recommendation (Section 4/6) that every refresh re-run the discovery query and report new statuses explicitly.
**Who approved:** Instructed explicitly by the task owner this session.

**Decision:** Write the final rebuild directly to a new dedicated path (`2026-07-14_utharsika_v002.html`) rather than overwriting the frozen `2026-07-10_utharsika_v002.html`.
**Alternatives considered:** Overwrite the existing `2026-07-10` v002 file in place.
**Reason for choice:** Explicit instruction to preserve `v001` and the existing `v002` unchanged, and to publish only after a fully independent, freshly-dated build passed every validation gate.
**Trade-off accepted:** Two "v002"-labelled files now exist on disk with different dates and different content — documented clearly here and in the evidence file to prevent confusion about which one is currently published (`2026-07-14_utharsika_v002.html` is the one stored in `ph_task` row `id=237`).
**Who approved:** Instructed explicitly by the task owner this session.

---

## 8. COMPANY KNOWLEDGE EXTRACT

### Business Rule:
For any reporting KPI driven by a free-text status column with no schema-level enumeration (`CHECK` constraint), prefer an **exclusion-based** inclusion rule (name the few statuses that must be excluded) over an **allow-list** (name every status that must be included) — an allow-list silently drops any future new status, while an exclusion-list includes it by default and only requires review, not a code change, to keep correct.

### Operational Assumption:
The system assumes new operational statuses (e.g. `Hold`, `Inprogress`, both first seen 2026-07-12/13) can appear in `order_transaction.order_status` at any time without a schema migration or announcement — the reporting layer must be resilient to that by design, not by manual maintenance.

### Reusable Logic / Formula:
**Dynamic Exclusion-List Pattern:** `is_included(status) = status IS NOT NULL AND TRIM(status) <> '' AND TRIM(status) NOT IN (<named exclusions>)`, implemented identically (same literal exclusion set) in every layer that touches the status (SQL extraction, client engine) so no two layers can drift into disagreement about which statuses count.

### Canonical Vocabulary:
Same as D01 (FBM, FBA, Vendor, Row Type), plus: **Dynamic exclusion rule** = the current, final UAWSO status rule (as opposed to the superseded "fixed seven-status allow-list"); **Cancellation variants** = the two excluded statuses `Cancelled` (double-L) and `Canceled` (single-L), which are distinct stored strings, not a spelling normalization of one another.

### Cross-Project Applicability:
YES. Any project with a free-text status/state column lacking a database-level enumeration should default to an exclusion-based inclusion rule for reporting KPIs, for the same reason documented above. This generalizes beyond UAWSO to any Sales/Orders/status-driven report in this codebase.

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
> A developer with no context could locate the dynamic status-exclusion rule, understand why it replaced a fixed allow-list, identify exactly which two statuses are excluded (and that `Cancelled`/`Canceled` are distinct strings, not a typo of each other), and safely extend the exclusion set for a future new status — using only this file and the referenced evidence, without reading the Python/JS source first.

---

## ── QUERY REFERENCE (for LLM retrieval) ──────────────────────────────────────

*(Addendum — answers to the standard queryability questions, so this file is self-sufficient without verbal explanation.)*

- **Requirement:** Validate the Utharsika Sales and Orders data mismatch, identify the root cause in order-status filtering, confirm the correct dynamic status rule, rebuild the complete historical v002 report, validate the output and publish the verified HTML.
- **Mismatch found:** The published v002 dashboard's Sales/Orders/Quantity did not fully reflect all valid order activity, because status inclusion was governed by a fixed seven-status allow-list rather than the business's true rule ("every status except cancellations").
- **Root cause:** Order-status filtering used a hardcoded allow-list instead of an exclusion-based rule — functionally correct on the day it was written (the allow-list happened to match all 7 non-cancellation statuses that existed at the time), but structurally unsafe against future new statuses.
- **All 9 statuses that exist today:** Canceled, Cancelled, Completed, Deleted, Hold, Inprogress, New, Pending, Refunded.
- **Excluded statuses:** Cancelled, Canceled — the only two, by name, forever (unless a future decision explicitly changes this).
- **Dynamic inclusion rule:** `status IS NOT NULL AND BTRIM(status) <> '' AND BTRIM(status) NOT IN ('Cancelled','Canceled')` — implemented identically in `extract_uawso_v4_ordered_sales.py` (SQL) and `uawso_client_engine.js` (JS mirror).
- **Source tables used:** `public.order_transaction`, `public.vendor_sales`, `public.user`, `public.ph_categories`, `public.ph_cate_products`.
- **Data range fetched:** 2025-01-01 through 2026-07-13 inclusive (19 distinct reporting months, July 2026 capped at the 13th).
- **Scale:** 1,723 assigned ASINs; 34,413 qualifying `order_transaction` rows; 960 `vendor_sales` rows; 2,575 final output rows (2,138 ASIN+SKU + 105 no-SKU + 332 Vendor).
- **Sales calculation:** `item_price × quantity`, `source_name='AMAZON'`, dynamically-included status. Refunded value is never deducted from the month the order was originally placed.
- **Orders calculation:** `COUNT(DISTINCT order_item_info)`, dynamically-included status, `source_name IN ('AMAZON','REPLACEMENT')`. Vendor Units are never added to Total Orders.
- **Quantity calculation:** FBM Quantity + FBA Quantity + Vendor Units.
- **Vendor handling:** `ordered_revenue` → Vendor Sales, `ordered_units` → Vendor Units, ASIN-level only (never duplicated across SKU rows), Vendor Orders = N/A (no valid order key exists in `vendor_sales`). Overlap allocation uses the corrected `periodsOverlapV4`/`sumVendorRangeV4` boundary logic — a Vendor period ending exactly at the next reporting period's start is not double-counted into that next period.
- **Validation proving completeness:** All 19 monthly periods reconciled to exactly £0.00 Sales / 0 Orders / 0 Quantity difference between PostgreSQL, the embedded HTML, the dashboard engine, and the CSV export; missing/extra/duplicate `order_item_info` all confirmed zero; 0 duplicate ASIN–SKU pairs.
- **Final HTML location:** `09_OUTPUTS\2026-07-14_utharsika_v002.html` (SHA-256 `16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684`).
- **Evidence location:** `07_EVIDENCE\2026-07-14_utharsika_v002_DYNAMIC_STATUS_FINAL_BUILD_AND_PUBLICATION.md`, plus the two reconciliation CSVs listed in the metadata block above.
- **Published ph_task row:** `tech_team_outputs.ph_task.id = 237` (`task_id = UAWSO-2026-07-14-utharsika-v002`), stored-hash verified matching the local file.
- **Daily work record:** `daily_task.tbl_uawso_satheskanth.id = 2`.
- **Limitations remaining:** `order_date` is the best-supported original-order-date field but is not absolutely provable as such (no separate refund-date column exists in the schema); Vendor data has no order ID or SKU, so Vendor Orders cannot be calculated and remain N/A; one reference-CSV row (ASIN `B0GY3G4S1F`) only reconciles via its Mapped SKU `LSGL1275CL3PK+RPM40WH3PK`, not its supplied SKU, because the supplied SKU has zero transactions anywhere in the system.
- **Next refresh action:** Re-run the status discovery query first; explicitly report any status not present in this file's list of 9, along with its row count and Sales contribution, before treating the refreshed totals as final.
- **Safe to reuse:** YES — the asset is hash-verified against the stored `ph_task` HTML, the extraction/engine status rule is centralized (no second independently-maintained status list exists), and the row grain/Vendor non-duplication rules carried over unchanged and re-validated from D01.

---

## ── SUBMISSION CHECKLIST ─────────────────────────────────────────────────────

- [x] File named correctly: `2026-07-14__satheskanth__uawso__REQ-01-D02.md`
- [x] All metadata fields filled
- [x] Sections 1–9 completed (or explicitly marked NONE)
- [x] No credentials, passwords, or API keys included
- [x] LLM Standard Check table completed
- [x] Three-Am Standard self-assessment written
- [x] Evidence location referenced

---
*DIGITWEB LK LTD — Daily Skill Increment System — v3.0 — May 2026*
*Filed by: Satheskanth*
