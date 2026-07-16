# UAWSO Runtime & System Guide

**What this asset is:** The operational reference for running, debugging, and extending the UAWSO system.

**Why it exists:** So a new developer (or future Satheskanth) can run and reason about the system without re-reading every design document.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Two systems now exist side by side (see §Two Report Architectures below), both built this project. Current as of the 2026-07-10 interactive-dashboard session.
**Known limits:** `main.py` (the scheduled Daily/Weekly/MTD `ph_task`-publishing path) has not been run end-to-end via psycopg2 in this environment. The dashboard extraction path (`extract_uawso_daily_aggregates.py`) HAS been run end-to-end via real psycopg2 this session and works.
**Next action:** User reviews `09_OUTPUTS\2026-07-10_utharsika_v001.html`, then approves the first live `ph_task` publish.

---

## Two Report Architectures (read this first)

This project now contains two related but distinct deliverables, built in two sessions:

1. **Scheduled batch report** (`main.py`, `src/report_query.py`, `src/html_renderer.py`, `templates/report_template.html`) — the original design: a fixed Daily/Weekly/MTD three-section HTML, generated server-side once per day and published to `ph_task`.
2. **Interactive self-contained dashboard** (`src/extract_uawso_daily_aggregates.py`, `src/uawso_client_engine.js`, `src/dashboard_renderer.py`, `templates/uawso_report_template.html`) — the current requirement: one HTML file embedding the full `2025-01-01`→`2026-07-09` daily-grain history, with client-side filtering (any date/month/week/range/ASIN/SKU), still intended to be published as the daily `ph_task` row once approved.

Both share the same underlying business rules (Sales/Orders/Change/Trend/Achieve% formulas) and the same `config/config.py` project constants — they are not contradictory designs, the dashboard is the evolved deliverable. `main.py` has not yet been updated to call the dashboard path instead of the old static-report path; that wiring is a follow-up.

## Dashboard Data Flow (the current deliverable)

```
extract_uawso_daily_aggregates.py  (real psycopg2, read-only, Stage B credential path)
  -> 07_EVIDENCE/generated_data/<identity>_{assigned_asins,product_master,daily_aggregates}.json
       -> dashboard_renderer.render_dashboard()  (safe placeholder substitution)
            -> templates/uawso_report_template.html + src/uawso_client_engine.js (inlined)
                 -> 09_OUTPUTS/staging/<identity>.staging.html
                      -> (validation passes) -> 09_OUTPUTS/<identity>.html  (final, self-contained)
```

Test the engine directly: `node tests/test_uawso_client_engine.js` (42 checks, real data, no browser needed).
Regenerate the dashboard: `python tests/generate_final_dashboard.py` (after re-running the extraction script for a new date).

## System Purpose

Produces a daily Amazon UK Sales & Orders report (Daily/Weekly/MTD, vs. prior year, 130% achievement) for PH user `utharsika`, and publishes it as a dated row in `tech_team_outputs.ph_task` on the `ph_priors` board.

## Architecture

```
main.py (orchestrator)
  ├─ config/config.py          constants + env-var DB config loader
  ├─ src/db.py                 psycopg2 connection manager (read-only by default)
  ├─ src/sku_resolver.py       Utharsika assigned-ASIN resolution
  ├─ src/period_calculator.py  Daily/Weekly/MTD boundaries, Asia/Colombo
  ├─ src/report_query.py       raw Sales/Orders per ASIN+SKU
  ├─ src/calculations.py       Change/Trend/Achieve% derivation
  ├─ src/html_renderer.py      original HTML report (templates/report_template.html)
  ├─ src/validator.py          validation-gate checks
  ├─ src/version_resolver.py   vNNN tracking (state/version_state.json)
  ├─ src/ph_task_publisher.py  guarded INSERT/UPDATE into ph_task
  ├─ src/evidence_writer.py    structured evidence Markdown
  └─ src/logger.py             execution-log entries
scheduler/
  ├─ run_daily_uawso.ps1       Task Scheduler wrapper
  └─ UAWSO_SCHEDULER_DESIGN.md registration command (not yet run)
```

## Module Paths

