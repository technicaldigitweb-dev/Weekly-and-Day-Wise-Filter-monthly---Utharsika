"""
Pure-Python KPI total computation for uawso_daily - the SAME arithmetic the
client-side engine (uawso_client_engine.js, buildCanonicalRowsV5/computeTotalV5)
performs in the browser, reimplemented server-side so the automation run can
know its own totals (for the run-state JSON and evidence file) without
needing a browser. This is used for REPORTING only - the authoritative
cross-check against the live database is validation.py's independent SQL
re-derivation, not this function.

Vendor rule: one Vendor Unit = one Vendor Order (direct, no COUNT DISTINCT);
a vendor_sales period is included in full (no proration) whenever it
overlaps the report window at all - end_date > report_start AND
start_date <= report_end - matching extract_uawso_v5_asin_level.py's
vendor_periods query and the independent reconciliation script's inclusion
rule.
"""
from datetime import date


def compute_kpi_totals(daily_aggregates_asin: list, vendor_periods: list,
                        report_start: date, report_end: date) -> dict:
    fbm_sales = 0.0
    fbm_orders = 0
    fba_sales = 0.0
    fba_orders = 0
    for row in daily_aggregates_asin:
        fbm_sales += row["fbm_sales"]
        fbm_orders += row["fbm_orders"]
        fba_sales += row["fba_sales"]
        fba_orders += row["fba_orders"]

    vendor_sales = 0.0
    vendor_orders = 0
    for vp in vendor_periods:
        start = date.fromisoformat(vp["start_date"])
        end = date.fromisoformat(vp["end_date"])
        if end > report_start and start <= report_end:
            vendor_sales += vp["revenue"]
            vendor_orders += vp["units"]

    total_sales = fbm_sales + fba_sales + vendor_sales
    total_orders = fbm_orders + fba_orders + vendor_orders

    return {
        "fbm_sales": round(fbm_sales, 2),
        "fba_sales": round(fba_sales, 2),
        "vendor_sales": round(vendor_sales, 2),
        "total_sales": round(total_sales, 2),
        "fbm_orders": fbm_orders,
        "fba_orders": fba_orders,
        "vendor_orders": vendor_orders,
        "total_orders": total_orders,
    }


def compute_image_coverage(product_master_asin_level: list) -> dict:
    assigned_count = len(product_master_asin_level)
    image_covered = sum(1 for p in product_master_asin_level if p.get("image_url"))
    no_image = assigned_count - image_covered
    return {
        "assigned_asin_count": assigned_count,
        "image_covered_count": image_covered,
        "no_image_count": no_image,
    }
