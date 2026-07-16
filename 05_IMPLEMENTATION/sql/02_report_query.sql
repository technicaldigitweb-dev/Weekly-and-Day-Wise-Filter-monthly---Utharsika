-- UAWSO: aggregate Sales/Orders per ASIN+SKU for one current-year window
-- and one previous-year window of a single reporting period.
-- Run once per period (DAILY / WEEKLY / MTD) with different date params.
--
-- Params:
--   %(asins)s       - tuple of assigned ASINs (from 01_resolve_assigned_asins.sql)
--   %(cy_start)s, %(cy_end)s - current-year window (inclusive, date)
--   %(py_start)s, %(py_end)s - previous-year window (inclusive, date)
--
-- Mandatory filters per 04_DESIGN/UAWSO_BUSINESS_RULES_SPEC.md Section 1:
-- Amazon UK Completed orders only, all UK accounts included (no ss_name filter).

WITH filtered AS (
    SELECT
        ot.asin,
        ot.sku,
        ot.order_total,
        ot.order_item_info,
        ot.order_date::date AS order_date
    FROM public.order_transaction ot
    WHERE ot.asin = ANY(%(asins)s)
      AND ot.source_name  = 'AMAZON'
      AND ot.market_place = 'UK'
      AND ot.order_status = 'Completed'
      AND ot.order_date::date BETWEEN LEAST(%(py_start)s, %(cy_start)s) AND GREATEST(%(py_end)s, %(cy_end)s)
)
SELECT
    asin,
    sku,
    SUM(CASE WHEN order_date BETWEEN %(cy_start)s AND %(cy_end)s
             THEN COALESCE(order_total, 0) ELSE 0 END) AS this_year_sales,
    COUNT(DISTINCT CASE WHEN order_date BETWEEN %(cy_start)s AND %(cy_end)s
             THEN order_item_info END) AS this_year_orders,
    SUM(CASE WHEN order_date BETWEEN %(py_start)s AND %(py_end)s
             THEN COALESCE(order_total, 0) ELSE 0 END) AS previous_year_sales,
    COUNT(DISTINCT CASE WHEN order_date BETWEEN %(py_start)s AND %(py_end)s
             THEN order_item_info END) AS previous_year_orders
FROM filtered
GROUP BY asin, sku
ORDER BY asin, sku;
