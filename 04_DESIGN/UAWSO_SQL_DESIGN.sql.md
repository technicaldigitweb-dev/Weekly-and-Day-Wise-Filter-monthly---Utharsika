# UAWSO SQL Design (Draft — Not Executed)

**What this asset is:** Draft report-calculation SQL and a separately-marked draft publication SQL pattern. Neither has been executed against the database.

**Why it exists:** To turn `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` and `04_DESIGN\UAWSO_SOURCE_TO_TARGET_MAPPING.md` into a concrete, reviewable query design before any implementation.

**Business question supported:** "What would the actual query look like, and does it correctly encode every business rule?"

**Source or evidence used:** All prior `04_DESIGN\` documents in this project; live read-only schema checks of `public.user`, `public.ph_categories`, `public.ph_cate_products`, `public.order_transaction`, `tech_team_outputs.ph_task`.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Draft, not executed, not implemented.
**Known limits:** Untested against live data volumes; performance (index usage on `ph_cate_products.ass_cate_id`, `order_transaction.asin`/`order_date`) has not been evaluated.
**Pass/fail rule:** This draft passes review when every numbered requirement in the stage brief's SQL Design Requirements section is traceably covered by a commented block below.
**Next action:** Review with Satheesvaran, then move to `05_IMPLEMENTATION\` in a future stage — **do not execute from this file.**

---

## ⚠️ STATUS: DRAFT ONLY — NOT APPROVED FOR EXECUTION

This entire file is a design artifact. No statement in it has been run against the database during this stage.

---

## A. Report-Calculation SQL (read-only `SELECT`s — no writes)

```sql
-- =====================================================================
-- UAWSO Daily/Weekly/MTD Sales & Orders report — DRAFT DESIGN, NOT EXECUTED
-- Scope: Amazon UK SKUs assigned to utharsika only. See business rules
-- spec (04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md) for every rule cited here.
-- =====================================================================

-- [Req 1] Derive Sri Lanka "today" safely, independent of DB server timezone.
WITH sl_now AS (
    SELECT (now() AT TIME ZONE 'Asia/Colombo')::date AS sl_today
),

-- [Req 2] report_date = previous completed Sri Lanka calendar day.
-- Current day's partial data is never included (Daily Refresh Rule).
report_anchor AS (
    SELECT sl_today - INTERVAL '1 day' AS report_date
    FROM sl_now
),

-- [Req 3,4,5,6,7] Define one row per reporting period with its current-year
-- and equivalent previous-year boundaries. All four boundaries are computed
-- from report_date using calendar-safe interval arithmetic, so Feb 29 in a
-- leap year safely resolves to Feb 28 in a non-leap comparison year
-- (Postgres 'interval 1 year' subtraction handles this automatically —
-- no manual leap-year branching required). [Req 7: leap-year handling]
period_boundaries AS (
    SELECT
        'DAILY' AS period_name,
        report_date AS cy_start, report_date AS cy_end,
        report_date - INTERVAL '1 year' AS py_start,
        report_date - INTERVAL '1 year' AS py_end
    FROM report_anchor
    UNION ALL
    SELECT
        'WEEKLY' AS period_name,
        -- Monday of report_date's week (ISO: Monday = 1)
        report_date - ((EXTRACT(ISODOW FROM report_date)::int - 1) || ' days')::interval AS cy_start,
        report_date AS cy_end,
        -- CORRECTED 2026-07-10 (see business rules spec §4 Weekly): py_start/py_end
        -- are a plain calendar-date shift of cy_start/cy_end, NOT a re-derived
        -- "Monday of the shifted date's own week". A Node.js test against the
        -- interactive dashboard's identical engine (src/uawso_client_engine.js)
        -- caught this exact bug this stage - this expression now matches the
        -- corrected engine behaviour.
        (report_date - ((EXTRACT(ISODOW FROM report_date)::int - 1) || ' days')::interval) - INTERVAL '1 year' AS py_start,
        report_date - INTERVAL '1 year' AS py_end
    FROM report_anchor
    UNION ALL
    SELECT
        'MTD' AS period_name,
        date_trunc('month', report_date)::date AS cy_start,
        report_date AS cy_end,
        date_trunc('month', (report_date - INTERVAL '1 year')::date)::date AS py_start,
        report_date - INTERVAL '1 year' AS py_end
    FROM report_anchor
),

-- [Req 8,9] Resolve Utharsika's assigned Amazon ASINs.
-- Never filter order_transaction.user_name — assignment is via the
-- category chain only (stage brief §5).
utharsika_user AS (
    SELECT "user" AS user_id
    FROM public."user"
    WHERE lower(user_name) = 'utharsika'
),
utharsika_categories AS (
    SELECT c.id AS category_id
    FROM public.ph_categories c
    JOIN utharsika_user u ON u.user_id = c.user_id
),
assigned_asins AS (
    -- [Req 9] DISTINCT removes duplicate assignment rows defensively,
    -- even though none exist for Utharsika today (confirmed by live check).
    SELECT DISTINCT p.ref_id AS asin
    FROM public.ph_cate_products p
    JOIN utharsika_categories c ON c.category_id = p.ass_cate_id
    WHERE p.which_channel = 1  -- confirmed: 1 = Amazon
),

