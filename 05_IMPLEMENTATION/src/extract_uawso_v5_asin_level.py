"""
UAWSO read-only extraction v5 - TRUE ASIN-LEVEL grain (REQ-02-D01).

Replaces the ASIN+SKU visible row grain with one row per ASIN, replaces
the SKU column with a deterministically-selected product image, and
computes Orders directly at (date, ASIN) grain rather than summing
(date, ASIN, SKU) partitions up to the ASIN level - see
03_DISCOVERY\\2026-07-15_uawso_REQ-01-D03_image_and_asin_orders_discovery.md
Section 8 for why grouping directly at the source (not just hiding the
SKU column) is required to structurally close the double-count risk.

Business rules (01_REQUIREMENTS\\Requirement\\2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md):
  Row grain: one row per assigned ASIN. SKU is not part of the grain,
    the SQL grouping, or any output field.
  Sales = SUM(item_price * quantity) for source_name='AMAZON' AND
    is_included_order_status(order_status), aggregated directly per
    (date, ASIN) - all SKU activity under an ASIN lands in the same row.
  Orders = COUNT(DISTINCT order_item_info) for is_included_order_status
    AND source_name = 'AMAZON' ONLY, grouped directly by (date, ASIN) -
    never grouped by SKU first and summed. REPLACEMENT-source rows do
    NOT contribute to Orders (2026-07-16 business-rule update - see
    01_REQUIREMENTS\\Requirement Updates\\2026-07-16_satheskanth_REQ-UAWSO_REQ-02-D01_amazon_only_orders_update.md
    - a real ASIN-level discrepancy for B0FX2XDLT5, June 2026, traced a
    non-cancelled REPLACEMENT row to an incorrect 17th Order where 16 was
    correct; the cancellation filter itself was proven correct). Total
    Orders = FBM Orders + FBA Orders + Vendor Orders (Vendor Orders =
    ordered_units directly - one Vendor Unit = one Vendor Order),
    computed at the row-compute layer (client engine) - see the
    2026-07-15 same-day amendment, REQ-02-D01 Section 3.2.
  Quantity is NOT part of this deliverable (removed by the 2026-07-15
    same-day amendment, REQ-02-D01 Section 3.2 - the report shows Sales
    and Orders only). This script still reads fbm_quantity/fba_quantity
    from public.order_transaction into daily_aggregates_asin.json for
    backward-compatible JSON shape only; the client engine (v5 functions
    in uawso_client_engine.js) no longer consumes those two fields.
  Image: public.listing_data.ref_id = ASIN, which_channel=1,
    market_place='UK', wrong_sku=0, main_image_url IS NOT NULL AND
    BTRIM(main_image_url) <> ''. When more than one valid row remains,
    the row with the LOWEST listing_data.id is selected deterministically
    (ROW_NUMBER() OVER (PARTITION BY ref_id ORDER BY id ASC) = 1 - never
    an unordered LIMIT 1). Business-confirmed (Utharsika, REQ-02-D01
    Section 5): any valid image under the ASIN is acceptable: the lowest-id
    rule exists only for run-to-run stability, not image quality.
  Status rule: identical dynamic exclusion rule as extract_uawso_v4_ordered_sales.py
    (EXCLUDED_ORDER_STATUSES = {"Cancelled", "Canceled"}), unchanged.

Produces four local JSON files (identity-prefixed), all reads via a
read-only session, never a write method:
    <identity>_assigned_asins.json          - the raw assigned-ASIN list.
    <identity>_product_master_asin_level.json - one row per assigned ASIN:
        {asin, image_url, product_title}. image_url/product_title are
        null when no valid filtered listing_data row exists.
    <identity>_daily_aggregates_asin.json   - daily ASIN grain (NOT
        asin+sku), FBM/FBA split, six metrics per row: fbm_sales,
        fbm_orders, fbm_quantity, fba_sales, fba_orders, fba_quantity.
    <identity>_vendor_periods.json          - unchanged shape/logic from
        v3/v4 (public.vendor_sales periods, no proration).

Does not modify extract_uawso_v4_ordered_sales.py or any file it
produces - this is a new, additive script for the ASIN-level report.
"""

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.config import load_db_config, redact, ASSIGNED_USER, AMAZON_CHANNEL_CODE

EXCLUDED_ORDER_STATUSES = {"Cancelled", "Canceled"}


