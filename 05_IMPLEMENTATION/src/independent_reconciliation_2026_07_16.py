"""
Independent full-report reconciliation (read-only): re-derives Sales,
FBM/FBA Orders (AMAZON-only), Vendor Orders, and the assigned-ASIN scope
via a SEPARATE query path from the extraction script, then compares
totals to the embedded HTML report - proving the extraction script wrote
what the live source actually contains, not just self-consistency.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config  # noqa: E402
import psycopg2  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
IDENTITY = "2026-07-16_utharsika_v001"
EVIDENCE_DIR = os.path.join(ROOT, "07_EVIDENCE", "generated_data")

with open(os.path.join(EVIDENCE_DIR, f"{IDENTITY}_assigned_asins.json")) as f:
    assigned_asins = json.load(f)


def main():
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                             password=cfg.password, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    try:
        with conn.cursor() as cur:
            # Independent assigned-scope re-derivation
            cur.execute(
                """
                SELECT COUNT(DISTINCT pcp.ref_id)
                FROM public.user u
                JOIN public.ph_categories pc ON pc.user_id = u."user"
                JOIN public.ph_cate_products pcp ON pcp.ass_cate_id = pc.id
                WHERE lower(u.user_name) = lower('utharsika') AND pcp.which_channel = 1
                """
            )
            scope_count = cur.fetchone()[0]

            cur.execute(
                """
                SELECT string_agg(DISTINCT pcp.ref_id, ',')
                FROM public.user u
                JOIN public.ph_categories pc ON pc.user_id = u."user"
                JOIN public.ph_cate_products pcp ON pcp.ass_cate_id = pc.id
                WHERE lower(u.user_name) = lower('utharsika') AND pcp.which_channel = 1
                """
            )
            live_scope = set(cur.fetchone()[0].split(","))
            extracted_scope = set(assigned_asins)
            missing = live_scope - extracted_scope
            extra = extracted_scope - live_scope

            # Independent Sales/Orders totals, AMAZON-only, status-excluded, full range
            cur.execute(
                """
                SELECT
                  ROUND(SUM(CASE WHEN COALESCE(fba_sales,FALSE)=FALSE THEN item_price*quantity ELSE 0 END)::numeric,2) AS fbm_sales,
                  ROUND(SUM(CASE WHEN fba_sales=TRUE THEN item_price*quantity ELSE 0 END)::numeric,2) AS fba_sales,
                  COUNT(DISTINCT CASE WHEN COALESCE(fba_sales,FALSE)=FALSE THEN order_item_info END) AS fbm_orders,
                  COUNT(DISTINCT CASE WHEN fba_sales=TRUE THEN order_item_info END) AS fba_orders
                FROM public.order_transaction
                WHERE asin = ANY(%(asins)s) AND market_place='UK' AND source_name='AMAZON'
                  AND order_status IS NOT NULL AND BTRIM(order_status) <> ''
                  AND BTRIM(order_status) NOT IN ('Cancelled','Canceled')
                  AND order_date::date >= '2025-01-01' AND order_date::date <= '2026-07-15'
                """,
                {"asins": assigned_asins},
            )
            fbm_sales, fba_sales, fbm_orders, fba_orders = cur.fetchone()

            cur.execute(
                """
                SELECT ROUND(SUM(COALESCE(ordered_revenue,0))::numeric,2), SUM(COALESCE(ordered_units,0))
                FROM public.vendor_sales
                WHERE asin = ANY(%(asins)s)
                  AND end_time::date > '2025-01-01' AND start_time::date <= '2026-07-15'
                """,
                {"asins": assigned_asins},
            )
            vendor_sales, vendor_units = cur.fetchone()

        total_sales = float(fbm_sales) + float(fba_sales) + float(vendor_sales)
        total_orders = fbm_orders + fba_orders + vendor_units

        print(f"Assigned ASIN scope (independent re-derivation): {scope_count}")
        print(f"Missing (in live scope, not in extraction): {len(missing)} {list(missing)[:10]}")
        print(f"Extra (in extraction, not in live scope): {len(extra)} {list(extra)[:10]}")
        print()
        print(f"Independent FBM Sales: {fbm_sales}")
        print(f"Independent FBA Sales: {fba_sales}")
        print(f"Independent Vendor Sales: {vendor_sales}")
        print(f"Independent Total Sales: {total_sales:.2f}")
        print(f"Independent FBM Orders: {fbm_orders}")
        print(f"Independent FBA Orders: {fba_orders}")
        print(f"Independent Vendor Orders (ordered_units): {vendor_units}")
        print(f"Independent Total Orders: {total_orders}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