-- [Req 10,11,12,13] Join assigned ASINs to order_transaction with the
-- mandatory filters. No ss_name / single-account filter is applied —
-- all UK Amazon accounts remain included by design.
filtered_transactions AS (
    SELECT
        ot.asin,
        ot.sku,
        ot.order_total,
        ot.order_item_info,
        ot.order_date::date AS order_date
    FROM public.order_transaction ot
    JOIN assigned_asins a ON a.asin = ot.asin
    WHERE ot.source_name  = 'AMAZON'
      AND ot.market_place = 'UK'
      AND ot.order_status = 'Completed'
),

-- [Req 14,15,16] Aggregate by ASIN+SKU, separately for the current-year and
-- previous-year window of each period. Sales = SUM(COALESCE(order_total,0)).
-- Orders = COUNT(DISTINCT order_item_info) — never order_id, never SUM(quantity).
period_asin_sku_metrics AS (
    SELECT
        pb.period_name,
        ft.asin,
        ft.sku,
        SUM(CASE WHEN ft.order_date BETWEEN pb.cy_start AND pb.cy_end
                 THEN COALESCE(ft.order_total, 0) ELSE 0 END) AS this_year_sales,
        COUNT(DISTINCT CASE WHEN ft.order_date BETWEEN pb.cy_start AND pb.cy_end
                 THEN ft.order_item_info END) AS this_year_orders,
        SUM(CASE WHEN ft.order_date BETWEEN pb.py_start AND pb.py_end
                 THEN COALESCE(ft.order_total, 0) ELSE 0 END) AS previous_year_sales,
        COUNT(DISTINCT CASE WHEN ft.order_date BETWEEN pb.py_start AND pb.py_end
                 THEN ft.order_item_info END) AS previous_year_orders
    FROM filtered_transactions ft
    CROSS JOIN period_boundaries pb
    GROUP BY pb.period_name, ft.asin, ft.sku
)

-- [Req 17,18,19,20,21,22,23] Row-level Sales Change, Order Change, Trend,
-- 130% targets, and safe (never-divide-by-zero) achievement percentages.
SELECT
    period_name,
    asin,
    sku,
    previous_year_sales,
    previous_year_orders,
    this_year_sales,
    this_year_orders,
    (this_year_sales - previous_year_sales) / NULLIF(previous_year_sales, 0) AS sales_change,
    (this_year_orders - previous_year_orders)::numeric / NULLIF(previous_year_orders, 0) AS order_change,
    CASE
        WHEN this_year_sales > previous_year_sales THEN 'UP'
        WHEN this_year_sales < previous_year_sales THEN 'DOWN'
        ELSE 'NO CHANGE'
    END AS trend,                                             -- [Req 19,20]: Sales-based only, 3 labels only
    previous_year_sales  * 1.30 AS sales_target,
    previous_year_orders * 1.30 AS order_target,
    (this_year_sales  / NULLIF(previous_year_sales  * 1.30, 0)) * 100 AS achieve_sales_pct,   -- [Req 21,22,23]
    (this_year_orders / NULLIF(previous_year_orders * 1.30, 0)) * 100 AS achieve_order_pct,
    CASE WHEN previous_year_sales = 0 AND this_year_sales = 0
         THEN 'NOT IMPROVED' ELSE NULL END AS zero_case_status  -- [business rules spec §6]
    -- NOTE: previous=0, current>0 case intentionally produces NULL achieve_*_pct
    -- above (via NULLIF) with no invented label — open question, see spec §6.
FROM period_asin_sku_metrics
ORDER BY period_name, asin, sku;

