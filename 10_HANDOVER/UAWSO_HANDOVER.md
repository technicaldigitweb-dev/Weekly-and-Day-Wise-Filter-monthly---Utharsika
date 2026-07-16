# UAWSO Handover & Continuation Context

**What this asset is:** The single place a new developer, or a future session of this same developer, should read first to pick up the project with zero verbal explanation.

**Why it exists:** AIOS's "unknown developer readiness" standard requires that closure/handover documentation alone be sufficient to continue work.

**Business question supported:** "If someone new picks this up tomorrow, do they need to ask anyone anything before they can start implementing?"

**Source or evidence used:** All documents produced in this stage.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Build complete. A validated, self-contained interactive dashboard HTML exists at `09_OUTPUTS\2026-07-10_utharsika_v001.html` (SHA-256 `024f7f28426125833f7091617afc7ef5c89adfb3a3f1cd543645dfd8b6fe7c23`), covering the full requested 2025-01-01→2026-07-09 history. **Publication to `tech_team_outputs.ph_task` and scheduler registration are the only two things not done** — both are explicitly gated pending user approval.
**Known limits:** See `07_EVIDENCE\2026-07-10_utharsika_v001_HTML_VALIDATION_EVIDENCE.md` §Known limits. Two earlier business questions (below) remain genuinely open; two real bugs were found and fixed this build session (Weekly comparison logic, self-referential placeholder) — see execution log.
**Pass/fail rule:** This handover passes if a new reader can answer every question in the Queryability Test (see below) using only files under this project root.
**Next action:** User reviews `09_OUTPUTS\2026-07-10_utharsika_v001.html` and the validation evidence, then either approves the first live `ph_task` publish or requests changes.

---

## Where things stand

- Full AIOS folder structure created under the approved project root.
- All 13 files formerly under the temporary `Sources` folder were inventoried, hashed, moved to canonical destinations, and re-verified byte-for-byte. `Sources` has been removed — see `07_EVIDENCE\source_migration\UAWSO_SOURCE_MIGRATION_VALIDATION.md` for proof.
- The requirement (`PH-2026-07-UTHAR03`) was re-read directly from the live worksheet (not just the screenshot) and confirmed unchanged.
- The Utharsika SKU-assignment chain was resolved against the live database (read-only): `user=109`, 2 categories, 1723 assigned Amazon ASINs, 0 internal duplicates, confirmed joinable to `order_transaction` (1610 matched ASINs / 830 distinct SKUs currently have UK Amazon Completed transactions).
- A live schema check confirmed `ph_task_task_id_unique` is a real, table-wide constraint — this directly shaped the same-date-correction `task_id` design (version-suffixed, not reused).
- Business rules, source-to-target mapping, draft SQL, `ph_task` publication plan, daily automation design, and a validation plan were all produced in the first (design) session — see the folder guide in `README.md`.
- **Second (build) session, 2026-07-10:** the requirement pivoted to a self-contained, client-side-interactive dashboard. Built and validated end-to-end against real data (see `07_EVIDENCE\2026-07-10_utharsika_v001_HTML_VALIDATION_EVIDENCE.md`). `ph_task.team` is now confirmed `'PH Team'` (was previously a proposed `'Technical'`). Daily automation run time is now confirmed `03:00 Asia/Colombo` (chosen in the first build session, per explicit instruction to select a safe time; not yet independently re-confirmed by Satheesvaran as a business preference, but no longer an unresolved gap in the design).
- **No `ph_task` row has been inserted or updated. No scheduler has been configured. No database write of any kind has occurred at any point in either session — all database access has been read-only.**

## Open Questions (remaining)

1. **Zero-base growth case.** Previous Year value = 0, Current Year value > 0. Trend is fully resolved (`UP`), confirmed and re-confirmed across sessions. Achieve %/Sales Change/Order Change remain **intentionally undefined** (never fabricated) — this interim treatment is now implemented and tested (`src/calculations.py` and `src/uawso_client_engine.js` both return `null`/undefined for this case). What remains open is only whether Satheesvaran wants a specific *business label* for this case beyond "undefined" — not a blocker to publishing. (Full context: `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §6.)
2. **Same-day idempotent-retry boundary.** Exactly when a same-day re-run should be treated as a silent no-op vs. a versioned correction depends on the automation runner's retry semantics, which are not yet exercised in a real run. Flagged for the first live publish. (Full context: `04_DESIGN\UAWSO_PH_TASK_PUBLICATION_PLAN.md`, §Idempotency.)
3. **`extract_uawso_daily_aggregates.py` is not yet wired into `main.py`'s orchestration** — it is a standalone script this session. A future pass should expose it as a callable module for the daily automated refresh path.

## Queryability Test — self-check

| Question | Answered in |
|---|---|
| What is being built / why / who benefits | `00_PROJECT_CONTROL\UAWSO_PROJECT_OVERVIEW.md` |
| What `UAWSO` means | `00_PROJECT_CONTROL\UAWSO_PROJECT_OVERVIEW.md` |
| Which SKUs are included | `04_DESIGN\UAWSO_SOURCE_TO_TARGET_MAPPING.md` §0, `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §1 |
| How Utharsika assignment is resolved | `04_DESIGN\UAWSO_SOURCE_TO_TARGET_MAPPING.md` §0, `02_SOURCE\UAWSO_SOURCE_REGISTER.md` (live DB objects table) |
| Which transaction source is used | `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §1 |
| Which Amazon accounts are included | `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §1 (all UK accounts, no restriction) |
| Which filters apply | `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §1 |
| How each reporting period is calculated | `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §4 |
| How Sales and Orders are defined | `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §3 |
| How Trend is calculated | `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §5 |
| How achievement is calculated | `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` §6 |
| Where all source files were migrated | `02_SOURCE\UAWSO_SOURCE_REGISTER.md`, `07_EVIDENCE\source_migration\UAWSO_SOURCE_MIGRATION_VALIDATION.md` |
| What remains unresolved | This file, §Open Questions |
| How daily publication will work | `04_DESIGN\UAWSO_PH_TASK_PUBLICATION_PLAN.md` |
| How duplicate rows will be prevented | `04_DESIGN\UAWSO_PH_TASK_PUBLICATION_PLAN.md` §Idempotency and §Same-Date Correction Rule |
| Who must review the work | This file (Satheesvaran, all documents) |
| Where the built system lives | `05_IMPLEMENTATION\UAWSO_RUNTIME_SYSTEM_GUIDE.md` |
| Where today's validated output is | `09_OUTPUTS\2026-07-10_utharsika_v001.html`, evidence at `07_EVIDENCE\2026-07-10_utharsika_v001_HTML_VALIDATION_EVIDENCE.md` |
| What the next action is | This file, §Next Action |

**Result: every question is answerable from project files alone. Queryability: PASS.**

## Next Action

**User reviews `09_OUTPUTS\2026-07-10_utharsika_v001.html`** (open it in a browser — it is fully self-contained) and `07_EVIDENCE\2026-07-10_utharsika_v001_HTML_VALIDATION_EVIDENCE.md`. On approval:
1. Clear the publication gate in `src/ph_task_publisher.py` / `main.py` (currently refuses `--publish` without an explicit human-confirmed flag by design).
2. Run the first live publish.
3. Only after a successful, verified first publish, register the daily scheduler per `05_IMPLEMENTATION\scheduler\UAWSO_SCHEDULER_DESIGN.md`.
