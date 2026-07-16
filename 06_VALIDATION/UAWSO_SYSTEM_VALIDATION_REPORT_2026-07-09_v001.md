# UAWSO System Validation Report — 2026-07-09_utharsika_v001

**What this asset is:** The `UAWSO_VALIDATION_PLAN.md` checklist applied to this session's actual dry-run results.

**Why it exists:** To turn the validation plan from a checklist into a record of what was actually verified, for this specific report date.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Applied to the 2026-07-09_utharsika_v001 dry run.
**Known limits:** Several checks apply only to a live `main.py` psycopg2 run or a real publish attempt, neither of which occurred this session — marked NOT RUN, not PASS, below.
**Pass/fail rule:** See `06_VALIDATION\UAWSO_VALIDATION_PLAN.md`.
**Next action:** Re-apply this report format after the first real `main.py --dry-run` (via psycopg2) and after the first real publish, once the user clears the gate.

---

## Scope Validation

| Check | Result |
|---|---|
| Only Utharsika-assigned SKUs included | PASS — assigned-ASIN resolution executed live (execution log S014), 1723 ASINs, matches prior confirmed count |
| No other user's assigned-only SKUs | PASS — resolution query never touches another user's `user_id`/category chain |
| Duplicate assignments removed | PASS — `DISTINCT` in SQL + `frozenset` in `sku_resolver.py`; live check in the design stage found 0 duplicates for Utharsika |
| Amazon only / UK only / all UK accounts / no account-specific filter / Completed only | PASS — verified by code review of `sql/02_report_query.sql` (mandatory filters hardcoded, no `ss_name` filter present) |

## Date Validation

| Check | Result |
|---|---|
| Asia/Colombo timezone used | PASS — `period_calculator.sri_lanka_today()` uses `zoneinfo("Asia/Colombo")`; session start independently confirmed as SLST via OS `date` |
| Current-day exclusion | PASS — `compute_report_date()` always subtracts 1 day; report_date=2026-07-09 for execution_date=2026-07-10, confirmed both in test and live run |
| Daily boundaries | PASS — unit test S007 |
| Monday-based Weekly boundaries | PASS — unit test S007 (Monday-edge collapse case) |
| MTD boundaries | PASS — unit test S007 (1st-of-month collapse case) |
| Month/year transitions | PASS — unit test S007 (January MTD previous-year case) |
| Leap-year handling | PASS — unit test S007 (Feb 29 2028 → Feb 28 2027) |

## Metric Validation

| Check | Result |
|---|---|
| Sales totals ±0.01 | PASS — DAILY reconciliation exact (350.94=350.94) |
| Orders = COUNT(DISTINCT order_item_info) | PASS — implemented exactly this way in `sql/02_report_query.sql`; DAILY reconciliation exact (12=12) |
| Sales/Order Change formula | PASS — unit test matches worksheet's own illustrative rows exactly (0.156, -0.105) |
| Sales-based Trend, 3 labels only | PASS — unit test + live DAILY validation (`DAILY-TREND-LABELS`) |
| Zero-base Trend rule (Prev=0,Curr>0 → UP; both zero → NO CHANGE) | PASS — unit test explicit cases |
| 130% targets | PASS — unit test matches worksheet example exactly (90.0%) |
| Achievement calculations | PASS — unit test + live DAILY validation (`DAILY-NO-FABRICATED-ACHIEVE`) |
| Totals from aggregates, not averaged | PASS — unit test explicit check + live DAILY validation (`DAILY-TOTAL-NOT-AVERAGED`) |

## Edge Cases

| Check | Result |
|---|---|
| Previous=0, Current=0 | PASS — unit test (`Trend=NO CHANGE`, `improvement_status=NOT IMPROVED`) |
| Previous=0, Current>0 | PASS — unit test (`Trend=UP`, achieve% undefined/None, no fabrication) |
| Missing ASIN/SKU | NOT RUN — no such row encountered in the live DAILY dataset this session |
| SKU assigned through multiple categories | PASS (design stage) — live check found 0 duplicate ASINs across Utharsika's 2 categories |
| SKU with no Completed transactions in a period | PASS — `render_section` shows "No transactions found" when a period's row list is empty (code-reviewed, not triggered by live DAILY data since it had rows) |
| Empty report period | NOT RUN — DAILY/WEEKLY/MTD all had data this session; empty-period path is code-reviewed only |
| Monday edge / first day of month / leap year | PASS — unit tests (S007) |

## Publication Validation

**NOT RUN** — no publish attempt occurred this session (gated). All publication-validation checks (task_id uniqueness, one-active-row rule, idempotency, correction versioning) are implemented in `src/ph_task_publisher.py` and code-reviewed against the live `ph_task_task_id_unique` constraint confirmed during the design stage, but have zero live executions.

## Isolation Validation

| Check | Result |
|---|---|
| Other users' ph_task content inspected or reused | **NO** — confirmed. Every query this session filtered exclusively on `user_name='utharsika'`/`user_id=109`; no other PH user's row, category, or ASIN was read or referenced. |

## Migration Validation

Carried over from the design stage — see `07_EVIDENCE\source_migration\UAWSO_SOURCE_MIGRATION_VALIDATION.md`. Verdict: PASS (unchanged this session).

---

## Overall Verdict For This Session

**Design/build/dry-run validation: PASS.**
**Publication validation: NOT RUN (intentionally gated).**
