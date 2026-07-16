import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.config import load_db_config  # noqa: E402
import psycopg2  # noqa: E402

cfg = load_db_config()
conn = psycopg2.connect(host=cfg.host, port=cfg.port, dbname=cfg.dbname, user=cfg.user,
                         password=cfg.password, connect_timeout=15)
conn.set_session(readonly=True, autocommit=True)
try:
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(order_date) FROM public.order_transaction WHERE market_place='UK' AND source_name='AMAZON'")
        max_date = cur.fetchone()[0]
        print("Max order_date (AMAZON, UK):", max_date)

        cur.execute("SELECT COUNT(DISTINCT order_item_info) FROM public.order_transaction WHERE order_date::date = %(d)s AND market_place='UK' AND source_name='AMAZON'", {"d": max_date.date() if max_date else None})
        print("Distinct order items on max date:", cur.fetchone()[0])
finally:
    conn.close()

colombo_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
print("Current Asia/Colombo time (approx, from system clock):", colombo_now.isoformat())
