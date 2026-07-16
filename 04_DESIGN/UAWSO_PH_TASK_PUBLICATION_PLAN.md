# UAWSO `ph_task` Publication Plan

**What this asset is:** The documented, field-by-field plan for how each daily report will be published into `tech_team_outputs.ph_task`. No insert or update has been executed.

**Why it exists:** To settle the identity, versioning, and idempotency design before any automation writes to a shared production table.

**Business question supported:** "What exactly will be written to `ph_task`, and how do we guarantee one clean row per report date without duplicates?"

**Source or evidence used:** `08_SKILLS\ph_task_rules\` (schema, versioning, `assigned_user_team` docs); live read-only schema check of `tech_team_outputs.ph_task` constraints (this stage).

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Design complete and implemented (`src/ph_task_publisher.py`), not yet executed against production — gated pending explicit go-ahead for the first live write.
**Known limits:** `description` wording is a proposed default, not sourced from an explicit instruction. `team` and the `task_id`/`task_name` identity patterns below were confirmed explicitly in this execution stage's instructions, superseding this document's earlier proposed values.
**Pass/fail rule:** Passes when every column below has a defined value, and the same-date correction sequence cannot violate the live `ph_task_task_id_unique` constraint.
**Next action:** User confirms go-ahead for the first live publish — see `10_HANDOVER\UAWSO_HANDOVER.md`.

---

## Confirmed Live Constraint (drives this design)

`tech_team_outputs.ph_task` has a live `UNIQUE` constraint named `ph_task_task_id_unique` on `task_id`, confirmed by direct schema inspection this stage (read-only). This is **table-wide**, not scoped to active rows only — so a rejected row's `task_id` can never be reused, even by its own replacement.

## Required Publication Values

| Column | Value | Rationale |
|---|---|---|
| `project_name` | `Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report` | Full project name, consistent across every row |
| `project_code` | `UAWSO` | Constant, per stage brief |
| `task_name` | `YYYY-MM-DD_utharsika_vNNN` (e.g. `2026-07-09_utharsika_v001`) | `YYYY-MM-DD` = `report_date`; **confirmed format, this execution stage** — supersedes this document's earlier proposed format |
| `task_id` | `UAWSO-YYYY-MM-DD-utharsika-vNNN` (e.g. `UAWSO-2026-07-09-utharsika-v001`) | **Confirmed format, this execution stage**; `vNNN` is 3-digit zero-padded and always present (including v001), satisfying `ph_task_task_id_unique` — see §Same-Date Correction Rule below |
| `team` | `PH Team` | **Confirmed, this execution stage** — supersedes the earlier proposed `Technical` value |
| `developer` | `Satheskanth` | Given in stage brief |
| `assigned_user` | `utharsika` | Copied verbatim from `public.user.user_name`, confirmed live (`user=109`) — not retyped, not re-capitalised |
| `assigned_user_team` | `ph_priors` | Given in stage brief; routes the task to the PH Priors board per `08_SKILLS\ph_task_rules\New column - assigned_user_team.md` |
| `html_content` | Generated HTML report body (structure: dated heading, three sections — Daily / Weekly / MTD — each with the 11-field table + Total row) | **Not generated this stage** — final production HTML generation is explicitly out of scope |
| `description` | `Automated Daily/Weekly/MTD Sales & Orders report for Utharsika's assigned Amazon UK SKUs vs. prior-year performance and 130% achievement targets.` (**proposed**) | Descriptive free text; confirm wording is acceptable |
| `phase_level` | `1` | First delivery phase of this capability |
| `version_level` | `1` for first publication of a `report_date`; incremented per same-date correction | Per `08_SKILLS\ph_task_rules\Versioning - phase_level and version_level.md` |
| `version_status` | `'released'` for the active row; `'rejected'` set on the row being superseded | Per versioning rule doc |
| `action_took_by` | `NULL` | Populated only when `utharsika` completes the action |
| `action_took_date_time` | `NULL` | Same as above |

## Daily Task Identity

- Every report date is a distinct task row. `report_date` appears in `task_id`, `task_name`, and (in the generated HTML, when built) the heading and filename/output identity.
- A normal next-day publication never touches a prior day's row — each `task_id` is date-scoped and, once past v1, version-scoped.

## Idempotency: Same-Date Retry

A retry (e.g. automation re-run after a transient failure, same `report_date`, no content correction) must not create a duplicate. Implemented in `src/ph_task_publisher.find_active_same_date_row()`: before inserting, check for an existing active (`version_status <> 'rejected'`) row matching the `UAWSO-YYYY-MM-DD-utharsika-%` prefix for that date. If one exists and this is not a declared correction, `publish_report()` refuses to insert and returns `duplicate_check_passed=False` rather than creating a second active row. Per the stage brief's Failure and Retry Rules: a failed attempt before any successful insert does not consume a version (`version_resolver.resolve_planned_version()` only advances after `consume_version_on_success()` is called, which only happens post-commit).

## Same-Date Correction Rule (content actually changed)

Implemented in `src/ph_task_publisher.publish_report(..., is_correction=True)`:

1. Identify the existing **active** same-date row (`version_status <> 'rejected'`, matching the `UAWSO-YYYY-MM-DD-utharsika-%` prefix).
2. `UPDATE` that row: `version_status = 'rejected'`. Its `task_id` is **left unchanged** — it must not be reused.
3. `INSERT` a new row with `version_level` incremented by 1 and `task_id = 'UAWSO-YYYY-MM-DD-utharsika-v{new_version_level:03d}'` — table-wide `task_id` uniqueness (`ph_task_task_id_unique`) is satisfied because every version's task_id, including v001, embeds the version number.
4. New row: `version_status = 'released'`.
5. Rows for **earlier** report dates are never touched by a same-date correction — the lookup in step 1 is always scoped to the one `report_date` being corrected.
6. The whole sequence runs inside one DB transaction (`conn.commit()`/`conn.rollback()`), with a read-back verification of the inserted row and a post-insert count confirming exactly one active row remains for the date, before committing.

## Isolation Confirmation

This plan defines only `utharsika`-scoped rows (`assigned_user = 'utharsika'`, `assigned_user_team = 'ph_priors'`). No other PH user's `ph_task` row, `task_id` pattern, or `html_content` was read or used as a template while designing this plan. **Other users' ph_task report content inspected or reused = NO.**

## Explicitly Out of Scope This Stage

No `INSERT`, `UPDATE`, or `DELETE` against `tech_team_outputs.ph_task` has been executed. This document is a plan only.
