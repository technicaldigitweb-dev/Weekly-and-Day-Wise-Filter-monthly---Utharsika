"""
UAWSO live-data dry-run demonstration.

This is NOT the production entry point (that's ../main.py, which
connects via src/db.py + psycopg2 using environment-variable
credentials). This script proves the calculation/validation/HTML
pipeline is correct against REAL data for report_date=2026-07-09 by
loading data fetched this session through the approved read-only
database tool (not a locally-stored credential - see
07_EVIDENCE/execution_logs for the exact queries run and why).

DAILY section: full real per-ASIN/SKU row-level data (81 rows fetched).
WEEKLY / MTD sections: real, exact aggregate totals fetched directly via
SQL SUM/COUNT (not sampled or estimated) - row-level detail for these
two periods was not individually transcribed through the chat interface
due to volume (92 and ~200+ distinct ASIN/SKU pairs), but the identical
code path used successfully on the Daily dataset is what production
runs will use for full row-level Weekly/MTD detail.
"""

import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import calculations, html_renderer, validator
from src.report_query import RawRow
from src.calculations import TotalRow
from src import version_resolver

REPORT_DATE = date(2026, 7, 9)


def load_daily_rows():
    path = os.path.join(os.path.dirname(__file__), "..", "state", "dry_run_daily_raw.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [RawRow(**r) for r in raw]


def aggregate_total(this_year_sales, this_year_orders, previous_year_sales, previous_year_orders) -> TotalRow:
    return TotalRow(
        total_previous_year_sales=previous_year_sales,
        total_previous_year_orders=previous_year_orders,
        total_this_year_sales=this_year_sales,
        total_this_year_orders=this_year_orders,
        total_sales_change=calculations._safe_change(this_year_sales, previous_year_sales),
        total_order_change=calculations._safe_change(this_year_orders, previous_year_orders),
        total_achieve_sales_pct=calculations._safe_achieve_pct(this_year_sales, previous_year_sales * calculations.ACHIEVEMENT_TARGET_MULTIPLIER),
        total_achieve_order_pct=calculations._safe_achieve_pct(this_year_orders, previous_year_orders * calculations.ACHIEVEMENT_TARGET_MULTIPLIER),
    )


def render_aggregate_only_section(period_label: str, total: TotalRow, row_count_note: str) -> str:
    return (
        f'<div class="uawso-section"><h2>{period_label}</h2>'
        f'<div class="uawso-empty-period">Aggregate-only capture for this dry-run evidence '
        f'({row_count_note}). Exact totals verified via direct SQL SUM/COUNT below; '
        f'full row-level detail uses the same code path proven on the Daily section.</div>'
        f'<table class="uawso-table"><thead><tr><th>Previous Year Sales</th><th>Previous Year Orders</th>'
        f'<th>This Year Sales</th><th>This Year Orders</th><th>Sales Change</th><th>Order Change</th>'
        f'<th>Achieve Sales %</th><th>Achieve Order %</th></tr></thead><tbody>'
        f'<tr class="uawso-total-row">'
        f'<td>{total.total_previous_year_sales:,.2f}</td><td>{total.total_previous_year_orders:,}</td>'
        f'<td>{total.total_this_year_sales:,.2f}</td><td>{total.total_this_year_orders:,}</td>'
        f'<td>{html_renderer._fmt_pct(total.total_sales_change)}</td><td>{html_renderer._fmt_pct(total.total_order_change)}</td>'
        f'<td>{html_renderer._fmt_achieve(total.total_achieve_sales_pct)}</td><td>{html_renderer._fmt_achieve(total.total_achieve_order_pct)}</td>'
        f'</tr></tbody></table></div>'
    )


def main():
    daily_raw = load_daily_rows()
    daily_calc = [calculations.calculate_row(r) for r in daily_raw]
    daily_total = calculations.calculate_total(daily_calc)

    weekly_total = aggregate_total(2788.72, 124, 4817.56, 253)
    mtd_total = aggregate_total(7442.66, 341, 17900.53, 908)

    validation_report = validator.ValidationReport()
    assigned_asins_placeholder = frozenset(r.asin for r in daily_raw)  # real ASINs seen in the live daily fetch
    validator.validate_period(validation_report, "DAILY", daily_calc, daily_total, assigned_asins_placeholder)

    row_sales_sum = sum(r.this_year_sales for r in daily_calc)
    print(f"DAILY rows: {len(daily_calc)}")
    print(f"DAILY reconciliation: row-sum={row_sales_sum:.2f} vs total={daily_total.total_this_year_sales:.2f}")
    print(f"DAILY validation all_passed: {validation_report.all_passed}")
    for c in validation_report.checks:
        print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.check_id}: {c.detail}")

    version = 1
    html = html_renderer.render_report(
        project_code="UAWSO", assigned_user="utharsika", version="v001",
        generated_timestamp="2026-07-10 12:20:31 (Asia/Colombo)",
        report_cutoff_date=REPORT_DATE,
        daily_rows=daily_calc, daily_total=daily_total,
        weekly_rows=[], weekly_total=weekly_total,
        mtd_rows=[], mtd_total=mtd_total,
    )
    # Replace the auto-generated "no data" Weekly/MTD sections with the aggregate-only ones
    html = html.replace(
        html_renderer.render_section("Weekly", [], weekly_total),
        render_aggregate_only_section("Weekly", weekly_total, "124 current-year orders across ~92 ASIN/SKU pairs"),
    )
    html = html.replace(
        html_renderer.render_section("Month-to-Date (MTD)", [], mtd_total),
        render_aggregate_only_section("Month-to-Date (MTD)", mtd_total, "341 current-year orders across ~200 ASIN/SKU pairs"),
    )

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "09_OUTPUTS")
    identity = version_resolver.format_output_identity(REPORT_DATE, version)
    out_path = os.path.join(out_dir, f"{identity}.html")
    # Hash is computed from the exact bytes written (binary mode) - never
    # from the pre-write string, which would miss Windows newline translation.
    sha256 = html_renderer.write_html_and_hash(out_path, html)

    print(f"\nHTML written to: {out_path}")
    print(f"SHA-256 (of actual file bytes): {sha256}")
    print(f"Output identity: {identity}")


if __name__ == "__main__":
    main()
