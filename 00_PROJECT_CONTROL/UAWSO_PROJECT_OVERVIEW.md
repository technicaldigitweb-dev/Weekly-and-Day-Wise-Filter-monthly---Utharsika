# UAWSO Project Overview

**What this asset is:** The top-level summary of the project — what is being built, why, and for whom.

**Why it exists:** So any reader (human or LLM) can understand the project without needing verbal explanation.

**Business question supported:** "What is UAWSO, and why does it exist?"

**Source or evidence used:** `01_REQUIREMENTS\source_requirements\PH-2026-07-UTHAR03 - Satheshkanth - 09-07.PNG` and the matching worksheet in `01_REQUIREMENTS\source_requirements\PHs Daily works - Dev_Automation.xlsx`.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Design stage complete; implementation not started.
**Known limits:** No implementation exists yet — this is documentation only.
**Pass/fail rule:** N/A (descriptive asset).
**Next action:** Proceed to implementation only after this documentation set is reviewed and the open questions in `10_HANDOVER\UAWSO_HANDOVER.md` are resolved.

---

## What is being built

An automated, daily-refreshed sales/orders performance report for one PH (portfolio holder) — `utharsika` — covering only her Amazon UK-assigned SKUs. The report gives three separate comparison views (Daily, Weekly, Month-to-Date), each comparing the current year's completed performance against the same completed period one year earlier, plus a 130% year-over-year achievement target.

## Why it is needed

Requirement `PH-2026-07-UTHAR03`, raised in the shared `PHs Daily works - Dev_Automation.xlsx` tracker, calls for a repeatable, automated way to monitor whether Utharsika's assigned Amazon UK listings are growing fast enough (130% of last year) at three cadences (day, week, month-to-date), refreshed daily, delivered through the existing `tech_team_outputs.ph_task` hosted-tool mechanism rather than a one-off spreadsheet.

## Who benefits

- **utharsika** — the PH who receives the daily task on the `ph_priors` board and uses it to track her portfolio's performance against target.
- **Satheskanth** — the developer, who gets a reusable, documented design instead of rebuilding logic from scratch each day.
- **Satheesvaran** — the business validator, who can review documented rules instead of interpreting ad hoc requests.

## What `UAWSO` means

`UAWSO` = **U**tharsika **A**mazon UK **W**eekly (and Daily/MTD) **S**ales and **O**rders report. It is the `project_code` value used consistently across all `tech_team_outputs.ph_task` rows this capability publishes.

## Scope boundary (one line)

Amazon UK only, `order_status = 'Completed'` only, SKUs specifically assigned to `utharsika` only, all UK Amazon accounts/sub-sources included (no single-account restriction).

## Where everything is

See `README.md` at the project root for the full folder guide, or `02_SOURCE\UAWSO_SOURCE_REGISTER.md` for the canonical location of every source file.
