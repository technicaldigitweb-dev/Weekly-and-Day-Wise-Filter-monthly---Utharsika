"""
UAWSO report query runner.

Executes 05_IMPLEMENTATION/sql/02_report_query.sql once per reporting
period against the assigned-ASIN set, returning raw (unrounded,
un-derived) Sales/Orders figures per ASIN+SKU. All derived figures
(Change, Trend, Achieve %) are computed in calculations.py, not here -
this module's only job is faithfully reproducing the mandatory filters.
"""

import os
from dataclasses import dataclass

SQL_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "02_report_query.sql")


@dataclass(frozen=True)
class RawRow:
    asin: str
    sku: str
    this_year_sales: float
    this_year_orders: int
    previous_year_sales: float
    previous_year_orders: int


def run_report_query(conn, asins, period_set) -> list:
    if not asins:
        return []

    with open(SQL_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    params = {
        "asins": list(asins),
        "cy_start": period_set.current_year.start,
        "cy_end": period_set.current_year.end,
        "py_start": period_set.previous_year.start,
        "py_end": period_set.previous_year.end,
    }
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [
        RawRow(
            asin=r[0], sku=r[1],
            this_year_sales=float(r[2] or 0), this_year_orders=int(r[3] or 0),
            previous_year_sales=float(r[4] or 0), previous_year_orders=int(r[5] or 0),
        )
        for r in rows
    ]
