"""
Pushes today's completed UAWSO commitment to daily_task.tbl_uawso_satheskanth.
Read-only search first (exactly one matching row expected: zero -> INSERT,
one -> UPDATE, more than one -> FAIL_DUPLICATE, abort). Does not touch
tech_team_outputs.ph_task or any other daily_task row.
"""
import os
import sys

import psycopg2
import psycopg2.extras

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config, redact

WORK_DATE = "2026-07-14"
DEVELOPER = "satheskanth"
PROJECT_CODE = "UAWSO"
PROJECT_NAME = "Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report"
DOMAIN = "E-commerce Operations - Amazon Marketplace - UK Sales and Orders"
AIOS_PHASE = "DEPLOY"
STATUS = "COMPLETE"  # CHECK constraint requires COMPLETE (not "Completed")
TASK_TITLE = "Sales and Orders mismatch validation"

COMMITMENT = (
    "Validate the Utharsika Sales and Orders data mismatch, identify the root cause in "
    "order-status filtering, and confirm the correct statuses to include."
)

TASK_SUMMARY = (
    "Assigned user: utharsika (team: ph_priors). "
    "Data period: 2025-01-01 through 2026-07-13. "
    "Assigned ASIN count: 1,723.\n\n"
    + COMMITMENT
)

WORK_PERFORMED = (
    "Result: PASS. Published ph_task row: 237.\n\n"
    "Validated the Utharsika Sales and Orders mismatch against PostgreSQL, the generated HTML, "
    "the user reference CSV and monthly reconciliations. Identified order-status filtering as the "
    "root cause and implemented a dynamic rule that includes every available nonblank order status "
    "except Cancelled and Canceled. Freshly extracted the complete dataset from 2025-01-01 through "
    "2026-07-13 for 1,723 assigned ASINs, validated all 19 reporting periods with zero PostgreSQL/HTML "
    "differences, and published the verified HTML to ph_task row 237 without creating a duplicate row."
)

FILES_MODIFIED = (
    "Asset: 09_OUTPUTS\\2026-07-14_utharsika_v002.html.\n"
    "Implementation changed: 05_IMPLEMENTATION\\src\\extract_uawso_v4_ordered_sales.py; "
    "05_IMPLEMENTATION\\src\\uawso_client_engine.js."
)

DECISIONS_MADE = (
    "Included status rule: Every available nonblank order status except Cancelled and Canceled "
    "(dynamic exclusion, not a hardcoded include-list).\n"
    "Excluded statuses: Cancelled, Canceled."
)

VALIDATION_RULES = (
    "Monthly periods validated: 19.\n"
    "PostgreSQL/HTML differences: 0.\n"
    "Missing order items: 0.\n"
    "Extra order items: 0.\n"
    "Duplicate order items: 0."
)

GAPS_FOUND = (
    "Next step: Monitor future refreshes and validate any newly introduced order statuses under the "
    "dynamic exclusion rule."
)

HARDCODED_THRESHOLDS = (
    "None remaining for order-status inclusion - replaced a fixed seven-status include-list with a "
    "dynamic exclusion rule (EXCLUDED_ORDER_STATUSES = Cancelled, Canceled) in both the SQL extraction "
    "and the JS client engine."
)

EVIDENCE_LOCATION = (
    "07_EVIDENCE\\2026-07-14_utharsika_v002_DYNAMIC_STATUS_FINAL_BUILD_AND_PUBLICATION.md; "
    "07_EVIDENCE\\generated_data\\2026-07-14_utharsika_v002_dynamic_status_monthly_reconciliation.csv; "
    "07_EVIDENCE\\generated_data\\2026-07-14_utharsika_v002_dynamic_status_reference_reconciliation.csv"
)

cfg = load_db_config()
print(f"Connecting to host={cfg.host} port={cfg.port} db={cfg.dbname} user={cfg.user} password={redact(cfg.password)}")
conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user, password=cfg.password, connect_timeout=15)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

