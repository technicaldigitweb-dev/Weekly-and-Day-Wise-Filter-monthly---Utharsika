"""
UAWSO read-only extraction v4 - Ordered Product Sales / Total Orders /
Total Quantity rules (v002 requirement), updated to the FINAL DYNAMIC
status rule (this update): include every non-null, non-blank order
status except the two cancellation variants. The included-status list
is never hardcoded - a newly-appearing status is picked up automatically
the next time this script runs, with no code change required.

Extends extract_uawso_full_coverage.py's approach (full 1723-ASIN master,
LEFT JOIN order_transaction, LEFT JOIN vendor_sales) with the REVISED
business rules:

  EXCLUDED_ORDER_STATUSES = {"Cancelled", "Canceled"} - the only two
  statuses ever excluded. Every other non-null, non-blank status is
  included automatically (see is_included_order_status() below and
  07_EVIDENCE\\2026-07-14_utharsika_v002_DYNAMIC_STATUS_FINAL_BUILD_AND_PUBLICATION.md
  for the full discovery this rule is based on - as of that discovery,
  the included set is Completed, Refunded, Deleted, New, Pending,
  Inprogress, Hold, but this code does not hardcode that list).

  Ordered Product Sales = SUM(item_price * quantity) for
    source_name='AMAZON' AND is_included_order_status(order_status).
    A same/later-month refund does NOT remove the original Sales from
    the month the order was placed (order_date is always the ORIGINAL
    order date, so grouping by order_date::date already places a
    refunded row's value back into the month it was ordered in).
    Refunded value is never deducted; order_total is never used as the
    primary Sales field.

  Total Orders = COUNT(DISTINCT order_item_info) for
    is_included_order_status(order_status) AND source_name IN ('AMAZON','REPLACEMENT').

  Total Quantity uses the SAME row-inclusion scope as Total Orders
  for FBM/FBA Quantity, plus Vendor Units (public.vendor_sales.ordered_units)
  added at the row-compute layer (client engine), not here.

Evidence for the prior (fixed seven-status) rule set: 07_EVIDENCE\\2026-07-14_utharsika_v002_SEVEN_STATUS_LOCAL_REFRESH_VALIDATION.md
Evidence for this dynamic-exclusion update: 07_EVIDENCE\\2026-07-14_utharsika_v002_DYNAMIC_STATUS_FINAL_BUILD_AND_PUBLICATION.md

Produces four local JSON files (identity-prefixed), all reads via a
read-only session, never a write method:
    <identity>_product_master_full.json  - ALL 1723 assigned ASINs, each
        with its SKU list widened to include SKUs that only appear via
        any included status (AMAZON or REPLACEMENT).
    <identity>_daily_aggregates_split.json - daily (asin, sku) grain,
        FBM/FBA split, carrying six metrics per row: fbm_sales,
        fbm_orders, fbm_quantity, fba_sales, fba_orders, fba_quantity.
    <identity>_vendor_periods.json - unchanged shape/logic from v3
        (public.vendor_sales periods, no proration - see
        extract_uawso_full_coverage.py's module docstring for why).
    <identity>_assigned_asins.json - the raw assigned-ASIN list.
"""

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.config import load_db_config, redact, ASSIGNED_USER, AMAZON_CHANNEL_CODE

EXCLUDED_ORDER_STATUSES = {"Cancelled", "Canceled"}


def is_included_order_status(value):
    """Python-side mirror of the SQL exclusion rule below - kept only for
    callers that need to test a single already-fetched status value
    in-process (e.g. ad-hoc validation scripts). The actual extraction
    queries below apply the equivalent condition directly in SQL
    (BTRIM(status) NOT IN (...)) so the database does the filtering,
    not this function."""
    if value is None:
        return False
    status = str(value).strip()
    return bool(status) and status not in EXCLUDED_ORDER_STATUSES


# The single SQL fragment used everywhere a status filter is needed -
# never duplicated or re-derived elsewhere in this file.
STATUS_FILTER_SQL = """
    ot.order_status IS NOT NULL
    AND BTRIM(ot.order_status) <> ''
    AND BTRIM(ot.order_status) NOT IN ('Cancelled', 'Canceled')
"""


