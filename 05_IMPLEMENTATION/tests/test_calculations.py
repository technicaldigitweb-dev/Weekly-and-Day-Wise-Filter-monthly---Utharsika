"""
Sanity tests for calculations.py, focused on the zero-base edge cases
that are the highest-risk part of this module. Run directly:
python tests/test_calculations.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.calculations import calculate_row, calculate_total
from src.report_query import RawRow


def check(label, actual, expected):
    status = "PASS" if actual == expected else "FAIL"
    print(f"[{status}] {label}: got {actual!r}, expected {expected!r}")
    return status == "PASS"


def main():
    results = []

    # Normal UP case, values from the worksheet's own illustrative row 3
    r1 = calculate_row(RawRow("B095PRHY6W", "SKU1", this_year_sales=520, this_year_orders=22,
                               previous_year_sales=450, previous_year_orders=18))
    results.append(check("row3 sales_change ~ 0.156", round(r1.sales_change, 3), 0.156))
    results.append(check("row3 order_change ~ 0.222", round(r1.order_change, 3), 0.222))
    results.append(check("row3 trend", r1.trend, "UP"))

    # Normal DOWN case, from worksheet row 4
    r2 = calculate_row(RawRow("B084RC5DQG", "SKU2", this_year_sales=340, this_year_orders=13,
                               previous_year_sales=380, previous_year_orders=15))
    results.append(check("row4 sales_change ~ -0.105", round(r2.sales_change, 3), -0.105))
    results.append(check("row4 trend", r2.trend, "DOWN"))

    # Zero-base: previous=0, current=0
    r3 = calculate_row(RawRow("A1", "S1", this_year_sales=0, this_year_orders=0,
                               previous_year_sales=0, previous_year_orders=0))
    results.append(check("both-zero trend", r3.trend, "NO CHANGE"))
    results.append(check("both-zero improvement_status", r3.improvement_status, "NOT IMPROVED"))
    results.append(check("both-zero achieve_sales_pct undefined", r3.achieve_sales_pct, None))
    results.append(check("both-zero sales_change undefined", r3.sales_change, None))

    # Zero-base: previous=0, current>0 -- Trend=UP (resolved this stage), achieve% stays undefined
    r4 = calculate_row(RawRow("A2", "S2", this_year_sales=150, this_year_orders=5,
                               previous_year_sales=0, previous_year_orders=0))
    results.append(check("prev-zero-curr-positive trend", r4.trend, "UP"))
    results.append(check("prev-zero-curr-positive achieve_sales_pct undefined", r4.achieve_sales_pct, None))
    results.append(check("prev-zero-curr-positive improvement_status", r4.improvement_status, None))
    results.append(check("prev-zero-curr-positive sales_change undefined", r4.sales_change, None))

    # Equal sales -> NO CHANGE
    r5 = calculate_row(RawRow("A3", "S3", this_year_sales=100, this_year_orders=4,
                               previous_year_sales=100, previous_year_orders=4))
    results.append(check("equal sales trend", r5.trend, "NO CHANGE"))

    # 130% achievement worked example straight from the worksheet:
    # Previous=100, Current=117 -> Target=130, Achieve%=90
    r6 = calculate_row(RawRow("A4", "S4", this_year_sales=117, this_year_orders=1,
                               previous_year_sales=100, previous_year_orders=1))
    results.append(check("worksheet example achieve_sales_pct", round(r6.achieve_sales_pct, 2), 90.0))

    # Total row: never an average of row-level percentages.
    total = calculate_total([r1, r2])
    naive_average = (r1.achieve_sales_pct or 0) if r1.achieve_sales_pct else 0  # not used - just proving intent
    expected_total_sales_pct = (r1.this_year_sales + r2.this_year_sales) / \
        ((r1.previous_year_sales + r2.previous_year_sales) * 1.30) * 100
    results.append(check("total achieve_sales_pct is aggregate-of-aggregate",
                          round(total.total_achieve_sales_pct, 4), round(expected_total_sales_pct, 4)))

    total_pct = len(results)
    passed = sum(results)
    print(f"\n{passed}/{total_pct} checks passed")
    if passed != total_pct:
        sys.exit(1)


if __name__ == "__main__":
    main()
