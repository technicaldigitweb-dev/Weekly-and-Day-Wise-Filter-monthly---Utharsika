"""
UAWSO read-only extraction v2 - full ASIN coverage + FBM/FBA/Vendor split.

Extends extract_uawso_daily_aggregates.py (kept unmodified/historical) to
satisfy the "start from the complete assigned-ASIN master, LEFT JOIN
order_transaction, LEFT JOIN vendor_sales" requirement, per
07_EVIDENCE/2026-07-10_utharsika_ASIN_SCOPE_VALIDATION.md and
07_EVIDENCE/2026-07-10_utharsika_VENDOR_SALES_VALIDATION.md.

Produces three local JSON files, all reads via a read-only session,
never a write method:
    <identity>_product_master_full.json  - ALL 1723 assigned ASINs, each
        with its known SKU list (possibly empty - 113 ASINs have none)
    <identity>_daily_aggregates_split.json - daily (asin, sku) grain,
        FBM and FBA split via fba_sales, from order_transaction
    <identity>_vendor_periods.json - vendor_sales rows for assigned ASINs,
        kept as (asin, start_date, end_date, revenue, units) PERIODS,
        not forced into daily buckets - see note below.

IMPORTANT - why vendor_sales is NOT bucketed into daily rows:
vendor_sales rows have a mix of granularities (~86% are ~1-hour "daily"
markers, ~14% are full-month periods, confirmed by inspecting
EXTRACT(EPOCH FROM (end_time-start_time)) this session). Forcing a
monthly row into a single calendar day would silently overstate that
one day and understate the rest of the month - a real correctness bug.
Instead, vendor periods are kept as ranges; the client engine allocates
a period's full revenue/units to any selected range it OVERLAPS with
(no proration), and this is documented as a known limitation of the
source data, not invented away.
"""

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.config import load_db_config, redact, ASSIGNED_USER, AMAZON_CHANNEL_CODE

HISTORY_START = date(2025, 1, 1)