-- =====================================================================
-- [Req 24] Total row per period — computed from AGGREGATE totals, never
-- from AVG() of the row-level percentages above.
-- =====================================================================
-- (Illustrative shape; would be UNION'd with the row-level SELECT above
-- in implementation, grouped only by period_name with no asin/sku.)
--
-- SELECT
--     period_name,
--     'TOTAL' AS asin,
--     NULL AS sku,
--     SUM(previous_year_sales)  AS previous_year_sales,
--     SUM(previous_year_orders) AS previous_year_orders,
--     SUM(this_year_sales)      AS this_year_sales,
--     SUM(this_year_orders)     AS this_year_orders,
--     (SUM(this_year_sales) - SUM(previous_year_sales)) / NULLIF(SUM(previous_year_sales),0) AS sales_change,
--     (SUM(this_year_sales)  / NULLIF(SUM(previous_year_sales)  * 1.30, 0)) * 100 AS achieve_sales_pct,
--     (SUM(this_year_orders) / NULLIF(SUM(previous_year_orders) * 1.30, 0)) * 100 AS achieve_order_pct
-- FROM period_asin_sku_metrics
-- GROUP BY period_name;
```

### Coverage checklist against Section 18 requirements

| # | Requirement | Covered by |
|---|---|---|
| 1 | Derive Sri Lanka current date safely | `sl_now` CTE |
| 2 | report_date = previous calendar day | `report_anchor` CTE |
| 3 | Daily boundaries | `period_boundaries` (`DAILY` branch) |
| 4 | Monday-based Weekly boundaries | `period_boundaries` (`WEEKLY` branch, `ISODOW`) |
| 5 | MTD boundaries | `period_boundaries` (`MTD` branch, `date_trunc`) |
| 6 | Equivalent previous-year boundaries | `py_start`/`py_end` in every branch |
| 7 | Leap-year handling | Comment above `period_boundaries`; relies on Postgres interval arithmetic, confirmed behaviour |
| 8 | Resolve Utharsika's assigned SKU set first | `utharsika_user` → `utharsika_categories` → `assigned_asins` |
| 9 | Remove duplicate assigned SKUs | `DISTINCT` in `assigned_asins` |
| 10 | Join assigned SKUs to `order_transaction` | `filtered_transactions` |
| 11 | Apply mandatory filters | `filtered_transactions WHERE` clause |
| 12 | Include all UK Amazon accounts | No `ss_name` filter present, by design |
| 13 | Avoid account-specific restrictions | Same as above |
| 14 | Aggregate by ASIN and SKU | `GROUP BY pb.period_name, ft.asin, ft.sku` |
| 15 | Current/previous Sales | `this_year_sales` / `previous_year_sales` |
| 16 | Current/previous Orders | `this_year_orders` / `previous_year_orders` |
| 17 | Sales Change | `sales_change` |
| 18 | Order Change | `order_change` |
| 19 | Sales-based Trend | `trend` CASE expression |
| 20 | Trend restricted to 3 labels | Same CASE expression, no `ELSE` beyond `'NO CHANGE'` |
| 21 | 130% targets | `sales_target` / `order_target` |
| 22 | Safe achievement % | `achieve_sales_pct` / `achieve_order_pct` with `NULLIF` |
| 23 | Prevent division-by-zero | `NULLIF(...,0)` throughout |
| 24 | Total from aggregates, not averages | Commented Total block, `SUM()`-of-`SUM()` pattern |
| 25 | Support dated daily publication | See Section B below (`task_id` design) |
| 26 | Support idempotent same-date retries | See Section B below |
| 27 | Comments explaining every business rule | Inline `--` comments throughout |

---

## B. Publication SQL Pattern — `NOT APPROVED FOR EXECUTION`

This section documents the **shape** of the eventual `ph_task` insert/update pattern for traceability. It is **not** to be run in this stage, per the stage brief ("Do not insert or update `tech_team_outputs.ph_task`").

```sql
-- ⚠️ NOT APPROVED FOR EXECUTION — design reference only.
-- Pattern adapted from 08_SKILLS\ph_task_rules\Versioning - phase_level and version_level.md,
-- combined with the live ph_task_task_id_unique constraint confirmed this stage.

-- Step 1: check for an existing ACTIVE row for this report_date.
-- SELECT id, task_id, version_level
-- FROM tech_team_outputs.ph_task
-- WHERE project_code = 'UAWSO'
--   AND task_id LIKE 'UAWSO-' || to_char(:report_date, 'YYYY-MM-DD') || '%'
--   AND version_status <> 'rejected'
-- ORDER BY version_level DESC
-- LIMIT 1;

-- Step 2 (correction only — skip on first publish of a date):
-- reject the superseded same-date row.
-- UPDATE tech_team_outputs.ph_task
-- SET version_status = 'rejected', updated_at = now()
-- WHERE id = :existing_row_id;

-- Step 3: insert the new/next row.
-- task_id must stay globally unique (live constraint ph_task_task_id_unique),
-- so a same-date correction uses a version-suffixed task_id rather than
-- reusing the v1 identity — see 04_DESIGN\UAWSO_PH_TASK_PUBLICATION_PLAN.md.
-- INSERT INTO tech_team_outputs.ph_task
--     (project_name, project_code, task_name, task_id, team, developer,
--      assigned_user, assigned_user_team, html_content, description,
--      phase_level, version_level, version_status)
-- VALUES
--     ('Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report',
--      'UAWSO',
--      'Utharsika Amazon UK Daily, Weekly and MTD Sales and Orders Report — ' || to_char(:report_date,'YYYY-MM-DD'),
--      'UAWSO-' || to_char(:report_date,'YYYY-MM-DD') || CASE WHEN :version_level > 1 THEN '-v' || :version_level ELSE '' END,
--      'Technical', 'Satheskanth', 'utharsika', 'ph_priors',
--      :generated_html, :description,
--      1, :version_level, 'released');
```

Full field-value rationale is in `04_DESIGN\UAWSO_PH_TASK_PUBLICATION_PLAN.md`.
