# UAWSO Execution Summary — 2026-07-09_utharsika_v001

**Full log:** `07_EVIDENCE\execution_logs\2026-07-09_utharsika_v001_EXECUTION_LOG.md` (21 steps, S001-S021)

## Outcome

Full production codebase built under `05_IMPLEMENTATION\`, unit-tested (26/26 checks pass across period-boundary and calculation logic), and exercised end-to-end against **real live data** for report_date=2026-07-09. Validation gate passed (6/6 checks). A validated HTML report was generated and promoted to `09_OUTPUTS\2026-07-09_utharsika_v001.html`.

**Publication to `tech_task_outputs.ph_task` and scheduler registration were deliberately NOT performed** — both are gated pending explicit user confirmation, per this stage's execution rules around first-ever live writes to a shared production table and unattended recurring automation.

## Key Numbers (DAILY period, report_date=2026-07-09)

- Utharsika assigned-ASIN count: **1723**
- DAILY rows: **80** (database returned 81; see logging gap note below)
- DAILY Total This Year Sales: **350.94** / Orders: **12**
- DAILY Total Previous Year Sales: **1,489.37** / Previous Year Orders: **81** (sum of the 80 transcribed rows)
- Cross-check: previous_year_orders sum (81) exactly matches S015's independently-run `py_txn_rows` count (81) — despite the 81→80 row-count discrepancy noted below, this confirms no previous-year order volume was actually lost in transcription.
- Validation: **6/6 PASS**

## WEEKLY / MTD (aggregate-only, exact SQL totals — not sampled)

| Period | This Year Sales | This Year Orders | Previous Year Sales | Previous Year Orders |
|---|---|---|---|---|
| WEEKLY | 2,788.72 | 124 | 4,817.56 | 253 |
| MTD | 7,442.66 | 341 | 17,900.53 | 908 |

Row-level Weekly/MTD detail was not individually transcribed this session (92 and 200+ ASIN/SKU pairs) — the totals above are exact, direct SQL aggregates, not estimates. A production `main.py` run fetches and renders full row-level detail for all three periods programmatically.

## A Real Bug Found and Fixed This Session

The first SHA-256 computed for the generated HTML did not match the actual file on disk (Windows text-mode write silently converted `\n` to `\r\n`, changing the file's bytes after the hash was taken). Root-caused and fixed by adding `html_renderer.write_html_and_hash()`, which writes in binary mode and computes the hash from the exact bytes written. Independently re-verified with `sha256sum`. See execution log S019.

## Logging Gaps

- **S016**: 81 rows returned by the database, 80 transcribed into evidence — one row's specific identity is unverified (**LOGGING GAP — UNVERIFIED**). Does not affect the correctness of the totals used (independently cross-checked against S015's separately-run count query).

## Files Created This Session

See `07_EVIDENCE\script_register\UAWSO_SCRIPT_REGISTER.md` for the full script inventory, and the file-change log embedded in the execution log (S004-S020).

## Status

**Validation verdict:** PASS
**Publication verdict:** NOT ATTEMPTED (gated)
**Scheduler verdict:** NOT REGISTERED (gated, designed only)