def extract(history_start: date, history_end: date):
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

            # --- Full product master: ALL assigned ASINs, LEFT JOIN to
            # SKUs discovered under the dynamic exclusion-based status
            # rule (any row that counts under either the Sales rule or
            # the Orders rule, for AMAZON or REPLACEMENT source), so a
            # SKU that only ever appears via a non-Completed included
            # status is still visible as its own row.
            cur.execute(
                f"""
                WITH assigned(asin) AS (SELECT unnest(%(asins)s::text[]))
                SELECT a.asin,
                       COALESCE(array_agg(DISTINCT ot.sku) FILTER (WHERE ot.sku IS NOT NULL), ARRAY[]::text[]) AS skus
                FROM assigned a
                LEFT JOIN public.order_transaction ot
                    ON ot.asin = a.asin
                   AND ot.market_place = 'UK'
                   AND ot.source_name IN ('AMAZON', 'REPLACEMENT')
                   AND {STATUS_FILTER_SQL}
                GROUP BY a.asin
                ORDER BY a.asin
                """,
                {"asins": assigned_asins},
            )
            product_master_full = [{"asin": r[0], "skus": list(r[1])} for r in cur.fetchall()]
            with_sku = sum(1 for p in product_master_full if p["skus"])
            without_sku = sum(1 for p in product_master_full if not p["skus"])
            print(f"Product master (full, v4 widened SKU scope): {len(product_master_full)} ASINs, {with_sku} with SKU, {without_sku} without")

            # --- Daily aggregates, FBM/FBA split, Ordered Sales / Orders
            # / Quantity per the dynamic exclusion-based status rule.
            # WHERE clause pre-restricts to source_name IN
            # ('AMAZON','REPLACEMENT') AND the shared STATUS_FILTER_SQL
            # fragment (covers both the Sales rule, which further
            # restricts to AMAZON via CASE WHEN, and the Orders/Quantity
            # rule, which allows both sources).
            cur.execute(
                f"""
                SELECT
                    ot.order_date::date AS calendar_date,
                    ot.asin,
                    ot.sku,
                    SUM(CASE WHEN COALESCE(ot.fba_sales, FALSE) = FALSE
                             AND ot.source_name = 'AMAZON'
                        THEN COALESCE(ot.item_price, 0) * COALESCE(ot.quantity, 0) ELSE 0 END) AS fbm_sales,
                    COUNT(DISTINCT CASE WHEN COALESCE(ot.fba_sales, FALSE) = FALSE
                        THEN ot.order_item_info END) AS fbm_orders,
                    SUM(CASE WHEN COALESCE(ot.fba_sales, FALSE) = FALSE
                        THEN COALESCE(ot.quantity, 0) ELSE 0 END) AS fbm_quantity,
                    SUM(CASE WHEN ot.fba_sales = TRUE
                             AND ot.source_name = 'AMAZON'
                        THEN COALESCE(ot.item_price, 0) * COALESCE(ot.quantity, 0) ELSE 0 END) AS fba_sales,
                    COUNT(DISTINCT CASE WHEN ot.fba_sales = TRUE
                        THEN ot.order_item_info END) AS fba_orders,
                    SUM(CASE WHEN ot.fba_sales = TRUE
                        THEN COALESCE(ot.quantity, 0) ELSE 0 END) AS fba_quantity
                FROM public.order_transaction ot
                WHERE ot.asin = ANY(%(asins)s)
                  AND ot.market_place = 'UK'
                  AND ot.source_name IN ('AMAZON', 'REPLACEMENT')
                  AND {STATUS_FILTER_SQL}
                  AND ot.order_date::date BETWEEN %(history_start)s AND %(history_end)s
                GROUP BY ot.order_date::date, ot.asin, ot.sku
                ORDER BY calendar_date, ot.asin, ot.sku
                """,
                {"asins": assigned_asins, "history_start": history_start, "history_end": history_end},
            )
            daily_split = [
                {"calendar_date": r[0].isoformat(), "asin": r[1], "sku": r[2],
                 "fbm_sales": float(r[3]), "fbm_orders": int(r[4]), "fbm_quantity": int(r[5]),
                 "fba_sales": float(r[6]), "fba_orders": int(r[7]), "fba_quantity": int(r[8])}
                for r in cur.fetchall()
            ]
            print(f"Daily split (v4) aggregate rows: {len(daily_split)}")

            # --- Vendor periods (unchanged from v3 - see
            # extract_uawso_full_coverage.py's module docstring).
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

        return assigned_asins, product_master_full, daily_split, vendor_periods
    finally:
        conn.close()
        print("Connection closed.")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--identity", required=True)
    parser.add_argument("--history-start", required=True)
    parser.add_argument("--history-end", required=True)
    args = parser.parse_args()

    history_start = date.fromisoformat(args.history_start)
    history_end = date.fromisoformat(args.history_end)
    assigned_asins, product_master_full, daily_split, vendor_periods = extract(history_start, history_end)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "07_EVIDENCE", "generated_data")
    os.makedirs(out_dir, exist_ok=True)

    def dump(name, data):
        path = os.path.join(out_dir, f"{args.identity}_{name}.json")
        with open(path, "wb") as f:
            f.write(json.dumps(data, separators=(",", ":")).encode("utf-8"))
        print(f"Wrote {path} ({os.path.getsize(path)} bytes)")

    dump("assigned_asins", assigned_asins)
    dump("product_master_full", product_master_full)
    dump("daily_aggregates_split", daily_split)
    dump("vendor_periods", vendor_periods)


if __name__ == "__main__":
    main()
