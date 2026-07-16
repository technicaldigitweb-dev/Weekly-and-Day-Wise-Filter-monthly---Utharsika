"""
Read-only investigation:
WORK 1 - True Vendor order count search
WORK 2 - Tax/shipping/return/replacement/shipment effect testing
"""
import json
import os
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    host=os.environ["PGHOST"],
    port=os.environ["PGPORT"],
    dbname=os.environ["PGDATABASE"],
    user=os.environ["PGUSER"],
    password=os.environ["PGPASSWORD"],
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

results = {}

# ---------- WORK 1: Vendor scope for Utharsika ASINs, both periods ----------
for label, start, end in [("june2025", "2025-06-01", "2025-06-30"), ("june2026", "2026-06-01", "2026-06-30")]:
    results[f"vendor_{label}"] = q(
        ASSIGNED_CTE
        + """
        SELECT
            COUNT(*) AS vendor_row_count,
            COUNT(DISTINCT v.asin) AS vendor_distinct_asins,
            SUM(v.ordered_units) AS vendor_units,
            SUM(v.ordered_revenue) AS vendor_sales,
            MIN(v.start_time) AS min_start, MAX(v.end_time) AS max_end
        FROM public.vendor_sales v
        JOIN assigned_asins a ON a.asin = v.asin
        WHERE NOT (v.end_time::date < %(start)s::date OR v.start_time::date > %(end)s::date)
        """,
        {"start": start, "end": end},
    )

# Vendor null-check on any candidate order-key-like column (there is none, but check id uniqueness/nullness anyway)
results["vendor_id_key_test"] = q(
    ASSIGNED_CTE
    + """
    SELECT
        COUNT(*) AS total_rows,
        COUNT(v.id) AS non_null_id,
        COUNT(DISTINCT v.id) AS distinct_id
    FROM public.vendor_sales v
    JOIN assigned_asins a ON a.asin = v.asin
    """
)

# ---------- WORK 2 Section 4: monetary column inventory (already known, re-confirm) ----------
results["order_transaction_columns"] = q(
    """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name='order_transaction'
    ORDER BY ordinal_position
    """
)

# ---------- Section 7: return/refund gross vs net for June 2025 ----------
results["status_breakdown_june2025"] = q(
    ASSIGNED_CTE
    + """
    SELECT
        t.order_status,
        COUNT(*) AS row_count,
        COUNT(DISTINCT t.order_item_info) AS distinct_order_item,
        SUM(COALESCE(t.order_total,0)) AS sales,
        SUM(CASE WHEN t.order_total > 0 THEN t.order_total ELSE 0 END) AS positive_sales,
        SUM(CASE WHEN t.order_total < 0 THEN t.order_total ELSE 0 END) AS negative_sales
    FROM public.order_transaction t
    JOIN assigned_asins a ON a.asin = t.asin
    WHERE t.source_name = 'AMAZON' AND t.market_place = 'UK'
      AND t.order_date::date BETWEEN '2025-06-01' AND '2025-06-30'
    GROUP BY t.order_status
    ORDER BY t.order_status
    """
)

# ---------- Section 8: replacement effect re-verify ----------
results["replacement_rows_june2025"] = q(
    ASSIGNED_CTE
    + """
    SELECT
        t.order_id, t.order_item_info, t.order_status, t.order_total, t.quantity,
        t.source_name, t.market_place, t.ss_name, t.order_date
    FROM public.order_transaction t
    JOIN assigned_asins a ON a.asin = t.asin
    WHERE t.market_place = 'UK'
      AND t.order_date::date BETWEEN '2025-06-01' AND '2025-06-30'
      AND (lower(t.source_name) LIKE '%%replacement%%' OR lower(t.order_status) LIKE '%%replace%%')
    ORDER BY t.order_date
    """
)
results["replacement_summary_june2025"] = q(
    ASSIGNED_CTE
    + """
    SELECT
        COUNT(*) AS row_count,
        COUNT(DISTINCT t.order_id) AS distinct_orders,
        SUM(COALESCE(t.order_total,0)) AS sales,
        SUM(COALESCE(t.quantity,0)) AS quantity
    FROM public.order_transaction t
    JOIN assigned_asins a ON a.asin = t.asin
    WHERE t.market_place = 'UK'
      AND t.order_date::date BETWEEN '2025-06-01' AND '2025-06-30'
      AND lower(t.source_name) LIKE '%%replacement%%'
    """
)

# ---------- Section 9: shipment-like fields check (none expected) ----------
results["distinct_key_counts_june2025"] = q(
    ASSIGNED_CTE
    + """
    SELECT
        COUNT(DISTINCT t.order_id) AS distinct_order_id,
        COUNT(DISTINCT t.order_item_info) AS distinct_order_item,
        SUM(COALESCE(t.quantity,0)) AS shipped_quantity_proxy,
        COUNT(*) AS row_count
    FROM public.order_transaction t
    JOIN assigned_asins a ON a.asin = t.asin
    WHERE t.source_name='AMAZON' AND t.market_place='UK' AND t.order_status='Completed'
      AND t.order_date::date BETWEEN '2025-06-01' AND '2025-06-30'
    """
)

# ---------- Exact pair adjustment check ----------
PAIR_ASIN = "B0FX2QT3B1"
PAIR_SKU = "LSCYRO300GD2PK+RPR44WH2PK"
for label, start, end in [("june2025", "2025-06-01", "2025-06-30"), ("june2026", "2026-06-01", "2026-06-30")]:
    results[f"pair_{label}"] = q(
        """
        SELECT
            t.order_status, COUNT(*) AS row_count,
            COUNT(DISTINCT t.order_item_info) AS distinct_order_item,
            COUNT(DISTINCT t.order_id) AS distinct_order_id,
            SUM(COALESCE(t.order_total,0)) AS sales,
            SUM(COALESCE(t.quantity,0)) AS quantity,
            BOOL_OR(t.fba_sales) AS any_fba,
            t.source_name
        FROM public.order_transaction t
        WHERE t.asin = %(asin)s AND t.sku = %(sku)s
          AND t.order_date::date BETWEEN %(start)s AND %(end)s
        GROUP BY t.order_status, t.source_name
        """,
        {"asin": PAIR_ASIN, "sku": PAIR_SKU, "start": start, "end": end},
    )

results["pair_vendor_check"] = q(
    "SELECT * FROM public.vendor_sales WHERE asin = %(asin)s",
    {"asin": PAIR_ASIN},
)

os.makedirs("state", exist_ok=True)
with open("state/vendor_and_adjustment_investigation.json", "w", encoding="utf-8") as f:
    json.dump(results, f, default=str, indent=2)

print("DONE")
for k, v in results.items():
    print(f"--- {k} ---")
    print(json.dumps(v, default=str, indent=2)[:2000])
