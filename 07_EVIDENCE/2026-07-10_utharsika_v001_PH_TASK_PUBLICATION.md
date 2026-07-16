# UAWSO ph_task Publication — 2026-07-10_utharsika_v001

**What this asset is:** The closure evidence record for the first live publication of the UAWSO capability.

**Why it exists:** To make the publish claim independently verifiable — the exact row, the exact HTML that was published, and the exact checks run before and after.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** **PUBLISHED.** Row `id=157` is live in `tech_team_outputs.ph_task`.
**Known limits:** ASIN completeness status = **PENDING_CORRECTION** (see below) — recorded in both this evidence file and the published row's `description` column, not hidden.
**Pass/fail rule:** PASS requires the row to exist, read back with correct values, be the only active row for this date, and for no other row in the table to have been modified.
**Next action:** A future corrected version (v002+) should resolve the 113-ASIN gap per the standard Same-Date Correction Rule if/when the underlying assignment/transaction-history question is resolved.

---

## HTML Source

| Field | Value |
|---|---|
| HTML file path | `09_OUTPUTS\2026-07-10_utharsika_v001.html` |
| HTML SHA-256 | `024f7f28426125833f7091617afc7ef5c89adfb3a3f1cd543645dfd8b6fe7c23` (verified identical immediately before publish via a fresh `sha256sum`, matching the hash recorded in `07_EVIDENCE\2026-07-10_utharsika_v001_HTML_VALIDATION_EVIDENCE.md` — the exact validated file was published, nothing was regenerated or modified) |
| HTML size | 3,420,089 bytes on disk / 3,420,081 characters as loaded and stored in `html_content` (8-byte difference is the file's trailing newline/encoding artifact accounted for by Python's universal-newline text read — content is otherwise identical) |

## Database Access Method

Credential-based (Stage B), consistent with the prior session: `05_IMPLEMENTATION\config\config.py`'s `load_db_config()`, reading `PGHOST`/`PGPORT`/`PGDATABASE`/`PGUSER`/`PGPASSWORD` from the environment only. Values sourced at invocation time from the project's approved `02_SOURCE\db_access_templates\temp_user.py` credential set — never hardcoded into any new script. MCP was **not** used for the insert (used only in earlier sessions for read-only schema/sizing checks).

**Credentials exposed:** NO. No password, connection string, or secret appears in any script, log, or evidence file created for this publish — only `[REDACTED]` in any place a credential-adjacent value might otherwise print.

## Pre-Insert Checks (read-only, before the write)

| Check | Result |
|---|---|
| Existing UAWSO records | **0** (this is the first-ever publish for this project) |
| Same-date (2026-07-10) UAWSO versions | **0** |
| Duplicate version risk | None — confirmed via `find_active_same_date_row()` inside `publish_report()`, and independently re-confirmed with a direct query before the script ran |
| `task_id` uniqueness | Confirmed no row with `task_id = 'UAWSO-2026-07-10-utharsika-v001'` existed prior to insert |
| Required columns | Cross-checked against `08_SKILLS\ph_task_rules\ph_task_schema 5.md` and the live schema constraints confirmed in the design stage (`ph_task_task_id_unique`, NOT NULL on `id`/`project_name`/`project_code`/`task_name`/`task_id`/`phase_level`/`version_level`) — all satisfied by the insert |

## Insert Executed

Reused `05_IMPLEMENTATION\src\ph_task_publisher.py::publish_report()` (already-designed, code-reviewed module from the prior session — not reimplemented) with `is_correction=False`. Sequence: pre-insert duplicate check → transaction begin → `INSERT ... RETURNING id` → read-back verification → active-row-count check → `COMMIT`.

### Inserted / Mapped Values

The prompt's conceptual field names were mapped to the real `tech_team_outputs.ph_task` columns per `ph_task_schema 5.md` — no new column was invented. Fields with no direct column (`frequency`, `timezone`, `data_cutoff_date`, `html_path`) were folded into `description`, per the "do not invent new columns" instruction.

