"""
Publishes the approved 2026-07-16_utharsika_v001.html to
tech_team_outputs.ph_task as a NEW row (new report date - INSERT only,
never touches row 256 or any prior-date row).

Reuses src/ph_task_publisher.publish_report() unmodified, and the same
approved credential mechanism (config/.env via config.config.load_db_config())
used for every prior UAWSO publication - no new publisher, no new
credential mechanism. project_name/team/developer/assigned_user/
assigned_user_team/phase_level all come from the existing config.config
constants (already proven to match every prior UAWSO row exactly, e.g.
row 256), not retyped here.
"""
import hashlib
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config  # noqa: E402
from src import ph_task_publisher  # noqa: E402
from src import version_resolver  # noqa: E402
import psycopg2  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
TARGET_PATH = os.path.join(ROOT, "09_OUTPUTS", "2026-07-16_utharsika_v001.html")
REPORT_DATE = date(2026, 7, 16)
VERSION = 1
TASK_NAME = "Utharsika Weekly and Day Wise Sales and Orders Report - 2026-07-16"
DESCRIPTION = (
    "Fresh Utharsika Sales and Orders report for 2025-01-01 through 2026-07-15. "
    "Uses AMAZON-only FBM/FBA Orders, Vendor ordered_units as Vendor Orders, and "
    "Total Orders = FBM Orders + FBA Orders + Vendor Orders. Quantity output fields "
    "removed. Validated result: 1,723 ASINs, GBP 719453.86 Sales and 38,994 Total Orders."
)
EXPECTED_LOCAL_SHA256 = "b0a781f4d79e5be64fe446bdbe93dd789f4c61f92dfa0dac3e90eb0fdecea2bf"
EXPECTED_LOCAL_SIZE = 5011392


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    size = os.path.getsize(TARGET_PATH)
    digest = sha256_of(TARGET_PATH)
    print(f"Local file size: {size} (expected {EXPECTED_LOCAL_SIZE})")
    print(f"Local file SHA-256: {digest}")
    if size != EXPECTED_LOCAL_SIZE or digest != EXPECTED_LOCAL_SHA256:
        print("LOCAL_HTML_VALIDATION_FAILED")
        sys.exit(1)
    print("Local file verified: MATCH")

    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                             password=cfg.password, connect_timeout=15)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # Duplicate check + row 256 / prior-date baseline (read-only)
            cur.execute(
                "SELECT id, task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
                "FROM tech_team_outputs.ph_task WHERE project_code = 'UAWSO' ORDER BY id"
            )
            baseline = cur.fetchall()
            print("\nUAWSO rows before publish:")
            for r in baseline:
                print(f"  id={r[0]} task_id={r[1]} html_sha256={r[2]} updated_at={r[3]}")

            existing_0716 = [r for r in baseline if r[1] and "2026-07-16" in r[1]]
            if existing_0716:
                exact_match = [r for r in existing_0716 if r[2] == EXPECTED_LOCAL_SHA256]
                if exact_match:
                    print(f"\nALREADY_PUBLISHED: row id={exact_match[0][0]} already stores this exact HTML.")
                    conn.rollback()
                    return
                print(f"\nSAME_DAY_OUTPUT_ALREADY_EXISTS: {existing_0716}")
                conn.rollback()
                return

        # Insert-only via the existing, unmodified publisher
        with open(TARGET_PATH, "r", encoding="utf-8") as f:
            html_content = f.read()

        result = ph_task_publisher.publish_report(
            conn,
            report_date=REPORT_DATE,
            version=VERSION,
            task_name=TASK_NAME,
            html_content=html_content,
            description=DESCRIPTION,
            is_correction=False,
        )
        print(f"\nPublish result: {result}")

        if not result.committed:
            print("\nNOT COMMITTED - see detail above.")
            return

        # Post-commit verification
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, task_id, project_code, assigned_user, assigned_user_team, phase_level, "
                "version_level, version_status, "
                "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
                "FROM tech_team_outputs.ph_task WHERE id = %(id)s",
                {"id": result.inserted_row_id},
            )
            stored = cur.fetchone()
            print(f"\nStored row (post-commit): id={stored[0]} task_id={stored[1]} project_code={stored[2]} "
                  f"assigned_user={stored[3]} assigned_user_team={stored[4]} phase_level={stored[5]} "
                  f"version_level={stored[6]} version_status={stored[7]} html_sha256={stored[8]} updated_at={stored[9]}")
            print(f"Stored/local SHA-256 match: {stored[8] == EXPECTED_LOCAL_SHA256}")

            cur.execute(
                "SELECT id, task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
                "FROM tech_team_outputs.ph_task WHERE project_code = 'UAWSO' AND id != %(new_id)s ORDER BY id",
                {"new_id": result.inserted_row_id},
            )
            after = cur.fetchall()
            before_by_id = {r[0]: r for r in baseline}
            all_unchanged = True
            print("\nOther UAWSO rows after publish (must be unchanged):")
            for r in after:
                prior = before_by_id.get(r[0])
                unchanged = prior is not None and prior[2] == r[2] and prior[3] == r[3]
                if not unchanged:
                    all_unchanged = False
                print(f"  id={r[0]} task_id={r[1]} html_sha256={r[2]} updated_at={r[3]} unchanged={unchanged}")
            print(f"\nAll other UAWSO rows unchanged: {all_unchanged}")

            cur.execute(
                "SELECT COUNT(*) FROM tech_team_outputs.ph_task WHERE project_code='UAWSO' AND task_id LIKE 'UAWSO-2026-07-16%'"
            )
            active_0716_count = cur.fetchone()[0]
            print(f"Active UAWSO rows for 2026-07-16: {active_0716_count}")

        version_resolver.consume_version_on_success(REPORT_DATE, VERSION)
        print(f"\nVersion state updated: report_date={REPORT_DATE.isoformat()} version={VERSION}")
        print(f"\nFINAL: inserted_row_id={result.inserted_row_id} task_id={result.task_id} committed={result.committed}")

    finally:
        conn.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()
