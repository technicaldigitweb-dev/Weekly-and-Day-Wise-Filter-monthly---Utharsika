# UAWSO Daily Automation System — Build & Validation Evidence
**Date:** 2026-07-16
**Task:** "UAWSO — Build Complete Unattended Daily Automation System"

## 1. What was built

`05_IMPLEMENTATION/uawso_daily/` — a 12-module Python package (1,509 lines)
providing a single stable command:

```
python -m uawso_daily update-for-today
```

Modules: `__init__.py`, `__main__.py`, `cli.py`, `config.py`, `dates.py`,
`extraction.py`, `transformation.py`, `validation.py`, `rendering.py`,
`publication.py`, `versioning.py`, `evidence.py`, `locking.py`, `result.py`.

Plus:
- `05_IMPLEMENTATION/commands/update_for_today.bat` and `.sh` (thin wrappers, no business logic).
- `05_IMPLEMENTATION/config/uawso_daily.example.env` (names/safe examples only — no credentials).
- `05_IMPLEMENTATION/deployment/uawso_daily.cron.example`, `uawso-daily.service.example`, `uawso-daily.timer.example` — **documented, not installed or enabled**.
- `05_IMPLEMENTATION/tests/test_uawso_daily_automation_package.py` — 42 checks.
- `05_IMPLEMENTATION/uawso_daily/README.md` — full documentation.

No cron job, systemd unit, or Windows Task Scheduler task was created or
enabled by this build. No new `ph_task` row was inserted by this build.

## 2. Architecture — reuse, not duplication

| New module | Calls (unmodified) |
|---|---|
| `extraction.py` | `src/extract_uawso_v5_asin_level.py::extract()` |
| `rendering.py` | `src/dashboard_renderer.py::render_dashboard_v5()`, `verify_no_placeholders()` |
| `publication.py` | `src/ph_task_publisher.py::publish_report()`, `find_active_same_date_row()`, `reject_row()`; `src/version_resolver.py::format_task_id()` |

`versioning.py` is new — filesystem-based (scans `09_OUTPUTS`), per the
task's explicit instruction not to rely solely on
`05_IMPLEMENTATION/state/version_state.json`.

Credentials: exclusively via `config.config.load_db_config()` — the
existing `.env`/`temp_user` mechanism. No credential value is read, stored,
or logged by any file in `uawso_daily/` — confirmed both structurally
(`RunResult` has no such field) and by a source-text audit (test check
`no uawso_daily/*.py file contains a literal hardcoded credential
assignment`).

## 3. Scope and interpretation notes (disclosed deviations)

- **Idempotency case boundaries**: the task described five cases (A–E) in
  prose; the exact verbatim case-boundary wording was not available to
  this build (summarized, not quoted, in the working context). This build
  implements a concrete, defensible interpretation — documented in
  `uawso_daily/README.md`, "Idempotency (five cases)" — built around: (1) a
  live count of active `ph_task` rows for the date (>1 → `DUPLICATE_ACTIVE_OUTPUT`),
  (2) a hash-match check against the one active row, if any (match → `ALREADY_COMPLETE`),
  (3) otherwise, filesystem-based next-version selection with
  `is_correction` set only when an active row already exists for that date.
  This was chosen because it is verifiable, live-tested (see Section 5),
  and structurally cannot touch any date other than `run_date`.
- **`--force-rerun` semantics**: bypasses the `ALREADY_COMPLETE`
  short-circuit only; it does not bypass the validation gate or the
  duplicate-active-row check.
- **Freshness gate**: implemented as "source `MAX(order_date)` reaches
  `report_end_date` within `UAWSO_FRESHNESS_TOLERANCE_DAYS` (default 0)" —
  a direct, minimal reading of "source-freshness gating" from the task.
- **`multi_image_count`**: `extract_uawso_v5_asin_level.py`'s return shape
  does not include this template field (it already collapses to one row
  per ASIN). Rather than modify that approved script's return signature
  (which other, already-published-report regeneration scripts depend on),
  `extraction.py::get_multi_image_count()` runs one small, additional,
  independent read-only query. Disclosed as a deliberate additive design
  choice, not a gap.

## 4. Automated test suite

`python tests/test_uawso_daily_automation_package.py` — **42/42 checks
passed**. No database access; locking/versioning tests use
`tempfile.mkdtemp()`, never the real `runtime/` or `09_OUTPUTS` folders.

Coverage: Asia/Colombo timezone fallback and report-window math (5 checks),
filesystem versioning (7), run-lock acquire/release/stale-reclaim/context-manager
(5), KPI-total arithmetic including the vendor no-proration overlap
boundary (5), image-coverage counting (3), `RunResult`/`Code` semantics
including a credential-field-name audit (5), config env-var overrides (3),
`ValidationReport` pass/fail aggregation (3), CLI argument parsing (4),
`ph_task` task_id formatting (1), and a source-text no-hardcoded-credential
audit (1).