| Requested field | Real column | Value |
|---|---|---|
| project_code | `project_code` | `UAWSO` |
| report_name | `project_name` | `Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report` |
| — | `task_name` | `2026-07-10_utharsika_v001` |
| — | `task_id` | `UAWSO-2026-07-10-utharsika-v001` |
| Business Team | `team` | `PH Team` |
| Developer | `developer` | `Satheskanth` |
| assigned_user | `assigned_user` | `utharsika` |
| assigned_user_team | `assigned_user_team` | `ph_priors` |
| html_file / html_path | `html_content` (full HTML) + path referenced in `description` | Full 3,420,081-character HTML content stored; path noted in description |
| frequency, timezone, data_cutoff_date, known limitation | `description` | See full text below |
| version | `phase_level`=1, `version_level` | `phase_level=1`, `version_level=1` |
| — | `version_status` | `released` |
| — | `action_took_by` | `NULL` |
| — | `action_took_date_time` | `NULL` |

### Description Text (verbatim, as stored)

> Automated Daily/Weekly/MTD Sales & Orders interactive dashboard for Utharsika's assigned Amazon UK SKUs vs prior-year performance and 130% achievement targets. Frequency: daily. Timezone: Asia/Colombo. Data cutoff (latest completed date): 2026-07-09. Source file: 09_OUTPUTS\2026-07-10_utharsika_v001.html. KNOWN LIMITATION - ASIN completeness status: PENDING_CORRECTION. Source assignment count: 1723 assigned ASINs. The product master embedded in this HTML represents only assigned ASINs with at least one historical Amazon UK Completed transaction (1610 ASINs represented); 113 assigned ASINs with no transaction history under these filters are not yet represented. Pending verification and correction in a later version.

## Known Limitation (recorded, not hidden)

```
Source assignment count:      1723 assigned ASINs
Current HTML product master:  1610 represented ASINs
Difference:                   113 ASINs
ASIN completeness status:     PENDING_CORRECTION
```

**Full completeness is explicitly NOT claimed anywhere in this evidence or in the published row.** Correction is deferred to a future version, per the approved same-date/versioning process.

## Post-Insert Validation (independent read-only SELECT, run after commit)

| Check | Result |
|---|---|
| Row exists | PASS — `id=157` |
| `project_code` = `UAWSO` | PASS |
| `assigned_user` = `utharsika` | PASS |
| `assigned_user_team` = `ph_priors` | PASS |
| `task_id` = `UAWSO-2026-07-10-utharsika-v001` | PASS |
| `task_name` = `2026-07-10_utharsika_v001` | PASS |
| `version_level` = `1`, `version_status` = `released` | PASS |
| `action_took_by` / `action_took_date_time` | Both `NULL`, as required for an unactioned task |
| `html_content` length | 3,420,081 — matches the file exactly |
| Exactly one active UAWSO row for 2026-07-10 | PASS — count = 1 |
| Total UAWSO rows in table | 1 (this is the only UAWSO row that exists — no accidental duplicate insert) |
| Other users' rows touched | **NO** — by construction: `is_correction=False` means `reject_row()` (the only UPDATE path in `publish_report()`) was never called; the function issued exactly one `INSERT` and three `SELECT`s. Total `ph_task` table row count (140, all projects) is consistent with one net new row added. |

## Insert Timestamp

`2026-07-10 15:12:15 (Asia/Colombo)` — read from the row's own `created_at AT TIME ZONE 'Asia/Colombo'`.

## Version State

`05_IMPLEMENTATION\state\version_state.json` updated to `{"last_published_report_date": "2026-07-10", "last_published_version": 1}` — the next distinct report date will receive `v001`; a correction to `2026-07-10` (if ever needed) will receive `v002` per the Same-Date Correction Rule, never reusing `task_id=...v001`.

## Final Verdict

**PASS.**
