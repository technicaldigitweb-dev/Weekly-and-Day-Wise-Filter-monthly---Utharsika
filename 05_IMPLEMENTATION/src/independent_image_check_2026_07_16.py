import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config  # noqa: E402
import psycopg2  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
IDENTITY = "2026-07-16_utharsika_v001"
EVIDENCE_DIR = os.path.join(ROOT, "07_EVIDENCE", "generated_data")

with open(os.path.join(EVIDENCE_DIR, f"{IDENTITY}_product_master_asin_level.json")) as f:
    pm = json.load(f)
html_by_asin = {r["asin"]: r["image_url"] for r in pm}

cfg = load_db_config()
conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                         password=cfg.password, connect_timeout=15)
conn.set_session(readonly=True, autocommit=True)
try:
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH valid_rows AS (
                SELECT ref_id AS asin, id, main_image_url,
                       ROW_NUMBER() OVER (PARTITION BY ref_id ORDER BY id ASC) AS rn
                FROM public.listing_data
                WHERE which_channel = 1 AND market_place = 'UK' AND wrong_sku = 0
                  AND main_image_url IS NOT NULL AND BTRIM(main_image_url) <> ''
            )
            SELECT asin, main_image_url FROM valid_rows WHERE rn = 1
            """
        )
        source_by_asin = {r[0]: r[1] for r in cur.fetchall()}
finally:
    conn.close()

mismatches = 0
for asin, html_img in html_by_asin.items():
    source_img = source_by_asin.get(asin)
    if source_img != html_img:
        mismatches += 1
        if mismatches <= 5:
            print(f"MISMATCH {asin}: source={source_img} html={html_img}")

print(f"\nTotal ASINs checked: {len(html_by_asin)}")
print(f"Image mismatches: {mismatches}")
