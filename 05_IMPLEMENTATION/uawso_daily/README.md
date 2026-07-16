# uawso_daily — UAWSO Unattended Daily Automation System

Complete, reusable, production-grade automation for the Utharsika Amazon UK
Daily, Weekly and Month-to-Date Sales and Orders Report (UAWSO): fresh
PostgreSQL extraction → validation → HTML generation → `ph_task`
publication, driven by one stable command:

```
python -m uawso_daily update-for-today
```

This package is **prepared and locally tested only**. No cron/systemd job
is installed or enabled by this build — see "Deployment (not installed)"
below. This is a deliberate, separate step left for explicit human
approval.

## Relationship to the earlier `05_IMPLEMENTATION/automation/` scripts

`automation/uawso_daily_runner.py` and `automation/run_uawso_daily.ps1` are
an earlier, separate automation build from a prior task in this project's
history. They are **not modified, removed, or superseded** by this package
— both exist side by side. This package (`uawso_daily/`) is the one built
to the current task's 31-section specification (filesystem-based
versioning, structured run-state JSON, the 5 idempotency cases, the 14
failure codes, etc.) and is the one described in this README.

## Architecture

Every module that touches business logic already proven elsewhere
**imports and calls the existing, approved script directly** — no
extraction/rendering/publication SQL or logic is duplicated:

