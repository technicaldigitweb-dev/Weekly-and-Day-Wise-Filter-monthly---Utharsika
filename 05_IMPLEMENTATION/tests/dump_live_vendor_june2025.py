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
        SELECT DISTINCT p.ref_id AS asin
        FROM public.ph_cate_products p
        JOIN target_categories c ON c.category_id = p.ass_cate_id
        WHERE p.which_channel = 1
    )
"""

cur.execute(ASSIGNED_CTE + """
    SELECT v.asin, v.start_time, v.end_time, v.ordered_units, v.ordered_revenue, v.created_at, v.updated_at
    FROM public.vendor_sales v
    JOIN assigned_asins a ON a.asin = v.asin
    WHERE v.start_time <= '2025-07-01'::date AND v.end_time >= '2025-06-01'::date
    ORDER BY v.asin, v.start_time
""")
rows = [dict(r) for r in cur.fetchall()]
print("Row count with strict monthly boundary (start<=2025-07-01, end>=2025-06-01):", len(rows))
for r in rows:
    print(r)
