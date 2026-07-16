"""
WORK 1 investigation: why does Utharsika's user-confirmed June 2025
total (£42,082.96 / 2,412 orders) differ from the current UAWSO
PostgreSQL/HTML result (£41,146.84 / 1,856 orders)?

Read-only. Writes all results to local JSON/CSV files - never modifies
order_transaction, vendor_sales, the workbook, the HTML, or ph_task.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config

STATE = os.path.join(os.path.dirname(__file__), "..", "state")
EVID_DATA = os.path.join(os.path.dirname(__file__), "..", "..", "07_EVIDENCE", "generated_data")
os.makedirs(EVID_DATA, exist_ok=True)


def main():
    import psycopg2
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user, password=cfg.password, connect_timeout=20)
    conn.set_session(readonly=True, autocommit=True)
    results = {}

    def q(sql, params=None):
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return [dict(zip(cols, r)) for r in rows]

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

    # ---- 1. Reproduce current UAWSO calc (Completed, Amazon, UK) ----
    r = q(ASSIGNED_CTE + """
        SELECT
            SUM(CASE WHEN COALESCE(ot.fba_sales,FALSE)=FALSE THEN COALESCE(ot.order_total,0) ELSE 0 END) AS fbm_sales,
            COUNT(DISTINCT CASE WHEN COALESCE(ot.fba_sales,FALSE)=FALSE THEN ot.order_item_info END) AS fbm_orders,
            SUM(CASE WHEN ot.fba_sales=TRUE THEN COALESCE(ot.order_total,0) ELSE 0 END) AS fba_sales,
            COUNT(DISTINCT CASE WHEN ot.fba_sales=TRUE THEN ot.order_item_info END) AS fba_orders,
            COUNT(*) AS row_count,
            COUNT(DISTINCT ot.order_id) AS distinct_order_id,
            COUNT(DISTINCT ot.order_item_info) AS distinct_order_item,
            SUM(COALESCE(ot.quantity,0)) AS total_quantity
        FROM public.order_transaction ot
        JOIN assigned_asins a ON a.asin = ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]
    results['current_uawso_calc'] = r
    print("1. Current UAWSO calc:", r)

    r2 = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(vs.ordered_revenue,0)) AS vendor_sales, SUM(COALESCE(vs.ordered_units,0)) AS vendor_units,
               COUNT(*) AS vendor_row_count, COUNT(DISTINCT vs.asin) AS vendor_distinct_asins
        FROM public.vendor_sales vs
        JOIN assigned_asins a ON a.asin = vs.asin
        WHERE vs.start_time::date <= DATE '2025-06-30' AND vs.end_time::date >= DATE '2025-06-01'
    """)[0]
    results['current_vendor_calc'] = r2
    print("1b. Current Vendor calc:", r2)

    # ---- 2. Column inventory ----
    results['order_transaction_columns'] = q("""
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_schema='public' AND table_name='order_transaction' ORDER BY ordinal_position
    """)
    results['vendor_sales_columns'] = q("""
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_schema='public' AND table_name='vendor_sales' ORDER BY ordinal_position
    """)

    # ---- 3. Status breakdown ----
    results['by_status'] = q(ASSIGNED_CTE + """
        SELECT ot.order_status,
               COUNT(*) AS row_count,
               COUNT(DISTINCT ot.order_id) AS distinct_order_id,
               COUNT(DISTINCT ot.order_item_info) AS distinct_order_item,
               SUM(COALESCE(ot.quantity,0)) AS quantity,
               SUM(COALESCE(ot.order_total,0)) AS sales
        FROM public.order_transaction ot
        JOIN assigned_asins a ON a.asin = ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
        GROUP BY ot.order_status ORDER BY sales DESC
    """)
    print("3. By status:", results['by_status'])

    # ---- 4. Marketplace breakdown ----
    results['by_marketplace'] = q(ASSIGNED_CTE + """
        SELECT COALESCE(ot.market_place, '(blank)') AS market_place,
               COUNT(*) AS row_count,
               COUNT(DISTINCT ot.order_item_info) AS distinct_order_item,
               SUM(COALESCE(ot.order_total,0)) AS sales
        FROM public.order_transaction ot
        JOIN assigned_asins a ON a.asin = ot.asin
        WHERE ot.source_name='AMAZON' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
        GROUP BY ot.market_place ORDER BY sales DESC
    """)
    print("4. By marketplace:", results['by_marketplace'])

    # ---- 5. Source breakdown ----
    results['by_source'] = q(ASSIGNED_CTE + """
        SELECT ot.source, COALESCE(ot.source_name,'(blank)') AS source_name,
               COUNT(*) AS row_count,
               COUNT(DISTINCT ot.order_item_info) AS distinct_order_item,
               SUM(COALESCE(ot.order_total,0)) AS sales
        FROM public.order_transaction ot
        JOIN assigned_asins a ON a.asin = ot.asin
        WHERE ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
        GROUP BY ot.source, ot.source_name ORDER BY sales DESC
    """)
    print("5. By source:", results['by_source'])

    # ---- 6. Account/ss_name breakdown ----
    results['by_account'] = q(ASSIGNED_CTE + """
        SELECT COALESCE(ot.ss_name,'(blank)') AS ss_name,
               SUM(CASE WHEN COALESCE(ot.fba_sales,FALSE)=FALSE THEN COALESCE(ot.order_total,0) ELSE 0 END) AS fbm_sales,
               SUM(CASE WHEN ot.fba_sales=TRUE THEN COALESCE(ot.order_total,0) ELSE 0 END) AS fba_sales,
               COUNT(DISTINCT ot.order_item_info) AS orders,
               SUM(COALESCE(ot.quantity,0)) AS quantity
        FROM public.order_transaction ot
        JOIN assigned_asins a ON a.asin = ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
        GROUP BY ot.ss_name
        ORDER BY SUM(CASE WHEN COALESCE(ot.fba_sales,FALSE)=FALSE THEN COALESCE(ot.order_total,0) ELSE 0 END)
               + SUM(CASE WHEN ot.fba_sales=TRUE THEN COALESCE(ot.order_total,0) ELSE 0 END) DESC
    """)
    print("6. By account (ss_name):", results['by_account'])

    # ---- 7. Sales definition variants ----
    variants = {}
    variants['net_sales_completed'] = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(ot.order_total,0)) AS sales, COUNT(*) AS rows
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]
    variants['positive_sales_only'] = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(ot.order_total,0)) AS sales, COUNT(*) AS rows
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
          AND COALESCE(ot.order_total,0) > 0
    """)[0]
    variants['all_non_cancelled'] = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(ot.order_total,0)) AS sales, COUNT(*) AS rows,
               COUNT(DISTINCT ot.order_item_info) AS orders
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status <> 'Cancelled'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]
    variants['all_statuses'] = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(ot.order_total,0)) AS sales, COUNT(*) AS rows,
               COUNT(DISTINCT ot.order_item_info) AS orders
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]
    variants['no_sku_restriction_asin_only'] = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(ot.order_total,0)) AS sales, COUNT(DISTINCT ot.order_item_info) AS orders
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]  # same as base since we already never restrict by SKU - included for completeness/proof
    results['sales_variants'] = variants
    print("7. Sales variants:", variants)

    # ---- 8. Order-count definition variants ----
    oc = {}
    oc['count_star'] = q(ASSIGNED_CTE + """
        SELECT COUNT(*) AS n FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]['n']
    oc['distinct_order_id'] = q(ASSIGNED_CTE + """
        SELECT COUNT(DISTINCT ot.order_id) AS n FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]['n']
    oc['distinct_order_item_info'] = q(ASSIGNED_CTE + """
        SELECT COUNT(DISTINCT ot.order_item_info) AS n FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]['n']
    oc['sum_quantity'] = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(ot.quantity,0)) AS n FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]['n']
    oc['positive_sales_row_count'] = q(ASSIGNED_CTE + """
        SELECT COUNT(*) AS n FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
          AND COALESCE(ot.order_total,0) > 0
    """)[0]['n']
    oc['distinct_asin_sku_date'] = q(ASSIGNED_CTE + """
        SELECT COUNT(DISTINCT (ot.asin, ot.sku, ot.order_date::date)) AS n
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]['n']
    results['order_count_variants'] = oc
    print("8. Order count variants:", oc)

    # ---- 9. Date field variants ----
    dv = {}
    dv['order_date_cast'] = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(ot.order_total,0)) AS sales, COUNT(DISTINCT ot.order_item_info) AS orders
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]
    dv['order_date_asia_colombo_shift'] = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(ot.order_total,0)) AS sales, COUNT(DISTINCT ot.order_item_info) AS orders
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND (ot.order_date + INTERVAL '5:30')::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]
    dv['order_date_exclusive_end_plus1'] = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(ot.order_total,0)) AS sales, COUNT(DISTINCT ot.order_item_info) AS orders
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date >= TIMESTAMP '2025-06-01 00:00:00' AND ot.order_date < TIMESTAMP '2025-07-01 00:00:00'
    """)[0]
    results['date_variants'] = dv
    print("9. Date variants:", dv)

    # ---- 10. SKU/assignment effects ----
    sk = {}
    sk['blank_sku_rows'] = q(ASSIGNED_CTE + """
        SELECT COUNT(*) AS n, SUM(COALESCE(ot.order_total,0)) AS sales
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
          AND (ot.sku IS NULL OR ot.sku = '')
    """)[0]
    sk['group_by_asin_only'] = q(ASSIGNED_CTE + """
        SELECT COUNT(DISTINCT ot.asin) AS distinct_asins, SUM(COALESCE(ot.order_total,0)) AS sales
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]
    sk['group_by_asin_sku'] = q(ASSIGNED_CTE + """
        SELECT COUNT(DISTINCT (ot.asin, ot.sku)) AS distinct_pairs, SUM(COALESCE(ot.order_total,0)) AS sales
        FROM public.order_transaction ot JOIN assigned_asins a ON a.asin=ot.asin
        WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
          AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
    """)[0]
    # duplicated assignment (no DISTINCT) effect - already confirmed raw=distinct=1723, so test explicitly
    sk['assignment_without_distinct_sales'] = q("""
        WITH target_user AS (SELECT "user" AS user_id FROM public."user" WHERE lower(user_name)=lower('utharsika')),
        target_categories_nodist AS (SELECT c.id AS category_id FROM public.ph_categories c JOIN target_user u ON u.user_id=c.user_id),
        raw_assigned AS (SELECT p.ref_id AS asin FROM public.ph_cate_products p JOIN target_categories_nodist c ON c.category_id=p.ass_cate_id WHERE p.which_channel=1)
        SELECT COUNT(*) AS raw_row_count,
               (SELECT SUM(COALESCE(ot.order_total,0)) FROM public.order_transaction ot
                WHERE ot.asin IN (SELECT asin FROM raw_assigned)
                  AND ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
                  AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30') AS sales_using_raw_in_clause
        FROM raw_assigned
    """)[0]
    results['sku_assignment_variants'] = sk
    print("10. SKU/assignment variants:", sk)

    # ---- 11. Vendor scope detail ----
    vd = {}
    vd['vendor_summary'] = q(ASSIGNED_CTE + """
        SELECT SUM(COALESCE(vs.ordered_revenue,0)) AS sales, SUM(COALESCE(vs.ordered_units,0)) AS units,
               COUNT(*) AS row_count, COUNT(DISTINCT vs.asin) AS distinct_asins,
               COUNT(DISTINCT (vs.asin, vs.start_time::date)) AS distinct_asin_date
        FROM public.vendor_sales vs JOIN assigned_asins a ON a.asin=vs.asin
        WHERE vs.start_time::date <= DATE '2025-06-30' AND vs.end_time::date >= DATE '2025-06-01'
    """)[0]
    vd['vendor_positive_zero_negative'] = q(ASSIGNED_CTE + """
        SELECT
          COUNT(*) FILTER (WHERE COALESCE(vs.ordered_revenue,0) > 0) AS positive_rows,
          COUNT(*) FILTER (WHERE COALESCE(vs.ordered_revenue,0) = 0) AS zero_rows,
          COUNT(*) FILTER (WHERE COALESCE(vs.ordered_revenue,0) < 0) AS negative_rows
        FROM public.vendor_sales vs JOIN assigned_asins a ON a.asin=vs.asin
        WHERE vs.start_time::date <= DATE '2025-06-30' AND vs.end_time::date >= DATE '2025-06-01'
    """)[0]
    results['vendor_detail'] = vd
    print("11. Vendor detail:", vd)

    with open(os.path.join(STATE, "june_difference_investigation.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, default=str, indent=2)
    print("\nSaved full results to state/june_difference_investigation.json")

    conn.close()


if __name__ == "__main__":
    main()
