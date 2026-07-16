"""
Authorized UPDATE (content-only) of tech_team_outputs.ph_task.id = 256 -
replaces html_content with the corrected 15-row-viewport v004 HTML.
Explicitly approved by the user. Does not touch any other row, does not
insert, does not change task identity/assigned user/team/requirement/
deliverable/report date/version/project code/KPI values/data range.

Reuses the same approved credential mechanism (config/.env via
config.config.load_db_config()) and connection pattern as the existing
publish_uawso_v004_2026_07_15.py script - no new publisher, no new
credential mechanism.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config  # noqa: E402
import psycopg2  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
TARGET_PATH = os.path.join(ROOT, "09_OUTPUTS", "2026-07-15_utharsika_v004.html")
ROW_ID = 256
EXPECTED_TASK_ID = "UAWSO-2026-07-15-utharsika-v004"
EXPECTED_VERSION_LEVEL = 4
EXPECTED_NEW_SHA256 = "51865bbb45a5b49c15c74156723efa12d8ec6211f397487e9dec12f288587b24"
EXPECTED_NEW_SIZE = 5124804


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    size = os.path.getsize(TARGET_PATH)
    digest = sha256_of(TARGET_PATH)
    print(f"Local file size: {size} (expected {EXPECTED_NEW_SIZE})")
    print(f"Local file SHA-256: {digest}")
    if size != EXPECTED_NEW_SIZE or digest != EXPECTED_NEW_SHA256:
        print("LOCAL_FILE_MISMATCH")
        sys.exit(1)
    print("Local file verified: MATCH")

    with open(TARGET_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                             password=cfg.password, connect_timeout=15)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # Pre-update baseline (read-only)
            cur.execute(
                "SELECT id, task_id, version_level, version_status, project_code, assigned_user, "
                "assigned_user_team, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, "
                "updated_at FROM tech_team_outputs.ph_task WHERE id = %(id)s",
                {"id": ROW_ID},
            )
            before = cur.fetchone()
            print(f"\nRow {ROW_ID} before update: task_id={before[1]} version_level={before[2]} "
                  f"version_status={before[3]} html_sha256={before[7]} updated_at={before[8]}")

            if before[1] != EXPECTED_TASK_ID or before[2] != EXPECTED_VERSION_LEVEL:
                raise RuntimeError(
                    f"STOP: row {ROW_ID} identity mismatch - task_id={before[1]} version_level={before[2]}, "
                    f"expected task_id={EXPECTED_TASK_ID} version_level={EXPECTED_VERSION_LEVEL}"
                )

            cur.execute(
                "SELECT id, task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
                "FROM tech_team_outputs.ph_task WHERE id IN (157, 237)"
            )
            other_before = {r[0]: r for r in cur.fetchall()}
            print(f"Baseline (must remain unchanged): {other_before}")

            # The single permitted operation: UPDATE by primary key, content only
            cur.execute(
                "UPDATE tech_team_outputs.ph_task SET html_content = %(html)s, updated_at = now() "
                "WHERE id = %(id)s",
                {"html": html_content, "id": ROW_ID},
            )
            affected = cur.rowcount
            print(f"\nRows affected by UPDATE: {affected}")

            if affected != 1:
                conn.rollback()
                raise RuntimeError(f"STOP: expected exactly 1 row affected, got {affected}. Rolled back.")

            # Pre-commit verification
            cur.execute(
                "SELECT id, task_id, version_level, project_code, assigned_user, assigned_user_team, "
                "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, "
                "length(html_content) AS char_len "
                "FROM tech_team_outputs.ph_task WHERE id = %(id)s",
                {"id": ROW_ID},
            )
            within_txn = cur.fetchone()

            cur.execute(
                "SELECT id, task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
                "FROM tech_team_outputs.ph_task WHERE id IN (157, 237)"
            )
            other_within_txn = {r[0]: r for r in cur.fetchall()}

            checks = {
                "task_id_unchanged": within_txn[1] == EXPECTED_TASK_ID,
                "version_level_unchanged": within_txn[2] == EXPECTED_VERSION_LEVEL,
                "project_code_unchanged": within_txn[3] == "UAWSO",
                "assigned_user_unchanged": within_txn[4] == "utharsika",
                "assigned_user_team_unchanged": within_txn[5] == "ph_priors",
                "stored_html_matches_local": within_txn[6] == EXPECTED_NEW_SHA256,
                "row_157_unchanged": other_within_txn[157][2] == other_before[157][2] and other_within_txn[157][3] == other_before[157][3],
                "row_237_unchanged": other_within_txn[237][2] == other_before[237][2] and other_within_txn[237][3] == other_before[237][3],
                "exactly_one_row_affected": affected == 1,
            }
            print(f"\nPre-commit checks: {checks}")

            if not all(checks.values()):
                conn.rollback()
                raise RuntimeError(f"STOP: pre-commit check failed: {checks}. Rolled back, not committed.")

        conn.commit()
        print("\nCOMMITTED.")

        # Post-commit verification
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, task_id, version_level, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, "
                "length(html_content) AS char_len, updated_at "
                "FROM tech_team_outputs.ph_task WHERE id = %(id)s",
                {"id": ROW_ID},
            )
            after = cur.fetchone()
            print(f"\nPost-commit row {ROW_ID}: task_id={after[1]} version_level={after[2]} "
                  f"html_sha256={after[3]} char_len={after[4]} updated_at={after[5]}")
            print(f"Stored/local SHA-256 match: {after[3] == EXPECTED_NEW_SHA256}")

            cur.execute(
                "SELECT id, task_id, encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
                "FROM tech_team_outputs.ph_task WHERE id IN (157, 237)"
            )
            other_after = {r[0]: r for r in cur.fetchall()}
            print(f"Row 157 after: {other_after[157]}")
            print(f"Row 237 after: {other_after[237]}")
            print(f"Row 157 unchanged: {other_after[157][2] == other_before[157][2] and other_after[157][3] == other_before[157][3]}")
            print(f"Row 237 unchanged: {other_after[237][2] == other_before[237][2] and other_after[237][3] == other_before[237][3]}")

            cur.execute("SELECT COUNT(*) FROM tech_team_outputs.ph_task WHERE project_code = 'UAWSO'")
            uawso_count = cur.fetchone()[0]
            print(f"Total UAWSO rows after update (must be unchanged count, still 3): {uawso_count}")

        print(f"\nFINAL: row_id={ROW_ID} action=UPDATE rows_inserted=0 rows_updated=1 rows_deleted=0")

    finally:
        conn.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()
