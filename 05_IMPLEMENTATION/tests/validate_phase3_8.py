"""
Phases 3-8 validation: assigned-ASIN scope integrity, canonical row-set
uniqueness, month-by-month PostgreSQL reconciliation, Vendor period
overlap check. Read-only. Writes results to
05_IMPLEMENTATION/state/phase3_8_validation.json for inspection.
"""
import json
import os
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    host=os.environ["PGHOST"], port=os.environ["PGPORT"], dbname=os.environ["PGDATABASE"],
    user=os.environ["PGUSER"], password=os.environ["PGPASSWORD"],
)
conn.set_session(readonly=True, autocommit=True)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def q(sql, params=None):
    cur.execute(sql, params or {})
    return [dict(r) for r in cur.fetchall()]


results = {}

ASSIGNED_CTE = """
    WITH target_user AS (
        SELECT "user" AS user_id FROM public."user" WHERE lower(user_name) = lower('utharsika')
    ),
    target_categories AS (
        SELECT DISTINCT c.id AS category_id FROM public.ph_categories c JOIN target_user u ON u.user_id = c.user_id
    ),
    assigned_asins AS (
        SELECT DISTINCT p.ref_id AS asin
        FROM public.ph_cate_products p
        JOIN target_categories c ON c.category_id = p.ass_cate_id
        WHERE p.which_channel = 1
    )
"""

# ---------------- Phase 3: assigned-ASIN scope integrity ----------------
results["phase3_distinct_count"] = q(ASSIGNED_CTE + "SELECT COUNT(*) AS n FROM assigned_asins")

results["phase3_raw_vs_distinct"] = q(
    """
    WITH target_user AS (
        SELECT "user" AS user_id FROM public."user" WHERE lower(user_name) = lower('utharsika')
    ),
    target_categories AS (
        SELECT DISTINCT c.id AS category_id FROM public.ph_categories c JOIN target_user u ON u.user_id = c.user_id
    ),
    raw_assignment AS (
        SELECT p.ref_id AS asin
        FROM public.ph_cate_products p
        JOIN target_categories c ON c.category_id = p.ass_cate_id
        WHERE p.which_channel = 1
    )
    SELECT COUNT(*) AS raw_count, COUNT(DISTINCT asin) AS distinct_count FROM raw_assignment
    """
)

results["phase3_txn_row_count_before_join"] = q(
    "SELECT COUNT(*) AS n FROM public.order_transaction WHERE market_place='UK' AND order_date::date >= '2025-01-01' AND order_date::date < '2026-07-14'"
)

results["phase3_txn_row_count_after_join"] = q(
    ASSIGNED_CTE
    + """
    SELECT COUNT(*) AS n
    FROM public.order_transaction t
    JOIN assigned_asins a ON a.asin = t.asin
    WHERE t.market_place='UK' AND t.order_date::date >= '2025-01-01' AND t.order_date::date < '2026-07-14'
    """
)

results["phase3_duplicate_order_item_info_after_join"] = q(
    ASSIGNED_CTE
    + """
    SELECT COUNT(*) AS dup_groups FROM (
        SELECT t.order_item_info, COUNT(*) AS c
        FROM public.order_transaction t
        JOIN assigned_asins a ON a.asin = t.asin
        WHERE t.market_place='UK' AND t.order_date::date >= '2025-01-01' AND t.order_date::date < '2026-07-14'
        GROUP BY t.order_item_info
        HAVING COUNT(*) > 1
    ) x
    """
)

# ---------------- Phase 4/5: canonical row set + month-by-month --------
# Canonical inclusion rule:
#   assigned ASIN; source_name='AMAZON'; status IN ('Completed','Refunded'); market_place='UK'
#   PLUS Completed REPLACEMENT rows counted for Orders/Quantity (not Sales)
results["canonical_duplicate_check"] = q(
    ASSIGNED_CTE
    + """
    SELECT COUNT(*) AS dup_groups FROM (
        SELECT t.order_item_info, COUNT(*) AS c
        FROM public.order_transaction t
        JOIN assigned_asins a ON a.asin = t.asin
        WHERE t.market_place='UK'
          AND t.order_date::date >= '2025-01-01' AND t.order_date::date < '2026-07-14'
          AND (
               (t.source_name='AMAZON' AND t.order_status IN ('Completed','Refunded'))
               OR (t.source_name='REPLACEMENT' AND t.order_status='Completed')
          )
        GROUP BY t.order_item_info
        HAVING COUNT(*) > 1
    ) x
    """
)

results["canonical_included_count"] = q(
    ASSIGNED_CTE
    + """
    SELECT COUNT(*) AS n, COUNT(DISTINCT t.order_item_info) AS distinct_n
    FROM public.order_transaction t
    JOIN assigned_asins a ON a.asin = t.asin
    WHERE t.market_place='UK'
      AND t.order_date::date >= '2025-01-01' AND t.order_date::date < '2026-07-14'
      AND (
           (t.source_name='AMAZON' AND t.order_status IN ('Completed','Refunded'))
           OR (t.source_name='REPLACEMENT' AND t.order_status='Completed')
      )
    """
)

