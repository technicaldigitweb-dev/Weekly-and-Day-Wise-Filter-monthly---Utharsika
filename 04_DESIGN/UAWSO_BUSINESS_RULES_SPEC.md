# UAWSO Business Rules Specification

**What this asset is:** The complete, unambiguous set of calculation and business rules for the report, written so implementation SQL requires no further interpretation.

**Why it exists:** To prevent drift between what different rows of the workbook imply and what gets built — one documented rule set.

**Business question supported:** "Exactly how is each number calculated, and what happens at the edges (zero, missing data, month/year boundaries)?"

**Source or evidence used:** `01_REQUIREMENTS\UAWSO_REQUIREMENT_RECORD.md`; `08_SKILLS\database_skills\skills_minimal_pack 2 (2).zip → TABLE_order_transaction.md`; live read-only schema checks.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Complete, pending business sign-off on the two open questions below.
**Known limits:** Two rules are explicitly unresolved and require Satheesvaran's confirmation before implementation (marked below).
**Pass/fail rule:** A rule is "resolved" only if it is either stated verbatim in the source worksheet, or unambiguously derivable from the worksheet's own illustrative numbers, or confirmed by a live read-only schema/data check. Anything else is marked open.
**Next action:** Route the two open questions to Satheesvaran; implement only after response, or implement with the open cases producing a visible "unresolved" marker rather than a guessed value (per Section 11 of the stage brief).

---

## 1. Scope Rules

- **Transaction source:** `public.order_transaction` only.
- **Mandatory filters (always applied together):** `source_name = 'AMAZON'`, `market_place = 'UK'`, `order_status = 'Completed'`.
- **Account scope:** All UK Amazon accounts/sub-sources (`ss_name`) included. No single-account, single-storefront restriction. Do not add an `ss_name =` filter.
- **SKU/ASIN scope:** Only ASINs resolved via the assignment chain `public.user → public.ph_categories → public.ph_cate_products` for `user_name = 'utharsika'` (see `04_DESIGN\UAWSO_SOURCE_TO_TARGET_MAPPING.md` §0). Never select rows by filtering `order_transaction.user_name = 'utharsika'` directly — that column reflects a different (transaction-level) attribution and is explicitly excluded from the assignment logic per the stage brief.
- **Assignment channel filter:** `ph_cate_products.which_channel = 1` (confirmed = Amazon).
- **De-duplication:** `DISTINCT ref_id` on the assigned-ASIN set before joining to `order_transaction`, defensively — even though 0 duplicates exist for Utharsika today.

## 2. Grouping Rule

Group all metrics by `(ASIN, SKU)`. Because one ASIN can resolve to more than one SKU (bundle pattern confirmed in sample data — `B084RC5DQG` appears with the same SKU across split rows in the sample), grouping by the pair, not ASIN alone, is required to avoid collapsing distinct SKU-level rows.

## 3. Metric Definitions

| Metric | Formula | Explicitly confirmed against |
|---|---|---|
| Sales | `SUM(COALESCE(order_total, 0))` | `TABLE_order_transaction.md` "CRITICAL: Revenue Metric Rule" — `item_price × quantity` is explicitly forbidden |
| Orders | `COUNT(DISTINCT order_item_info)` | Stage brief §8 — explicitly not `COUNT(DISTINCT order_id)`, row count, or `SUM(quantity)` |

## 4. Reporting Period Rules

All dates are computed in **Asia/Colombo** (Sri Lanka) time. Weeks start **Monday**.

```
report_date = (current Sri Lanka calendar date) − 1 day
```
The current, in-progress day is never included in any period.

### Daily

- Current-year period: `[report_date, report_date]`
- Previous-year period: `[report_date − 1 year, report_date − 1 year]` (same calendar date, prior year)

### Weekly

- Current-year period: `[Monday of report_date's week, report_date]`
- Previous-year period: `[current-year start date shifted back exactly one year, current-year end date shifted back exactly one year]`

**CORRECTED this execution stage (2026-07-10):** the previous-year weekly range is a **plain calendar-date shift of the current-year boundaries**, not a re-derived "that shifted date's own Monday." The interactive dashboard's execution stage gave an explicit worked example — `Current: 2026-06-08 to 2026-06-14` (a Monday-start week) → `Previous: 2025-06-08 to 2025-06-14` — which is the literal same day-of-month shifted back one year, and 2025-06-08 is **not** a Monday. A real bug was caught this stage by a Node.js test comparing the engine's output against this exact example: the original "re-anchor to the shifted date's own Monday" rule (documented in the paragraph this replaces) produced `2025-06-02→2025-06-08` instead, which is wrong per the confirmed instruction. `src/uawso_client_engine.js`'s `resolvePeriod()` now treats `WEEKLY` identically to `CUSTOM` (simple date-shift), fixed and re-verified (42/42 engine tests pass). **This paragraph supersedes the original "Monday re-anchor" design decision below, which is retained struck through for traceability, not deleted:**

> ~~compute `report_date − 1 year` first, then find *that* date's Monday (ISO week start), not "the same ISO week number a year ago."~~ — superseded; see above.

**Monday-run edge case:** if `report_date` itself is a Monday, the "current week" range collapses to a single day (`[Monday, Monday]`), which is functionally identical to the Daily case for that day. No special-case code is needed — the boundary formula naturally produces a 1-day range.

### Month-to-Date (MTD)

