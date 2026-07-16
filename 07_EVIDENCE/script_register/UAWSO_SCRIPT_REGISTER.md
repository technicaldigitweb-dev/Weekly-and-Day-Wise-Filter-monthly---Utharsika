# UAWSO Script Register

**What this asset is:** Inventory of every script created or reused during implementation.

**Why it exists:** So no script's purpose, ownership, or validation status has to be re-derived by reading code from scratch.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Current as of the 2026-07-10 interactive-dashboard build session (second build session; see additions at the bottom).
**Next action:** Add an entry here for any new script before it is used in production.

---

### config/config.py
- **Purpose:** Central constants (project identity, filters, timezone) and env-var-only DB config loader
- **Created or reused:** Created
- **Input:** Environment variables `PGHOST`/`PGPORT`/`PGDATABASE`/`PGUSER`/`PGPASSWORD`
- **Output:** `DBConfig` dataclass; raises `EnvironmentError` if any var missing
- **Database read/write:** None (no DB access itself)
- **Environment variables required:** PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
- **Credential handling:** Never hardcoded; `redact()` helper for safe logging
- **Called by:** `src/db.py`, `main.py`
- **Validation coverage:** Manually verified `load_db_config()` raises correctly when unset (not unit-tested this session)
- **Status:** Implemented, not exercised against real credentials this session
- **Last executed:** N/A (imported only)
- **Execution-log reference:** S005
- **Known limits:** No automated test for the missing-env-var error path

### src/db.py
- **Purpose:** psycopg2 connection context manager, read-only session mode by default
- **Created or reused:** Created
- **Input:** `DBConfig` (via `config.load_db_config()`)
- **Output:** psycopg2 connection (context-managed)
- **Database read/write:** Enables both; `readonly=True` default sets a DB-level read-only session as defense-in-depth
- **Credential handling:** Never logs raw credentials; `connection_summary()` redacts password
- **Called by:** `main.py`
- **Validation coverage:** Not exercised this session (no local credential available — see execution log S014 note)
- **Status:** Implemented, not executed this session
- **Last executed:** Never
- **Execution-log reference:** S005
- **Known limits:** Untested against the real production database from local psycopg2; the equivalent read operations this session went through the approved MCP-connected read-only tool instead

### sql/01_resolve_assigned_asins.sql
- **Purpose:** Resolve Utharsika's assigned Amazon ASINs (user → ph_categories → ph_cate_products)
- **Created or reused:** Created
- **Database read:** `public.user`, `public.ph_categories`, `public.ph_cate_products`
- **Database write:** None
- **Called by:** `src/sku_resolver.py`
- **Validation coverage:** Logic executed live via the approved read-only tool (S014); returned 1723 ASINs matching prior confirmed count
- **Status:** Verified against live data
- **Last executed:** 2026-07-10 (via equivalent inline query through the approved read-only tool)
- **Execution-log reference:** S014
- **Known limits:** None identified

### src/sku_resolver.py
- **Purpose:** Python wrapper around the above SQL; returns a de-duplicated `AssignedSkuResult`
- **Created or reused:** Created
- **Database read:** Via `sql/01_resolve_assigned_asins.sql`
- **Called by:** `main.py`
- **Validation coverage:** Not exercised via psycopg2 this session (equivalent logic verified via the read-only tool instead); includes `assert_no_cross_user_leakage` defensive helper for future test use
- **Status:** Implemented, logic-equivalent live-verified
- **Last executed:** Never (as Python code against a live connection)
- **Execution-log reference:** S006, S014
- **Known limits:** No automated test exercises this module directly against a live connection this session

### src/period_calculator.py
- **Purpose:** Daily/Weekly/MTD boundary calculation, Asia/Colombo, leap-year and Monday-edge safe
- **Created or reused:** Created
- **Input:** `date` objects
- **Output:** `PeriodSet` dataclasses
- **Called by:** `main.py`, `tests/test_period_calculator.py`
- **Validation coverage:** 10/10 unit checks pass (leap year, Monday edge, month/year transition, weekly previous-year anchoring)
- **Status:** Verified
- **Last executed:** 2026-07-10
- **Execution-log reference:** S007
- **Known limits:** Assumes `Asia/Colombo` has no DST (true as of this build; fixed UTC+5:30 fallback included if `zoneinfo` is unavailable)

