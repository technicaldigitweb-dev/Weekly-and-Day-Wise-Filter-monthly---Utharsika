# UAWSO v002 — ph_task Publication Record

**What this asset is:** Concise record of the ph_task publish action performed for v002, per explicit Phase 12 authorization in the resume task.

**Owner:** Satheskanth
**Status:** PUBLISHED — PASS

## Pre-publication validation

All 19 mandatory quality gates passed (full detail in `07_EVIDENCE\2026-07-10_utharsika_v002_ORDERED_SALES_ORDERS_QUANTITY_VALIDATION.md`), including the exact ASIN B0FX2QT3B1 June 2026 match (£726.65 / 22 Orders) and v001 byte-for-byte non-modification (SHA-256 unchanged).

## Existing row identification (read-only, before any write)

Query: `SELECT ... FROM tech_team_outputs.ph_task WHERE project_code='UAWSO' AND lower(assigned_user)=lower('utharsika')`

Exactly **one** row found:

| Field | Value (before update) |
|---|---|
| id | 157 |
| project_code | UAWSO |
| task_name | 2026-07-10_utharsika_v001 |
| task_id | UAWSO-2026-07-10-utharsika-v001 |
| assigned_user | utharsika |
| version_level | 1 |
| version_status | released |
| html_content length | 4,307,144 characters |

No duplicate row existed. No insert was performed.

## Update performed

Fields changed: **`html_content`, `updated_at`, `version_level`** only.
Fields explicitly left unchanged: `id`, `project_code`, `project_name`, `task_name`, `task_id`, `team`, `developer`, `assigned_user`, `assigned_user_team`, `phase_level`, `version_status`, `action_took_by`, `action_took_date_time`, `created_at`.

`task_name`/`task_id` were deliberately **not** changed to `...v002` — per instruction "Do not alter: task ownership; task ID; unrelated metadata" — this is the same row being updated in place, not a new task identity. `version_level` (1 → 2) was updated as the one workflow-native version field already present in the schema.

WHERE clause on the UPDATE was scoped to `id=157 AND project_code='UAWSO' AND lower(assigned_user)=lower('utharsika') AND task_id='UAWSO-2026-07-10-utharsika-v001'` — the exact row confirmed above, nothing broader. `UPDATE` affected exactly 1 row (checked programmatically; the transaction would have rolled back automatically if any other count had resulted).

## Post-publication verification (re-read after commit)

| Field | Value (after update) |
|---|---|
| id | 157 (unchanged) |
| task_name | 2026-07-10_utharsika_v001 (unchanged) |
| task_id | UAWSO-2026-07-10-utharsika-v001 (unchanged) |
| version_level | **2** |
| version_status | released (unchanged) |
| updated_at | 2026-07-14 13:41:17.983711+05:30 |

**Stored HTML SHA-256:** `cb8e15fb9813ff01a0dc3f1a2597f67644879f0cfe45663d6d2fe70c4cae95e4`
**Local v002 file SHA-256:** `cb8e15fb9813ff01a0dc3f1a2597f67644879f0cfe45663d6d2fe70c4cae95e4`
**Match: YES — confirmed identical.**

The full historical payload (2025-01-01 → 2026-07-09, all 1,723 assigned ASINs, 2,549 rows) is present in the published content — not June-only data (confirmed by the file size, 5,400,234 bytes, consistent with the full-scope local file already validated).

## Scope confirmation

- No other user's row was read, matched, or touched (query scoped to `project_code='UAWSO' AND assigned_user='utharsika'` throughout).
- No duplicate active task row was created.
- The scheduler was not touched.
- `v001.html`'s on-disk file and its own separate historical publication record were not altered by this action.

## Final verdict: **PASS — v002 published to the existing ph_task row (id=157) successfully, verified by hash match.**
