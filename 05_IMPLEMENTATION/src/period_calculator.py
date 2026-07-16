"""
UAWSO reporting-period calculator.

All boundaries are computed from the Sri Lanka (Asia/Colombo) calendar
date. Pure date-only logic (no time-of-day component beyond deriving
"today"), matching 04_DESIGN/UAWSO_BUSINESS_RULES_SPEC.md Section 4.

Weeks start Monday. Previous-year equivalents are computed by first
shifting the anchor date back exactly one year (calendar-safe, so
Feb 29 -> Feb 28 in a non-leap comparison year, matching Python's own
dateutil/relativedelta behaviour) and THEN deriving that shifted
date's own boundaries - never by reusing "the same ISO week number."
"""

from dataclasses import dataclass
from datetime import date, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback not expected in this project
    ZoneInfo = None

TIMEZONE_NAME = "Asia/Colombo"


@dataclass(frozen=True)
class PeriodRange:
    start: date
    end: date


@dataclass(frozen=True)
class PeriodSet:
    period_name: str
    current_year: PeriodRange
    previous_year: PeriodRange


def sri_lanka_today(now_utc=None) -> date:
    """
    Returns "today" in Asia/Colombo. now_utc is injectable for testing;
    in production it defaults to the real current UTC instant.
    """
    from datetime import datetime, timezone

    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    if ZoneInfo is not None:
        return now_utc.astimezone(ZoneInfo(TIMEZONE_NAME)).date()
    # Fixed-offset fallback (Asia/Colombo has no DST): UTC+5:30
    return (now_utc + timedelta(hours=5, minutes=30)).date()


def compute_report_date(execution_date: date) -> date:
    """report_date = execution_date - 1 day. Current day is never included."""
    return execution_date - timedelta(days=1)


def shift_one_year_back(d: date) -> date:
    """
    Calendar-safe subtraction of exactly one year. Feb 29 in a leap year
    maps to Feb 28 in the (non-leap) prior year - Python's date() raises
    on Feb-29-in-a-non-leap-year, so that case is handled explicitly.
    """
    try:
        return d.replace(year=d.year - 1)
    except ValueError:
        # d is Feb 29 and (d.year - 1) is not a leap year.
        assert d.month == 2 and d.day == 29
        return date(d.year - 1, 2, 28)


def monday_of_week(d: date) -> date:
    """ISO week: Monday = weekday() 0."""
    return d - timedelta(days=d.weekday())


def first_of_month(d: date) -> date:
    return d.replace(day=1)


def daily_period(report_date: date) -> PeriodSet:
    py_date = shift_one_year_back(report_date)
    return PeriodSet(
        period_name="DAILY",
        current_year=PeriodRange(report_date, report_date),
        previous_year=PeriodRange(py_date, py_date),
    )


def weekly_period(report_date: date) -> PeriodSet:
    """
    Monday-run edge case: if report_date is itself a Monday, monday_of_week
    returns report_date itself, so the range naturally collapses to a
    single day - no special-case branch required.
    """
    cy_start = monday_of_week(report_date)
    py_report_date = shift_one_year_back(report_date)
    py_start = monday_of_week(py_report_date)
    return PeriodSet(
        period_name="WEEKLY",
        current_year=PeriodRange(cy_start, report_date),
        previous_year=PeriodRange(py_start, py_report_date),
    )


def mtd_period(report_date: date) -> PeriodSet:
    py_report_date = shift_one_year_back(report_date)
    return PeriodSet(
        period_name="MTD",
        current_year=PeriodRange(first_of_month(report_date), report_date),
        previous_year=PeriodRange(first_of_month(py_report_date), py_report_date),
    )


def all_periods(report_date: date) -> list:
    return [daily_period(report_date), weekly_period(report_date), mtd_period(report_date)]
