# UAWSO Daily Automation — Pause Handover / Restart Checkpoint

**Date:** 2026-07-15
**Developer:** Satheskanth
**Status: PAUSED_PENDING_USER_REQUIREMENT_UPDATE**

Companion document: `07_EVIDENCE\automation\2026-07-15_uawso_automation_paused_for_user_updates.md`
(full status detail — this file is the shorter restart checkpoint).

---

## Do not resume automation implementation until the updated user requirement has been written, reviewed, and approved.

---

## Last safely completed step

A `--dry-run` execution of `uawso_daily_runner.py` against live production data completed
successfully (`DRY_RUN_PASS`), followed by a full read-only re-verification that all four
protected `09_OUTPUTS\*.html` baseline hashes were unchanged. Task #106 (Task Scheduler
investigation) and the first half of #107 (guard + move superseded scripts) were also completed.
The archiving pass was interrupted mid-verification (about to re-check `--help` output after the
file moves) when the user issued the stop instruction.

## Exact active implementation files

- Orchestrator: `05_IMPLEMENTATION\automation\uawso_daily_runner.py`
- Wrapper: `05_IMPLEMENTATION\automation\run_uawso_daily.ps1`
- Unit tests: `05_IMPLEMENTATION\tests\test_uawso_daily_runner.py` (23/23 passing as of last run)
- Extraction (unchanged, reused as-is): `05_IMPLEMENTATION\src\extract_uawso_v4_ordered_sales.py`
- Renderer (unchanged, reused as-is): `05_IMPLEMENTATION\src\dashboard_renderer.py` (`render_dashboard_v4`)
- Template: `05_IMPLEMENTATION\templates\uawso_report_template.html` (canonical, holds v4 content)

## Exact proposed scheduler name

`UAWSO Daily 11-30 - Satheskanth`

## Exact proposed schedule

Daily, 11:30 AM local time (Sri Lanka Standard Time / Asia/Colombo, UTC+05:30, no DST).
Prepared (not registered) definition: `07_EVIDENCE\automation\scheduler\UAWSO_Daily_11-30_Satheskanth.xml`,
`<Enabled>false</Enabled>` by design.

## Current credential blocker

Two independent, unresolved blockers, not one:
1. **OS-level:** registering an unattended ("run whether logged on or not") Scheduled Task
   requires local Administrator elevation, which the build session did not have. Confirmed by two
   failed real attempts (SYSTEM principal via `schtasks`, S4U logon via `Register-ScheduledTask`).
2. **DB-level:** the runner needs `PGHOST`/`PGPORT`/`PGDATABASE`/`PGUSER`/`PGPASSWORD` available
   unattended. The wrapper's mechanism (`05_IMPLEMENTATION\config\.env.local`, NTFS-restricted) is
   built and tested (correctly reports `BLOCKED_CREDENTIAL_SETUP` when absent), but the user
   explicitly declined to have the password persisted to disk. **This decision should be
   re-confirmed, not assumed, when work resumes** — the updated requirement may specify a
   different credential mechanism (e.g. Windows Credential Manager, a secrets vault) that wasn't
   evaluated yet.

## Historical Output Protection rule (permanent, carries forward regardless of requirement changes)

Never overwrite/modify any existing `09_OUTPUTS\*.html` file or any existing `ph_task` row. Every
successful run creates exactly one new dated/versioned HTML file and exactly one new `ph_task` row.
Implemented in `uawso_daily_runner.py`'s inventory-before/inventory-after gate. This rule is not
up for renegotiation by the pending requirement update unless the user says otherwise explicitly.

## Current template path

`05_IMPLEMENTATION\templates\uawso_report_template.html` (holds v4 content as of the 2026-07-15
migration; legacy v3 preserved at
`12_ARCHIVE\automation_cleanup\2026-07-15\templates\uawso_report_template_v3_legacy.html`)

## Current runner path

`05_IMPLEMENTATION\automation\uawso_daily_runner.py` (entry: `python uawso_daily_runner.py
--dry-run` or `--publish`)

## Tests completed

- 23/23 unit tests passing (`test_uawso_daily_runner.py`): dynamic status rule, version
  resolution, filename/task-id construction, `ALREADY_COMPLETED` detection, Vendor
  period-overlap arithmetic, duplicate-prevention gates.
- One live `--dry-run` against production data: `DRY_RUN_PASS`, all 11 validation gates passed,
  1,723 assigned ASINs, 29,418 daily aggregate rows, 961 vendor period rows, resolved next
  version correctly as `v003`, zero protected-file drift confirmed before and after.

## Tests not completed

- No live `--publish` run has ever been executed (would create a real new HTML file + `ph_task`
  row — deliberately not done without further explicit confirmation).
- No true unattended execution test (SYSTEM/Task-Scheduler context, no interactive session) —
  blocked on the elevation issue above.
- `archive_manifest.md` verification / write not done.

## User decisions already approved (during this build, before the pause)

- 11:30 AM daily, Asia/Colombo timezone — from the original task spec.
- Scheduled Task name `UAWSO Daily 11-30 - Satheskanth` — from the original task spec.
- Mandatory Historical Output Protection policy (verbatim, issued 2026-07-15 after the v001
  incident) — permanent, see above.
- **Declined:** persisting the DB password to `.env.local` (asked via `AskUserQuestion` on
  2026-07-15; user chose "No, leave it blocked").

## Decisions that must be reconfirmed after the new update

- Whether the 11:30 AM / daily / Asia/Colombo schedule still holds.
- Whether `--publish` (real production writes) should still be fully automated daily, or scoped
  differently under the new requirement.
- Whether the credential-persistence decision (declined above) should be revisited under the new
  requirement's own guidance.
- Whether any already-built KPI/status/extraction logic changes under the new requirement (re-diff
  against `05_IMPLEMENTATION\src\extract_uawso_v4_ordered_sales.py`'s dynamic status rule and the
  KPI definitions before assuming they still apply).

## One safe next step

When the user provides the updated requirement: read it in full, diff it explicitly against the
original 19-section spec, and confirm with the user in writing which already-built components
(orchestrator, wrapper, tests, scheduler XML, archived-script list) remain valid — before writing,
running, or modifying any code.