| Module | Responsibility | Reuses |
|---|---|---|
| `config.py` | Non-secret operational settings (timezone, dates, retry counts, toggles) | — |
| `dates.py` | Asia/Colombo time, report-window math, output-identity naming | — (fixed-offset fallback, see below) |
| `locking.py` | Single-run file lock (PID + timestamp, stale-lock reclaim) | — |
| `versioning.py` | Filesystem-based next-version inspection for a run_date | — |
| `extraction.py` | DB connect, source-freshness probe, extraction | `src/extract_uawso_v5_asin_level.py::extract()` |
| `transformation.py` | Pure-Python KPI totals (mirrors the client engine's arithmetic) | — |
| `rendering.py` | Staged-then-atomic HTML render/promote | `src/dashboard_renderer.py::render_dashboard_v5()` |
| `validation.py` | Full validation gate (independent SQL re-derivation + structural checks) | — |
| `publication.py` | `ph_task` publish wrapper, post-commit hash verification | `src/ph_task_publisher.py`, `src/version_resolver.py` |
| `evidence.py` | Run-state JSON + evidence markdown writers | — |
| `result.py` | `RunResult` dataclass, `Code` failure-code constants | — |
| `cli.py` / `__main__.py` | Orchestration, argument parsing, exit codes | all of the above |

Credentials are **never** read or stored inside this package. All DB access
goes through `config.config.load_db_config()` — the same `.env`/`temp_user`
mechanism every prior UAWSO publication in this project has used.

## Business rules this build assumes (confirmed against the live code as of 2026-07-16)

- Orders = AMAZON-source only (REPLACEMENT excluded) — `extract_uawso_v5_asin_level.py`'s `source_name = 'AMAZON'` filter.
- Vendor Orders = `vendor_sales.ordered_units` directly (one Vendor Unit = one Vendor Order, no proration, whole-period-overlap inclusion).
- Total Orders = FBM Orders + FBA Orders + Vendor Orders.
- Sales-and-Orders-only report — no Quantity fields anywhere in the v5 UI/data (the shared `uawso_client_engine.js` file still contains the *frozen* v1–v4 Quantity-era functions for the historical 2026-07-09/10/14 reports — this is expected and is excluded from the Quantity-absence check, see `validation.py::validate_quantity_absent`).
- `report_start_date` is fixed at `2025-01-01`; `report_end_date` defaults to **yesterday, Asia/Colombo** (the run date itself is always excluded as a partial/incomplete day).

## CLI usage

```
python -m uawso_daily update-for-today [--dry-run] [--no-publish] [--report-end-date YYYY-MM-DD] [--force-rerun] [--verbose]
```

- `--dry-run` — extract, render, and validate only. Writes nothing to `09_OUTPUTS` or `ph_task` (not even a version is consumed). Final status `DRY_RUN_COMPLETE`.
- `--no-publish` — full run including promotion to `09_OUTPUTS`, skips `ph_task` publication. Final status `NO_PUBLISH_COMPLETE`. (If the day is already complete, this still short-circuits to `ALREADY_COMPLETE` with zero writes — see below.)
- `--report-end-date` — **manual testing override only**. The scheduled/production command must never pass this; it exists so an operator can regenerate a specific historical window without waiting for "yesterday" to change.
- `--force-rerun` — bypasses the `ALREADY_COMPLETE` short-circuit so a new corrected version is produced even though today's report already matches `ph_task`.
- `--verbose` — prints a numbered step-by-step progress trace to stdout.

Exit code: `0` for any success-family outcome (`SUCCESS`, `ALREADY_COMPLETE`,
`DRY_RUN_COMPLETE`, `NO_PUBLISH_COMPLETE`); `1` for any failure code.

### Wrapper scripts

`commands/update_for_today.bat` (Windows) and `commands/update_for_today.sh`
(Linux/cron) both just set the working directory to `05_IMPLEMENTATION` and
exec `python -m uawso_daily update-for-today "$@"` — no business logic of
their own.

## Idempotency (five cases)

Version selection is **filesystem-based** (inspects `09_OUTPUTS`, not only
`05_IMPLEMENTATION/state/version_state.json`, which has not reliably
reflected every version actually published across this project's history).
On each run:

1. Count active (non-rejected) `ph_task` rows for `run_date`. **More than
   one → `DUPLICATE_ACTIVE_OUTPUT`, stop, zero writes** (case E).
2. If exactly one active row exists, and the local output file for that
   row's version exists and its SHA-256 matches the row's stored
   `html_content` SHA-256, and neither `--dry-run` nor `--force-rerun` was
   passed → **`ALREADY_COMPLETE`, stop, zero writes** (case B).
3. Otherwise, the run proceeds and picks `version = next_version_for_date(run_date)`
   (max existing local version + 1, or 1 if none exist):
   - No active row yet, no local files yet → fresh day, `version=1`, `INSERT` (case A).
   - No active row yet, but an earlier local version file exists (a prior
     attempt failed before it ever published) → next version, `INSERT`
     only for the newly-passing version (case C).
   - An active row already exists (case B's match failed, or
     `--force-rerun` was passed) → next version, publish is a **same-day
     correction** (`is_correction=True`, which internally rejects the
     superseded row for `run_date` only — never any other date's row).

This is this build's concrete interpretation of the task's five described
idempotency cases; it is disclosed here rather than left implicit because
the exact case-boundary wording was not available verbatim during this
build (see the evidence file's "Scope and interpretation notes" section).

## Validation gate (`validation.py`)

Runs after rendering and before promotion/publication. All checks must pass
or the run stops with `VALIDATION_FAILED` and nothing is written to
`09_OUTPUTS` or `ph_task`:

- `duplicate_asins_zero` — no ASIN appears twice in the product master.
- `duplicate_date_asin_rows_zero` — no `(date, ASIN)` daily-aggregate row is duplicated.
- `quantity_fields_absent` — no Quantity marker in the page outside the shared frozen engine JS blob.
- `ui_elements_present` — table wrap, Column Definitions panel, pagination markers all present.
- `assigned_scope_missing_extra_zero` — an INDEPENDENT re-derivation of the assigned-ASIN scope (separate SQL, not a re-read of the extraction script's own list) has zero missing/extra vs. the extracted list.
- `source_vs_computed_totals_diff_zero` — an INDEPENDENT re-derivation of FBM/FBA/Vendor Sales+Orders (separate SQL) diffs to zero against the computed KPI totals.
- `b0fx2xdlt5_regression_control` — for ASIN `B0FX2XDLT5`, June 2026, when that ASIN is in scope and June 2026 is fully inside the report window: AMAZON-only Orders must equal **16** (the confirmed root-caused figure — see `07_EVIDENCE/2026-07-16_B0FX2XDLT5_june_cancelled_order_diagnosis.md`). Skipped (not silently passed) when the precondition doesn't hold, with the reason recorded.
- `replacement_source_structurally_excluded` — confirms REPLACEMENT-source rows exist in the live window (so the AMAZON-only filter has something real to exclude) and are excluded by a live filter, not by their simple absence.

## Failure codes (`result.Code`)

`SUCCESS`, `ALREADY_COMPLETE`, `SOURCE_NOT_READY`, `RUN_ALREADY_IN_PROGRESS`,
`CONFIGURATION_ERROR`, `DATABASE_CONNECTION_FAILED`, `EXTRACTION_FAILED`,
`VALIDATION_FAILED`, `OUTPUT_VERSION_ALREADY_EXISTS`,
`DUPLICATE_ACTIVE_OUTPUT`, `LOCAL_HTML_VALIDATION_FAILED`,
`PUBLICATION_FAILED`, `POST_PUBLICATION_HASH_MISMATCH`,
`CRITICAL_POST_COMMIT_MISMATCH`, plus the two non-error completion codes
`DRY_RUN_COMPLETE` / `NO_PUBLISH_COMPLETE`.

`CRITICAL_POST_COMMIT_MISMATCH` is raised when a fresh, independent SELECT
of the just-committed `ph_task` row's `html_content` does not SHA-256-match
the local file — this is checked and reported even after a successful
commit; a mismatch here is never silently ignored.

## Run lock

`runtime/uawso_daily/locks/update_for_today.lock` — a PID+timestamp JSON
file created with an exclusive (`O_CREAT|O_EXCL`) open. A second concurrent
run fails immediately with `RUN_ALREADY_IN_PROGRESS`. A lock is only
auto-reclaimed as stale when **both** its recorded PID is confirmed not
running on this machine **and** it is older than 6 hours — never on either
condition alone (see `locking.py` module docstring for the rationale).

## Structured run-state and evidence

Every run (success, expected stop, or exception) writes:

- `runtime/uawso_daily/state/<run_id>.json` — the full `RunResult` as JSON. Contains **no credential or connection-string field** — this is structural (the dataclass has no such field), not a redaction filter applied at write time.
- `07_EVIDENCE/<run_date>_uawso_daily_<run_id>.md` — human-readable run evidence, including every validation-gate check result.

`run_id` format: `uawso_YYYYMMDD_HHMMSS` (Asia/Colombo).

## Output naming

`09_OUTPUTS/<run_date>_utharsika_v<NNN>.html` — uses the **run date**, not
`report_end_date`. Never overwritten: promotion uses `os.rename()`, which
fails outright if the target already exists (`OUTPUT_VERSION_ALREADY_EXISTS`),
on top of an explicit pre-check.

## Retry policy

Retries apply **only** to transient DB connection failures during
extraction/publication (`UAWSO_DB_RETRY_COUNT`, default 3, with an
increasing base delay `UAWSO_DB_RETRY_BASE_DELAY_SECONDS`, default 2s). A
`VALIDATION_FAILED` or `EXTRACTION_FAILED` (business-logic) result is never
auto-retried within a single invocation — that risks silently republishing
bad data. A human/scheduler re-running the command later is the retry
mechanism for those.

## Configuration

All non-secret settings are environment-variable driven — see
`config/uawso_daily.example.env` for the full list and defaults. Real
database credentials live exclusively in `config/.env`
(`PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD`, git-ignored, NTFS-restricted)
via the existing `config.config.load_db_config()` mechanism — this package
never reads or stores a credential value itself.

## Deployment (not installed)

`deployment/uawso_daily.cron.example`,
`deployment/uawso-daily.service.example`, and
`deployment/uawso-daily.timer.example` document a 12:00 PM Asia/Colombo
daily schedule. **None of these are installed or enabled by this task** —
copying them into an active crontab or `systemctl enable`-ing them is a
separate, explicit deployment step for a human to take later, on a real
target host.

## Testing

`tests/test_uawso_daily_automation_package.py` — 42 checks, no DB access,
no writes to any real project folder (uses `tempfile.mkdtemp()` for
locking/versioning fixtures). Run: `python tests/test_uawso_daily_automation_package.py`.

Two controlled acceptance runs were performed against the **live** database
(see `07_EVIDENCE/2026-07-16_uawso_daily_automation_system_validation.md`
for full output):

1. `--dry-run --verbose` — ran a full live extraction (1,723 ASINs, 29,240
   daily rows) and validation (8/8 checks passed), producing totals that
   exactly match the already-published `2026-07-16_utharsika_v001.html` /
   `ph_task` row 262 (Total Sales £719,453.86, Total Orders 38,994).
   Nothing was written outside the run-scoped staging directory.
2. `--no-publish --verbose` — correctly detected `ALREADY_COMPLETE` against
   the live, already-published v001/row 262 and stopped with **zero**
   writes (no new extraction, no new file, no new `ph_task` row) — proving
   the idempotency detection logic end-to-end without a new live publish,
   per the task's explicit instruction not to perform a new live
   publication without further approval.

No live publish of a *new* row was performed by this build, per that same
instruction.
