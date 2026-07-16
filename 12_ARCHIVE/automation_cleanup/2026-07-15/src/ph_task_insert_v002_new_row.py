"""
UAWSO v002 - INSERT as a new ph_task row (explicit user approval).

Does NOT touch the existing row (id=157, task_id=UAWSO-2026-07-10-utharsika-v001).
Inserts a new row via the table's own id sequence (never copies the PK from
row 157). Runs inside an explicit transaction: verifies the inserted row's
identity and HTML hash BEFORE commit, rolls back on any mismatch.

*** PERMANENTLY DISABLED as of 2026-07-15 - DO NOT RUN. ***
Hardcodes a single, already-used task_id/version - re-running it today
would attempt to insert a duplicate under a stale identity, not the
next unused version, violating the version-resolution rule in the
mandatory Historical Output Protection policy adopted 2026-07-15 (see
07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md).
Superseded by 05_IMPLEMENTATION\\automation\\uawso_daily_runner.py, which
resolves the next version dynamically against both local files and
ph_task before every insert. Archived; kept for historical reference
only.
"""
import sys

print("REFUSED: this script is permanently disabled - it hardcodes an already-used "
      "task_id/version and does not perform dynamic version resolution, risking a "
      "duplicate insert. See the module docstring and "
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
EXPECTED_SHA256 = "60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff"
EXISTING_ROW_ID = 157
EXISTING_TASK_ID = "UAWSO-2026-07-10-utharsika-v001"
NEW_TASK_ID = "UAWSO-2026-07-14-utharsika-v002"

with open(V002_PATH, "rb") as f:
    v002_bytes = f.read()
v002_text = v002_bytes.decode("utf-8")
v002_sha256 = hashlib.sha256(v002_bytes).hexdigest()
print(f"Local v002 file: {len(v002_bytes)} bytes, SHA-256={v002_sha256}")
if v002_sha256 != EXPECTED_SHA256:
    raise RuntimeError(f"STOP: local hash {v002_sha256} does not match expected {EXPECTED_SHA256}. Refusing to insert.")

DESCRIPTION = (
    "UAWSO v002 - Utharsika Amazon UK Sales, Orders & Quantity Dashboard. "
    "Ordered Product Sales / Total Orders / Total Quantity rules (Completed+Refunded "
    "AMAZON Sales; Completed AMAZON+REPLACEMENT Orders; Vendor Orders=N/A). "
    "Data range 2025-01-01 to 2026-07-13 inclusive. 1723 assigned ASINs. "
    "Reference source: 02_SOURCE/user_provided/2026-07-14_utharsika_june_kpi_reference_b02.csv. "
    "Validation evidence: 07_EVIDENCE/2026-07-14_utharsika_june_kpi_reference_b02_VALIDATION.md. "
    "Monthly completeness evidence: 07_EVIDENCE/2026-07-14_utharsika_v002_MONTH_BY_MONTH_SALES_RECONCILIATION.md. "
    "Inserted as a new row alongside the preserved original v001 row (id=157) per explicit user approval - "
    "this row does not replace or modify that row."
)

cfg = load_db_config()
print(f"Connecting to host={cfg.host} port={cfg.port} db={cfg.dbname} user={cfg.user} password={redact(cfg.password)}")
conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user, password=cfg.password, connect_timeout=15)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

