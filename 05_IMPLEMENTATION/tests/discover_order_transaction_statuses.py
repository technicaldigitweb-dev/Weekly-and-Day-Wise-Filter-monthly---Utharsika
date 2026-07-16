"""
Read-only, full-table (all users) status discovery for public.order_transaction.
No business-rule decision made here - pure discovery.
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

# ---- Full status discovery, all time, all users ----
results["status_discovery"] = q(
    """
    SELECT
        order_status AS exact_status,
        (order_status IS NULL) AS is_null,
        LOWER(TRIM(COALESCE(order_status, ''))) AS normalized_status,
        COUNT(*) AS row_count,
        COUNT(DISTINCT order_item_info) AS distinct_order_item_info,
        COUNT(DISTINCT order_id) AS distinct_order_id,
        SUM(COALESCE(quantity,0)) AS total_quantity,
        SUM(COALESCE(item_price,0)*COALESCE(quantity,0)) AS sum_item_price_times_qty,
        SUM(COALESCE(order_total,0)) AS sum_order_total,
        MIN(order_date) AS earliest_order_date,
        MAX(order_date) AS latest_order_date,
        array_agg(DISTINCT source_name) AS distinct_source_names,
        array_agg(DISTINCT fba_sales) AS distinct_fba_sales,
        COUNT(DISTINCT ss_name) AS distinct_ss_name_count
    FROM public.order_transaction
    GROUP BY order_status
    ORDER BY row_count DESC
    """
)

# ---- Blank (empty string, non-null) status check separately, in case GROUP BY treated '' and NULL differently ----
results["blank_status_check"] = q(
    """
    SELECT COUNT(*) AS blank_string_count
    FROM public.order_transaction
    WHERE order_status = ''
    """
)

results["null_status_check"] = q(
    """
    SELECT COUNT(*) AS null_count
    FROM public.order_transaction
    WHERE order_status IS NULL
    """
)

# ---- Case/spelling variation check: group by normalized form to see if any normalized bucket has >1 exact variant ----
results["normalized_groups"] = q(
    """
    SELECT LOWER(TRIM(COALESCE(order_status,''))) AS normalized_status,
           array_agg(DISTINCT order_status) AS exact_variants,
           COUNT(DISTINCT order_status) AS variant_count,
           SUM(cnt) AS total_rows
    FROM (
        SELECT order_status, COUNT(*) AS cnt
        FROM public.order_transaction
        GROUP BY order_status
    ) x
    GROUP BY LOWER(TRIM(COALESCE(order_status,'')))
    ORDER BY total_rows DESC
    """
)

# ---- June 2025 / June 2026 breakdown, full table, all users ----
for label, start, end in [("june_2025", "2025-06-01", "2025-06-30"), ("june_2026", "2026-06-01", "2026-06-30")]:
    results[label] = q(
        """
        SELECT
            order_status AS exact_status,
            COUNT(*) AS row_count,
            COUNT(DISTINCT order_item_info) AS distinct_order_items,
            SUM(COALESCE(quantity,0)) AS total_quantity,
            SUM(COALESCE(item_price,0)*COALESCE(quantity,0)) AS original_sales_value,
            SUM(COALESCE(order_total,0)) AS sum_order_total,
            array_agg(DISTINCT source_name) AS source_names
        FROM public.order_transaction
        WHERE order_date::date >= %(start)s AND order_date::date <= %(end)s
        GROUP BY order_status
        ORDER BY row_count DESC
        """,
        {"start": start, "end": end},
    )
    # source_name breakdown within status for the period
    results[f"{label}_by_source"] = q(
        """
        SELECT
            order_status AS exact_status,
            source_name,
            COUNT(*) AS row_count,
            COUNT(DISTINCT order_item_info) AS distinct_order_items,
            SUM(COALESCE(quantity,0)) AS total_quantity,
            SUM(COALESCE(item_price,0)*COALESCE(quantity,0)) AS original_sales_value,
            SUM(COALESCE(order_total,0)) AS sum_order_total
        FROM public.order_transaction
        WHERE order_date::date >= %(start)s AND order_date::date <= %(end)s
        GROUP BY order_status, source_name
        ORDER BY order_status, source_name
        """,
        {"start": start, "end": end},
    )

os.makedirs("state", exist_ok=True)
with open("state/order_transaction_status_discovery.json", "w", encoding="utf-8") as f:
    json.dump(results, f, default=str, indent=2)

print("=== Status discovery (all time, all users) ===")
for r in results["status_discovery"]:
    print(r)

print("\n=== Blank status count ===", results["blank_status_check"])
print("=== Null status count ===", results["null_status_check"])

print("\n=== Normalized groups (case/spelling variants) ===")
for r in results["normalized_groups"]:
    print(r)

print("\n=== June 2025 breakdown ===")
for r in results["june_2025"]:
    print(r)

print("\n=== June 2026 breakdown ===")
for r in results["june_2026"]:
    print(r)

print("\n=== June 2025 by source ===")
for r in results["june_2025_by_source"]:
    print(r)

print("\n=== June 2026 by source ===")
for r in results["june_2026_by_source"]:
    print(r)

cur.close()
conn.close()
