"""
Read-only inspection of daily_task.tbl_uawso_satheskanth: schema,
constraints, and existing rows matching the target identity. No write.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config  # noqa: E402
import psycopg2  # noqa: E402
import psycopg2.extras  # noqa: E402

WORK_DATE = "2026-07-15"
DEVELOPER = "satheskanth"
PROJECT_CODE = "UAWSO"
REQUIREMENT_ID = "REQ-02"
DELIVERABLE_ID = "REQ-02-D01"


def main():
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                             password=cfg.password, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name, data_type, is_nullable, column_default "
                "FROM information_schema.columns "
                "WHERE table_schema='daily_task' AND table_name='tbl_uawso_satheskanth' "
                "ORDER BY ordinal_position"
            )
            cols = cur.fetchall()
            print("Columns of daily_task.tbl_uawso_satheskanth:")
            for c in cols:
                print(f"  {c[0]} ({c[1]}, nullable={c[2]}, default={c[3]})")

            cur.execute(
                "SELECT tc.constraint_type, tc.constraint_name, kcu.column_name "
                "FROM information_schema.table_constraints tc "
                "JOIN information_schema.key_column_usage kcu "
                "  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema "
                "WHERE tc.table_schema='daily_task' AND tc.table_name='tbl_uawso_satheskanth' "
                "ORDER BY tc.constraint_type, tc.constraint_name"
            )
            constraints = cur.fetchall()
            print("\nConstraints:")
            for c in constraints:
                print(f"  {c[0]} {c[1]} ({c[2]})")

            # Check for CHECK constraints (e.g. status enum) separately
            cur.execute(
                "SELECT con.conname, pg_get_constraintdef(con.oid) "
                "FROM pg_constraint con "
                "JOIN pg_class rel ON rel.oid = con.conrelid "
                "JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace "
                "WHERE nsp.nspname='daily_task' AND rel.relname='tbl_uawso_satheskanth' AND con.contype='c'"
            )
            checks = cur.fetchall()
            print("\nCHECK constraints:")
            for c in checks:
                print(f"  {c[0]}: {c[1]}")

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, work_date, developer, project_code, requirement_id, deliverable_id, "
                "status, updated_at "
                "FROM daily_task.tbl_uawso_satheskanth "
                "WHERE work_date = %(wd)s AND lower(developer) = lower(%(dev)s) "
                "AND project_code = %(pc)s AND requirement_id = %(rid)s AND deliverable_id = %(did)s",
                {"wd": WORK_DATE, "dev": DEVELOPER, "pc": PROJECT_CODE, "rid": REQUIREMENT_ID, "did": DELIVERABLE_ID},
            )
            matches = cur.fetchall()
            print(f"\nExisting matching rows (work_date={WORK_DATE}, developer={DEVELOPER}, "
                  f"project_code={PROJECT_CODE}, requirement_id={REQUIREMENT_ID}, deliverable_id={DELIVERABLE_ID}): "
                  f"{len(matches)}")
            for m in matches:
                print(f"  {dict(m)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