### tests/test_period_calculator.py
- **Purpose:** Unit tests for period_calculator.py
- **Created or reused:** Created
- **Called by:** Run directly
- **Validation coverage:** Self — 10/10 PASS
- **Status:** PASS
- **Last executed:** 2026-07-10
- **Execution-log reference:** S007

### sql/02_report_query.sql
- **Purpose:** Aggregate Sales/Orders per ASIN+SKU for one current/previous-year window
- **Created or reused:** Created
- **Database read:** `public.order_transaction`
- **Database write:** None
- **Called by:** `src/report_query.py`
- **Validation coverage:** Logic-equivalent live-verified for DAILY (S016) and aggregate-verified for WEEKLY/MTD (S017)
- **Status:** Verified against live data
- **Last executed:** 2026-07-10 (equivalent inline query via the read-only tool)
- **Execution-log reference:** S016, S017
- **Known limits:** None identified for the mandatory-filter logic; performance at full production volume not load-tested

### src/report_query.py
- **Purpose:** Python wrapper for the above SQL; returns `RawRow` list
- **Created or reused:** Created
- **Called by:** `main.py`, `tests/dry_run_live_data_demo.py` (via `RawRow` construction)
- **Validation coverage:** `RawRow` dataclass exercised directly with real fetched data in the dry-run demo
- **Status:** Implemented, data-shape verified
- **Last executed:** 2026-07-10 (RawRow construction only; SQL execution path not run via psycopg2 this session)
- **Execution-log reference:** S008, S018

### src/calculations.py
- **Purpose:** Sales Change/Order Change/Trend/130% achievement calculation
- **Created or reused:** Created
- **Called by:** `main.py`, `tests/test_calculations.py`, `tests/dry_run_live_data_demo.py`
- **Validation coverage:** 16/16 unit checks pass; additionally exercised against 80 real live rows in the dry run with a 6/6 validation-gate pass
- **Status:** Verified against both synthetic and real data
- **Last executed:** 2026-07-10
- **Execution-log reference:** S008, S018
- **Known limits:** The Previous=0,Current>0 achievement-percentage case is intentionally left undefined (`None`) per the still-open business question in `10_HANDOVER\UAWSO_HANDOVER.md`

### tests/test_calculations.py
- **Purpose:** Unit tests for calculations.py, including worksheet-example and zero-base edge cases
- **Created or reused:** Created
- **Validation coverage:** Self — 16/16 PASS
- **Status:** PASS
- **Last executed:** 2026-07-10
- **Execution-log reference:** S008

### templates/report_template.html
- **Purpose:** Original UAWSO HTML shell (CSS + placeholders) — not copied from any other user's report
- **Created or reused:** Created
- **Called by:** `src/html_renderer.py`
- **Status:** Verified — rendered successfully into `09_OUTPUTS\2026-07-09_utharsika_v001.html`
- **Last executed:** 2026-07-10
- **Execution-log reference:** S009, S020

### src/html_renderer.py
- **Purpose:** Fills the template with computed Daily/Weekly/MTD sections; `write_html_and_hash()` writes the file and returns its true SHA-256
- **Created or reused:** Created
- **Called by:** `main.py`, `tests/dry_run_live_data_demo.py`
- **Validation coverage:** Exercised end-to-end this session; a hash-integrity bug (S019) was found and fixed here
- **Status:** Verified, one bug found and fixed this session
- **Last executed:** 2026-07-10
- **Execution-log reference:** S009, S019, S020
- **Known limits:** None outstanding after the S019 fix

### src/validator.py
- **Purpose:** Programmatic validation checks (scope, trend labels, totals-not-averaged, reconciliation, no-fabricated-achieve)
- **Created or reused:** Created
- **Called by:** `main.py`, `tests/dry_run_live_data_demo.py`
- **Validation coverage:** Exercised against 80 real rows — 6/6 checks PASS
- **Status:** Verified
- **Last executed:** 2026-07-10
- **Execution-log reference:** S010, S018
- **Known limits:** Does not (and cannot) verify structural SQL properties like "no ss_name filter present" at runtime — that is a code-review-time check against `sql/02_report_query.sql`

