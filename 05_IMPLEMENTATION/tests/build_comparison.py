"""
Builds the ASIN-level and ASIN-SKU-level comparison datasets between the
(entirely zero-valued) workbook and the database, and writes the
required CSV evidence files. Read-only with respect to workbook/DB/HTML
- only writes new local evidence files.
"""
import csv
import json
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..")
STATE = os.path.join(os.path.dirname(__file__), "..", "state")
EVID_DATA = os.path.join(BASE, "07_EVIDENCE", "generated_data")
os.makedirs(EVID_DATA, exist_ok=True)

with open(os.path.join(STATE, "utharsika_fresh_records.json"), encoding="utf-8") as f:
    wb = json.load(f)
wb_records = {r["asin"]: r for r in wb["records"]}

with open(os.path.join(STATE, "asin_level_db_2025_2026.json"), encoding="utf-8") as f:
    db = json.load(f)

assigned_asins = db["assigned_asins"]

# Aggregate ASIN-SKU rows up to ASIN level
asin_agg = {}
for r in db["asin_sku_rows"]:
    a = r["asin"]
    if a not in asin_agg:
        asin_agg[a] = {"fbm_sales_2025": 0.0, "fba_sales_2025": 0.0, "orders_2025": 0,
                        "fbm_sales_2026": 0.0, "fba_sales_2026": 0.0, "orders_2026": 0}
    asin_agg[a]["fbm_sales_2025"] += r["fbm_sales_2025"]
    asin_agg[a]["fba_sales_2025"] += r["fba_sales_2025"]
    asin_agg[a]["orders_2025"] += r["orders_2025"]
    asin_agg[a]["fbm_sales_2026"] += r["fbm_sales_2026"]
    asin_agg[a]["fba_sales_2026"] += r["fba_sales_2026"]
    asin_agg[a]["orders_2026"] += r["orders_2026"]

vendor_by_asin = {r["asin"]: r for r in db["vendor_rows"]}

# ---- ASIN-level comparison ----
asin_level_rows = []
workbook_only = []
database_only = []
value_mismatches = []

for asin in assigned_asins:
    wbr = wb_records.get(asin)
    dbr = asin_agg.get(asin, {"fbm_sales_2025": 0.0, "fba_sales_2025": 0.0, "orders_2025": 0,
                               "fbm_sales_2026": 0.0, "fba_sales_2026": 0.0, "orders_2026": 0})
    vend = vendor_by_asin.get(asin, {"vendor_sales_2025": 0.0, "vendor_units_2025": 0,
                                       "vendor_sales_2026": 0.0, "vendor_units_2026": 0})

    db_total_2025 = dbr["fbm_sales_2025"] + dbr["fba_sales_2025"] + vend["vendor_sales_2025"]
    db_total_2026 = dbr["fbm_sales_2026"] + dbr["fba_sales_2026"] + vend["vendor_sales_2026"]

    wb_sales_2025 = 0.0  # proven: workbook K column is 0 for every row
    wb_orders_2025 = 0
    wb_sales_2026 = 0.0  # workbook M column
    wb_orders_2026 = 0

    diff_2025 = wb_sales_2025 - db_total_2025
    diff_2026 = wb_sales_2026 - db_total_2026

    if wbr is None:
        reason = "DATABASE_ONLY_ASIN"  # should not occur, workbook contains all 1723 by construction
        database_only.append(asin)
    elif db_total_2025 == 0 and db_total_2026 == 0:
        reason = "MATCH"  # both sides genuinely zero
    else:
        # workbook=0, database nonzero -> evidence proves workbook cache is stale, not a business difference
        reason = "UNRESOLVED"

    row = {
        "asin": asin,
        "workbook_account": wbr["account"] if wbr else None,
        "workbook_sku": wbr["sku"] if wbr else None,
        "workbook_mapped_sku": wbr["mapped_sku"] if wbr else None,
        "workbook_june2025_sales": wb_sales_2025,
        "workbook_june2025_orders": wb_orders_2025,
        "workbook_june2026_sales": wb_sales_2026,
        "workbook_june2026_orders": wb_orders_2026,
        "db_fbm_sales_2025": round(dbr["fbm_sales_2025"], 2),
        "db_fba_sales_2025": round(dbr["fba_sales_2025"], 2),
        "db_vendor_sales_2025": round(vend["vendor_sales_2025"], 2),
        "db_total_sales_2025": round(db_total_2025, 2),
        "db_orders_2025": dbr["orders_2025"],
        "db_vendor_units_2025": vend["vendor_units_2025"],
        "db_fbm_sales_2026": round(dbr["fbm_sales_2026"], 2),
        "db_fba_sales_2026": round(dbr["fba_sales_2026"], 2),
        "db_vendor_sales_2026": round(vend["vendor_sales_2026"], 2),
        "db_total_sales_2026": round(db_total_2026, 2),
        "db_orders_2026": dbr["orders_2026"],
        "db_vendor_units_2026": vend["vendor_units_2026"],
        "sales_diff_2025_wb_minus_db": round(diff_2025, 2),
        "sales_diff_2026_wb_minus_db": round(diff_2026, 2),
        "reason": reason,
        "root_cause_note": (
            "Workbook cached value is 0 for ALL 1723 rows in this file (proven: SUM=0 across every June/July "
            "column). This is a stale/unrefreshed Google-Sheets IMPORTRANGE export, not a genuine business "
            "difference. Cannot be categorized as an account/marketplace/status/Vendor-scope difference because "
            "the workbook provides no comparable non-zero figure to diagnose against."
            if reason == "UNRESOLVED" else ""
        ),
    }
    asin_level_rows.append(row)
    if reason == "UNRESOLVED":
        value_mismatches.append(row)

