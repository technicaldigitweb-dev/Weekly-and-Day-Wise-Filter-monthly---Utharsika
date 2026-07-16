"""
One-off live publication driver for 2026-07-10_utharsika_v001.

Reuses src/ph_task_publisher.py (already designed, gated, tested-by-
code-review module) - does NOT reimplement insert logic. This script's
only job is to load the validated HTML, open a real (non-readonly)
transaction-controlled connection, and call publish_report() exactly
once with is_correction=False (first publish for this date - the
pre-insert check already confirmed zero existing UAWSO rows).

*** PERMANENTLY DISABLED as of 2026-07-15 - DO NOT RUN. ***
Its target row (task_id='UAWSO-2026-07-10-utharsika-v001', id=157)
already exists - re-running this would attempt a duplicate first-
publish for an identity that is no longer new, which the mandatory
Historical Output Protection policy adopted 2026-07-15 forbids (see
07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md).
Superseded by 05_IMPLEMENTATION\\automation\\uawso_daily_runner.py.
Archived; kept for historical reference only. (src/ph_task_publisher.py
itself is left active/unguarded - it is still referenced by the older
main.py pipeline.)
"""
import sys

print("REFUSED: this script is permanently disabled - its target ph_task row already "
      "exists, and it does not perform dynamic version/duplicate resolution. See the "
      "module docstring and "
      "07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md.")
sys.exit(1)

import os  # noqa: E402  (unreachable - kept only so the rest of the file still parses)
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.config import load_db_config
from src.ph_task_publisher import publish_report

REPORT_DATE = date(2026, 7, 10)
VERSION = 1
TASK_NAME = "2026-07-10_utharsika_v001"
HTML_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "09_OUTPUTS", "2026-07-10_utharsika_v001.html")

DESCRIPTION = (
    "Automated Daily/Weekly/MTD Sales & Orders interactive dashboard for Utharsika's "
    "assigned Amazon UK SKUs vs prior-year performance and 130% achievement targets. "
    "Frequency: daily. Timezone: Asia/Colombo. Data cutoff (latest completed date): 2026-07-09. "
    "Source file: 09_OUTPUTS\\2026-07-10_utharsika_v001.html. "
    "KNOWN LIMITATION - ASIN completeness status: PENDING_CORRECTION. "
    "Source assignment count: 1723 assigned ASINs. The product master embedded in this HTML "
    "represents only assigned ASINs with at least one historical Amazon UK Completed transaction "
    "(1610 ASINs represented); 113 assigned ASINs with no transaction history under these filters "
    "are not yet represented. Pending verification and correction in a later version."
)


def main():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    print(f"Loaded HTML: {len(html_content)} chars from {HTML_PATH}")

    cfg = load_db_config()
    import psycopg2
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user, password=cfg.password, connect_timeout=15)
    conn.autocommit = False  # explicit transaction control, per the publish sequence

    try:
        result = publish_report(
            conn,
            report_date=REPORT_DATE,
            version=VERSION,
            task_name=TASK_NAME,
            html_content=html_content,
            description=DESCRIPTION,
            is_correction=False,
        )
    finally:
        conn.close()

    print(f"Committed: {result.committed}")
    print(f"Inserted row ID: {result.inserted_row_id}")
    print(f"Task ID: {result.task_id}")
    print(f"Task name: {result.task_name}")
    print(f"Version level: {result.version_level}")
    print(f"Same-day active row count: {result.same_day_active_row_count}")
    print(f"Duplicate check passed: {result.duplicate_check_passed}")
    print(f"Detail: {result.detail}")

    if not result.committed:
        print("PUBLISH FAILED - see detail above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