try:
    # Pre-insert duplicate checks (inside the same transaction for consistency).
    cur.execute("SELECT COUNT(*) AS n FROM tech_team_outputs.ph_task WHERE task_id = %(tid)s", {"tid": NEW_TASK_ID})
    dup_count = cur.fetchone()["n"]
    print(f"Pre-insert duplicate task_id count: {dup_count}")
    if dup_count != 0:
        conn.rollback()
        raise RuntimeError("FAIL_DUPLICATE_TASK_ID: proposed task_id already exists. Refusing to insert.")

    cur.execute(
        "SELECT id, task_id, project_code, assigned_user, version_level, "
        "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256 "
        "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
        {"rid": EXISTING_ROW_ID},
    )
    before = cur.fetchone()
    print(f"Existing row before insert: {dict(before)}")
    if before["task_id"] != EXISTING_TASK_ID:
        conn.rollback()
        raise RuntimeError("STOP: existing row id=157 does not match expected task_id. Refusing to insert.")

    cur.execute(
        """
        INSERT INTO tech_team_outputs.ph_task
            (id, project_name, project_code, task_name, task_id, team, developer,
             assigned_user, assigned_user_team, html_content, description,
             phase_level, version_level, version_status, created_at, updated_at)
        VALUES
            (nextval('tech_team_outputs.ph_task_id_seq'),
             %(project_name)s, %(project_code)s, %(task_name)s, %(task_id)s, %(team)s, %(developer)s,
             %(assigned_user)s, %(assigned_user_team)s, %(html_content)s, %(description)s,
             %(phase_level)s, %(version_level)s, %(version_status)s, now(), now())
        RETURNING id
        """,
        {
            "project_name": "Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report",
            "project_code": "UAWSO",
            "task_name": "Utharsika Weekly and Day Wise Sales Comparison v002",
            "task_id": NEW_TASK_ID,
            "team": "PH Team",
            "developer": "Satheskanth",
            "assigned_user": "utharsika",
            "assigned_user_team": "ph_priors",
            "html_content": v002_text,
            "description": DESCRIPTION,
            "phase_level": 1,
            "version_level": 2,
            "version_status": "released",
        },
    )
    new_id = cur.fetchone()["id"]
    print(f"Inserted row id (pre-commit): {new_id}")

    # Pre-commit verification.
    cur.execute(
        "SELECT id, task_id, project_code, assigned_user, assigned_user_team, version_level, "
        "length(html_content) AS html_length, "
        "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, "
        "created_at, updated_at "
        "FROM tech_team_outputs.ph_task WHERE id = %(nid)s",
        {"nid": new_id},
    )
    inserted = cur.fetchone()
    print(f"Inserted row (pre-commit re-read): {dict(inserted)}")

    checks = {
        "task_id_matches": inserted["task_id"] == NEW_TASK_ID,
        "project_code_matches": inserted["project_code"] == "UAWSO",
        "assigned_user_matches": inserted["assigned_user"] == "utharsika",
        "assigned_user_team_matches": inserted["assigned_user_team"] == "ph_priors",
        "version_level_matches": inserted["version_level"] == 2,
        "html_sha256_matches": inserted["html_sha256"] == EXPECTED_SHA256,
        "new_id_not_157": new_id != EXISTING_ROW_ID,
    }
    print(f"Pre-commit checks: {checks}")

    cur.execute(
        "SELECT id, task_id, "
        "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256 "
        "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
        {"rid": EXISTING_ROW_ID},
    )
    existing_after = cur.fetchone()
    checks["existing_row_unchanged"] = (
        existing_after["task_id"] == EXISTING_TASK_ID and existing_after["html_sha256"] == before["html_sha256"]
    )
    print(f"Existing row 157 within transaction: {dict(existing_after)}")

    if not all(checks.values()):
        conn.rollback()
        raise RuntimeError(f"STOP: pre-commit check failed: {checks}. Rolled back, not committed.")

    conn.commit()
    print("COMMITTED.")

finally:
    pass

# Post-commit validation (new connection/cursor read, confirming durability).
cur.execute("SELECT COUNT(*) AS n FROM tech_team_outputs.ph_task WHERE task_id = %(tid)s", {"tid": NEW_TASK_ID})
post_count = cur.fetchone()["n"]
print(f"\nPost-commit: rows with new task_id: {post_count}")

cur.execute(
    "SELECT id, task_id, project_code, assigned_user, assigned_user_team, version_level, "
    "length(html_content) AS html_length, "
    "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, created_at, updated_at "
    "FROM tech_team_outputs.ph_task WHERE task_id = %(tid)s",
    {"tid": NEW_TASK_ID},
)
final_row = cur.fetchone()
print(f"Final new row: {dict(final_row)}")
print(f"Stored HTML contains '2026-07-13': {'2026-07-13' in v002_text}")

cur.execute(
    "SELECT id, task_id, "
    "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
    "FROM tech_team_outputs.ph_task WHERE id = %(rid)s",
    {"rid": EXISTING_ROW_ID},
)
existing_final = cur.fetchone()
print(f"Existing row 157 after commit: {dict(existing_final)}")

cur.execute("SELECT COUNT(*) AS n FROM tech_team_outputs.ph_task WHERE project_code='UAWSO'")
uawso_count = cur.fetchone()["n"]
print(f"Total UAWSO rows now: {uawso_count}")

cur.close()
conn.close()
print("Connection closed.")
