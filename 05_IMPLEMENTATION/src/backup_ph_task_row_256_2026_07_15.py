"""
Read-only backup of tech_team_outputs.ph_task row 256's current
html_content, taken before the 15-row-viewport correction is applied.
Writes the full HTML straight from the database to a local file (never
routed through chat/tool-result text) plus a small metadata file.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config  # noqa: E402
import psycopg2  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT_DIR = os.path.join(ROOT, "07_EVIDENCE", "ph_task_backups")
HTML_OUT = os.path.join(OUT_DIR, "2026-07-15_utharsika_v004_row_256_before_15_row_view_update.html")
META_OUT = os.path.join(OUT_DIR, "2026-07-15_utharsika_v004_row_256_before_15_row_view_update.meta.json")

ROW_ID = 256


def main():
    cfg = load_db_config()
    conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                             password=cfg.password, connect_timeout=15)
    conn.set_session(readonly=True, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, task_id, version_level, version_status, html_content, "
                "encode(sha256(convert_to(html_content,'UTF8')),'hex') AS html_sha256, "
                "length(html_content) AS char_len, updated_at "
                "FROM tech_team_outputs.ph_task WHERE id = %(id)s",
                {"id": ROW_ID},
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError(f"STOP: row id={ROW_ID} not found")
            id_, task_id, version_level, version_status, html_content, html_sha256, char_len, updated_at = row

        os.makedirs(OUT_DIR, exist_ok=True)
        with open(HTML_OUT, "w", encoding="utf-8", newline="") as f:
            f.write(html_content)

        byte_size = os.path.getsize(HTML_OUT)
        file_sha256 = hashlib.sha256(open(HTML_OUT, "rb").read()).hexdigest()

        meta = {
            "row_id": id_, "task_id": task_id, "version_level": version_level,
            "version_status": version_status, "stored_html_sha256_in_db": html_sha256,
            "stored_char_len_in_db": char_len, "backup_file_sha256": file_sha256,
            "backup_file_byte_size": byte_size, "updated_at_before_backup": str(updated_at),
            "backup_path": HTML_OUT,
        }
        with open(META_OUT, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        print(f"Backed up row {id_} ({task_id}) to {HTML_OUT}")
        print(f"DB html_sha256: {html_sha256}")
        print(f"Backup file sha256: {file_sha256}")
        print(f"Match: {html_sha256 == file_sha256}")
        print(f"Metadata written: {META_OUT}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
