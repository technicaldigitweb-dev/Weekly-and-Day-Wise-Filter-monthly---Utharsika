"""
Seven-status rule validation: grain checks, status-by-status impact,
month-by-month PostgreSQL totals (Utharsika-assigned scope).
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

APPROVED = ('Completed', 'Refunded', 'Deleted', 'New', 'Pending', 'Inprogress', 'Hold')

results = {}

# ---- Grain checks ----
results["assigned_count"] = q(ASSIGNED_CTE + "SELECT COUNT(*) AS n FROM assigned_asins")

results["duplicate_order_item_check"] = q(
    ASSIGNED_CTE
    + """
    SELECT COUNT(*) AS dup_groups FROM (
        SELECT t.order_item_info, COUNT(*) AS c
        FROM public.order_transaction t
        JOIN assigned_asins a ON a.asin = t.asin
        WHERE t.market_place='UK' AND t.source_name IN ('AMAZON','REPLACEMENT')
          AND t.order_status = ANY(%(statuses)s)
          AND t.order_date::date >= '2025-01-01' AND t.order_date::date < '2026-07-14'
        GROUP BY t.order_item_info
        HAVING COUNT(*) > 1
    ) x
    """,
    {"statuses": list(APPROVED)},
)

# ---- Status-by-status impact (full period, June2025, June2026, Jul2026-13) ----
periods = {
    "full_period": ("2025-01-01", "2026-07-13"),
    "june_2025": ("2025-06-01", "2025-06-30"),
    "june_2026": ("2026-06-01", "2026-06-30"),
    "july_2026_13": ("2026-07-01", "2026-07-13"),
}

for label, (start, end) in periods.items():
    results[f"status_breakdown_{label}"] = q(
        ASSIGNED_CTE
        + """
        SELECT
            t.order_status,
            COUNT(*) AS row_count,
            COUNT(DISTINCT t.order_item_info) AS distinct_order_items,
            SUM(COALESCE(t.quantity,0)) AS quantity,
            SUM(CASE WHEN t.source_name='AMAZON' THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS amazon_sales
        FROM public.order_transaction t
        JOIN assigned_asins a ON a.asin = t.asin
        WHERE t.market_place='UK' AND t.source_name IN ('AMAZON','REPLACEMENT')
          AND t.order_date::date >= %(start)s AND t.order_date::date <= %(end)s
        GROUP BY t.order_status
        ORDER BY t.order_status
        """,
        {"start": start, "end": end},
    )
    # Totals under NEW (7-status) rule vs OLD (Completed+Refunded Sales / Completed Orders) rule
    results[f"rule_comparison_{label}"] = q(
        ASSIGNED_CTE
        + """
        SELECT
            SUM(CASE WHEN t.source_name='AMAZON' AND t.order_status IN %(approved)s
                     THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS new_amazon_sales,
            COUNT(DISTINCT CASE WHEN t.order_status IN %(approved)s THEN t.order_item_info END) AS new_orders,
            SUM(CASE WHEN t.order_status IN %(approved)s THEN COALESCE(t.quantity,0) ELSE 0 END) AS new_quantity,
            SUM(CASE WHEN t.source_name='AMAZON' AND t.order_status IN ('Completed','Refunded')
                     THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS old_amazon_sales,
            COUNT(DISTINCT CASE WHEN t.order_status='Completed' THEN t.order_item_info END) AS old_orders,
            SUM(CASE WHEN t.order_status='Completed' THEN COALESCE(t.quantity,0) ELSE 0 END) AS old_quantity
        FROM public.order_transaction t
        JOIN assigned_asins a ON a.asin = t.asin
        WHERE t.market_place='UK' AND t.source_name IN ('AMAZON','REPLACEMENT')
          AND t.order_date::date >= %(start)s AND t.order_date::date <= %(end)s
        """,
        {"start": start, "end": end, "approved": APPROVED},
    )

# ---- Month-by-month (19 months) under NEW rule ----
results["month_by_month_new"] = q(
    ASSIGNED_CTE
    + """
    SELECT
        to_char(t.order_date::date, 'YYYY-MM') AS month,
        SUM(CASE WHEN t.source_name='AMAZON' AND t.order_status='Completed' THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS completed_sales,
        SUM(CASE WHEN t.source_name='AMAZON' AND t.order_status='Refunded' THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS refunded_sales,
        SUM(CASE WHEN t.source_name='AMAZON' AND t.order_status='Deleted' THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS deleted_sales,
        SUM(CASE WHEN t.source_name='AMAZON' AND t.order_status='New' THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS new_sales,
        SUM(CASE WHEN t.source_name='AMAZON' AND t.order_status='Pending' THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS pending_sales,
        SUM(CASE WHEN t.source_name='AMAZON' AND t.order_status='Inprogress' THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS inprogress_sales,
        SUM(CASE WHEN t.source_name='AMAZON' AND t.order_status='Hold' THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS hold_sales,
        SUM(CASE WHEN t.source_name='AMAZON' AND t.order_status IN %(approved)s THEN COALESCE(t.item_price,0)*COALESCE(t.quantity,0) ELSE 0 END) AS total_amazon_sales,
        COUNT(DISTINCT CASE WHEN t.order_status IN %(approved)s THEN t.order_item_info END) AS total_orders,
        SUM(CASE WHEN t.order_status IN %(approved)s THEN COALESCE(t.quantity,0) ELSE 0 END) AS total_quantity
    FROM public.order_transaction t
    JOIN assigned_asins a ON a.asin = t.asin
    WHERE t.market_place='UK' AND t.source_name IN ('AMAZON','REPLACEMENT')
      AND t.order_date::date >= '2025-01-01' AND t.order_date::date < '2026-07-14'
    GROUP BY to_char(t.order_date::date, 'YYYY-MM')
    ORDER BY month
    """,
    {"approved": APPROVED},
)

# ---- Vendor monthly (corrected overlap, unchanged from prior task) ----
results["vendor_monthly"] = q(
    ASSIGNED_CTE
    + """
    SELECT to_char(gs::date,'YYYY-MM') AS month,
           COALESCE((SELECT SUM(v.ordered_revenue) FROM public.vendor_sales v JOIN assigned_asins a2 ON a2.asin=v.asin
                     WHERE NOT (v.end_time::date <= date_trunc('month',gs)::date OR v.start_time::date > (date_trunc('month',gs) + INTERVAL '1 month - 1 day')::date)),0) AS vendor_sales,
           COALESCE((SELECT SUM(v.ordered_units) FROM public.vendor_sales v JOIN assigned_asins a2 ON a2.asin=v.asin
                     WHERE NOT (v.end_time::date <= date_trunc('month',gs)::date OR v.start_time::date > (date_trunc('month',gs) + INTERVAL '1 month - 1 day')::date)),0) AS vendor_units
    FROM generate_series('2025-01-01'::date, '2026-07-01'::date, INTERVAL '1 month') gs
    """
)

os.makedirs("state", exist_ok=True)
with open("state/seven_status_validation.json", "w", encoding="utf-8") as f:
    json.dump(results, f, default=str, indent=2)

print("Assigned count:", results["assigned_count"])
print("Duplicate order_item_info groups:", results["duplicate_order_item_check"])

for label in periods:
    print(f"\n=== {label} status breakdown ===")
    for r in results[f"status_breakdown_{label}"]:
        print(r)
    print(f"--- {label} rule comparison (new vs old) ---")
    print(results[f"rule_comparison_{label}"])

print("\n=== Month by month (new rule) ===")
for r in results["month_by_month_new"]:
    print(r)

print("\n=== Vendor monthly (corrected overlap) ===")
for r in results["vendor_monthly"]:
    print(r)

cur.close()
conn.close()
