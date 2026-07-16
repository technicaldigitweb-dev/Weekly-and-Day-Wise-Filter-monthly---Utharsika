# New column: `assigned_user_team` on `tech_team_outputs.ph_task`

**For:** Vithushali
**Table:** `tech_team_outputs.ph_task` (PostgreSQL)
**Date:** 2026-07-08

## What changed

A new column has been added: **`assigned_user_team`** (text, placed after `assigned_user`).

This column decides **which board a task appears on** in the dashboard. The dashboard now has two separate task boards reading from this same table:

- **PH Priors** — the existing board
- **Ebay Priors** — a new board, same layout, separate list of tasks

A task only ever shows up on one board, based on this column.

## What value to put in it

When you insert a task, set `assigned_user_team` to exactly one of:

| Value | Task shows up on |
|---|---|
| `ph_priors` | PH Priors board |
| `ebay_priors` | Ebay Priors board |

Please use these exact values (lowercase, underscore) so they match consistently.

## Important — please set this on every new row

If `assigned_user_team` is left empty, the task **will not appear on either board**. It won't error, it will just be invisible to the user until someone fills in the value. So please make sure every insert going forward sets this field.

## Existing tasks

All tasks that were already in the table before this change have been automatically set to `ph_priors`, so nothing changes for tasks you've already pushed — they'll keep showing up on PH Priors exactly as before.

## Example

```sql
INSERT INTO tech_team_outputs.ph_task
    (project_name, project_code, task_name, team, developer,
     assigned_user, assigned_user_team, html_content, description,
     phase_level, version_level, version_status)
VALUES
    ('Example Project', 'EXPRJ', 'Example Task', 'PPC', 'Vithushali',
     'Jasmini', 'ebay_priors', '<html>...</html>', 'Task description',
     1, 1, 'released');
```

Everything else about pushing a task (columns, HTML content, versioning) works exactly as before — this is the only new field.

## Questions

If anything about this is unclear, or you're not sure which value to use for a particular task, please check with the dev team before inserting.
