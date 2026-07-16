import json, os, psycopg2, psycopg2.extras
conn = psycopg2.connect(host=os.environ["PGHOST"], port=os.environ["PGPORT"], dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"], password=os.environ["PGPASSWORD"])
conn.set_session(readonly=True, autocommit=True)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

ASSIGNED_CTE = """
    WITH target_user AS (
        SELECT "user" AS user_id FROM public."user" WHERE lower(user_name) = lower('utharsika')
    ),
    target_categories AS (
        SELECT DISTINCT c.id AS category_id FROM public.ph_categories c JOIN target_user u ON u.user_id = c.user_id
    ),
    assigned_asins AS (
        SELECT DISTINCT p.ref_id AS asin FROM public.ph_cate_products p JOIN target_categories c ON c.category_id = p.ass_cate_id WHERE p.which_channel = 1
    )
"""

months = [
  ("2025-01","2025-01-01","2025-01-31"), ("2025-02","2025-02-01","2025-02-28"), ("2025-03","2025-03-01","2025-03-31"),
  ("2025-04","2025-04-01","2025-04-30"), ("2025-05","2025-05-01","2025-05-31"), ("2025-06","2025-06-01","2025-06-30"),
  ("2025-07","2025-07-01","2025-07-31"), ("2025-08","2025-08-01","2025-08-31"), ("2025-09","2025-09-01","2025-09-30"),
  ("2025-10","2025-10-01","2025-10-31"), ("2025-11","2025-11-01","2025-11-30"), ("2025-12","2025-12-01","2025-12-31"),
  ("2026-01","2026-01-01","2026-01-31"), ("2026-02","2026-02-01","2026-02-28"), ("2026-03","2026-03-01","2026-03-31"),
  ("2026-04","2026-04-01","2026-04-30"), ("2026-05","2026-05-01","2026-05-31"), ("2026-06","2026-06-01","2026-06-30"),
  ("2026-07","2026-07-01","2026-07-13"),
]

print(f"{'month':8} {'vendor_sales_correct_overlap':>28} {'vendor_units':>14}")
for label, start, end in months:
    cur.execute(
        ASSIGNED_CTE + """
        SELECT COALESCE(SUM(v.ordered_revenue),0) AS sales, COALESCE(SUM(v.ordered_units),0) AS units, COUNT(*) AS rows
        FROM public.vendor_sales v
        JOIN assigned_asins a ON a.asin = v.asin
        WHERE NOT (v.end_time::date <= %(start)s::date OR v.start_time::date > %(end)s::date)
        """,
        {"start": start, "end": end},
    )
    r = cur.fetchone()
    print(f"{label:8} {float(r['sales']):>28.2f} {int(r['units']):>14}  (rows={r['rows']})")

cur.close(); conn.close()
