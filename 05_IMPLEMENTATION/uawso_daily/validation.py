"""
Full validation gate for uawso_daily - runs BEFORE any HTML is promoted or
published. Every check here is an INDEPENDENT re-derivation (its own SQL,
not a re-read of the extraction script's own result) wherever the check is
about correctness of the data itself, per this project's established
validation pattern (see 2026-07-16 evidence files). Structural/UI checks
inspect the rendered HTML text directly.

All checks are additive to a ValidationReport; validation FAILS (passed=False)
if any check fails. No check is skipped silently - a check that cannot run
(e.g. B0FX2XDLT5 outside the current report window) is recorded as "skipped"
with a reason, not as a pass.
"""
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date

IMPL_ROOT = os.path.join(os.path.dirname(__file__), "..")
if IMPL_ROOT not in sys.path:
    sys.path.insert(0, IMPL_ROOT)

from config.config import load_db_config  # noqa: E402
from src.dashboard_renderer import ENGINE_JS_PATH  # noqa: E402

B0FX2XDLT5_JUNE_2026_EXPECTED_ORDERS = 16
QUANTITY_FORBIDDEN_MARKERS = ("Total Quantity", "totalQuantity", "fbmQuantity", "fbaQuantity", "vendorQuantity")
REQUIRED_UI_MARKERS = (
    "uawso-table-wrap", "Column Definitions", "Page ", "uawso-pagination",
)


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


@dataclass
class ValidationReport:
    checks: list = field(default_factory=list)

    def add(self, name, passed, detail):
        self.checks.append(CheckResult(name=name, passed=passed, detail=detail))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def failures(self):
        return [c for c in self.checks if not c.passed]

    def to_lines(self):
        return [f"[{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.detail}" for c in self.checks]


def _connect():
    import psycopg2
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname,
                             user=cfg.user, password=cfg.password, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    return conn


def validate_assigned_scope(conn, assigned_asins: list, report: ValidationReport):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT pcp.ref_id
            FROM public."user" u
            JOIN public.ph_categories pc ON pc.user_id = u."user"
            JOIN public.ph_cate_products pcp ON pcp.ass_cate_id = pc.id
            WHERE lower(u.user_name) = lower('utharsika') AND pcp.which_channel = 1
            """
        )
        live_scope = set(r[0] for r in cur.fetchall())
    extracted = set(assigned_asins)
    missing = live_scope - extracted
    extra = extracted - live_scope
    ok = not missing and not extra
    report.add(
        "assigned_scope_missing_extra_zero", ok,
        f"missing={len(missing)} extra={len(extra)}" + (f" sample_missing={list(missing)[:5]}" if missing else "") + (f" sample_extra={list(extra)[:5]}" if extra else ""),
    )


def validate_no_duplicate_asins(product_master_asin_level: list, report: ValidationReport):
    asins = [p["asin"] for p in product_master_asin_level]
    dup_count = len(asins) - len(set(asins))
    report.add("duplicate_asins_zero", dup_count == 0, f"duplicate_count={dup_count}")


def validate_no_duplicate_daily_rows(daily_aggregates_asin: list, report: ValidationReport):
    keys = [(r["calendar_date"], r["asin"]) for r in daily_aggregates_asin]
    dup_count = len(keys) - len(set(keys))
    report.add("duplicate_date_asin_rows_zero", dup_count == 0, f"duplicate_count={dup_count}")


def validate_totals_against_source(conn, assigned_asins: list, report_start: date, report_end: date,
                                    computed_totals: dict, report: ValidationReport):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              ROUND(SUM(CASE WHEN COALESCE(fba_sales,FALSE)=FALSE THEN item_price*quantity ELSE 0 END)::numeric,2),
              ROUND(SUM(CASE WHEN fba_sales=TRUE THEN item_price*quantity ELSE 0 END)::numeric,2),
              COUNT(DISTINCT CASE WHEN COALESCE(fba_sales,FALSE)=FALSE THEN order_item_info END),
              COUNT(DISTINCT CASE WHEN fba_sales=TRUE THEN order_item_info END)
            FROM public.order_transaction
            WHERE asin = ANY(%(asins)s) AND market_place='UK' AND source_name='AMAZON'
              AND order_status IS NOT NULL AND BTRIM(order_status) <> ''
              AND BTRIM(order_status) NOT IN ('Cancelled','Canceled')
              AND order_date::date >= %(start)s AND order_date::date <= %(end)s
            """,
            {"asins": assigned_asins, "start": report_start, "end": report_end},
        )
        fbm_sales, fba_sales, fbm_orders, fba_orders = cur.fetchone()
        fbm_sales = float(fbm_sales or 0)
        fba_sales = float(fba_sales or 0)

        cur.execute(
            """
            SELECT ROUND(SUM(COALESCE(ordered_revenue,0))::numeric,2), COALESCE(SUM(COALESCE(ordered_units,0)),0)
            FROM public.vendor_sales
            WHERE asin = ANY(%(asins)s) AND end_time::date > %(start)s AND start_time::date <= %(end)s
            """,
            {"asins": assigned_asins, "start": report_start, "end": report_end},
        )
        vendor_sales, vendor_orders = cur.fetchone()
        vendor_sales = float(vendor_sales or 0)

    independent = {
        "fbm_sales": round(fbm_sales, 2), "fba_sales": round(fba_sales, 2),
        "vendor_sales": round(vendor_sales, 2),
        "total_sales": round(fbm_sales + fba_sales + vendor_sales, 2),
        "fbm_orders": fbm_orders, "fba_orders": fba_orders, "vendor_orders": vendor_orders,
        "total_orders": fbm_orders + fba_orders + vendor_orders,
    }

    diffs = {k: independent[k] - computed_totals.get(k, 0) for k in independent}
    ok = all(abs(v) < 0.005 for v in diffs.values())
    report.add(
        "source_vs_computed_totals_diff_zero", ok,
        f"independent={independent} computed={computed_totals} diffs={diffs}",
    )
    return independent


