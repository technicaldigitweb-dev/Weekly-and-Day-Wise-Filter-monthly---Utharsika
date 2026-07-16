# `phase_level` and `version_level` on `tech_team_outputs.ph_task`

**For:** Vithushali
**Table:** `tech_team_outputs.ph_task` (PostgreSQL)
**Date:** 2026-07-08

## What each column is for

| Column | Data type | Purpose |
|---|---|---|
| `phase_level` | **integer** (whole number, e.g. `1`, `2`, `3`) — defaults to `0` | Which **project phase** this task belongs to. Used when a project is delivered in stages — e.g. Phase 1 = discovery/setup, Phase 2 = rollout, etc. |
| `version_level` | **integer** (whole number, e.g. `1`, `2`, `3`) — defaults to `0` | Which **revision/version** of the task this row is. Used when the same task gets reworked and re-published — e.g. v1, v2, v3 of the same report/output. |

Both are plain integer columns — not text, not decimals. Just increase the number by 1 each time (e.g. `1` → `2` → `3`). Right now the dashboard doesn't use them to filter or sort anything on its own. They exist so the history of a task's phase/version is recorded on each row.

## What to do when a new version is released

When you release version 2 (or later) of a task:

1. **Insert a new row** for the new version — same `project_name` / `project_code` / `task_name` (or whatever identifies it as "the same task" to you), `version_level` incremented, new `html_content`.
2. **On the old row (the version being replaced), set `version_status = 'rejected'`.**

This second step matters — it's not just a label. As of 2026-07-08, the dashboard's Pending/Completed views actively **hide any row with `version_status = 'rejected'`** from both boards (PH Priors and Ebay Priors). So once you mark the old row `rejected`, it disappears from the PH/Ebay holder's task list entirely, and only the new version shows up.

If you release a new version but forget to set the old row to `rejected`, the old version will keep showing up in the holder's list alongside the new one — so please make this a standard step whenever you push a new version.

## Example

```sql
-- 1. Reject the old version
UPDATE tech_team_outputs.ph_task
SET version_status = 'rejected'
WHERE id = 42; -- the v1 row being replaced

-- 2. Insert the new version
INSERT INTO tech_team_outputs.ph_task
    (project_name, project_code, task_name, team, developer,
     assigned_user, assigned_user_team, html_content, description,
     phase_level, version_level, version_status)
VALUES
    ('Example Project', 'EXPRJ', 'Example Task', 'PPC', 'Vithushali',
     'Jasmini', 'ph_priors', '<html>...</html>', 'Task description',
     1, 2, 'released'); -- version_level bumped from 1 to 2
```

## A note on what `rejected` should NOT be used for

`rejected` now specifically means "superseded by a newer version, don't show this row as active." Please don't reuse it for other meanings (e.g. "the PH holder rejected the task") — there's no such action in the dashboard today. If a different kind of rejection is ever needed, we'll add a distinct status value rather than overload this one.

## Questions

If you're ever unsure whether something counts as "a new version" vs. "a new task," or which `phase_level`/`version_level` to use, please check with the dev team before inserting.
