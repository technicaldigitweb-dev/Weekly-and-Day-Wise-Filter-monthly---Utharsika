"""
Publishes the approved 2026-07-15_utharsika_v004.html to
tech_team_outputs.ph_task as a new row (REQ-02-D01 v004).

Reuses src/ph_task_publisher.publish_report() unmodified - this script
only wires together: (a) the existing approved credential template at
02_SOURCE/db_access_templates/temp_user.py (imported, never retyped),
(b) config.config.load_db_config() (existing loader, unmodified), and
(c) the existing publisher. No new publication logic is introduced.

Credential values are never printed. Only [REDACTED] placeholders are
shown for PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD.
"""
import hashlib
import importlib.util
import os
import sys
from datetime import date

import psycopg2

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.config import load_db_config  # noqa: E402
from src import ph_task_publisher  # noqa: E402
from src import version_resolver  # noqa: E402

TARGET_PATH = os.path.join(ROOT, "09_OUTPUTS", "2026-07-15_utharsika_v004.html")
EXPECTED_SIZE = 5123369
EXPECTED_SHA256 = "8751b4d373772d4bc38c5e424000f846b842b61b73a9bb40368ba71df57d6f1e"
REPORT_DATE = date(2026, 7, 15)
VERSION = 4
TASK_NAME = "UAWSO REQ-02-D01 - ASIN-Level Sales and Orders Report (v004)"
DESCRIPTION = (
    "Requirement ID: REQ-02. Deliverable ID: REQ-02-D01. Result: PASS.\n"
    "Report grain: one row per ASIN. ASIN rows: 1,723.\n"
    "Data range: 2025-01-01 through 2026-07-14.\n"
    "Sales: 718835.91 GBP. Orders: 34,454. Quantity: 47,166.\n"
    "Image column added (deterministic listing_data.main_image_url selection, ref_id join). "
    "Sticky header/first-two-columns, single CSV download of the full filtered set, "
    "Column Definitions panel, and sticky pagination bar with go-to-page all included."
)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_temp_user_config():
    """Imports DB_CONFIG straight from the approved template file - the
    values are never retyped by hand, only moved from that file into
    this process's environment."""
    template_path = os.path.join(ROOT, "02_SOURCE", "db_access_templates", "temp_user.py")
    spec = importlib.util.spec_from_file_location("temp_user_template", template_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.DB_CONFIG


def main():
    # --- Phase 2: local file verification (fail fast, no DB needed yet) ---
    if not os.path.exists(TARGET_PATH):
        print("LOCAL_FILE_MISMATCH: target file does not exist")
        sys.exit(1)
    size = os.path.getsize(TARGET_PATH)
    digest = sha256_of(TARGET_PATH)
    print(f"Local file size: {size} (expected {EXPECTED_SIZE})")
    print(f"Local file SHA-256: {digest}")
    if size != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        print("LOCAL_FILE_MISMATCH")
        sys.exit(1)
    print("Local file verified: MATCH")

    # --- Phase 1: recover credentials (held in memory only) ---
    raw_cfg = load_temp_user_config()
    os.environ["PGHOST"] = str(raw_cfg["host"])
    os.environ["PGPORT"] = str(raw_cfg["port"])
    os.environ["PGDATABASE"] = str(raw_cfg["dbname"])
    os.environ["PGUSER"] = str(raw_cfg["user"])
    os.environ["PGPASSWORD"] = str(raw_cfg["password"])
    cfg = load_db_config()
    print("Credentials recovered from 02_SOURCE/db_access_templates/temp_user.py: "
          "PGHOST=[REDACTED] PGPORT=[REDACTED] PGDATABASE=[REDACTED] PGUSER=[REDACTED] PGPASSWORD=[REDACTED]")

    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                             password=cfg.password, connect_timeout=15)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # --- Phase 3: live schema inspection (read-only) ---
            cur.execute(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_schema='tech_team_outputs' AND table_name='ph_task' "
                "ORDER BY ordinal_position"
            )
            cols = cur.fetchall()
            print("\nLive ph_task columns:")
            for c in cols:
                print(f"  {c[0]} ({c[1]}, nullable={c[2]})")

            # --- Phase 4: duplicate + historical baseline (read-only) ---
            cur.execute(
                "SELECT id, task_id, version_level, "
                "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
                "FROM tech_team_outputs.ph_task WHERE project_code = 'UAWSO' ORDER BY id"
            )
            baseline = cur.fetchall()
            print("\nUAWSO rows before publish:")
            for r in baseline:
                print(f"  id={r[0]} task_id={r[1]} version_level={r[2]} html_sha256={r[3]} updated_at={r[4]}")

            exact_dup = [r for r in baseline if r[3] == EXPECTED_SHA256]
            if exact_dup:
                print(f"\nALREADY_PUBLISHED: row id={exact_dup[0][0]} already stores this exact HTML content.")
                conn.rollback()
                return

        # --- Phase 5/6: publish via the existing, unmodified publisher ---
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

        # --- Phase 7: post-commit verification ---
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, task_id, version_level, version_status, "
                "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, "
                "length(html_content) AS char_len, updated_at "
                "FROM tech_team_outputs.ph_task WHERE id = %(id)s",
                {"id": result.inserted_row_id},
            )
            stored = cur.fetchone()
            print(f"\nStored row (post-commit): id={stored[0]} task_id={stored[1]} "
                  f"version_level={stored[2]} version_status={stored[3]} "
                  f"html_sha256={stored[4]} char_len={stored[5]} updated_at={stored[6]}")
            print(f"Stored/local SHA-256 match: {stored[4] == EXPECTED_SHA256}")

            # Re-verify every pre-existing UAWSO row is untouched
            cur.execute(
                "SELECT id, task_id, version_level, "
                "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, updated_at "
                "FROM tech_team_outputs.ph_task WHERE project_code = 'UAWSO' AND id != %(new_id)s ORDER BY id",
                {"new_id": result.inserted_row_id},
            )
            after = cur.fetchall()
            before_by_id = {r[0]: r for r in baseline}
            all_unchanged = True
            print("\nOther UAWSO rows after publish (must be unchanged):")
            for r in after:
                prior = before_by_id.get(r[0])
                unchanged = prior is not None and prior[3] == r[3] and prior[4] == r[4]
                if not unchanged:
                    all_unchanged = False
                print(f"  id={r[0]} task_id={r[1]} html_sha256={r[3]} updated_at={r[4]} unchanged={unchanged}")
            print(f"\nAll other UAWSO rows unchanged: {all_unchanged}")

        version_resolver.consume_version_on_success(REPORT_DATE, VERSION)
        print(f"\nVersion state updated: report_date={REPORT_DATE.isoformat()} version={VERSION}")
        print(f"\nFINAL: inserted_row_id={result.inserted_row_id} task_id={result.task_id} committed={result.committed}")

    finally:
        conn.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    main()
