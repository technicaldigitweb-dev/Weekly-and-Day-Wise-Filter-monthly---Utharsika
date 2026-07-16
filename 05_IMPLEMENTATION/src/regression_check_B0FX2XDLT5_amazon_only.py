"""
Focused regression check (read-only): confirms the corrected AMAZON-only
Orders SQL (matching the updated extract_uawso_v5_asin_level.py query)
reproduces the business-confirmed B0FX2XDLT5 June 2026 figures, and that
the specific REPLACEMENT row (order_item_info=1177733) is excluded.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config  # noqa: E402
import psycopg2  # noqa: E402

ASIN = "B0FX2XDLT5"


def main():
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                             password=cfg.password, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    try:
        with conn.cursor() as cur:
            # Same shape as the corrected extraction query, restricted to this ASIN/month
            cur.execute(
                """
                SELECT
                    COUNT(DISTINCT CASE WHEN COALESCE(fba_sales, FALSE) = FALSE THEN order_item_info END) AS fbm_orders,
                    COUNT(DISTINCT CASE WHEN fba_sales = TRUE THEN order_item_info END) AS fba_orders,
                    COUNT(DISTINCT order_item_info) AS total_orders,
                    bool_or(order_item_info = 1177733) AS replacement_row_present
                FROM public.order_transaction
                WHERE asin = %(asin)s
                  AND market_place = 'UK'
                  AND source_name = 'AMAZON'
                  AND order_status IS NOT NULL
                  AND BTRIM(order_status) <> ''
                  AND BTRIM(order_status) NOT IN ('Cancelled', 'Canceled')
                  AND order_date::date >= '2026-06-01' AND order_date::date < '2026-07-01'
                """,
                {"asin": ASIN},
            )
            fbm_orders, fba_orders, total_orders, replacement_present = cur.fetchone()

            cur.execute(
                """
                SELECT COUNT(DISTINCT order_item_info) AS raw_amazon,
                       COUNT(DISTINCT CASE WHEN BTRIM(order_status) IN ('Cancelled','Canceled') THEN order_item_info END) AS cancelled_count
                FROM public.order_transaction
                WHERE asin = %(asin)s AND market_place = 'UK' AND source_name = 'AMAZON'
                  AND order_date::date >= '2026-06-01' AND order_date::date < '2026-07-01'
                """,
                {"asin": ASIN},
            )
            raw_amazon, cancelled_count = cur.fetchone()

        print(f"Raw AMAZON distinct order items: {raw_amazon} (expected 17)")
        print(f"Cancelled AMAZON order items: {cancelled_count} (expected 1)")
        print(f"Valid FBM Orders: {fbm_orders} (expected 14)")
        print(f"Valid FBA Orders: {fba_orders} (expected 2)")
        print(f"Valid Amazon Orders (total): {total_orders} (expected 16)")
        print(f"REPLACEMENT row 1177733 present in AMAZON-only result: {replacement_present} (expected False/None)")

        ok = (raw_amazon == 17 and cancelled_count == 1 and fbm_orders == 14
              and fba_orders == 2 and total_orders == 16 and not replacement_present)
        print(f"\nREGRESSION CHECK: {'PASS' if ok else 'FAIL'}")
        if not ok:
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
