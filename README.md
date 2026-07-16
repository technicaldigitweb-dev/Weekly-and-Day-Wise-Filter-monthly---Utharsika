# UAWSO — Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report

**Project code:** `UAWSO`
**Requirement ID:** `PH-2026-07-UTHAR03`
**Developer:** Satheskanth
**Business clarification / validator:** Satheesvaran
**Assigned user (report recipient):** `utharsika`
**Dashboard board:** `ph_priors`
**Team:** `PH Team`
**Status:** System built and dry-run tested against live data (report_date=2026-07-09, validation PASS). `ph_task` publication and scheduler registration are gated pending explicit user go-ahead — see `10_HANDOVER\UAWSO_HANDOVER.md`.

## What this project is

A daily-refreshed report, built exclusively for the PH (portfolio holder) `utharsika`, covering only the Amazon UK SKUs specifically assigned to her. For each of her ASINs/SKUs it shows Daily, Weekly, and Month-to-Date Sales and Orders compared against the equivalent completed period one year earlier, with Sales Change, Order Change, a Sales-based Trend, and Achieve Sales %/Achieve Order % against a 130% year-over-year target. The report is delivered as a dated row in `tech_team_outputs.ph_task`, routed to the `ph_priors` board.

## Folder guide

| Folder | Contents |
|---|---|
| `00_PROJECT_CONTROL\` | Project overview, AIOS governance sources |
| `01_REQUIREMENTS\` | The canonical requirement workbook/worksheet and requirement record |
| `02_SOURCE\` | Source register, migration manifest, DB access templates |
| `03_DISCOVERY\` | Discovery summary (what existed before this stage) |
| `04_DESIGN\` | Source-to-target mapping, business rules, SQL design, `ph_task` publication plan, daily automation design |
| `05_IMPLEMENTATION\` | Production Python system — config, SQL, src modules, templates, scheduler, tests. See `05_IMPLEMENTATION\UAWSO_RUNTIME_SYSTEM_GUIDE.md`. |
| `06_VALIDATION\` | Validation plan + per-run system validation report |
| `07_EVIDENCE\` | Migration validation evidence, execution logs, script register, dry-run/publication evidence |
| `08_SKILLS\` | Reusable database and `ph_task` schema/rule references |
| `09_OUTPUTS\` | Generated HTML reports (`2026-07-09_utharsika_v001.html` — dry-run validated, not yet published) |
| `10_HANDOVER\` | Handover and continuation context |
| `11_REVIEW\` | Reserved for review notes (not used yet) |
| `12_ARCHIVE\` | Reserved for superseded assets (not used yet) |

## Start here

1. `00_PROJECT_CONTROL\UAWSO_PROJECT_OVERVIEW.md` — what/why/who
2. `01_REQUIREMENTS\UAWSO_REQUIREMENT_RECORD.md` — the approved requirement
3. `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` — all calculation rules
4. `04_DESIGN\UAWSO_SQL_DESIGN.sql.md` — draft SQL (not executed)
5. `10_HANDOVER\UAWSO_HANDOVER.md` — current status and next action

## Open questions

See `10_HANDOVER\UAWSO_HANDOVER.md` for the full list. Headline items:
- Daily automation run time is not specified anywhere in the source workbook — needs confirmation from Satheesvaran.
- Behaviour when Previous Year value = 0 and Current Year value > 0 (undefined achievement/growth percentage) needs confirmation from Satheesvaran.
