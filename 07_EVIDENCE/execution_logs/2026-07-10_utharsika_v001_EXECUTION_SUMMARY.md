# UAWSO Execution Summary — 2026-07-10_utharsika_v001

**Full log:** `07_EVIDENCE\execution_logs\2026-07-10_utharsika_v001_EXECUTION_LOG.md` (steps S101-S110)

## Outcome

Built a self-contained, interactive, filterable UAWSO dashboard covering the full requested history (`2025-01-01`→`2026-07-09`, 28,601 daily aggregate rows, 1723 assigned ASINs, 1947 ASIN×SKU combinations). Data was extracted via a real, credential-based, read-only Python/psycopg2 connection (the project's approved `temp_user` access), bypassing the LLM chat context entirely for the bulk transfer — the earlier MCP-tool path confirmed this dataset (28,601 rows) was too large to transcribe reliably through chat.

The dashboard's calculation engine (`src/uawso_client_engine.js`) is a single source of truth, inlined verbatim into the shipped HTML and independently tested under Node.js against the real data — 42/42 functional checks pass, including cross-checks against values fetched independently earlier this session.

**Two real bugs were found and fixed this session** (see below). `ph_task` publication and scheduler registration were **not attempted** — both remain gated pending explicit user approval.

## Key Numbers

- Assigned ASIN count: **1723**
- Matching SKU count: **830**
- Product master (valid ASIN×SKU combinations): **1947**
- Daily aggregate rows: **28,601** (exact range: 2025-01-01 to 2026-07-09)
- Default MTD view: 1947 rows (all assigned products, zero-activity retained — 1491 rows have zero Sales in both periods and are still shown)
- Final HTML: `09_OUTPUTS\2026-07-10_utharsika_v001.html`, SHA-256 `024f7f28426125833f7091617afc7ef5c89adfb3a3f1cd543645dfd8b6fe7c23`, 3,420,089 bytes (3.26 MB), independently re-verified with `sha256sum`

## Two Real Bugs Found and Fixed This Session

1. **Weekly comparison logic bug** (S106): the previous-year Weekly period was computed by re-deriving "the shifted date's own Monday" (a carryover from the first session's design), producing `2025-06-02→2025-06-08` instead of the instructed `2025-06-08→2025-06-14`. Caught by a Node.js test asserting the exact worked example from this session's instructions. Fixed in `src/uawso_client_engine.js`; also corrected `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` and `04_DESIGN\UAWSO_SQL_DESIGN.sql.md` to match. Re-verified: 42/42 tests pass post-fix.
2. **Self-referential placeholder bug** (S107): the engine JS file's own doc-comment literally contained the text of its own injection placeholder, which the `verify_no_placeholders()` safety gate correctly caught as "unresolved" after injection. Fixed by rewording the comment (the check itself was working correctly and was not weakened).

## Architecture Note (Filter Architecture Used)

Client-side JavaScript, operating entirely on pre-aggregated, embedded data (never raw order rows, never a live database connection from the browser). The core engine (`uawso_client_engine.js`) deliberately mirrors the Python production formulas (`calculations.py`, `period_calculator.py`) rather than calling them — there is no backend for the static HTML to call. This is a necessary architectural tradeoff given the "self-contained HTML, no browser-to-Postgres connection" constraint, not a second, independently-invented calculation engine: the formulas are identical by construction and cross-checked against the Python-tested values.

## Known Limits

- No real-browser render/interaction test was performed (no browser automation tool available in this environment). Correctness was verified by running the exact shipped JS under Node.js instead — stronger for calculation correctness, but does not measure actual browser paint/interaction performance.
- `extract_uawso_daily_aggregates.py` is a standalone script, not yet wired into `main.py`'s orchestration for the daily automated refresh — flagged as a follow-up.
- The 2026-07-09-identity HTML from the prior session (`09_OUTPUTS\2026-07-09_utharsika_v001.html`) was **not deleted** — it is a superseded artifact from an earlier design iteration (static 3-section report, different naming scheme), left in place per the no-silent-deletion rule and clearly distinguishable by its different identity/date. It is not "today's" output and does not violate the one-file-per-day rule for `2026-07-10`.

## Status

**Data coverage verdict:** PASS
**Default view verdict:** PASS
**Filter tests verdict:** PASS
**Boundary tests verdict:** PASS
**Calculation tests verdict:** PASS
**Security/isolation verdict:** PASS
**Publication verdict:** NOT ATTEMPTED (gated)
**Scheduler verdict:** NOT REGISTERED (gated, unchanged from prior session)