### src/version_resolver.py
- **Purpose:** vNNN version tracking (one-day-one-file rule), task_id/output-identity formatting
- **Created or reused:** Created
- **Input/Output:** Persists to `state/version_state.json`
- **Database read/write:** None (local file state only)
- **Called by:** `main.py`, `tests/dry_run_live_data_demo.py`
- **Validation coverage:** `resolve_planned_version()` exercised this session (returned v001, no prior state existed); `consume_version_on_success()` NOT called this session (no successful publish yet)
- **Status:** Implemented; "planned" path verified, "consumed" path not yet exercised
- **Last executed:** 2026-07-10
- **Execution-log reference:** S013, S018
- **Known limits:** Version is only consumed on a real successful `ph_task` insert — since publication is gated this session, `state/version_state.json` was not written/updated

### src/ph_task_publisher.py
- **Purpose:** Guarded pre-insert-duplicate-check → transaction → insert → read-back-verify → commit/rollback sequence for `tech_team_outputs.ph_task`
- **Created or reused:** Created
- **Database write:** Yes (INSERT, UPDATE for rejection) — **not called this session**
- **Called by:** `main.py` (`--publish` path only)
- **Validation coverage:** Code-reviewed against the live schema/constraints confirmed in the design stage (`ph_task_task_id_unique`); not executed
- **Status:** Implemented, gated, not executed
- **Last executed:** Never
- **Execution-log reference:** S010, S021
- **Known limits:** Entirely unexercised at runtime — first live call should be treated as a first-of-its-kind action requiring close monitoring

### src/evidence_writer.py
- **Purpose:** Writes structured dry-run/publication evidence Markdown
- **Created or reused:** Created
- **Called by:** Intended for `main.py`; not invoked this session (evidence for this session was hand-authored to accurately capture the interactive/reconstructed nature of the run)
- **Status:** Implemented, not exercised this session
- **Last executed:** Never
- **Execution-log reference:** S010
- **Known limits:** Not yet integrated into `main.py`'s call sequence (main.py currently logs via `src/logger.py` directly; wiring `evidence_writer` into main.py's dry-run path is a follow-up for the next implementation pass)

### src/logger.py
- **Purpose:** Appends structured execution-log entries in the mandated field format
- **Created or reused:** Created
- **Called by:** `main.py`
- **Validation coverage:** Class implemented and importable; **not used to produce this session's execution log** (which was hand-reconstructed — see the log file's header note)
- **Status:** Implemented, not exercised this session
- **Last executed:** Never
- **Execution-log reference:** S010

### main.py
- **Purpose:** Main orchestration entry point (`--dry-run` / `--publish` / `--promote`)
- **Created or reused:** Created
- **Called by:** Operator / scheduler
- **Database read/write:** Read in `--dry-run`; read+write in `--publish` (blocked by `NotImplementedError` unless the gate is explicitly cleared in a future revision)
- **Validation coverage:** Not run end-to-end this session (no local DB credential available) — its logic was proven correct piece-by-piece via the module unit tests and the `tests/dry_run_live_data_demo.py` live-data run
- **Status:** Implemented, not run as a whole process this session
- **Last executed:** Never (as a full process)
- **Execution-log reference:** S011
- **Known limits:** First full end-to-end `python main.py --dry-run` execution (via real psycopg2) has not happened yet — it requires real DB credentials to be placed in the environment, which was out of scope for this interactive session

### scheduler/run_daily_uawso.ps1, scheduler/UAWSO_SCHEDULER_DESIGN.md
- **Purpose:** Windows Task Scheduler wrapper and registration design
- **Created or reused:** Created
- **Database write:** Indirect (invokes `main.py --publish`) — **not registered with the OS this session**
- **Status:** Designed, not registered
- **Last executed:** Never
- **Execution-log reference:** S011, S021

