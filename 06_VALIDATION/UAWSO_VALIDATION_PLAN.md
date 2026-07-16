# UAWSO Validation Plan

**What this asset is:** The full set of checks the report and its publication must pass before being trusted or trusted-published.

**Why it exists:** To make "the report is correct" a checkable claim, not an assertion.

**Business question supported:** "How do we know this report is right before we let Utharsika see it?"

**Source or evidence used:** `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md`, `04_DESIGN\UAWSO_SOURCE_TO_TARGET_MAPPING.md`, `04_DESIGN\UAWSO_PH_TASK_PUBLICATION_PLAN.md`.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Plan only — no run has occurred yet to validate.
**Known limits:** Cannot be executed until implementation exists; this stage produced the checklist only.
**Pass/fail rule:** A run is fit to publish only when every applicable check below passes; any failed check blocks publication (see automation design §6 Validation Gate).
**Next action:** Apply this checklist to the first implementation test run.

---

## Scope Validation

- [ ] Only ASINs resolved via `public.user → public.ph_categories → public.ph_cate_products` (`which_channel=1`) for `user_name='utharsika'` are included.
- [ ] No SKU assigned only to another PH user appears in the output.
- [ ] The assignment join (`ph_cate_products.ass_cate_id = ph_categories.id`, `ph_categories.user_id = public.user.user` for `utharsika`) is verified against a fresh schema/data check, not assumed.
- [ ] Duplicate assigned ASINs are confirmed removed (`DISTINCT` applied; spot-check row count before/after).
- [ ] All UK Amazon accounts (`ss_name` values) are represented in the output when they have matching transactions — no `ss_name` filter is present in the query.
- [ ] No account-specific filter was applied.
- [ ] Amazon-only: every output row's source data has `source_name='AMAZON'`.
- [ ] UK-only: every output row's source data has `market_place='UK'`.
- [ ] Completed-only: every output row's source data has `order_status='Completed'`.

## Date Validation

- [ ] All date boundaries computed in `Asia/Colombo`, confirmed via `now() AT TIME ZONE 'Asia/Colombo'`, not server default timezone.
- [ ] Current (in-progress) day's data is excluded from every period.
- [ ] Daily boundary = exactly `report_date` (previous completed day) in both years.
- [ ] Weekly boundary starts Monday of `report_date`'s week; previous-year weekly boundary starts Monday of `(report_date − 1 year)`'s week — computed independently, not by ISO week number.
- [ ] Monday-run edge case: when `report_date` is itself a Monday, the Weekly range correctly collapses to one day and matches the Daily range for that day.
- [ ] MTD boundary starts the 1st of `report_date`'s month; previous-year MTD boundary starts the 1st of `(report_date − 1 year)`'s month.
- [ ] Month transition: a run on the 1st of a month produces a 1-day MTD range, not a rollover into the prior month.
- [ ] Year transition: a January run correctly computes its previous-year MTD range in the prior January, not the current year.
- [ ] Leap-year previous-year mapping: a `report_date` of Feb 29 maps to Feb 28 in a non-leap comparison year — confirmed via Postgres interval arithmetic, not manual date-string logic.

## Metric Validation

- [ ] Sales totals independently recomputed via `SUM(COALESCE(order_total,0))` and compared to report output.
- [ ] Currency tolerance: `±0.01`.
- [ ] Orders count matches `COUNT(DISTINCT order_item_info)` exactly — not `COUNT(DISTINCT order_id)`, not row count, not `SUM(quantity)`.
- [ ] Sales Change independently recomputed as `(This−Prev)/Prev` and compared.
- [ ] Order Change independently recomputed the same way.
- [ ] Trend confirmed derived from Sales only (spot-check a row where Sales and Orders trends would disagree, if one exists, to confirm Orders is not influencing Trend).
- [ ] Trend labels confirmed limited to exactly `UP`, `DOWN`, `NO CHANGE` — no other string appears in output.
- [ ] 130% target recomputed as `Previous × 1.30` and compared.
- [ ] Achieve Sales % recomputed as `(This ÷ Target) × 100` and compared.
- [ ] Achieve Order % recomputed the same way for Orders.
- [ ] Total row recalculated from aggregate `SUM()`s of the underlying rows, not from the report's own row-level percentage values.
- [ ] Confirm Total Achieve % ≠ `AVG()` of row-level Achieve % (this would indicate the averaging bug the business rules spec explicitly forbids).

## Edge-Case Validation

- [ ] Previous and current both zero → Trend = `NO CHANGE`, achievement/status field = `NOT IMPROVED`.
- [ ] Previous zero, current greater than zero → output shows the documented "unresolved/needs definition" marker, not a blank, zero, or invented percentage (open question — see business rules spec §6).
- [ ] Missing ASIN on a transaction row → row is excluded from ASIN-grouped output (cannot group what has no identity) and is flagged in run logs, not silently dropped without trace.
- [ ] Missing SKU on a transaction row → same handling as missing ASIN.
- [ ] SKU assigned to Utharsika through multiple categories → confirmed not double-counted (dedup at `assigned_asins` stage, before the transaction join).
- [ ] SKU/ASIN with zero Completed transactions in a period → appears with zero Sales/Orders for that period (if it has transactions in the other period being compared) or is correctly omitted if it has no transactions in either period at all — exact inclusion rule to be finalized in implementation based on whether "assigned but never sold" rows should appear.
- [ ] ASIN/SKU mapping changes (a SKU changes which ASIN it's under) between the current and previous-year windows → previous-year figures still reflect the transaction record's own `asin`/`sku` at the time of that order, not today's mapping (transaction-level attribution is immutable; only the assignment filter is "as of today").
- [ ] A reporting period with zero matching rows still produces a valid (empty but structurally correct) section, per automation design §4.

## Publication Validation

- [ ] `project_code = 'UAWSO'` on every published row.
- [ ] `report_date` is present in `task_id`, `task_name`, and the HTML heading (once HTML generation is implemented).
- [ ] Exactly one **active** (`version_status <> 'rejected'`) row exists per `report_date` at any given time.
- [ ] A same-date retry with unchanged content does not create a second `released` row.
- [ ] A same-date correction increments `version_level` and inserts a new `task_id` (`-vN` suffix), satisfying `ph_task_task_id_unique`.
- [ ] The superseded same-date row is set to `version_status='rejected'`.
- [ ] Rows for earlier report dates remain untouched and active after a same-date correction.
- [ ] `assigned_user` is exactly `utharsika` — verified character-for-character against `public.user.user_name`.
- [ ] `assigned_user_team` is exactly `ph_priors`.
- [ ] `action_took_by` and `action_took_date_time` are `NULL` at publication time.

## Isolation Validation

- [ ] **Other users' `ph_task` report content inspected or reused = NO.** (Confirmed throughout this design stage — no other PH user's `html_content`, task names, descriptions, ASIN/SKU values, or evidence paths were read or used as a template.)

## Migration Validation (already executed and passed this stage — restated here for completeness)

- [x] All 13 source files inventoried.
- [x] Every file has one canonical destination.
- [x] Original and destination SHA-256 hashes match for all 13 files.
- [x] Unresolved files = 0.
- [x] Unresolved conflicts = 0.
- [x] Files lost = 0.
- [x] Source contents modified during migration = 0.
- [x] Active documentation references to `Sources\` = 0 (only historical mentions in the manifest/evidence files).
- [x] `Sources` removed only after validation passed. See `07_EVIDENCE\source_migration\UAWSO_SOURCE_MIGRATION_VALIDATION.md`.