# Month-by-month reconciliation, 2025-01 through 2026-07 (partial, capped at 07-13)
results["month_by_month"] = q(
    ASSIGNED_CTE
    + """
    SELECT
        to_char(t.order_date::date, 'YYYY-MM') AS month,
        SUM(CASE WHEN COALESCE(t.fba_sales,FALSE)=FALSE AND t.source_name='AMAZON' AND t.order_status IN ('Completed','Refunded')
                 THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS fbm_sales,
        SUM(CASE WHEN t.fba_sales=TRUE AND t.source_name='AMAZON' AND t.order_status IN ('Completed','Refunded')
                 THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS fba_sales,
        COUNT(DISTINCT CASE WHEN t.order_status='Completed' AND t.source_name IN ('AMAZON','REPLACEMENT') THEN t.order_item_info END) AS included_order_items,
        SUM(CASE WHEN t.order_status='Completed' AND t.source_name IN ('AMAZON','REPLACEMENT') THEN COALESCE(t.quantity,0) ELSE 0 END) AS included_quantity,
        COUNT(*) FILTER (WHERE t.order_status='Refunded' AND t.source_name='AMAZON') AS refunded_row_count,
        SUM(CASE WHEN t.order_status='Refunded' AND t.source_name='AMAZON' THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS refunded_original_sales,
        COUNT(*) FILTER (WHERE t.order_status IN ('Cancelled','Canceled')) AS excluded_cancelled_rows,
        SUM(CASE WHEN t.order_status IN ('Cancelled','Canceled') THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS excluded_cancelled_value
    FROM public.order_transaction t
    JOIN assigned_asins a ON a.asin = t.asin
    WHERE t.market_place='UK'
      AND t.order_date::date >= '2025-01-01' AND t.order_date::date < '2026-07-14'
    GROUP BY to_char(t.order_date::date, 'YYYY-MM')
    ORDER BY month
    """
)

# ---------------- Phase 6: Vendor period granularity / overlap ----------
results["vendor_period_lengths"] = q(
    ASSIGNED_CTE
    + """
    SELECT
        EXTRACT(EPOCH FROM (v.end_time - v.start_time))/86400.0 AS period_days,
        COUNT(*) AS n
    FROM public.vendor_sales v
    JOIN assigned_asins a ON a.asin = v.asin
    GROUP BY 1
    ORDER BY 1
    """
)

results["vendor_overlap_check"] = q(
    ASSIGNED_CTE
    + """
    SELECT v1.asin, v1.id AS id1, v1.start_time AS start1, v1.end_time AS end1,
           v2.id AS id2, v2.start_time AS start2, v2.end_time AS end2
    FROM public.vendor_sales v1
    JOIN public.vendor_sales v2 ON v1.asin = v2.asin AND v1.id < v2.id
    JOIN assigned_asins a ON a.asin = v1.asin
    WHERE v1.start_time < v2.end_time AND v1.end_time > v2.start_time
    LIMIT 20
    """
)

results["vendor_monthly"] = q(
    ASSIGNED_CTE
    + """
    SELECT to_char(v.start_time::date, 'YYYY-MM') AS month,
           SUM(v.ordered_revenue) AS vendor_sales, SUM(v.ordered_units) AS vendor_units, COUNT(*) AS row_count
    FROM public.vendor_sales v
    JOIN assigned_asins a ON a.asin = v.asin
    WHERE v.start_time::date >= '2025-01-01' AND v.start_time::date < '2026-07-14'
    GROUP BY to_char(v.start_time::date, 'YYYY-MM')
    ORDER BY month
    """
)

os.makedirs("state", exist_ok=True)
with open("state/phase3_8_validation.json", "w", encoding="utf-8") as f:
    json.dump(results, f, default=str, indent=2)

print("DONE")
for k in ["phase3_distinct_count", "phase3_raw_vs_distinct", "phase3_txn_row_count_before_join",
          "phase3_txn_row_count_after_join", "phase3_duplicate_order_item_info_after_join",
          "canonical_duplicate_check", "canonical_included_count", "vendor_overlap_check"]:
    print(f"--- {k} ---")
    print(json.dumps(results[k], default=str, indent=2)[:1500])

print("\n--- month_by_month (count) ---", len(results["month_by_month"]))
for row in results["month_by_month"]:
    print(row)

print("\n--- vendor_period_lengths ---")
for row in results["vendor_period_lengths"]:
    print(row)

print("\n--- vendor_monthly ---")
for row in results["vendor_monthly"]:
    print(row)
