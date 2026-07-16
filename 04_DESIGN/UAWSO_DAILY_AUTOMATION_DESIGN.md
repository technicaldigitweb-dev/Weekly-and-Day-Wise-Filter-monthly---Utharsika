# UAWSO Daily Automation Design

**What this asset is:** The future-state design for the daily automated run. No scheduler has been configured or executed.

**Why it exists:** To think through failure modes, retries, and evidence capture before any automation is built, per AIOS's evidence-first and drift-prevention standards.

**Business question supported:** "How will this run every day, unattended, without silently failing or duplicating?"

**Source or evidence used:** `01_REQUIREMENTS\UAWSO_REQUIREMENT_RECORD.md` (Daily Refresh Rule); `04_DESIGN\UAWSO_SQL_DESIGN.sql.md`; `04_DESIGN\UAWSO_PH_TASK_PUBLICATION_PLAN.md`.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Design implemented (`05_IMPLEMENTATION\scheduler\`); registration with the OS scheduler is gated pending explicit user go-ahead.
**Known limits:** The 03:00 Asia/Colombo start time (below) is this build's proposed choice, made per this execution stage's explicit instruction to "choose a safe start time" — it has not been separately validated by a production run's actual measured duration.
**Pass/fail rule:** Design passes review when every stage of the pipeline below has a defined success and failure behaviour.
**Next action:** User confirms go-ahead → run the `schtasks /Create` command in `05_IMPLEMENTATION\scheduler\UAWSO_SCHEDULER_DESIGN.md`.

---

## Frequency & Timezone

- **Frequency:** Daily.
- **Timezone:** `Asia/Colombo` — all date logic (report cutoff, scheduling) uses Sri Lanka calendar time, not server/UTC time.
- **Report cutoff:** `report_date` = previous completed Sri Lanka calendar day (never the current, in-progress day).
- **Run time:** `03:00 Asia/Colombo` daily — chosen this execution stage per explicit instruction to select a safe start time before the 06:00 deadline. Gives a 3-hour buffer for a lightweight pipeline (three aggregate queries + HTML render + one insert) plus room for one automatic retry. See `05_IMPLEMENTATION\scheduler\UAWSO_SCHEDULER_DESIGN.md` for the registration command (not yet run).
- **Daily publication deadline:** `06:00 Asia/Colombo`.

## Pipeline Stages

| Stage | Behaviour |
|---|---|
| **1. Input validation** | Confirm DB connectivity and that `report_date` computes to a sane, non-future, non-duplicate-of-today value before proceeding. |
| **2. SKU-assignment resolution** | Run the §0 assignment chain (`public.user` → `ph_categories` → `ph_cate_products`) fresh each run — assignments can change day to day, so this is never cached long-term. |
| **3. SQL execution sequence** | Execute the Daily, Weekly, MTD aggregation queries (per `UAWSO_SQL_DESIGN.sql.md`) in that order; each is independent and could run in parallel, but sequential execution simplifies failure isolation. |
| **4. Empty-result handling** | If the assigned-SKU set is empty (e.g. all categories unassigned), or a period has zero matching transactions, the report still publishes with an explicit "no data for this period" state per section rather than omitting the section — never silently skip a period. |
| **5. HTML generation sequence** | Build the three-section HTML (Daily, Weekly, MTD) only after all three SQL results are confirmed successful. Do not publish a partial report from a partially-failed run. |
| **6. Validation gate** | Run the checks in `06_VALIDATION\UAWSO_VALIDATION_PLAN.md` (scope, date, metric, edge-case) against the generated result before publication. A failed validation gate blocks publication and raises a failure (see Failure Handling). |
| **7. `ph_task` publication sequence** | Only after the validation gate passes: run the same-date-check → (optional reject) → insert sequence from `UAWSO_PH_TASK_PUBLICATION_PLAN.md`. |
| **8. Same-date idempotency** | A same-day re-run with unchanged inputs should not create a second `released` row — see the idempotency note in the publication plan (exact no-op vs. correction boundary is an implementation-stage decision). |
| **9. Same-date correction versioning** | A same-day re-run with changed/corrected output uses the reject-old + insert-new-versioned-row sequence. |
| **10. Logging** | Each run logs: `report_date`, assigned-SKU count, row counts per period, validation gate result, publication result (row id / task_id), and total run duration. |
| **11. Failure handling** | On failure at any stage, no partial `ph_task` row is published. The run is marked failed with the stage it failed at and the error detail. |
| **12. Retry handling** | A failed run may be retried manually or automatically; a retry must re-run from Stage 1 (never resume mid-pipeline with stale intermediate state), and must respect the idempotency rule in Stage 8. |
| **13. Credential handling** | Database credentials are read from environment variables (per the pattern in `02_SOURCE\db_access_templates\temp_user.py`), never hard-coded into the automation script or logged in evidence output. |
| **14. Evidence capture** | Each successful run's log (Stage 10 fields) is retained as evidence — exact storage location (e.g. `07_EVIDENCE\`) to be finalized at implementation time. |
| **15. Rollback** | If a publication is later found incorrect after the fact (post-run), the correction path is the Same-Date Correction Rule (reject + new version) — there is no destructive rollback/delete of a published row. |
| **16. Next-day behaviour** | The next day's run is fully independent — it computes its own `report_date` (today's run's `report_date + 1`) and does not depend on or re-validate the prior day's row. |

## Explicitly Out of Scope This Stage

No scheduler (cron, Task Scheduler, CI job, or otherwise) has been configured or run. This document describes intended future behaviour only.