### tests/dry_run_live_data_demo.py
- **Purpose:** One-off harness proving the calculation/validation/HTML pipeline against real fetched data, without requiring a local DB credential
- **Created or reused:** Created (not a permanent part of the production pipeline — see module docstring)
- **Input:** `state/dry_run_daily_raw.json` (real data fetched via the approved read-only tool) + hardcoded Weekly/MTD aggregate totals (also real, fetched the same way)
- **Output:** `09_OUTPUTS\2026-07-09_utharsika_v001.html` — **superseded** by the interactive dashboard (`2026-07-10_utharsika_v001.html`) built in the second session; retained as a historical artifact of the earlier static-report design iteration, not deleted.
- **Database read/write:** None directly (consumes pre-fetched data)
- **Validation coverage:** Self — drives `calculations.py` and `validator.py` for real; 6/6 validation checks PASS
- **Status:** PASS (superseded design)
- **Last executed:** 2026-07-10 (twice — once before, once after the S019 hash fix)
- **Execution-log reference:** S018, S019, S020

---

## Second Build Session (2026-07-10): Interactive Filterable Dashboard

The user's requirement pivoted mid-session from a fixed three-section (Daily/Weekly/MTD) static report to one self-contained, client-side-interactive dashboard covering the full 2025-01-01→2026-07-09 history with arbitrary date/month/week/range/ASIN/SKU filtering. The scripts below implement that pivot. They reuse (not duplicate) the first session's `config/config.py` for project constants.

### src/extract_uawso_daily_aggregates.py
- **Purpose:** Read-only Stage-B credential-based extraction of (a) Utharsika's assigned ASINs, (b) the product master (assigned ASIN × matching SKU), (c) the full daily-grain aggregate dataset, writing all three straight to local JSON — bypassing the LLM chat context entirely (necessary because Stage A/MCP confirmed the full dataset is 28,601 rows, too large to transcribe reliably through chat).
- **Created or reused:** Created
- **Input:** `PGHOST`/`PGPORT`/`PGDATABASE`/`PGUSER`/`PGPASSWORD` env vars (values sourced at invocation time from the approved `02_SOURCE\db_access_templates\temp_user.py` credential set — never written into this script or any new file)
- **Output:** `07_EVIDENCE\generated_data\2026-07-10_utharsika_v001_{product_master,daily_aggregates,assigned_asins}.json`
- **Database read:** `public.user`, `public.ph_categories`, `public.ph_cate_products`, `public.order_transaction` — SELECT only, session explicitly set `readonly=True`
- **Database write:** None. No write method is called anywhere in this script.
- **Credential handling:** Read-only session; password never printed/logged (`config.redact()`); connection closed in a `finally` block
- **Called by:** Run directly (one-off extraction, not wired into `main.py` yet — see known limits)
- **Validation coverage:** Connectivity and read-permission verified with small `COUNT(*)` probes before the full extraction ran (all 4 tables confirmed readable); full run produced exactly the expected counts (1723 ASINs, 1947 product-master rows, 28,601 daily rows, date range exactly 2025-01-01 to 2026-07-09)
- **Status:** PASS
- **Last executed:** 2026-07-10
- **Execution-log reference:** See `07_EVIDENCE\execution_logs\2026-07-10_utharsika_v001_EXECUTION_LOG.md`
- **Known limits:** Not yet wired into `main.py`'s orchestration flow as a callable module (currently a standalone CLI script); a future pass should expose its logic as an importable function for the daily automation path

### src/uawso_client_engine.js
- **Purpose:** Single source of truth for the client-side date/period math and Sales/Orders/Change/Trend/Achieve% formulas. Inlined verbatim into the shipped HTML by `dashboard_renderer.py` AND required directly by the Node test suite — the tested code and shipped code are byte-identical (verified: `engine_source in html` is `True`).
- **Created or reused:** Created
- **Called by:** `templates/uawso_report_template.html` (via injection), `tests/test_uawso_client_engine.js`
- **Validation coverage:** 42/42 checks pass under Node.js against the real extracted dataset, including cross-checks against independently-fetched MCP values, boundary rejections, leap-year handling, and the Total-not-averaged rule. **One real bug found and fixed this session**: the Weekly comparison mode's previous-year calculation (see execution log and `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §4 Weekly correction note).
- **Status:** PASS (post-fix)
- **Last executed:** 2026-07-10
- **Execution-log reference:** See execution log
- **Known limits:** No real-browser test performed (Node.js execution of the exact shipped code is a strong but not identical substitute — DOM/browser-specific behaviour is not exercised)