All paths relative to `05_IMPLEMENTATION\`. See the table above.

## Environment Variables

| Variable | Purpose |
|---|---|
| `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` | Database connection — required, no defaults, no fallback. See `config/.env.example`. |

## Execution Command

```
python main.py --publish --i-understand-this-writes-to-production
```

(Currently raises `NotImplementedError` by design — see Phase 8 gate status in `10_HANDOVER\UAWSO_HANDOVER.md`. Remove that guard only after the user has explicitly cleared the first-live-write gate.)

## Dry-Run Command

```
python main.py --dry-run
python main.py --dry-run --promote   # also writes the staged HTML to 09_OUTPUTS if validation passes
```

## Publication Command

```
python main.py --publish --i-understand-this-writes-to-production
```

## Scheduler

Windows Task Scheduler, daily at `03:00 Asia/Colombo`, running `scheduler/run_daily_uawso.ps1`. Not yet registered — see `scheduler/UAWSO_SCHEDULER_DESIGN.md` for the exact `schtasks` command.

## Date Logic

`execution_date` = today in Asia/Colombo. `report_date` = `execution_date - 1 day`. Daily/Weekly (Monday-start)/MTD boundaries and their previous-year equivalents computed in `src/period_calculator.py` — see that module's docstring and `tests/test_period_calculator.py` for the leap-year and Monday-edge handling.

## SKU Assignment Logic

`public.user` (resolve `utharsika` → `user=109`) → `public.ph_categories` (her categories) → `public.ph_cate_products` (`ref_id` = ASIN, `which_channel=1` = Amazon), deduplicated. See `src/sku_resolver.py`.

## Calculations

Sales = `SUM(COALESCE(order_total,0))`. Orders = `COUNT(DISTINCT order_item_info)`. Change = `(This-Prev)/Prev` (undefined if Prev=0). Trend = Sales-based UP/DOWN/NO CHANGE (Prev=0,Curr>0 → UP). Achieve% = `(This/(Prev*1.30))*100` (undefined if Prev=0). See `src/calculations.py`.

## HTML Generation

`src/html_renderer.py` fills `templates/report_template.html`. **Always** write via `html_renderer.write_html_and_hash()` — never compute a SHA-256 from the in-memory HTML string before writing; a text-mode write on Windows silently translates line endings and changes the file's bytes (this was a real bug found and fixed during this session's dry run — see execution log S019).

## Validation

`src/validator.py` — scope, trend-label, total-reconciliation, no-fabricated-achieve checks. A `ValidationReport.all_passed == False` must block both HTML promotion and `ph_task` publication.

## Versioning

`src/version_resolver.py`. `resolve_planned_version()` is safe to call repeatedly (retries). `consume_version_on_success()` must be called **only** after a committed, read-back-verified `ph_task` insert.

## Retry Behaviour

See `04_DESIGN\UAWSO_PH_TASK_PUBLICATION_PLAN.md` §Idempotency and §Same-Date Correction Rule. A failed attempt never consumes a version; a same-day retry with unchanged content is refused as a duplicate by `ph_task_publisher.find_active_same_date_row()` unless explicitly flagged `is_correction=True`.

## Database Publication

`src/ph_task_publisher.publish_report()` — pre-insert duplicate check → transaction → (correction: reject old row) → insert → read-back verify → active-row-count check → commit or rollback. Never call outside a transaction; never call with `conn.autocommit=True`.

## Evidence

`07_EVIDENCE\execution_logs\` (per-run logs), `07_EVIDENCE\script_register\` (script inventory), `07_EVIDENCE\<date>_<identity>_PUBLICATION_EVIDENCE.md` (per-publish closure record).

## Rollback

There is no destructive rollback of a published `ph_task` row. A wrong publication is corrected via the Same-Date Correction Rule (reject + new version), never a `DELETE`.

## Known Limits

- `main.py` has not been run as a full process against a live DB connection this session (see header).
- Weekly/MTD row-level data was not individually verified this session (aggregate-only) — see `07_EVIDENCE\2026-07-09_utharsika_v001_DRY_RUN_DATA_EVIDENCE.md`.
- The Previous=0,Current>0 Achieve%/Change% case remains without a permanent business label (interim: undefined/"—", never fabricated) — see business rules spec §6.
- `src/logger.py` IS wired into `main.py` for both `--dry-run` and `--publish`. `src/evidence_writer.py` is implemented but **not yet called from `main.py`** — this session's evidence files were hand-authored instead; wiring `evidence_writer` into `main.py`'s dry-run/publish paths is a follow-up for the next implementation pass.
