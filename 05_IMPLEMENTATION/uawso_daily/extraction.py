"""
Extraction wrapper for uawso_daily.

Imports and calls the existing, approved src/extract_uawso_v5_asin_level.py
extract() function directly - no business logic is duplicated here. Credentials
come exclusively from config.config.load_db_config() (the existing .env /
temp_user mechanism). This module never prints a credential value; it relies
on extract_uawso_v5_asin_level's own redact() usage for its one connect-log line.
"""
import os
import sys
from datetime import date

IMPL_ROOT = os.path.join(os.path.dirname(__file__), "..")
if IMPL_ROOT not in sys.path:
    sys.path.insert(0, IMPL_ROOT)

from config.config import load_db_config  # noqa: E402
from src.extract_uawso_v5_asin_level import extract as _extract_v5  # noqa: E402


class SourceNotReadyError(Exception):
    """Raised when the live source has no data reaching report_end_date within tolerance."""


def _connect():
    import psycopg2
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname,
                             user=cfg.user, password=cfg.password, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    return conn


def get_source_max_date() -> date:
    """
    Independent, lightweight freshness probe - opens and closes its own
    read-only connection (separate from the one extract() uses internally)
    so a freshness check can be made BEFORE committing to a full extraction.
    """
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(order_date::date) FROM public.order_transaction "
                "WHERE market_place = 'UK' AND source_name = 'AMAZON'"
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def check_source_freshness(report_end_date: date, tolerance_days: int) -> tuple:
    """
    Returns (is_ready: bool, source_max_date: date). Ready when
    source_max_date >= report_end_date - tolerance_days, i.e. the source
    has data reaching close enough to the requested report window.
    """
    source_max_date = get_source_max_date()
    if source_max_date is None:
        return False, None
    from datetime import timedelta
    is_ready = source_max_date >= (report_end_date - timedelta(days=tolerance_days))
    return is_ready, source_max_date


def extract_report_data(report_start: date, report_end: date):
    """
    Returns (assigned_asins, product_master_asin_level, daily_aggregates_asin, vendor_periods)
    exactly as produced by src/extract_uawso_v5_asin_level.extract() - no
    reshaping. Raises whatever extract() raises (RuntimeError on zero-ASIN
    scope or duplicate-assignment rows; psycopg2 errors on connection failure).
    """
    return _extract_v5(report_start, report_end)


def get_multi_image_count(assigned_asins: list) -> int:
    """
    Count of assigned ASINs with MORE THAN ONE qualifying public.listing_data
    row (which_channel=1, market_place='UK', wrong_sku=0, non-blank
    main_image_url) - a template field extract_uawso_v5_asin_level.extract()
    does not itself return (it already collapses to one row per ASIN via
    ROW_NUMBER()). Implemented as a separate, additional read-only query
    rather than by modifying that approved extraction script's return shape,
    since other callers (historical regeneration scripts) depend on its
    existing 4-tuple signature.
    """
    if not assigned_asins:
        return 0
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM (
                    SELECT ref_id
                    FROM public.listing_data
                    WHERE which_channel = 1 AND market_place = 'UK' AND wrong_sku = 0
                      AND main_image_url IS NOT NULL AND BTRIM(main_image_url) <> ''
                      AND ref_id = ANY(%(asins)s)
                    GROUP BY ref_id
                    HAVING COUNT(*) > 1
                ) multi
                """,
                {"asins": assigned_asins},
            )
            return cur.fetchone()[0]
    finally:
        conn.close()