try:
    # --- ph_task baseline (read-only, must remain unchanged) ---
    cur.execute(
        "SELECT id, task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
        "FROM tech_team_outputs.ph_task WHERE id = 237"
    )
    ph_task_237_before = cur.fetchone()
    print(f"ph_task 237 before (must remain unchanged): {dict(ph_task_237_before)}")

    # --- Search for existing matching row ---
    cur.execute(
        """
        SELECT id FROM daily_task.tbl_uawso_satheskanth
        WHERE work_date = %(work_date)s
          AND lower(developer) = lower(%(developer)s)
          AND project_code = %(project_code)s
          AND task_title = %(task_title)s
        """,
        {"work_date": WORK_DATE, "developer": DEVELOPER, "project_code": PROJECT_CODE, "task_title": TASK_TITLE},
    )
    matches = cur.fetchall()
    print(f"Existing matching rows before write: {len(matches)} -> {[dict(m) for m in matches]}")

    if len(matches) > 1:
        conn.rollback()
        raise RuntimeError("FAIL_DUPLICATE: more than one matching row found. Refusing to write.")

    if len(matches) == 1:
        row_id = matches[0]["id"]
        cur.execute(
            """
            UPDATE daily_task.tbl_uawso_satheskanth
            SET status = %(status)s, task_summary = %(task_summary)s, work_performed = %(work_performed)s,
                files_modified = %(files_modified)s, decisions_made = %(decisions_made)s,
                validation_rules = %(validation_rules)s, gaps_found = %(gaps_found)s,
                hardcoded_thresholds = %(hardcoded_thresholds)s, evidence_location = %(evidence_location)s,
                updated_at = NOW()
            WHERE id = %(row_id)s
            """,
            {
                "status": STATUS, "task_summary": TASK_SUMMARY, "work_performed": WORK_PERFORMED,
                "files_modified": FILES_MODIFIED, "decisions_made": DECISIONS_MADE,
                "validation_rules": VALIDATION_RULES, "gaps_found": GAPS_FOUND,
                "hardcoded_thresholds": HARDCODED_THRESHOLDS, "evidence_location": EVIDENCE_LOCATION,
                "row_id": row_id,
            },
        )
        action = "UPDATE"
    else:
        cur.execute(
            """
            INSERT INTO daily_task.tbl_uawso_satheskanth
                (work_date, developer, project_name, project_code, domain, aios_phase, status,
                 task_title, task_summary, work_performed, files_modified, decisions_made,
                 validation_rules, gaps_found, hardcoded_thresholds, evidence_location)
            VALUES
                (%(work_date)s, %(developer)s, %(project_name)s, %(project_code)s, %(domain)s, %(aios_phase)s,
                 %(status)s, %(task_title)s, %(task_summary)s, %(work_performed)s, %(files_modified)s,
                 %(decisions_made)s, %(validation_rules)s, %(gaps_found)s, %(hardcoded_thresholds)s,
                 %(evidence_location)s)
            RETURNING id
            """,
            {
                "work_date": WORK_DATE, "developer": DEVELOPER, "project_name": PROJECT_NAME,
                "project_code": PROJECT_CODE, "domain": DOMAIN, "aios_phase": AIOS_PHASE, "status": STATUS,
                "task_title": TASK_TITLE, "task_summary": TASK_SUMMARY, "work_performed": WORK_PERFORMED,
                "files_modified": FILES_MODIFIED, "decisions_made": DECISIONS_MADE,
                "validation_rules": VALIDATION_RULES, "gaps_found": GAPS_FOUND,
                "hardcoded_thresholds": HARDCODED_THRESHOLDS, "evidence_location": EVIDENCE_LOCATION,
            },
        )
        row_id = cur.fetchone()["id"]
        action = "INSERT"

    print(f"Action performed: {action}, row id: {row_id}")

    # --- Pre-commit verification ---
    cur.execute("SELECT * FROM daily_task.tbl_uawso_satheskanth WHERE id = %(rid)s", {"rid": row_id})
    stored = cur.fetchone()

    cur.execute(
        "SELECT COUNT(*) AS n FROM daily_task.tbl_uawso_satheskanth "
        "WHERE work_date=%(wd)s AND lower(developer)=lower(%(dev)s) AND project_code=%(pc)s AND task_title=%(tt)s",
        {"wd": WORK_DATE, "dev": DEVELOPER, "pc": PROJECT_CODE, "tt": TASK_TITLE},
    )
    match_count_after = cur.fetchone()["n"]

    cur.execute(
        "SELECT id, task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
        "FROM tech_team_outputs.ph_task WHERE id = 237"
    )
    ph_task_237_within_txn = cur.fetchone()

    checks = {
        "correct_table_row_exists": stored is not None,
        "correct_date": str(stored["work_date"]) == WORK_DATE,
        "correct_staff": stored["developer"].lower() == DEVELOPER,
        "correct_project": stored["project_code"] == PROJECT_CODE,
        "correct_commitment_present": COMMITMENT in stored["task_summary"],
        "status_is_complete": stored["status"] == STATUS,
        "result_pass_present": "Result: PASS" in stored["work_performed"],
        "asset_path_present": "2026-07-14_utharsika_v002.html" in stored["files_modified"],
        "evidence_path_present": "DYNAMIC_STATUS_FINAL_BUILD_AND_PUBLICATION" in stored["evidence_location"],
        "exactly_one_matching_row": match_count_after == 1,
        "ph_task_237_unchanged": (
            ph_task_237_within_txn["html_sha256"] == ph_task_237_before["html_sha256"]
            and ph_task_237_within_txn["updated_at"] == ph_task_237_before["updated_at"]
        ),
    }
    print(f"Pre-commit checks: {checks}")

    if not all(checks.values()):
        conn.rollback()
        raise RuntimeError(f"STOP: pre-commit check failed: {checks}. Rolled back, not committed.")

    conn.commit()
    print("COMMITTED.")

finally:
    pass

# --- Post-write verification ---
cur.execute("SELECT * FROM daily_task.tbl_uawso_satheskanth WHERE id = %(rid)s", {"rid": row_id})
final_row = cur.fetchone()
print("\n=== Final stored row ===")
for k, v in final_row.items():
    if isinstance(v, str) and len(v) > 200:
        print(f"{k}: {v[:200]}...[truncated]")
    else:
        print(f"{k}: {v}")

cur.execute(
    "SELECT COUNT(*) AS n FROM daily_task.tbl_uawso_satheskanth "
    "WHERE work_date=%(wd)s AND lower(developer)=lower(%(dev)s) AND project_code=%(pc)s AND task_title=%(tt)s",
    {"wd": WORK_DATE, "dev": DEVELOPER, "pc": PROJECT_CODE, "tt": TASK_TITLE},
)
print(f"\nMatching rows after write: {cur.fetchone()['n']}")

cur.execute(
    "SELECT id, task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
    "FROM tech_team_outputs.ph_task WHERE id = 237"
)
ph_task_237_after = cur.fetchone()
print(f"ph_task 237 after (must be unchanged): {dict(ph_task_237_after)}")
print(f"ph_task 237 unchanged: {ph_task_237_after['html_sha256'] == ph_task_237_before['html_sha256'] and ph_task_237_after['updated_at'] == ph_task_237_before['updated_at']}")

cur.close()
conn.close()
print("Connection closed.")
