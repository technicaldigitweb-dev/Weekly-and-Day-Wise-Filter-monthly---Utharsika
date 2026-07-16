"""
UAWSO read-only daily aggregate extraction (Stage B credential-based path).

Used when the approved MCP-connected read-only tool cannot reliably
return a dataset this large (confirmed this session: the full
2025-01-01..2026-07-09 daily grain is 28,601 rows - too large to
transcribe through a chat interface). This script connects directly
via psycopg2, using env-var-only credentials (never hardcoded here),
runs READ-ONLY queries, and writes the result straight to local JSON
files - the data never passes through an LLM context window.

Usage:
    PGHOST=... PGPORT=... PGDATABASE=... PGUSER=... PGPASSWORD=... \
        python src/extract_uawso_daily_aggregates.py

Produces:
    07_EVIDENCE/generated_data/<identity>_product_master.json
    07_EVIDENCE/generated_data/<identity>_daily_aggregates.json

Never writes to the database. Never prints or logs credential values.
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
            # Step 1: resolve Utharsika's assigned ASINs (same logic as sql/01_resolve_assigned_asins.sql)
            cur.execute(
                """
                WITH target_user AS (
                    SELECT "user" AS user_id FROM public."user" WHERE lower(user_name) = lower(%(assigned_user)s)
                ),
                target_categories AS (
                    SELECT c.id AS category_id FROM public.ph_categories c JOIN target_user u ON u.user_id = c.user_id
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

            # Step 2: product master - all distinct (asin, sku) pairs ever seen for
            # these ASINs in the approved Amazon UK Completed scope (any date - this
            # defines "matching SKU", independent of the embedded history window).
            cur.execute(
                """
                SELECT DISTINCT ot.asin, ot.sku
                FROM public.order_transaction ot
                WHERE ot.asin = ANY(%(asins)s)
                  AND ot.source_name = 'AMAZON'
                  AND ot.market_place = 'UK'
                  AND ot.order_status = 'Completed'
                ORDER BY ot.asin, ot.sku
                """,
                {"asins": assigned_asins},
            )
            product_master = [{"asin": r[0], "sku": r[1]} for r in cur.fetchall()]
            print(f"Product master (assigned ASIN x matching SKU) rows: {len(product_master)}")

            # Step 3: daily aggregate grain - calendar_date, asin, sku, sales_total, orders_total
            cur.execute(
                """
                SELECT
                    ot.order_date::date AS calendar_date,
                    ot.asin,
                    ot.sku,
                    SUM(COALESCE(ot.order_total, 0)) AS sales_total,
                    COUNT(DISTINCT ot.order_item_info) AS orders_total
                FROM public.order_transaction ot
                WHERE ot.asin = ANY(%(asins)s)
                  AND ot.source_name = 'AMAZON'
                  AND ot.market_place = 'UK'
                  AND ot.order_status = 'Completed'
                  AND ot.order_date::date BETWEEN %(history_start)s AND %(history_end)s
                GROUP BY ot.order_date::date, ot.asin, ot.sku
                ORDER BY calendar_date, ot.asin, ot.sku
                """,
                {"asins": assigned_asins, "history_start": HISTORY_START, "history_end": history_end},
            )
            daily_aggregates = [
                {"calendar_date": r[0].isoformat(), "asin": r[1], "sku": r[2],
                 "sales_total": float(r[3]), "orders_total": int(r[4])}
                for r in cur.fetchall()
            ]
            print(f"Daily aggregate rows: {len(daily_aggregates)}")
            print(f"Date range in result: {daily_aggregates[0]['calendar_date'] if daily_aggregates else 'N/A'} "
                  f"to {daily_aggregates[-1]['calendar_date'] if daily_aggregates else 'N/A'}")

        return assigned_asins, product_master, daily_aggregates
    finally:
        conn.close()
        print("Connection closed.")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--identity", required=True, help="e.g. 2026-07-10_utharsika_v001")
    parser.add_argument("--history-end", required=True, help="YYYY-MM-DD, e.g. 2026-07-09")
    args = parser.parse_args()

    history_end = date.fromisoformat(args.history_end)
    assigned_asins, product_master, daily_aggregates = extract(history_end)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "07_EVIDENCE", "generated_data")
    os.makedirs(out_dir, exist_ok=True)

    pm_path = os.path.join(out_dir, f"{args.identity}_product_master.json")
    with open(pm_path, "wb") as f:
        f.write(json.dumps(product_master, indent=None, separators=(",", ":")).encode("utf-8"))

    da_path = os.path.join(out_dir, f"{args.identity}_daily_aggregates.json")
    with open(da_path, "wb") as f:
        f.write(json.dumps(daily_aggregates, indent=None, separators=(",", ":")).encode("utf-8"))

    print(f"Wrote {pm_path} ({os.path.getsize(pm_path)} bytes)")
    print(f"Wrote {da_path} ({os.path.getsize(da_path)} bytes)")
    print(f"Assigned ASIN count: {len(assigned_asins)}")

    # Also persist the assigned ASIN list itself for evidence/traceability
    asins_path = os.path.join(out_dir, f"{args.identity}_assigned_asins.json")
    with open(asins_path, "wb") as f:
        f.write(json.dumps(assigned_asins, indent=None, separators=(",", ":")).encode("utf-8"))
    print(f"Wrote {asins_path} ({os.path.getsize(asins_path)} bytes)")


if __name__ == "__main__":
    main()
