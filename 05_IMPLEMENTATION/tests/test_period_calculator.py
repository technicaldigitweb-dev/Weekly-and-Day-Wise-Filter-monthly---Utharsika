"""
Sanity tests for period_calculator.py - leap year, Monday edge, month/year
transitions. Run directly: python tests/test_period_calculator.py
(no test framework dependency, per the project's minimal-dependency stance).
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src import period_calculator as pc


def check(label, actual, expected):
    status = "PASS" if actual == expected else "FAIL"
    print(f"[{status}] {label}: got {actual!r}, expected {expected!r}")
    return status == "PASS"


def main():
    results = []

    # Leap year: Feb 29 2028 -> Feb 28 2027 (prior year not a leap year)
    results.append(check(
        "shift_one_year_back(2028-02-29)",
        pc.shift_one_year_back(date(2028, 2, 29)),
        date(2027, 2, 28),
    ))

    # Ordinary shift
    results.append(check(
        "shift_one_year_back(2026-07-09)",
        pc.shift_one_year_back(date(2026, 7, 9)),
        date(2025, 7, 9),
    ))

    # Monday-run edge case: report_date itself is a Monday -> weekly range collapses to 1 day
    monday = date(2026, 7, 6)  # confirmed Monday
    assert monday.weekday() == 0, "fixture date must be a Monday"
    wk = pc.weekly_period(monday)
    results.append(check("weekly Monday-edge start==end", wk.current_year.start == wk.current_year.end, True))
    results.append(check("weekly Monday-edge start", wk.current_year.start, monday))

    # MTD on the 1st of the month -> 1-day range
    first = date(2026, 8, 1)
    mtd = pc.mtd_period(first)
    results.append(check("MTD 1st-of-month collapses to 1 day", mtd.current_year.start == mtd.current_year.end, True))

    # Year transition: January report_date -> previous-year MTD also in January
    jan_date = date(2026, 1, 15)
    mtd_jan = pc.mtd_period(jan_date)
    results.append(check("MTD year transition py_start", mtd_jan.previous_year.start, date(2025, 1, 1)))
    results.append(check("MTD year transition py_end", mtd_jan.previous_year.end, date(2025, 1, 15)))

    # Weekly equivalent-previous-year is anchored on the shifted date's OWN Monday,
    # not "same ISO week number a year ago".
    wed = date(2026, 7, 8)  # a Wednesday
    assert wed.weekday() == 2
    wk2 = pc.weekly_period(wed)
    py_equiv = pc.shift_one_year_back(wed)  # 2025-07-08
    results.append(check("weekly py_end == shifted date", wk2.previous_year.end, py_equiv))
    results.append(check("weekly py_start == shifted date's own Monday", wk2.previous_year.start, pc.monday_of_week(py_equiv)))

    # report_date computation
    results.append(check("compute_report_date", pc.compute_report_date(date(2026, 7, 10)), date(2026, 7, 9)))

    total = len(results)
    passed = sum(results)
    print(f"\n{passed}/{total} checks passed")
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
