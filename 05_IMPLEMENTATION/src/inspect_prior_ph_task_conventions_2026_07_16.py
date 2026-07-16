"""
Read-only inspection: exact assigned_user (from public.user), and the
established team/phase_level/project_name conventions from the most
recent UAWSO ph_task row (256), plus a duplicate-check for any existing
2026-07-16 UAWSO row.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config  # noqa: E402
import psycopg2  # noqa: E402
import psycopg2.extras  # noqa: E402


def main():
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                             password=cfg.password, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_name, user_firstname, user_status FROM public.\"user\" WHERE lower(user_name) = lower('utharsika')")
            print("Resolved PH user row(s):", cur.fetchall())

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, project_name, project_code, task_name, task_id, team, developer, "
                "assigned_user, assigned_user_team, phase_level, version_level, version_status, updated_at "
                "FROM tech_team_outputs.ph_task WHERE id = 256"
            )
            row256 = cur.fetchone()
            print("\nRow 256 (most recent UAWSO publication) conventions:")
            for k, v in row256.items():
                print(f"  {k}: {v}")

            cur.execute(
                "SELECT id, task_id, task_name, assigned_user, version_level, version_status, updated_at "
                "FROM tech_team_outputs.ph_task "
                "WHERE project_code = 'UAWSO' AND task_id LIKE 'UAWSO-2026-07-16%'"
            )
            existing_0716 = cur.fetchall()
            print(f"\nExisting UAWSO rows matching task_id LIKE 'UAWSO-2026-07-16%%': {len(existing_0716)}")
            for r in existing_0716:
                print(" ", dict(r))

            cur.execute(
                "SELECT id, task_id, assigned_user, updated_at "
                "FROM tech_team_outputs.ph_task "
                "WHERE project_code = 'UAWSO' AND lower(assigned_user) = lower('utharsika') "
                "AND (description ILIKE '%%2026-07-16%%' OR task_name ILIKE '%%2026-07-16%%')"
            )
            existing_desc = cur.fetchall()
            print(f"\nExisting UAWSO rows mentioning 2026-07-16 in task_name/description: {len(existing_desc)}")
            for r in existing_desc:
                print(" ", dict(r))

            cur.execute("SELECT COUNT(*) AS n FROM tech_team_outputs.ph_task WHERE project_code='UAWSO'")
            print("\nTotal UAWSO rows currently in ph_task:", cur.fetchone()["n"])
    finally:
        conn.close()


if __name__ == "__main__":
    main()
