"""
Read-only fetch of per-ASIN June 2025 and June 2026 FBM/FBA/Vendor
breakdown for Utharsika's assigned ASINs, written directly to local
JSON (never through chat context, since the row count is too large).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "state", "asin_level_db_2025_2026.json")


def main():
    import psycopg2
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user, password=cfg.password, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
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
                ),
                tx_2025 AS (
                    SELECT ot.asin, ot.sku,
                        SUM(CASE WHEN COALESCE(ot.fba_sales,FALSE)=FALSE THEN COALESCE(ot.order_total,0) ELSE 0 END) AS fbm_sales,
                        SUM(CASE WHEN ot.fba_sales=TRUE THEN COALESCE(ot.order_total,0) ELSE 0 END) AS fba_sales,
                        COUNT(DISTINCT ot.order_item_info) AS orders
                    FROM public.order_transaction ot
                    JOIN assigned_asins a ON a.asin = ot.asin
                    WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
                      AND ot.order_date::date BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'
                    GROUP BY ot.asin, ot.sku
                ),
                tx_2026 AS (
                    SELECT ot.asin, ot.sku,
                        SUM(CASE WHEN COALESCE(ot.fba_sales,FALSE)=FALSE THEN COALESCE(ot.order_total,0) ELSE 0 END) AS fbm_sales,
                        SUM(CASE WHEN ot.fba_sales=TRUE THEN COALESCE(ot.order_total,0) ELSE 0 END) AS fba_sales,
                        COUNT(DISTINCT ot.order_item_info) AS orders
                    FROM public.order_transaction ot
                    JOIN assigned_asins a ON a.asin = ot.asin
                    WHERE ot.source_name='AMAZON' AND ot.market_place='UK' AND ot.order_status='Completed'
                      AND ot.order_date::date BETWEEN DATE '2026-06-01' AND DATE '2026-06-30'
                    GROUP BY ot.asin, ot.sku
                ),
                vend_2025 AS (
                    SELECT vs.asin, SUM(COALESCE(vs.ordered_revenue,0)) AS vendor_sales, SUM(COALESCE(vs.ordered_units,0)) AS vendor_units
                    FROM public.vendor_sales vs JOIN assigned_asins a ON a.asin = vs.asin
                    WHERE vs.start_time::date <= DATE '2025-06-30' AND vs.end_time::date >= DATE '2025-06-01'
                    GROUP BY vs.asin
                ),
                vend_2026 AS (
                    SELECT vs.asin, SUM(COALESCE(vs.ordered_revenue,0)) AS vendor_sales, SUM(COALESCE(vs.ordered_units,0)) AS vendor_units
                    FROM public.vendor_sales vs JOIN assigned_asins a ON a.asin = vs.asin
                    WHERE vs.start_time::date <= DATE '2026-06-30' AND vs.end_time::date >= DATE '2026-06-01'
                    GROUP BY vs.asin
                )
                SELECT asin, sku,
                    SUM(fbm_sales_2025) AS fbm_sales_2025, SUM(fba_sales_2025) AS fba_sales_2025,
                    SUM(orders_2025) AS orders_2025,
                    SUM(fbm_sales_2026) AS fbm_sales_2026, SUM(fba_sales_2026) AS fba_sales_2026,
                    SUM(orders_2026) AS orders_2026
                FROM (
                    SELECT asin, sku, fbm_sales AS fbm_sales_2025, fba_sales AS fba_sales_2025, orders AS orders_2025,
                           0::numeric AS fbm_sales_2026, 0::numeric AS fba_sales_2026, 0::bigint AS orders_2026
                    FROM tx_2025
                    UNION ALL
                    SELECT asin, sku, 0, 0, 0, fbm_sales, fba_sales, orders
                    FROM tx_2026
                ) combined
                GROUP BY asin, sku
                ORDER BY asin, sku
                """
            )
            asin_sku_rows = cur.fetchall()

            cur.execute(
                """
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
                SELECT vs.asin,
                    SUM(CASE WHEN vs.start_time::date <= DATE '2025-06-30' AND vs.end_time::date >= DATE '2025-06-01'
                             THEN COALESCE(vs.ordered_revenue,0) ELSE 0 END) AS vendor_sales_2025,
                    SUM(CASE WHEN vs.start_time::date <= DATE '2025-06-30' AND vs.end_time::date >= DATE '2025-06-01'
                             THEN COALESCE(vs.ordered_units,0) ELSE 0 END) AS vendor_units_2025,
                    SUM(CASE WHEN vs.start_time::date <= DATE '2026-06-30' AND vs.end_time::date >= DATE '2026-06-01'
                             THEN COALESCE(vs.ordered_revenue,0) ELSE 0 END) AS vendor_sales_2026,
                    SUM(CASE WHEN vs.start_time::date <= DATE '2026-06-30' AND vs.end_time::date >= DATE '2026-06-01'
                             THEN COALESCE(vs.ordered_units,0) ELSE 0 END) AS vendor_units_2026
                FROM public.vendor_sales vs
                JOIN assigned_asins a ON a.asin = vs.asin
                GROUP BY vs.asin
                """
            )
            vendor_rows = cur.fetchall()

            cur.execute(
                """
                SELECT DISTINCT p.ref_id AS asin
                FROM public.ph_cate_products p
                JOIN (
                    SELECT DISTINCT c.id AS category_id FROM public.ph_categories c
                    JOIN (SELECT "user" AS user_id FROM public."user" WHERE lower(user_name) = lower('utharsika')) u
                        ON u.user_id = c.user_id
                ) tc ON tc.category_id = p.ass_cate_id
                WHERE p.which_channel = 1
                """
            )
            assigned_asins = [r[0] for r in cur.fetchall()]

    finally:
        conn.close()

    data = {
        "assigned_asins": assigned_asins,
        "asin_sku_rows": [
            {"asin": r[0], "sku": r[1], "fbm_sales_2025": float(r[2]), "fba_sales_2025": float(r[3]),
             "orders_2025": int(r[4]), "fbm_sales_2026": float(r[5]), "fba_sales_2026": float(r[6]),
             "orders_2026": int(r[7])}
            for r in asin_sku_rows
        ],
        "vendor_rows": [
            {"asin": r[0], "vendor_sales_2025": float(r[1]), "vendor_units_2025": int(r[2]),
             "vendor_sales_2026": float(r[3]), "vendor_units_2026": int(r[4])}
            for r in vendor_rows
        ],
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"Assigned ASINs: {len(assigned_asins)}")
    print(f"ASIN+SKU rows with June 2025 or 2026 activity: {len(asin_sku_rows)}")
    print(f"ASINs with any Vendor activity: {len(vendor_rows)}")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
