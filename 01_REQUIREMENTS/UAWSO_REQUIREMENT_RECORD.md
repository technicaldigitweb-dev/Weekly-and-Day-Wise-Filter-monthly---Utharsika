# UAWSO Requirement Record — `PH-2026-07-UTHAR03`

**What this asset is:** The approved, re-read requirement as captured verbatim from the canonical worksheet, plus its interpretation into unambiguous rules.

**Why it exists:** To be the single documented source of truth for what was asked, distinct from how it will be implemented.

**Business question supported:** "What exactly was requested, and where did it come from?"

**Source or evidence used:** Worksheet `PH-2026-07-UTHAR03 - Satheshkan…` (internal name `sheet12.xml`, workbook relationship `rId16`) inside `01_REQUIREMENTS\source_requirements\PHs Daily works - Dev_Automation.xlsx`, re-parsed cell-by-cell on 2026-07-10 (37 populated rows, A1:K42). Cross-checked against the supporting screenshot `01_REQUIREMENTS\source_requirements\PH-2026-07-UTHAR03 - Satheshkanth - 09-07.PNG` — content is identical between the two; no rows exist beyond what the screenshot shows.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Confirmed — re-read on 2026-07-10 found no changes since the prior discovery pass.
**Known limits:** Only the `PH-2026-07-UTHAR03 - Satheshkan…` worksheet was read. No other worksheet in the shared workbook was inspected, per the strict Utharsika-only isolation rule.
**Pass/fail rule:** This record is current as long as no newer edit is made to the source worksheet. Re-read before any future implementation to confirm no drift.
**Next action:** Feed this record into `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` for formal rule extraction.

---

## Worksheet title (A1)

> Weekly Wise and Day Wise Filter monthly

## Column headers (row 2)

`ASIN (Amazon UK)` · `SKU` · `Previous Year sales` · `Previous Year orders` · `This year Sales` · `This year Orders` · `Sales Change` · `Order Change` · `Trend` · `Achieve sales %` · `Achieve order %`

A `Total` row is present (row 6 in the sample). All row-level numeric values (rows 3–6) are explicitly marked illustrative only by the worksheet's own instructions and are **not** used as literal targets — see `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` for the formulas actually derived from them.

## Implementation Instructions (verbatim, A10)

> Generate all required tables, datasets, dashboards, and outputs exclusively for Utharsika.
> Treat the provided tables, worksheets, columns, and field definitions as the minimum mandatory functional requirements.
> The sample row counts, numbering, IDs, formulas, and values are illustrative only and should not be considered final. Modify, expand, or replace them as required to deliver a complete and functional solution.
> Preserve the required table structure, relationships, and intended functionality rather than reproducing the sample data exactly.
> If any business logic, calculation rules, assumptions, validation criteria, or workflow requirements are unclear or missing, consult Satheesvaran before implementation.
> Any clarified logic or business rules will be documented and incorporated into the relevant workbook worksheet(s) to ensure a single source of truth.

## Comparison Period Rule (verbatim, A16–A24)

> This report must provide Daily, Weekly, and Month-to-Date (MTD) comparisons against the same reporting period from the previous year.
>
> Daily Comparison: Compare the previous completed day's performance with the corresponding day from the previous year.
> Weekly Comparison: Compare the current week's completed period (up to the previous day) with the same week and equivalent completed period from the previous year.
> Month-to-Date (MTD) Comparison: Compare the period from the 1st day of the current month up to the previous day with the corresponding period from the previous year.
>
> Daily Refresh Rule: This report must be updated every day using the latest completed data. The current day's partial data must not be included. All metrics, trends, growth percentages, and achievement calculations must be based only on completed data available as of the previous day.
>
> The comparison logic must be applied consistently to Sales, Orders, Achievement %, Growth %, and all other applicable KPIs.

## Achievement Percentage Rule (verbatim, A26–A42)

> The report must include Achieve Sales % and Achieve Order % for each ASIN. These percentages shall measure progress against the 130% target, which is calculated using the same reporting period from the previous year.
>
> Calculation Logic:
> Sales Target = Previous Year Sales × 130%
> Order Target = Previous Year Orders × 130%
> Achieve Sales % = (Current Year Sales ÷ Sales Target) × 100
> Achieve Order % = (Current Year Orders ÷ Order Target) × 100
>
> Example:
> Previous Year Sales = 100
> Current Year Sales Target = 130
> Current Year Sales = 117
> Achieve Sales % = (117 ÷ 130) × 100 = 90%
>
> The same calculation logic must be applied to Orders. Achievement percentages must be calculated separately for Daily, Weekly, and Month-to-Date (MTD) reporting periods based on their respective [periods].

## What was re-read and confirmed unchanged

The 2026-07-10 re-read (this session) parsed the worksheet XML directly (not just the screenshot) and found identical content to the prior discovery pass — no new rows, no edited formulas, no additional instructions. **Requirement changes confirmed: NONE.**

## What the worksheet does NOT specify (carried into open questions)

- No explicit daily run/refresh **time** — only "daily" and "previous completed day" are stated.
- No explicit rule for the case Previous Year value = 0 and Current Year value > 0.
- No explicit "Sales Change"/"Order Change" formula text — derived from the illustrative sample numbers instead (see business rules spec).
