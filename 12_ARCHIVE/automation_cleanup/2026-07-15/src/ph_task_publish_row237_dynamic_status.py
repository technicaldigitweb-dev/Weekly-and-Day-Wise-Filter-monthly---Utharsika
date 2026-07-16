"""
UAWSO final publication: updates the EXISTING ph_task row (id=237,
task_id='UAWSO-2026-07-14-utharsika-v002') with the dynamic-status-rule
build (09_OUTPUTS/2026-07-14_utharsika_v002.html). Does NOT insert a
row, does NOT touch row 157, does NOT change task_id/version_level -
only html_content and updated_at change.

*** PERMANENTLY DISABLED as of 2026-07-15 - DO NOT RUN. ***
UPDATEs an existing ph_task row (the CURRENT live row 237), forbidden
under the mandatory Historical Output Protection policy adopted
2026-07-15 (see
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

FINAL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "09_OUTPUTS", "2026-07-14_utharsika_v002.html")
EXISTING_ROW_ID = 237
EXISTING_TASK_ID = "UAWSO-2026-07-14-utharsika-v002"
UNTOUCHED_ROW_ID = 157
UNTOUCHED_TASK_ID = "UAWSO-2026-07-10-utharsika-v001"

with open(FINAL_PATH, "rb") as f:
    final_bytes = f.read()
final_text = final_bytes.decode("utf-8")
final_sha256 = hashlib.sha256(final_bytes).hexdigest()
print(f"Local final file: {len(final_bytes)} bytes, SHA-256={final_sha256}")
assert "2026-07-13" in final_text, "STOP: local file does not contain the 2026-07-13 marker."

cfg = load_db_config()
print(f"Connecting to host={cfg.host} port={cfg.port} db={cfg.dbname} user={cfg.user} password={redact(cfg.password)}")
conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user, password=cfg.password, connect_timeout=15)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

try:
    # --- Pre-update: confirm both rows' identity, inside the transaction.
    cur.execute(
        "SELECT id, task_id, project_code, assigned_user, assigned_user_team, version_level, "
        "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
        "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
        {"rid": EXISTING_ROW_ID},
    )
    row237_before = cur.fetchone()
    print(f"Row 237 before: {dict(row237_before)}")
    if row237_before is None or row237_before["task_id"] != EXISTING_TASK_ID:
        conn.rollback()
        raise RuntimeError(f"STOP: row {EXISTING_ROW_ID} identity mismatch. Refusing to write.")
    if row237_before["project_code"] != "UAWSO" or row237_before["assigned_user"] != "utharsika" or row237_before["version_level"] != 2:
        conn.rollback()
        raise RuntimeError(f"STOP: row {EXISTING_ROW_ID} ownership/version mismatch. Refusing to write.")

    cur.execute(
        "SELECT id, task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
        "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
        {"rid": UNTOUCHED_ROW_ID},
    )
    row157_before = cur.fetchone()
    print(f"Row 157 before (must remain untouched): {dict(row157_before)}")
    if row157_before is None or row157_before["task_id"] != UNTOUCHED_TASK_ID:
        conn.rollback()
        raise RuntimeError("STOP: row 157 identity mismatch. Refusing to write.")

    # --- Update ONLY html_content and updated_at, tightly scoped WHERE.
    cur.execute(
        """
        UPDATE tech_team_outputs.ph_task
        SET html_content = %(html_content)s,
            updated_at = NOW()
        WHERE id = %(row_id)s
          AND project_code = 'UAWSO'
          AND lower(assigned_user) = lower('utharsika')
          AND task_id = %(task_id)s
          AND version_level = 2
        """,
        {"html_content": final_text, "row_id": EXISTING_ROW_ID, "task_id": EXISTING_TASK_ID},
    )
    affected = cur.rowcount
    print(f"Rows affected by UPDATE: {affected}")
    if affected != 1:
        conn.rollback()
        raise RuntimeError(f"UPDATE affected {affected} rows (expected exactly 1) - rolled back, not committed.")

    # --- Pre-commit verification.
    cur.execute(
        "SELECT id, task_id, project_code, assigned_user, version_level, "
        "length(html_content) AS html_length, "
        "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
        "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
        {"rid": EXISTING_ROW_ID},
    )
    row237_after = cur.fetchone()
    print(f"Row 237 after UPDATE (pre-commit): {dict(row237_after)}")

    cur.execute(
        "SELECT id, task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
        "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
        {"rid": UNTOUCHED_ROW_ID},
    )
    row157_within_txn = cur.fetchone()

    checks = {
        "hash_matches_local": row237_after["html_sha256"] == final_sha256,
        "assigned_user_correct": row237_after["assigned_user"] == "utharsika",
        "project_code_correct": row237_after["project_code"] == "UAWSO",
        "version_level_correct": row237_after["version_level"] == 2,
        "max_date_marker_present": "2026-07-13" in final_text,
        "row157_task_id_unchanged": row157_within_txn["task_id"] == UNTOUCHED_TASK_ID,
        "row157_hash_unchanged": row157_within_txn["html_sha256"] == row157_before["html_sha256"],
        "row157_updated_at_unchanged": row157_within_txn["updated_at"] == row157_before["updated_at"],
    }
    print(f"Pre-commit checks: {checks}")

    if not all(checks.values()):
        conn.rollback()
        raise RuntimeError(f"STOP: pre-commit check failed: {checks}. Rolled back, not committed.")

    conn.commit()
    print("COMMITTED.")

finally:
    pass

# --- Post-commit re-read.
cur.execute(
    "SELECT id, task_id, project_code, assigned_user, version_level, "
    "length(html_content) AS html_length, "
    "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
    "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
    {"rid": EXISTING_ROW_ID},
)
final_row237 = cur.fetchone()
print(f"\nFinal row 237 (post-commit): {dict(final_row237)}")
print(f"Stored/local hash match: {final_row237['html_sha256'] == final_sha256}")

cur.execute(
    "SELECT id, task_id, version_level, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
    "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
    {"rid": UNTOUCHED_ROW_ID},
)
final_row157 = cur.fetchone()
print(f"Final row 157 (post-commit, must be unchanged): {dict(final_row157)}")

cur.execute("SELECT COUNT(*) AS n FROM tech_team_outputs.ph_task WHERE project_code='UAWSO'")
print(f"Total UAWSO rows: {cur.fetchone()['n']}")

cur.close()
conn.close()
print("Connection closed.")