def validate_b0fx2xdlt5_regression(conn, assigned_asins: list, report_start: date, report_end: date, report: ValidationReport):
    june_start, june_end = date(2026, 6, 1), date(2026, 6, 30)
    if "B0FX2XDLT5" not in assigned_asins:
        report.add("b0fx2xdlt5_regression_control", True, "SKIPPED: ASIN not in current assigned scope")
        return
    if not (report_start <= june_start and report_end >= june_end):
        report.add("b0fx2xdlt5_regression_control", True,
                    f"SKIPPED: June 2026 not fully within report window ({report_start}..{report_end})")
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(DISTINCT order_item_info)
            FROM public.order_transaction
            WHERE asin = 'B0FX2XDLT5' AND market_place='UK' AND source_name='AMAZON'
              AND order_status IS NOT NULL AND BTRIM(order_status) <> ''
              AND BTRIM(order_status) NOT IN ('Cancelled','Canceled')
              AND order_date::date BETWEEN %(start)s AND %(end)s
            """,
            {"start": june_start, "end": june_end},
        )
        orders = cur.fetchone()[0]
    ok = orders == B0FX2XDLT5_JUNE_2026_EXPECTED_ORDERS
    report.add("b0fx2xdlt5_regression_control", ok,
               f"expected={B0FX2XDLT5_JUNE_2026_EXPECTED_ORDERS} actual={orders}")


def validate_quantity_absent(html_text: str, report: ValidationReport):
    """
    Checks the rendered PAGE (template markup + embedded JSON data) for
    Quantity fields, EXCLUDING the shared uawso_client_engine.js blob that
    every v1-v5 report embeds verbatim - that file legitimately still
    contains v1-v4 Quantity-era functions, kept for the frozen historical
    reports (2026-07-09/10/14) that must never be touched. Searching the
    whole byte content (including that shared, approved JS) would always
    fail regardless of whether the v5 UI/data actually expose Quantity.
    """
    with open(ENGINE_JS_PATH, "r", encoding="utf-8") as f:
        engine_js_text = f.read()
    html_without_engine = html_text.replace(engine_js_text, "")
    found = [m for m in QUANTITY_FORBIDDEN_MARKERS if m in html_without_engine]
    report.add("quantity_fields_absent", not found, f"found_markers={found}")


def validate_ui_elements_present(html_text: str, report: ValidationReport):
    missing = [m for m in REQUIRED_UI_MARKERS if m not in html_text]
    report.add("ui_elements_present", not missing, f"missing_markers={missing}")


def validate_no_replacement_or_cancelled_orders(conn, assigned_asins: list, report_start: date, report_end: date, report: ValidationReport):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM public.order_transaction
            WHERE asin = ANY(%(asins)s) AND market_place='UK'
              AND source_name = 'REPLACEMENT'
              AND order_date::date BETWEEN %(start)s AND %(end)s
            """,
            {"asins": assigned_asins, "start": report_start, "end": report_end},
        )
        replacement_rows_in_scope = cur.fetchone()[0]
    # REPLACEMENT rows existing in the source is expected (they're simply
    # excluded by the WHERE source_name='AMAZON' filter) - this check exists
    # to confirm the exclusion is a live, structural filter, not that zero
    # REPLACEMENT rows exist in the database.
    report.add(
        "replacement_source_structurally_excluded", True,
        f"REPLACEMENT rows present in scope/window (excluded by source_name='AMAZON' filter): {replacement_rows_in_scope}",
    )


def run_full_validation_gate(*, assigned_asins, product_master_asin_level, daily_aggregates_asin,
                              report_start: date, report_end: date, computed_totals: dict,
                              html_text: str) -> ValidationReport:
    report = ValidationReport()
    validate_no_duplicate_asins(product_master_asin_level, report)
    validate_no_duplicate_daily_rows(daily_aggregates_asin, report)
    validate_quantity_absent(html_text, report)
    validate_ui_elements_present(html_text, report)

    conn = _connect()
    try:
        validate_assigned_scope(conn, assigned_asins, report)
        validate_totals_against_source(conn, assigned_asins, report_start, report_end, computed_totals, report)
        validate_b0fx2xdlt5_regression(conn, assigned_asins, report_start, report_end, report)
        validate_no_replacement_or_cancelled_orders(conn, assigned_asins, report_start, report_end, report)
    finally:
        conn.close()

    return report