def extract(history_end: date):
    import psycopg2

    cfg = load_db_config()
    print(f"Connecting to host={cfg.host} port={cfg.port} db={cfg.dbname} user={cfg.user} password={redact(cfg.password)}")
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user, password=cfg.password, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    print("Connected (read-only session).")

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH target_user AS (
                    SELECT "user" AS user_id FROM public."user" WHERE lower(user_name) = lower(%(assigned_user)s)
                ),
                target_categories AS (
                    SELECT DISTINCT c.id AS category_id FROM public.ph_categories c JOIN target_user u ON u.user_id = c.user_id
                )
                SELECT DISTINCT p.ref_id AS asin
                FROM public.ph_cate_products p
                JOIN target_categories c ON c.category_id = p.ass_cate_id
                WHERE p.which_channel = %(channel_code)s
                """,
                {"assigned_user": ASSIGNED_USER, "channel_code": AMAZON_CHANNEL_CODE},
            )
            assigned_asins = sorted(r[0] for r in cur.fetchall())
            print(f"Assigned ASIN count: {len(assigned_asins)}")
            if not assigned_asins:
                raise RuntimeError("Assigned-ASIN resolution returned zero ASINs - refusing to proceed.")

            # --- Full product master: ALL assigned ASINs, LEFT JOIN to their
            # known SKUs (empty list for ASINs with no qualifying transaction).
            cur.execute(
                """
                WITH assigned(asin) AS (SELECT unnest(%(asins)s::text[]))
                SELECT a.asin,
                       COALESCE(array_agg(DISTINCT ot.sku) FILTER (WHERE ot.sku IS NOT NULL), ARRAY[]::text[]) AS skus
                FROM assigned a
                LEFT JOIN public.order_transaction ot
                    ON ot.asin = a.asin
                   AND ot.source_name = 'AMAZON' AND ot.market_place = 'UK' AND ot.order_status = 'Completed'
                GROUP BY a.asin
                ORDER BY a.asin
                """,
                {"asins": assigned_asins},
            )
            product_master_full = [{"asin": r[0], "skus": list(r[1])} for r in cur.fetchall()]
            with_sku = sum(1 for p in product_master_full if p["skus"])
            without_sku = sum(1 for p in product_master_full if not p["skus"])
            print(f"Product master (full): {len(product_master_full)} ASINs, {with_sku} with SKU, {without_sku} without")

            # --- Daily aggregates, FBM/FBA split via fba_sales.
            cur.execute(
                """
                SELECT
                    ot.order_date::date AS calendar_date,
                    ot.asin,
                    ot.sku,
                    SUM(CASE WHEN COALESCE(ot.fba_sales, FALSE) = FALSE THEN COALESCE(ot.order_total, 0) ELSE 0 END) AS fbm_sales,
                    COUNT(DISTINCT CASE WHEN COALESCE(ot.fba_sales, FALSE) = FALSE THEN ot.order_item_info END) AS fbm_orders,
                    SUM(CASE WHEN ot.fba_sales = TRUE THEN COALESCE(ot.order_total, 0) ELSE 0 END) AS fba_sales,
                    COUNT(DISTINCT CASE WHEN ot.fba_sales = TRUE THEN ot.order_item_info END) AS fba_orders
                FROM public.order_transaction ot
                WHERE ot.asin = ANY(%(asins)s)
                  AND ot.source_name = 'AMAZON' AND ot.market_place = 'UK' AND ot.order_status = 'Completed'
                  AND ot.order_date::date BETWEEN %(history_start)s AND %(history_end)s
                GROUP BY ot.order_date::date, ot.asin, ot.sku
                ORDER BY calendar_date, ot.asin, ot.sku
                """,
                {"asins": assigned_asins, "history_start": HISTORY_START, "history_end": history_end},
            )
            daily_split = [
                {"calendar_date": r[0].isoformat(), "asin": r[1], "sku": r[2],
                 "fbm_sales": float(r[3]), "fbm_orders": int(r[4]),
                 "fba_sales": float(r[5]), "fba_orders": int(r[6])}
                for r in cur.fetchall()
            ]
            print(f"Daily split aggregate rows: {len(daily_split)}")

            # --- Vendor periods (kept as ranges - see module docstring).
            cur.execute(
                """
                SELECT asin, start_time::date AS start_date, end_time::date AS end_date,
                       COALESCE(ordered_revenue, 0) AS revenue, COALESCE(ordered_units, 0) AS units
                FROM public.vendor_sales
                WHERE asin = ANY(%(asins)s)
                ORDER BY asin, start_date
                """,
                {"asins": assigned_asins},
            )
            vendor_periods = [
                {"asin": r[0], "start_date": r[1].isoformat(), "end_date": r[2].isoformat(),
                 "revenue": float(r[3]), "units": int(r[4])}
                for r in cur.fetchall()
            ]
            print(f"Vendor period rows: {len(vendor_periods)}, ASINs with vendor data: {len(set(v['asin'] for v in vendor_periods))}")

        return product_master_full, daily_split, vendor_periods
    finally:
        conn.close()
        print("Connection closed.")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--identity", required=True)
    parser.add_argument("--history-end", required=True)
    args = parser.parse_args()

    history_end = date.fromisoformat(args.history_end)
    product_master_full, daily_split, vendor_periods = extract(history_end)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "07_EVIDENCE", "generated_data")
    os.makedirs(out_dir, exist_ok=True)

    def dump(name, data):
        path = os.path.join(out_dir, f"{args.identity}_{name}.json")
        with open(path, "wb") as f:
            f.write(json.dumps(data, separators=(",", ":")).encode("utf-8"))
        print(f"Wrote {path} ({os.path.getsize(path)} bytes)")

    dump("product_master_full", product_master_full)
    dump("daily_aggregates_split", daily_split)
    dump("vendor_periods", vendor_periods)


if __name__ == "__main__":
    main()
