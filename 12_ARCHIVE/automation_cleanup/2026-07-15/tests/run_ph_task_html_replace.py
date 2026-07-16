"""
One-off driver: replaces the stored html_content for the existing
UAWSO v001 ph_task row with the local, corrected v001 HTML. UPDATE only.

*** PERMANENTLY DISABLED as of 2026-07-15 - DO NOT RUN. ***
This script performs an UPDATE against an existing ph_task row, which
directly violates the mandatory Historical Output Protection policy
adopted 2026-07-15 ("do not update, replace, delete, or reuse any
existing ph_task row" - see
07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md).
Its own EXPECTED_SHA256 guard would already abort against the current
(post-incident) on-disk v001.html, but the script is disabled outright
so it can never run against any future row either. Archived; kept for
historical reference only.
"""
import sys

print("REFUSED: this script is permanently disabled - it performs an UPDATE against an "
      "existing ph_task row, forbidden under the Historical Output Protection policy. "
      "See the module docstring and "
      "07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md.")
sys.exit(1)

import hashlib  # noqa: E402  (unreachable - kept only so the rest of the file still parses)
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.config import load_db_config
from src.ph_task_html_replacer import replace_html_content

HTML_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "09_OUTPUTS", "2026-07-10_utharsika_v001.html")
EXPECTED_SHA256 = "58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3"


def main():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        new_html = f.read()

    local_sha = hashlib.sha256(new_html.encode("utf-8")).hexdigest()
    print(f"Local HTML SHA-256 (as loaded): {local_sha}")
    if local_sha != EXPECTED_SHA256:
        print("ABORT: local file hash does not match expected value.")
        sys.exit(1)

    cfg = load_db_config()
    import psycopg2
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user, password=cfg.password, connect_timeout=15)
    conn.autocommit = False

    try:
        result = replace_html_content(
            conn, task_id="UAWSO-2026-07-10-utharsika-v001", assigned_user="utharsika",
            project_code="UAWSO", new_html_content=new_html,
        )
    finally:
        conn.close()

    print(f"Matched row id: {result.matched_row_id}")
    print(f"Rows affected: {result.rows_affected}")
    print(f"Committed: {result.committed}")
    print(f"Detail: {result.detail}")

    if not result.committed:
        print("REPLACE FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
