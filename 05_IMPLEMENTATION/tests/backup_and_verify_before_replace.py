"""
One-off, read-only: fetch the CURRENT stored html_content for ph_task
row id=157 (the UAWSO v001 row), save it as a local backup, and compute
its true SHA-256 - so the before-state is provably accurate rather than
assumed from an earlier session's own claim.

Read-only. No write to the database.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.config import load_db_config

BACKUP_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "07_EVIDENCE", "ph_task_backups",
                            "2026-07-10_utharsika_v001_before_replace.html")


def main():
    import psycopg2
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user, password=cfg.password, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT html_content, length(html_content) FROM tech_team_outputs.ph_task WHERE id = 157")
            row = cur.fetchone()
            if row is None:
                print("ROW NOT FOUND - abort")
                sys.exit(1)
            content, db_len = row
    finally:
        conn.close()

    data = content.encode("utf-8")
    sha = hashlib.sha256(data).hexdigest()

    os.makedirs(os.path.dirname(BACKUP_PATH), exist_ok=True)
    with open(BACKUP_PATH, "wb") as f:
        f.write(data)

    print(f"DB-reported length() (characters): {db_len}")
    print(f"Python len(content) (characters): {len(content)}")
    print(f"Backup written: {BACKUP_PATH}")
    print(f"Backup file size (bytes): {os.path.getsize(BACKUP_PATH)}")
    print(f"SHA-256 of stored content (as currently in the database): {sha}")


if __name__ == "__main__":
    main()