### tests/test_uawso_client_engine.js
- **Purpose:** Real functional test suite for `uawso_client_engine.js` against the real extracted data (not synthetic fixtures)
- **Created or reused:** Created
- **Validation coverage:** Self — 42/42 PASS (after the Weekly bug fix)
- **Status:** PASS
- **Last executed:** 2026-07-10
- **Execution-log reference:** See execution log

### templates/uawso_report_template.html
- **Purpose:** Canonical, reusable, original UAWSO dashboard template — HTML structure, CSS, filter controls, DOM-wiring JS. No daily-specific data hardcoded; the engine and data are injected by the renderer.
- **Created or reused:** Created
- **Called by:** `src/dashboard_renderer.py`
- **Validation coverage:** Structural checks (one table, no `<script src>`, no credentials) pass on the rendered output; DOM-wiring logic code-reviewed (not independently unit-tested — the pure calculation logic it calls into is what's unit-tested via the engine)
- **Status:** PASS (structural), code-reviewed (UI wiring)
- **Last executed:** 2026-07-10 (rendered into the final HTML)
- **Execution-log reference:** See execution log

### src/dashboard_renderer.py
- **Purpose:** Safe placeholder-substitution renderer — HTML-escapes text values, safely serializes JSON payloads (escapes `</` so embedded data cannot break out of its `<script>` tag), injects the engine JS verbatim, and exposes `verify_no_placeholders()` for a hard pre-promotion gate.
- **Created or reused:** Created
- **Called by:** `tests/generate_final_dashboard.py`
- **Validation coverage:** `verify_no_placeholders()` returned `[]` (zero unresolved) on the real run; one real bug found and fixed this session (the engine.js file's own doc-comment literally contained the placeholder token text, which the verifier correctly flagged — fixed by rewording the comment, not by weakening the check)
- **Status:** PASS
- **Last executed:** 2026-07-10
- **Execution-log reference:** See execution log

### tests/generate_final_dashboard.py
- **Purpose:** One-off driver: loads the real extracted JSON, renders via `dashboard_renderer`, verifies placeholders, writes staging, runs structural/security checks, promotes to `09_OUTPUTS`
- **Created or reused:** Created
- **Database read/write:** None (consumes pre-extracted local JSON only)
- **Validation coverage:** Self — ran to completion, all structural/security checks passed, final SHA-256 independently verified via `sha256sum`
- **Status:** PASS
- **Last executed:** 2026-07-10
- **Execution-log reference:** See execution log
- **Known limits (fixed):** an earlier version of this script hardcoded the literal credential value as a check string; fixed to read it from the environment at check-time instead — see `07_EVIDENCE\2026-07-10_utharsika_v001_HTML_VALIDATION_EVIDENCE.md`

---

## Third Session (2026-07-10): ph_task Publication

### tests/publish_2026_07_10.py
- **Purpose:** One-off live-publish driver — loads the validated HTML, opens a real (non-readonly) transaction-controlled connection, calls the already-designed `src/ph_task_publisher.py::publish_report()` exactly once. Does not reimplement insert logic.
- **Created or reused:** Created (driver only; insert logic reused from `ph_task_publisher.py`)
- **Input:** `09_OUTPUTS\2026-07-10_utharsika_v001.html`
- **Database read:** Pre-insert duplicate check (via `publish_report`'s internal `find_active_same_date_row`)
- **Database write:** **YES — one INSERT into `tech_team_outputs.ph_task`.** This is the first live write this project has performed.
- **Credential handling:** Env-var only via `config.load_db_config()`; no hardcoded values
- **Called by:** Run directly, once
- **Validation coverage:** Pre-insert checks (0 existing UAWSO rows, 0 same-date rows, task_id available) run and passed before execution; post-insert independent read-only SELECT confirmed all required field values, exactly one active row, `html_content` length matches source file exactly
- **Status:** PASS — row `id=157` committed
- **Last executed:** 2026-07-10 15:12:15 (Asia/Colombo)
- **Execution-log reference:** `07_EVIDENCE\2026-07-10_utharsika_v001_PH_TASK_PUBLICATION.md`
- **Known limits:** None — ran exactly once, exactly as designed

---

## Fourth Session (2026-07-10): Full ASIN Coverage + FBM/FBA/Vendor + CSV/Dropdown Update (same v001)

### src/extract_uawso_full_coverage.py
- **Purpose:** Read-only extraction of the full 1723-ASIN assigned master (LEFT JOIN order_transaction, LEFT JOIN vendor_sales), FBM/FBA-split daily aggregates, and vendor period rows
- **Created or reused:** Created (does not modify `extract_uawso_daily_aggregates.py`, kept as historical v1 record)
- **Database read:** `public.user`, `public.ph_categories`, `public.ph_cate_products`, `public.order_transaction`, `public.vendor_sales` — SELECT only, read-only session
- **Database write:** None
- **Status:** PASS — produced exactly 1723/28601/951 rows as expected, matching the prior validation sessions' independently-computed figures exactly
- **Last executed:** 2026-07-10
- **Known limits:** Vendor periods are not bucketed into daily rows (see module docstring) — handled by the client engine's overlap allocation, not this script

### src/uawso_client_engine.js (v2 additions)
- **Purpose:** Added `buildDailyIndexSplit`, `sumRangeSplitByAsin`, `periodsOverlap`, `sumVendorRange`, `computeRowsV2`, `computeTotalV2` — additive, v1 functions unchanged
- **Validation coverage:** 61/61 total checks pass (42 v1 + 19 v2), including exact-value cross-checks against two independent prior validation reports
- **Status:** PASS

### tests/test_uawso_client_engine_v2.js
- **Purpose:** Real functional tests for the v2 engine functions against real extracted data
- **Validation coverage:** Self — 19/19 PASS
- **Status:** PASS
- **Last executed:** 2026-07-10

### templates/uawso_report_template.html (v2 rewrite)
- **Purpose:** Full ASIN coverage, FBM/FBA/Vendor columns, CSV export, searchable multi-select ASIN/SKU dropdowns, Data Coverage Notes section
- **Validation coverage:** Structural checks pass (one table, CSV button present, dropdowns present, coverage notes present); `node --check` confirms valid JS syntax; DOM-level interaction (dropdown clicks, CSV download) not executed in a real browser (no browser automation tool available)
- **Status:** PASS (structural/logic), advisory (UI interaction not browser-tested)

### src/dashboard_renderer.py (v2 changes)
- **Purpose:** `render_dashboard()` signature updated to inject `product_master_full`, `daily_aggregates_split`, `vendor_periods`, `no_sku_count` instead of the v1 `product_master`/`daily_aggregates` pair
- **Validation coverage:** `verify_no_placeholders()` returned `[]`; embedded JSON payloads confirmed byte-identical to source files
- **Status:** PASS
- **Known limits:** Breaking change to the function signature — `tests/generate_final_dashboard.py` (v1 driver) would no longer work against this renderer if re-run; superseded by `tests/generate_final_dashboard_v2.py`

### tests/generate_final_dashboard_v2.py
- **Purpose:** Regenerates the SAME `2026-07-10_utharsika_v001` identity in place (no v002) using the v2 renderer/data
- **Database read/write:** None (consumes pre-extracted local JSON only)
- **Validation coverage:** Ran to completion, all structural/security checks passed, final SHA-256 independently re-verified via `sha256sum`
- **Status:** PASS
- **Last executed:** 2026-07-10
- **Known limits:** Weekly/MTD sections render as aggregate-only summaries in this demo's output, clearly labeled as such in the HTML itself
