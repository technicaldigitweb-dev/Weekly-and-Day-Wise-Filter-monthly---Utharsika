"""
UAWSO HTML renderer.

Fills templates/report_template.html (an original UAWSO-authored
template - not copied from any other user's report) with computed
Daily/Weekly/MTD sections. Pure string templating, no external
dependency required.
"""

import hashlib
import os
from typing import Optional

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "report_template.html")

COLUMN_HEADERS = [
    "ASIN", "SKU", "Previous Year Sales", "Previous Year Orders",
    "This Year Sales", "This Year Orders", "Sales Change", "Order Change",
    "Trend", "Achieve Sales %", "Achieve Order %",
]


def _fmt_money(v: float) -> str:
    return f"{v:,.2f}"


def _fmt_int(v: int) -> str:
    return f"{v:,}"


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return '<span class="uawso-undefined">—</span>'
    return f"{v * 100:.2f}%"


def _fmt_achieve(v: Optional[float]) -> str:
    if v is None:
        return '<span class="uawso-undefined">—</span>'
    return f"{v:.2f}%"


def _trend_span(trend: str) -> str:
    cls = {"UP": "uawso-trend-up", "DOWN": "uawso-trend-down", "NO CHANGE": "uawso-trend-flat"}[trend]
    return f'<span class="{cls}">{trend}</span>'


def render_section(period_label: str, rows, total) -> str:
    if not rows:
        return (
            f'<div class="uawso-section"><h2>{period_label}</h2>'
            f'<div class="uawso-empty-period">No transactions found for this period '
            f'within the assigned Amazon UK SKU set.</div></div>'
        )

    header_html = "".join(f"<th>{h}</th>" for h in COLUMN_HEADERS)
    body_rows = []
    for r in rows:
        improvement = f' <span class="uawso-undefined">({r.improvement_status})</span>' if r.improvement_status else ""
        body_rows.append(
            "<tr>"
            f"<td>{r.asin}</td><td>{r.sku}</td>"
            f"<td>{_fmt_money(r.previous_year_sales)}</td><td>{_fmt_int(r.previous_year_orders)}</td>"
            f"<td>{_fmt_money(r.this_year_sales)}</td><td>{_fmt_int(r.this_year_orders)}</td>"
            f"<td>{_fmt_pct(r.sales_change)}</td><td>{_fmt_pct(r.order_change)}</td>"
            f"<td>{_trend_span(r.trend)}{improvement}</td>"
            f"<td>{_fmt_achieve(r.achieve_sales_pct)}</td><td>{_fmt_achieve(r.achieve_order_pct)}</td>"
            "</tr>"
        )

    total_row = (
        '<tr class="uawso-total-row">'
        f'<td>Total</td><td></td>'
        f"<td>{_fmt_money(total.total_previous_year_sales)}</td><td>{_fmt_int(total.total_previous_year_orders)}</td>"
        f"<td>{_fmt_money(total.total_this_year_sales)}</td><td>{_fmt_int(total.total_this_year_orders)}</td>"
        f"<td>{_fmt_pct(total.total_sales_change)}</td><td>{_fmt_pct(total.total_order_change)}</td>"
        f"<td></td>"
        f"<td>{_fmt_achieve(total.total_achieve_sales_pct)}</td><td>{_fmt_achieve(total.total_achieve_order_pct)}</td>"
        "</tr>"
    )

    return (
        f'<div class="uawso-section"><h2>{period_label}</h2>'
        f'<table class="uawso-table"><thead><tr>{header_html}</tr></thead>'
        f"<tbody>{''.join(body_rows)}{total_row}</tbody></table></div>"
    )


def render_report(*, project_code, assigned_user, version, generated_timestamp,
                   report_cutoff_date, daily_rows, daily_total,
                   weekly_rows, weekly_total, mtd_rows, mtd_total) -> str:
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    head_title = f"UAWSO — {assigned_user} Amazon UK Sales & Orders Report — {report_cutoff_date}"

    replacements = {
        "{{HEAD_TITLE}}": head_title,
        "{{PROJECT_CODE}}": project_code,
        "{{ASSIGNED_USER}}": assigned_user,
        "{{VERSION}}": version,
        "{{GENERATED_TIMESTAMP}}": generated_timestamp,
        "{{REPORT_CUTOFF_DATE}}": str(report_cutoff_date),
        "{{DAILY_SECTION}}": render_section("Daily", daily_rows, daily_total),
        "{{WEEKLY_SECTION}}": render_section("Weekly", weekly_rows, weekly_total),
        "{{MTD_SECTION}}": render_section("Month-to-Date (MTD)", mtd_rows, mtd_total),
    }
    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    return html


def write_html_and_hash(path: str, html: str) -> str:
    """
    Writes html to path in BINARY mode (never text mode) and returns the
    SHA-256 of the exact bytes on disk.

    IMPORTANT: never compute a "final" SHA-256 from the in-memory string
    before writing - on Windows, a text-mode file write silently
    translates '\\n' to '\\r\\n', changing the byte content, so a hash
    taken before the write will not match the file that actually exists
    on disk. Always hash the bytes you are about to write (or read the
    file back) to guarantee the recorded hash is provably correct.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = html.encode("utf-8")
    with open(path, "wb") as f:
        f.write(data)
    return hashlib.sha256(data).hexdigest()
