"""
Clean-process verification (Phase 11): run with NO PG* variables
pre-set, confirm config.config.load_db_config() resolves all five from
config/.env, connect, run SELECT 1, and a read-only ph_task SELECT.
Never inserts, updates, or deletes anything. Never prints values.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

assert not any(os.getenv(k) for k in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD")), \
    "STOP: this process already has PG* vars set - not a clean baseline"

from config.config import load_db_config, redact  # noqa: E402
import psycopg2  # noqa: E402

cfg = load_db_config()
print("Clean-process .env load: PASS "
      f"(PGHOST=[REDACTED] PGPORT=[REDACTED] PGDATABASE=[REDACTED] PGUSER=[REDACTED] PGPASSWORD={redact(cfg.password)})")

conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                         password=cfg.password, connect_timeout=15)
try:
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        print(f"SELECT 1 -> {cur.fetchone()[0]}. PostgreSQL connection: PASS")

        cur.execute("SELECT COUNT(*) FROM tech_team_outputs.ph_task WHERE project_code = 'UAWSO'")
        n = cur.fetchone()[0]
        print(f"Read-only ph_task SELECT -> {n} UAWSO rows visible. ph_task SELECT: PASS")
finally:
    conn.close()
    print("Connection closed. No write of any kind was performed in this verification run.")