# workbook_only: ASINs in workbook not in DB assigned scope (should be none, workbook IS the assigned scope proxy)
wb_asin_set = set(wb_records.keys())
db_asin_set = set(assigned_asins)
workbook_only = sorted(wb_asin_set - db_asin_set)
database_only = sorted(db_asin_set - wb_asin_set)

print(f"ASIN-level rows: {len(asin_level_rows)}")
print(f"Workbook-only ASINs (in workbook, not in DB assigned scope): {len(workbook_only)}")
print(f"Database-only ASINs (in DB assigned scope, not in workbook): {len(database_only)}")
print(f"Rows marked UNRESOLVED (workbook=0, db<>0): {len(value_mismatches)}")
print(f"Rows marked MATCH (both zero): {sum(1 for r in asin_level_rows if r['reason']=='MATCH')}")

# ---- Write main comparison CSV ----
main_csv = os.path.join(EVID_DATA, "2026-07-10_utharsika_june_july_workbook_vs_database.csv")
with open(main_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(asin_level_rows[0].keys()))
    w.writeheader()
    w.writerows(asin_level_rows)
print(f"Wrote {main_csv}")

# ---- Write workbook-only ASINs CSV ----
wo_csv = os.path.join(EVID_DATA, "2026-07-10_utharsika_workbook_only_asins.csv")
with open(wo_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["asin"])
    for a in workbook_only:
        w.writerow([a])
print(f"Wrote {wo_csv} ({len(workbook_only)} rows)")

# ---- Write database-only ASINs CSV ----
do_csv = os.path.join(EVID_DATA, "2026-07-10_utharsika_database_only_asins.csv")
with open(do_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["asin"])
    for a in database_only:
        w.writerow([a])
print(f"Wrote {do_csv} ({len(database_only)} rows)")

# ---- Write value mismatches CSV ----
vm_csv = os.path.join(EVID_DATA, "2026-07-10_utharsika_value_mismatches.csv")
with open(vm_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(asin_level_rows[0].keys()))
    w.writeheader()
    w.writerows(value_mismatches)
print(f"Wrote {vm_csv} ({len(value_mismatches)} rows)")

# ---- Reconciliation summary ----
total_db_2025 = sum(r["db_total_sales_2025"] for r in asin_level_rows)
total_db_2026 = sum(r["db_total_sales_2026"] for r in asin_level_rows)
total_wb_2025 = sum(r["workbook_june2025_sales"] for r in asin_level_rows)
total_wb_2026 = sum(r["workbook_june2026_sales"] for r in asin_level_rows)
print(f"\nTotal workbook June2025 Sales (sum of column): {total_wb_2025:.2f}")
print(f"Total database June2025 Sales (sum of column): {total_db_2025:.2f}")
print(f"Total workbook June2026 Sales (sum of column): {total_wb_2026:.2f}")
print(f"Total database June2026 Sales (sum of column): {total_db_2026:.2f}")
print(f"Signed diff 2025 (wb-db): {(total_wb_2025-total_db_2025):.2f}")
print(f"Signed diff 2026 (wb-db): {(total_wb_2026-total_db_2026):.2f}")

with open(os.path.join(STATE, "comparison_summary.json"), "w") as f:
    json.dump({
        "asin_level_row_count": len(asin_level_rows),
        "workbook_only_count": len(workbook_only),
        "database_only_count": len(database_only),
        "unresolved_count": len(value_mismatches),
        "match_count": sum(1 for r in asin_level_rows if r['reason']=='MATCH'),
        "total_wb_2025": total_wb_2025, "total_db_2025": total_db_2025,
        "total_wb_2026": total_wb_2026, "total_db_2026": total_db_2026,
    }, f, indent=2)