def is_included_order_status(value):
    """Python-side mirror of the SQL exclusion rule below - see
    extract_uawso_v4_ordered_sales.py's identical helper for rationale."""
    if value is None:
        return False
    status = str(value).strip()
    return bool(status) and status not in EXCLUDED_ORDER_STATUSES


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
            # --- Assigned ASIN scope (DISTINCT, duplicate-assignment-row guard) ---
            cur.execute(
                """
                WITH target_user AS (
                    SELECT "user" AS user_id FROM public."user" WHERE lower(user_name) = lower(%(assigned_user)s)
                ),
                target_categories AS (
                    SELECT DISTINCT c.id AS category_id FROM public.ph_categories c JOIN target_user u ON u.user_id = c.user_id
                ),
                raw_assign AS (
                    SELECT p.ref_id AS asin, COUNT(*) AS row_count
                    FROM public.ph_cate_products p
                    JOIN target_categories c ON c.category_id = p.ass_cate_id
                    WHERE p.which_channel = %(channel_code)s
                    GROUP BY p.ref_id
                )
                SELECT asin, row_count FROM raw_assign ORDER BY asin
                """,
                {"assigned_user": ASSIGNED_USER, "channel_code": AMAZON_CHANNEL_CODE},
            )
            raw_rows = cur.fetchall()
            duplicate_assignment_asins = [r[0] for r in raw_rows if r[1] > 1]
            if duplicate_assignment_asins:
                raise RuntimeError(
                    "STOP: assignment join would multiply transactions - "
                    f"{len(duplicate_assignment_asins)} ASIN(s) have more than one "
                    f"assignment row: {duplicate_assignment_asins[:20]}"
                )
            assigned_asins = sorted(r[0] for r in raw_rows)
            print(f"Assigned ASIN count: {len(assigned_asins)} (duplicate assignment rows: 0)")
            if not assigned_asins:
                raise RuntimeError("Assigned-ASIN resolution returned zero ASINs - refusing to proceed.")

            # --- Product master, ASIN-level grain, deterministic image ---
            cur.execute(
                """
                WITH assigned(asin) AS (SELECT unnest(%(asins)s::text[])),
                filtered AS (
                    SELECT ref_id AS asin, id, main_image_url, title,
                           ROW_NUMBER() OVER (PARTITION BY ref_id ORDER BY id ASC) AS rn
                    FROM public.listing_data
                    WHERE which_channel = 1 AND market_place = 'UK' AND wrong_sku = 0
                      AND main_image_url IS NOT NULL AND BTRIM(main_image_url) <> ''
                )
                SELECT a.asin, f.main_image_url AS image_url, f.title AS product_title
                FROM assigned a
                LEFT JOIN filtered f ON f.asin = a.asin AND f.rn = 1
                ORDER BY a.asin
                """,
                {"asins": assigned_asins},
            )
            product_master_asin_level = [
                {"asin": r[0], "image_url": r[1], "product_title": r[2]} for r in cur.fetchall()
            ]
            with_image = sum(1 for p in product_master_asin_level if p["image_url"])
            print(f"Product master (v5, ASIN-level): {len(product_master_asin_level)} ASINs, {with_image} with a usable image, {len(product_master_asin_level) - with_image} without")

            # --- Daily aggregates, grouped DIRECTLY by (date, ASIN) - not
            # (date, ASIN, SKU) then summed. This is the structural fix for
            # the double-count risk flagged in the REQ-01-D03 discovery. ---
            cur.execute(
                f"""
                SELECT
                    ot.order_date::date AS calendar_date,
                    ot.asin,
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
                  AND ot.source_name = 'AMAZON'
                  AND {STATUS_FILTER_SQL}
                  AND ot.order_date::date BETWEEN %(history_start)s AND %(history_end)s
                GROUP BY ot.order_date::date, ot.asin
                ORDER BY calendar_date, ot.asin
                """,
                {"asins": assigned_asins, "history_start": history_start, "history_end": history_end},
            )
            daily_asin = [
                {"calendar_date": r[0].isoformat(), "asin": r[1],
                 "fbm_sales": float(r[2]), "fbm_orders": int(r[3]), "fbm_quantity": int(r[4]),
                 "fba_sales": float(r[5]), "fba_orders": int(r[6]), "fba_quantity": int(r[7])}
                for r in cur.fetchall()
            ]
            print(f"Daily ASIN-grain aggregate rows: {len(daily_asin)}")

            # --- Vendor periods (unchanged shape/logic from v3/v4) ---
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

        return assigned_asins, product_master_asin_level, daily_asin, vendor_periods
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
    assigned_asins, product_master_asin_level, daily_asin, vendor_periods = extract(history_start, history_end)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "07_EVIDENCE", "generated_data")
    os.makedirs(out_dir, exist_ok=True)

    def dump(name, data):
        path = os.path.join(out_dir, f"{args.identity}_{name}.json")
        with open(path, "wb") as f:
            f.write(json.dumps(data, separators=(",", ":")).encode("utf-8"))
        print(f"Wrote {path} ({os.path.getsize(path)} bytes)")

    dump("assigned_asins", assigned_asins)
    dump("product_master_asin_level", product_master_asin_level)
    dump("daily_aggregates_asin", daily_asin)
    dump("vendor_periods", vendor_periods)


if __name__ == "__main__":
    main()