## 5. Live two-phase acceptance run

Per the task's instruction not to perform a new live `ph_task` publication
without further explicit approval, the acceptance test relied on the fact
that today's report was already published earlier in this session
(`09_OUTPUTS/2026-07-16_utharsika_v001.html`, `ph_task` row id=262) — this
lets a real, unmodified `update-for-today` invocation naturally exercise
the `ALREADY_COMPLETE` idempotency path with zero new writes, instead of a
mock.

### Run 1 — `python -m uawso_daily update-for-today --dry-run --verbose`

Full live extraction and validation ran (nothing promoted or published):

```
[1/9] run_date=2026-07-16 report_window=2025-01-01..2026-07-15
[2/9] Checking existing local output versions and ph_task state...
[3/9] Proceeding: version=v002 is_correction=True
[4/9] Checking source freshness...
[5/9] Extracting from PostgreSQL (read-only)...
Assigned ASIN count: 1723 (duplicate assignment rows: 0)
Product master (v5, ASIN-level): 1723 ASINs, 1700 with a usable image, 23 without
Daily ASIN-grain aggregate rows: 29240
Vendor period rows: 961, ASINs with vendor data: 333
[5/9] Extracted totals: fbm_sales=487957.12 fba_sales=184681.8 vendor_sales=46814.94
       total_sales=719453.86 fbm_orders=26271 fba_orders=7975 vendor_orders=4748 total_orders=38994
[6/9] Staged: runtime/uawso_daily/staging/uawso_20260716_163651/report.staging.html
       sha256=ca83ca0b0b0cb78453b232ca4930455b047da099381e6c223715ee5c823239bf
[7/9] Running full validation gate...
[7/9] Validation PASSED (8 checks)
[8/9] --dry-run: skipping promotion and publication.
final_status: DRY_RUN_COMPLETE
PASS
```

The extracted totals **exactly match** the already-published v001 report's
totals (Total Sales £719,453.86, Total Orders 38,994 = 26,271 FBM + 7,975
FBA + 4,748 Vendor) — confirming the live extraction/render/validate path
reproduces the correct, already-verified numbers from a completely fresh
run. All 8 validation-gate checks passed, including the independent
SQL-vs-computed-totals diff (zero) and the B0FX2XDLT5 regression control
(16 Orders confirmed).

Verified after Run 1: `09_OUTPUTS/` still contains only
`2026-07-16_utharsika_v001.html` for this date (no new file written); the
staged file exists only under `runtime/uawso_daily/staging/`.

### Run 2 — `python -m uawso_daily update-for-today --no-publish --verbose`

```
[1/9] run_date=2026-07-16 report_window=2025-01-01..2026-07-15
[2/9] Checking existing local output versions and ph_task state...
[3/9] ALREADY_COMPLETE: version v001 already matches ph_task row 262.
final_status: ALREADY_COMPLETE
version: v001
output_path: 09_OUTPUTS/2026-07-16_utharsika_v001.html
publication_action: none_already_matches
ph_task_row_id: 262
PASS
```

**Zero writes**: no extraction ran, no new file was created under
`09_OUTPUTS`, no new `ph_task` row was inserted, row 262 was not read-back
modified. This is the live, end-to-end proof that the idempotency
detection logic correctly identifies an already-complete day and takes no
action — the substitute this build used in place of a new live publish
test, as instructed.

Post-run verification:
```
09_OUTPUTS files matching 2026-07-16: 2026-07-16_utharsika_v001.html   (only one — unchanged)
runtime/uawso_daily/state/*.json:     no credential-like key found (grep for PGPASSWORD/password/12we34rt: no matches)
```

## 6. Not performed in this task (by explicit instruction)

- No cron job, systemd timer, or Windows Task Scheduler entry was created or enabled.
- No new live `ph_task` row was published (Runs 1–2 above are read/validate-only or hit the zero-write `ALREADY_COMPLETE` path).
- No existing `ph_task` row (157, 237, 256, 262) was modified.
- No credential value was printed, logged, or written to any state/evidence file at any point.

## 7. Verdict

**PASS** — package built per architecture, 42/42 automated checks passed,
both controlled acceptance runs against the live database completed with
the expected outcomes (`DRY_RUN_COMPLETE` with correct totals and a full
passing validation gate; `ALREADY_COMPLETE` with zero writes), and no
prohibited action (scheduler installation, new live publish, secret
exposure, modification of another date's row) was taken.

**Outstanding, deferred to a human decision:**
- Actual deployment (installing the cron/systemd example onto a real host) — not requested by this task.
- Whether/when to schedule the first live unattended run for a genuinely new future date.
