"""
Asia/Colombo date handling for uawso_daily.

Asia/Colombo has used a fixed UTC+05:30 offset with no daylight-saving
changes since 1996 - a hardcoded fixed-offset fallback is therefore
always correct for this specific timezone (unlike most others), which is
why it is safe to use when the IANA tzdata database is unavailable (this
machine's Python has no `tzdata` package installed - `zoneinfo.ZoneInfo(
"Asia/Colombo")` raises ZoneInfoNotFoundError here). Prefer real zoneinfo
when available (e.g. on a Linux VM with system tzdata) for
defense-in-depth; fall back to the fixed offset otherwise.
"""
from datetime import date, datetime, timedelta, timezone

_FIXED_COLOMBO_OFFSET = timezone(timedelta(hours=5, minutes=30), name="Asia/Colombo")

try:
    from zoneinfo import ZoneInfo
    try:
        COLOMBO_TZ = ZoneInfo("Asia/Colombo")
        # Prove it actually resolves (raises ZoneInfoNotFoundError lazily on some platforms)
        datetime.now(COLOMBO_TZ)
        TZ_SOURCE = "zoneinfo"
    except Exception:
        COLOMBO_TZ = _FIXED_COLOMBO_OFFSET
        TZ_SOURCE = "fixed-offset-fallback"
except ImportError:
    COLOMBO_TZ = _FIXED_COLOMBO_OFFSET
    TZ_SOURCE = "fixed-offset-fallback"


def now_colombo() -> datetime:
    """Current wall-clock time in Asia/Colombo, timezone-aware."""
    return datetime.now(COLOMBO_TZ)


def today_colombo() -> date:
    return now_colombo().date()


def report_window(run_date: date, report_start: date, report_end_override: date = None):
    """
    Default rule: report_end_date = the day before run_date (the latest
    complete business day - the run date itself is always excluded as a
    partial/incomplete day). report_start_date is the fixed, approved
    project start date, passed in by the caller (config.REPORT_START_DATE).

    report_end_override is for --report-end-date, controlled manual
    testing only - the scheduled command must never pass this.
    """
    if report_end_override is not None:
        report_end = report_end_override
    else:
        report_end = run_date - timedelta(days=1)
    if report_end < report_start:
        raise ValueError(
            f"Computed report_end_date ({report_end}) is before report_start_date "
            f"({report_start}) - refusing to build a report with a negative/empty window."
        )
    return report_start, report_end


def output_identity(run_date: date, version: int, username: str = "utharsika") -> str:
    """
    Permanent output filename identity: YYYY-MM-DD_<username>_vNNN.
    Uses the RUN/publication date, never the report_end_date - see
    uawso_daily README, "Output naming" section, for the rationale.
    """
    return f"{run_date.isoformat()}_{username}_v{version:03d}"
