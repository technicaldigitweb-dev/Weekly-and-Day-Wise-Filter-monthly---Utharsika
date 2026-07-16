"""
Read-only validation of 02_SOURCE/user_provided/2026-07-14_utharsika_june_kpi_reference_b02.csv
against PostgreSQL, for June 2025 and June 2026, at 4 match levels per row.
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


ROWS = [
    {"asin": "B084RC5DQG", "account": "Ledsone", "sku": "LASGSABL+LSFRYBS", "mapped_sku": "LSGD280AR+SCRN70YB",
     "ref_2025_sales": 0, "ref_2025_orders": 0, "ref_2026_sales": 0, "ref_2026_orders": 0},
    {"asin": "B0GY3G4S1F", "account": "DCvoltage", "sku": "LSGL7512CL3PK+RPM40WH3PK", "mapped_sku": "LSGL1275CL3PK+RPM40WH3PK",
     "ref_2025_sales": 0, "ref_2025_orders": 0, "ref_2026_sales": 21.89, "ref_2026_orders": 1},
    {"asin": "B0GY423LQJ", "account": "DCvoltage", "sku": "LSGL9015CL2PK+RPM40WH2PK", "mapped_sku": None,
     "ref_2025_sales": 0, "ref_2025_orders": 0, "ref_2026_sales": 25.78, "ref_2026_orders": 2},
    {"asin": "B0H38YJTN8", "account": "DCvoltage", "sku": "LSGL9015GY2PK+RPM40WH2PK", "mapped_sku": None,
     "ref_2025_sales": 0, "ref_2025_orders": 0, "ref_2026_sales": 94.45, "ref_2026_orders": 4},
    {"asin": "B0H393YSKV", "account": "DCvoltage", "sku": "LSGL9015GY3PK+RPM40WH3PK", "mapped_sku": None,
     "ref_2025_sales": 0, "ref_2025_orders": 0, "ref_2026_sales": 57.78, "ref_2026_orders": 2},
    {"asin": "B0H3918NPV", "account": "DCvoltage", "sku": "LSGL9015GY5PK+RPM40WH5PK", "mapped_sku": None,
     "ref_2025_sales": 0, "ref_2025_orders": 0, "ref_2026_sales": 45.89, "ref_2026_orders": 1},
    {"asin": "B0D9Q142ZZ", "account": "Ledsone", "sku": "LSGLBC150CO2PK", "mapped_sku": "LSGLBG145AR+RPM40WH",
     "ref_2025_sales": 0, "ref_2025_orders": 0, "ref_2026_sales": 0, "ref_2026_orders": 0},
]

PERIODS = {"2025": ("2025-06-01", "2025-06-30"), "2026": ("2026-06-01", "2026-06-30")}

results = {"asin_all_data": {}, "account_landscape": {}, "matches": []}

# ---- Account landscape: all distinct ss_name/source_name/status for these ASINs, all time
asins = [r["asin"] for r in ROWS]
account_landscape = q(
    """
    SELECT asin, ss_name, source_name, order_status, COUNT(*) AS row_count,
           MIN(order_date) AS first_tx, MAX(order_date) AS latest_tx
    FROM public.order_transaction
    WHERE asin = ANY(%(asins)s)
    GROUP BY asin, ss_name, source_name, order_status
    ORDER BY asin, ss_name
    """,
    {"asins": asins},
)
results["account_landscape"] = account_landscape

# ---- All SKUs per ASIN (all time, any status/source) for diagnostic context
all_skus = q(
    """
    SELECT asin, sku, COUNT(*) AS row_count
    FROM public.order_transaction
    WHERE asin = ANY(%(asins)s)
    GROUP BY asin, sku
    ORDER BY asin, sku
    """,
    {"asins": asins},
)
results["all_skus_per_asin"] = all_skus


def metrics_query(where_extra, params):
    sql = f"""
        SELECT
            SUM(CASE WHEN COALESCE(fba_sales,FALSE)=FALSE AND source_name='AMAZON' AND order_status IN ('Completed','Refunded')
                     THEN COALESCE(item_price,0)*COALESCE(quantity,0) ELSE 0 END) AS fbm_sales,
            SUM(CASE WHEN fba_sales=TRUE AND source_name='AMAZON' AND order_status IN ('Completed','Refunded')
                     THEN COALESCE(item_price,0)*COALESCE(quantity,0) ELSE 0 END) AS fba_sales,
            COUNT(DISTINCT CASE WHEN COALESCE(fba_sales,FALSE)=FALSE AND order_status='Completed' AND source_name IN ('AMAZON','REPLACEMENT')
                     THEN order_item_info END) AS fbm_orders,
            COUNT(DISTINCT CASE WHEN fba_sales=TRUE AND order_status='Completed' AND source_name IN ('AMAZON','REPLACEMENT')
                     THEN order_item_info END) AS fba_orders,
            SUM(CASE WHEN COALESCE(fba_sales,FALSE)=FALSE AND order_status='Completed' AND source_name IN ('AMAZON','REPLACEMENT')
                     THEN COALESCE(quantity,0) ELSE 0 END) AS fbm_quantity,
            SUM(CASE WHEN fba_sales=TRUE AND order_status='Completed' AND source_name IN ('AMAZON','REPLACEMENT')
                     THEN COALESCE(quantity,0) ELSE 0 END) AS fba_quantity,
            COUNT(*) FILTER (WHERE order_status='Refunded' AND source_name='AMAZON') AS refunded_row_count,
            SUM(CASE WHEN order_status='Refunded' AND source_name='AMAZON' THEN COALESCE(item_price,0)*COALESCE(quantity,0) ELSE 0 END) AS refunded_original_sales,
            COUNT(*) FILTER (WHERE order_status='Completed' AND source_name='REPLACEMENT') AS completed_replacement_count,
            COUNT(*) FILTER (WHERE order_status IN ('Cancelled','Canceled')) AS cancelled_row_count,
            SUM(CASE WHEN order_status IN ('Cancelled','Canceled') THEN COALESCE(item_price,0)*COALESCE(quantity,0) ELSE 0 END) AS excluded_cancelled_value
        FROM public.order_transaction
        WHERE market_place='UK'
          AND order_date::date >= %(start)s AND order_date::date <= %(end)s
          {where_extra}
    """
    r = q(sql, params)[0]
    for k in r:
        if r[k] is None:
            r[k] = 0
    r["amazon_sales"] = float(r["fbm_sales"]) + float(r["fba_sales"])
    r["total_orders"] = int(r["fbm_orders"]) + int(r["fba_orders"])
    r["total_quantity"] = int(r["fbm_quantity"]) + int(r["fba_quantity"])
    return r


def account_ss_names(account_label):
    # Documented normalization: strip "amazon " prefix, trim, case-insensitive.
    # Do NOT merge different accounts based on similarity - only look up the
    # actual ss_name values that normalize to this label.
    norm = account_label.strip().lower()
    matches = set()
    for row in account_landscape:
        ss = (row["ss_name"] or "").strip()
        ss_norm = ss.lower()
        if ss_norm == ("amazon " + norm) or ss_norm == norm:
            matches.add(row["ss_name"])
    return sorted(matches)


for ref in ROWS:
    asin, account, sku, mapped_sku = ref["asin"], ref["account"], ref["sku"], ref["mapped_sku"]
    matched_ss_names = account_ss_names(account)

    row_result = {"ref": ref, "matched_ss_names": matched_ss_names}

    for yr, (start, end) in PERIODS.items():
        # Match 1: exact ASIN + ACCOUNT + SKU
        m1 = metrics_query(
            "AND asin=%(asin)s AND sku=%(sku)s AND ss_name = ANY(%(ss_names)s)",
            {"start": start, "end": end, "asin": asin, "sku": sku, "ss_names": matched_ss_names or [""]},
        )
        row_result[f"match1_{yr}"] = m1

        # Match 2: ASIN + ACCOUNT + Mapped SKU (only if mapped sku present)
        if mapped_sku:
            m2 = metrics_query(
                "AND asin=%(asin)s AND sku=%(sku)s AND ss_name = ANY(%(ss_names)s)",
                {"start": start, "end": end, "asin": asin, "sku": mapped_sku, "ss_names": matched_ss_names or [""]},
            )
        else:
            m2 = None
        row_result[f"match2_{yr}"] = m2

        # Match 3: ASIN + ACCOUNT across all SKUs
        m3 = metrics_query(
            "AND asin=%(asin)s AND ss_name = ANY(%(ss_names)s)",
            {"start": start, "end": end, "asin": asin, "ss_names": matched_ss_names or [""]},
        )
        row_result[f"match3_{yr}"] = m3

        # Match 4: ASIN + SKU across ALL accounts
        m4 = metrics_query(
            "AND asin=%(asin)s AND sku=%(sku)s",
            {"start": start, "end": end, "asin": asin, "sku": sku},
        )
        row_result[f"match4_{yr}"] = m4

    results["matches"].append(row_result)

os.makedirs("state", exist_ok=True)
with open("state/kpi_reference_b02_validation.json", "w", encoding="utf-8") as f:
    json.dump(results, f, default=str, indent=2)

print("=== Account landscape ===")
for r in account_landscape:
    print(r)

print("\n=== Match results ===")
for rr in results["matches"]:
    ref = rr["ref"]
    print(f"\nASIN={ref['asin']} account={ref['account']} sku={ref['sku']} mapped={ref['mapped_sku']}")
    print(f"  matched ss_names: {rr['matched_ss_names']}")
    for yr in ["2025", "2026"]:
        m1 = rr[f"match1_{yr}"]
        print(f"  {yr} match1(exact): sales={m1['amazon_sales']:.2f} orders={m1['total_orders']} refunded={m1['refunded_original_sales']:.2f} qty={m1['total_quantity']}")
        m2 = rr[f"match2_{yr}"]
        if m2:
            print(f"  {yr} match2(mapped): sales={m2['amazon_sales']:.2f} orders={m2['total_orders']}")
        m3 = rr[f"match3_{yr}"]
        print(f"  {yr} match3(asin/acct all sku): sales={m3['amazon_sales']:.2f} orders={m3['total_orders']}")
        m4 = rr[f"match4_{yr}"]
        print(f"  {yr} match4(asin+sku all acct): sales={m4['amazon_sales']:.2f} orders={m4['total_orders']}")

cur.close()
conn.close()
