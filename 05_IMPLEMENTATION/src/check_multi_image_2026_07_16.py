import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config  # noqa: E402
import psycopg2  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
with open(os.path.join(ROOT, "07_EVIDENCE", "generated_data", "2026-07-16_utharsika_v001_assigned_asins.json")) as f:
    assigned = json.load(f)

cfg = load_db_config()
conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                         password=cfg.password, connect_timeout=15)
conn.set_session(readonly=True, autocommit=True)
try:
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH valid_rows AS (
                SELECT ref_id AS asin, id, main_image_url
                FROM public.listing_data
                WHERE which_channel = 1 AND market_place = 'UK' AND wrong_sku = 0
                  AND main_image_url IS NOT NULL AND BTRIM(main_image_url) <> ''
                  AND ref_id = ANY(%(asins)s)
            )
            SELECT COUNT(*) FROM (
                SELECT asin FROM valid_rows GROUP BY asin HAVING COUNT(DISTINCT main_image_url) > 1
            ) sub
            """,
            {"asins": assigned},
        )
        multi_image_count = cur.fetchone()[0]
        print("Multi-image ASIN count (fresh):", multi_image_count)
finally:
    conn.close()
