# UAWSO Publication Evidence — 2026-07-09_utharsika_v001

**What this asset is:** The closure evidence record for this report date's publication attempt.

**Why it exists:** Required Closure Evidence per this stage's brief — but honestly reflects that publication was **NOT** attempted this session (gated), rather than fabricating a completed-publication record.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** PENDING — awaiting explicit user go-ahead before the first live `ph_task` insert for this capability.
**Known limits:** Every field below that would normally describe a completed publication is explicitly marked N/A (not yet occurred), not filled with a guessed or placeholder-as-if-real value.
**Pass/fail rule:** This record is only complete once a real publish attempt (success or failure) has occurred and this file is updated with the true outcome.
**Next action:** User confirms go-ahead → `main.py --publish --i-understand-this-writes-to-production` is run → this file is updated with the real result.

---

| Field | Value |
|---|---|
| Report date | 2026-07-09 |
| Version | v001 (planned, not yet consumed — see `state/version_state.json`, currently absent since no successful publish has occurred) |
| Assigned-SKU count | 1723 |
| Report row counts | DAILY: 80 (rows fetched this session); WEEKLY/MTD: aggregate-only this session (see dry-run data evidence) |
| Daily totals | Prev Sales 1,489.37 / Prev Orders 81 / This Sales 350.94 / This Orders 12 |
| Weekly totals | Prev Sales 4,817.56 / Prev Orders 253 / This Sales 2,788.72 / This Orders 124 |
| MTD totals | Prev Sales 17,900.53 / Prev Orders 908 / This Sales 7,442.66 / This Orders 341 |
| Validation results | DAILY 6/6 PASS; WEEKLY/MTD row-level validation not run this session (aggregate-only capture) — see dry-run data evidence |
| HTML path | `09_OUTPUTS\2026-07-09_utharsika_v001.html` |
| HTML SHA-256 | `52667eebadb04234f098af67d48d6005402f36e9f4e7b9e7ecdeb0cdc736aa9b` (verified independently via `sha256sum`, matches exactly) |
| Task name | `2026-07-09_utharsika_v001` (planned, not yet published) |
| Task ID | `UAWSO-2026-07-09-utharsika-v001` (planned, not yet published) |
| Inserted row ID | **N/A — not inserted. Publication not attempted this session.** |
| Publication timestamp (Asia/Colombo) | **N/A — not published.** |
| Duplicate check | Not run against the live table this session (no pre-insert check was executed since no insert was attempted) |
| Scheduler state | Not registered (designed only — see `05_IMPLEMENTATION\scheduler\UAWSO_SCHEDULER_DESIGN.md`) |
| Execution-log paths | `07_EVIDENCE\execution_logs\2026-07-09_utharsika_v001_EXECUTION_LOG.md`, `..._EXECUTION_SUMMARY.md` |
| PASS/FAIL | **PASS for dry-run/validation stage. NOT APPLICABLE for publication (not attempted).** |
