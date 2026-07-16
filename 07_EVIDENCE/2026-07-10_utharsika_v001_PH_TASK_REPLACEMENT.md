# UAWSO ph_task HTML Replacement — 2026-07-10_utharsika_v001

**What this asset is:** Closure evidence for the controlled UPDATE that replaced the stored HTML for the existing UAWSO v001 `ph_task` row with the corrected local HTML (ASIN+SKU grain fix).

**Why it exists:** To make the replacement independently verifiable — the exact row, the exact before/after content hashes, and the exact checks run.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** **REPLACED.** Row `id=157` now stores the corrected HTML.
**Explicit user approval:** The user explicitly instructed this session to replace the existing `ph_task` HTML with the updated local v001 file — this was an authorized UPDATE of the existing row, not a new publication.
**Known limits:** The June £940.12 reference-value discrepancy (see below) remains unresolved and is recorded here again for continuity — it was not changed or hardcoded, consistent with the prior instruction not to force that figure.
**Pass/fail rule:** PASS requires exactly one row updated, hash match after update, all identity fields unchanged, no duplicate row, and no other user's row touched.
**Next action:** None required from this update. The June reference-value question (see below) remains open for business clarification.

---

## Database Table

`tech_team_outputs.ph_task`

## Access Method

Credential-based (Stage B), consistent with every prior write to this table this project: `config.load_db_config()`, env-var-only credentials (`temp_user`, sourced from the approved `02_SOURCE\db_access_templates\temp_user.py` template at invocation time, never hardcoded in any new script). **Credentials exposed: NO** — verified no password/connection-string value appears in any script, log, or this evidence file.

## Target Row Identity

| Field | Value |
|---|---|
| Primary key (`id`) | **157** |
| `task_id` | `UAWSO-2026-07-10-utharsika-v001` |
| `task_name` | `2026-07-10_utharsika_v001` |
| `project_code` | `UAWSO` |
| `assigned_user` | `utharsika` |

Located via `find_unique_target_row()` filtering on `task_id AND assigned_user AND project_code` together — exactly **1** matching row found before any write, confirming no ambiguity.

## Before-State (captured before UPDATE)

| Field | Value |
|---|---|
| Previous stored HTML SHA-256 | `024f7f28426125833f7091617afc7ef5c89adfb3a3f1cd543645dfd8b6fe7c23` |
| Previous stored HTML length | 3,420,081 characters |
| Local backup path | `07_EVIDENCE\ph_task_backups\2026-07-10_utharsika_v001_before_replace.html` |
| Backup file SHA-256 | `024f7f28426125833f7091617afc7ef5c89adfb3a3f1cd543645dfd8b6fe7c23` (identical to the stored value — confirms the backup is byte-exact) |
| Cross-check | This SHA-256 is identical to the value recorded in the original `07_EVIDENCE\2026-07-10_utharsika_v001_PH_TASK_PUBLICATION.md` from the first publish — confirms zero drift in the stored row between the initial insert and this update |

The backup was fetched directly from the live `html_content` column (read-only `SELECT`), not reconstructed from a local file, so it is a provably faithful record of what was actually stored before replacement.

## Columns Updated

**Exactly two:** `html_content`, `updated_at` (`= now()`).

**Not touched:** `task_id`, `task_name`, `project_code`, `project_name`, `assigned_user`, `assigned_user_team`, `team`, `developer`, `phase_level`, `version_level`, `version_status`, `action_took_by`, `action_took_date_time`, `created_at` — all confirmed identical before and after (see Post-Update Verification).

No filename/path/hash/size columns exist on `tech_team_outputs.ph_task` (confirmed via live schema inspection this session) — the schema stores the full HTML directly in `html_content`; there is nothing else that "points to" the file, so no such reference needed updating.

## UPDATE Execution

Reused `src/ph_task_html_replacer.py::replace_html_content()` — a new, purpose-built guarded module (pre-check unique row → `UPDATE ... WHERE id AND task_id AND assigned_user` → check `rowcount == 1` → commit, else rollback). Local file hash was verified to match the expected value (`58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3`) before the connection was even opened.

| Field | Value |
|---|---|
| Rows affected | **1** |
| Transaction result | **COMMIT** |

## Post-Update Verification (independent read-back, read-only session)

| Check | Result |
|---|---|
| Row identity (`id=157`, `task_id`) unchanged | PASS |
| `assigned_user` | `utharsika` (unchanged) |
| `assigned_user_team` | `ph_priors` (unchanged) |
| `task_name` (carries the report date/version identity) | `2026-07-10_utharsika_v001` (unchanged) |
| `version_level` / `version_status` | `1` / `released` (unchanged) |
| `phase_level`, `team`, `developer` | Unchanged |
| `action_took_by` / `action_took_date_time` | Both still `NULL` (correctly undisturbed) |
| `created_at` | Unchanged (`2026-07-10 15:12:15 Asia/Colombo`) |
| `updated_at` | Changed to `2026-07-10 17:14:27 Asia/Colombo` — confirms the write actually occurred |
| Stored HTML not truncated | PASS — 4,307,144 stored characters (Python-string-length; the ~12-character difference from the 4,307,156-byte local file size is normal UTF-8 multi-byte character accounting, not truncation) |
| Stored HTML SHA-256 after update | `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` |
| Matches expected/local SHA-256 | **YES — exact match** |
| No second UAWSO v001 row created | PASS — exactly 1 row with `task_id='UAWSO-2026-07-10-utharsika-v001'`; exactly 1 row total with `project_code='UAWSO'` |
| No other user's row modified | PASS — this session's only database write was the single `UPDATE ... WHERE id=157 AND task_id=... AND assigned_user='utharsika'`, which by construction cannot match any other user's row. (Note: the table's total row count moved from 140 to 142 between sessions due to other teams' independent, concurrent publications to this shared table — confirmed unrelated to this update, since the UAWSO-scoped count remained exactly 1 throughout.) |

## June Reference-Value Limitation (recorded again for continuity)

The HTML now stored in `ph_task` shows the source-backed June 2025 previous-year Sales value of **£41,146.84**. A separately user-provided reference value of **£42,086.96** (difference: **£940.12**) could not be reproduced or explained from `order_transaction`/`vendor_sales` source data across eight tested variants (full reconciliation table in `07_EVIDENCE\2026-07-10_utharsika_v001_ASIN_SKU_GRAIN_AND_JUNE_RECONCILIATION.md`). **The value was not changed or hardcoded** — the stored HTML reflects the actual source-backed figure. This remains an open item requiring business clarification on how the £42,086.96 reference was derived.

## Timestamp

Replacement committed at **2026-07-10 17:14:27 (Asia/Colombo)**.

## Final Verdict

**PASS** — exactly one row updated, hash-verified before and after, all identity fields preserved, no duplicate created, no other user's data touched, credentials never exposed. (The separate, pre-existing June reference-value question remains open but does not affect the validity of this replacement operation itself — the HTML replaced is the one already reviewed and explicitly approved for publication, June limitation included.)
