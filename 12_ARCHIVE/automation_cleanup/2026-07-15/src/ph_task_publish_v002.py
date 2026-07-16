"""
UAWSO v002 ph_task publication.

Updates the EXISTING ph_task row (id=157, task_id='UAWSO-2026-07-10-utharsika-v001')
in place with the v002 HTML content. Does NOT insert a new row, does NOT
alter task_id/task_name/project identity/ownership fields - only
html_content, updated_at, and version_level (a pre-existing workflow
field) are changed. Refuses to proceed if the pre-update row identity
does not match exactly, and refuses to commit if the UPDATE affects
anything other than exactly one row.

*** PERMANENTLY DISABLED as of 2026-07-15 - DO NOT RUN. ***
UPDATEs an existing ph_task row, forbidden under the mandatory
Historical Output Protection policy adopted 2026-07-15 (see
07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md).
Superseded by 05_IMPLEMENTATION\\automation\\uawso_daily_runner.py, which
only ever INSERTs one new versioned row. Archived; kept for historical
reference only.
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

import psycopg2
import psycopg2.extras

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config, redact

V002_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "09_OUTPUTS", "2026-07-10_utharsika_v002.html")
EXPECTED_ROW_ID = 157
EXPECTED_TASK_ID = "UAWSO-2026-07-10-utharsika-v001"

with open(V002_PATH, "rb") as f:
    v002_bytes = f.read()
v002_text = v002_bytes.decode("utf-8")
v002_sha256 = hashlib.sha256(v002_bytes).hexdigest()
print(f"Local v002 file: {len(v002_bytes)} bytes, SHA-256={v002_sha256}")

cfg = load_db_config()
print(f"Connecting to host={cfg.host} port={cfg.port} db={cfg.dbname} user={cfg.user} password={redact(cfg.password)}")
conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user, password=cfg.password, connect_timeout=15)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

try:
    # --- Step 1: confirm the existing row BEFORE any write.
    cur.execute(
        """
        SELECT id, project_code, task_name, task_id, assigned_user, version_level, version_status,
               length(html_content) AS html_length
        FROM tech_team_outputs.ph_task
        WHERE project_code = 'UAWSO' AND lower(assigned_user) = lower('utharsika')
        """
    )
    rows = cur.fetchall()
    print(f"Matching rows found (project_code=UAWSO, assigned_user=utharsika): {len(rows)}")
    for r in rows:
        print(dict(r))

    if len(rows) != 1:
        raise RuntimeError(f"Expected exactly 1 existing row, found {len(rows)}. Refusing to write.")
    row = rows[0]
    if row["id"] != EXPECTED_ROW_ID or row["task_id"] != EXPECTED_TASK_ID:
        raise RuntimeError(
            f"Row identity mismatch: expected id={EXPECTED_ROW_ID} task_id={EXPECTED_TASK_ID}, "
            f"found id={row['id']} task_id={row['task_id']}. Refusing to write."
        )
    print("Row identity confirmed. Proceeding with UPDATE (html_content, updated_at, version_level only).")

    # --- Step 2: update ONLY the approved fields, tightly scoped WHERE.
    cur.execute(
        """
        UPDATE tech_team_outputs.ph_task
        SET html_content = %(html_content)s,
            updated_at = NOW(),
            version_level = 2
        WHERE id = %(row_id)s
          AND project_code = 'UAWSO'
          AND lower(assigned_user) = lower('utharsika')
          AND task_id = %(task_id)s
        """,
        {"html_content": v002_text, "row_id": EXPECTED_ROW_ID, "task_id": EXPECTED_TASK_ID},
    )
    affected = cur.rowcount
    print(f"Rows affected by UPDATE: {affected}")
    if affected != 1:
        conn.rollback()
        raise RuntimeError(f"UPDATE affected {affected} rows (expected exactly 1) - rolled back, not committed.")

    conn.commit()
    print("Committed.")

    # --- Step 3: re-read and verify stored hash matches local file hash.
    cur.execute(
        """
        SELECT id, task_name, task_id, version_level, version_status, updated_at,
               html_content
        FROM tech_team_outputs.ph_task
        WHERE id = %(row_id)s
        """,
        {"row_id": EXPECTED_ROW_ID},
    )
    after = cur.fetchone()
    stored_sha256 = hashlib.sha256(after["html_content"].encode("utf-8")).hexdigest()
    print(f"Re-read row: id={after['id']} task_name={after['task_name']} task_id={after['task_id']} "
          f"version_level={after['version_level']} version_status={after['version_status']} updated_at={after['updated_at']}")
    print(f"Stored HTML SHA-256: {stored_sha256}")
    print(f"Local v002 SHA-256:  {v002_sha256}")
    print(f"MATCH: {stored_sha256 == v002_sha256}")

finally:
    cur.close()
    conn.close()
    print("Connection closed.")