- Current-year period: `[1st of report_date's month, report_date]`
- Previous-year period: `[1st of (report_date − 1 year)'s month, report_date − 1 year]`

**Leap-year / invalid-date handling:** `report_date − 1 year` uses calendar-safe date subtraction (Postgres `report_date - interval '1 year'`), not naive string substitution. The one edge case is **Feb 29 → Feb 29 of a non-leap prior/next year does not exist**. Rule: if `report_date` is Feb 29, the previous-year equivalent date is **Feb 28** of the prior year (Postgres's `interval '1 year'` subtraction already produces this automatically — confirmed behaviour, not assumed). This affects the Daily comparison date and the upper bound of Weekly/MTD previous-year ranges only; it does not affect month boundaries (1st of the month always exists).

**Month/year transition:** No special handling needed beyond calendar-correct date arithmetic — `report_date`'s month and year are read directly from the calendar date, so a report run on the 1st of a month naturally produces an MTD range of exactly one day, and a report run in January naturally computes its previous-year MTD range in the previous January.

## 5. Change and Trend Rules

### Sales Change / Order Change

Formula (derived from and confirmed against two independent illustrative rows in the source worksheet — row 3: `(520−450)/450 = 0.156` matches; row 4: `(340−380)/380 = −0.105` matches):

```
Sales Change  = (This Year Sales   − Previous Year Sales)   ÷ Previous Year Sales
Order Change  = (This Year Orders  − Previous Year Orders)  ÷ Previous Year Orders
```

Expressed as a percentage growth figure (not a numeric difference, and not both — the worksheet has exactly one "Sales Change" column and one "Order Change" column, each holding a decimal that displays as a percentage). No additional output column is introduced.

**Zero-denominator handling:** `÷ NULLIF(Previous Year Sales, 0)` / `÷ NULLIF(Previous Year Orders, 0)`. When Previous = 0 and Current = 0, the division returns NULL; display convention for that case is `NOT IMPROVED` (see §6). When Previous = 0 and Current > 0, the division is mathematically undefined (infinite growth) — Sales/Order Change stays undefined (NULL) for this case, same as Achieve %, see §6. This is a genuinely separate concept from Trend, which IS fully defined for this case (below).

### Trend

Sales-based only. Exactly three allowed labels:

```
This Year Sales > Previous Year Sales → UP        (this includes Previous = 0, Current > 0)
This Year Sales < Previous Year Sales → DOWN
This Year Sales = Previous Year Sales → NO CHANGE  (this includes Previous = 0, Current = 0)
```

**Confirmed this execution stage:** the Previous=0,Current>0 case was previously flagged as an open question in the design stage's handover — on review it was never actually ambiguous for Trend specifically (0 < any positive Current Sales trivially satisfies "Current > Previous"), only for Change%/Achieve% (below), which are genuinely undefined at a zero base. The execution stage's instructions make this explicit; `src/calculations.py`'s `_trend()` function implements it directly.

Trend is never derived from Orders, and never uses a fourth label. `NOT IMPROVED` (§6) is a separate, achievement/growth-status concept — it must never replace a Trend value.

## 6. Achievement Percentage Rule

```
Sales Target = Previous Year Sales × 1.30
Order Target = Previous Year Orders × 1.30

Achieve Sales % = (This Year Sales  ÷ Sales Target) × 100
Achieve Order % = (This Year Orders ÷ Order Target) × 100
```

Calculated **independently per reporting period** (Daily, Weekly, MTD each get their own Achieve Sales %/Achieve Order %) — never reused across periods.

**Total row:** never an average of row-level percentages.

```
Total Achieve Sales % = Total This Year Sales  ÷ (Total Previous Year Sales  × 1.30) × 100
Total Achieve Order % = Total This Year Orders ÷ (Total Previous Year Orders × 1.30) × 100
```

**Zero-Value Rule (confirmed):**
- Previous = 0 **and** Current = 0 → display **`NOT IMPROVED`** in the achievement/improvement-status presentation. Trend still evaluates independently and correctly resolves to `NO CHANGE` for this case (see §5) — `NOT IMPROVED` never overwrites the Trend label.
- Division safety: use `NULLIF(Sales Target, 0)` / `NULLIF(Order Target, 0)` so the SQL never raises a division-by-zero error regardless of which zero case is hit.

**OPEN QUESTION — still requires Satheesvaran's confirmation for a permanent business label; interim safe treatment now confirmed for this execution stage:**
> Previous Year value = 0, Current Year value > 0. No achievement percentage is mathematically defined (division by a zero target), and the worksheet does not state a business label for this case. Trend is fully resolved for this case (`UP`, see §5) — only Achieve Sales %/Achieve Order %/Sales Change/Order Change remain undefined. Per this execution stage's explicit instruction, the interim treatment is: **no percentage or label is fabricated** — `src/calculations.py` returns `None` for these four fields via `NULLIF`-equivalent logic, and `src/html_renderer.py` displays an explicit "—" (undefined) marker, never a blank, zero, or assumed value. This interim rule is confirmed safe to ship; a permanent business label (if Satheesvaran wants one beyond "undefined") remains open.

## 7. Isolation Rule (restated for traceability)

Every rule above operates only on the ASIN/SKU set resolved for `utharsika` (§1). No other PH user's assigned SKUs, transactions, or `ph_task` content were read, derived from, or used as a template while writing this specification. **Other users' ph_task report content inspected or reused = NO.**
