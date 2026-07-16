"""
Merges the incremental 2026-07-10..2026-07-13 daily-split rows (fetched
via MCP, since the direct psycopg2 credential connection was
intermittently refused by the DB host during this session) into the
existing v002 extracted JSON files, and widens product_master_full's
SKU lists for any (asin, sku) pair newly observed in this window.
Read-only against PostgreSQL (no DB call in this script); only local
JSON files are modified.
"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "07_EVIDENCE", "generated_data")
IDENTITY = "2026-07-10_utharsika_v002"
STATE_DIR = os.path.join(os.path.dirname(__file__), "..", "state")


def load(name):
    path = os.path.join(DATA_DIR, f"{IDENTITY}_{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump(name, data):
    path = os.path.join(DATA_DIR, f"{IDENTITY}_{name}.json")
    with open(path, "wb") as f:
        f.write(json.dumps(data, separators=(",", ":")).encode("utf-8"))
    print(f"Wrote {path} ({os.path.getsize(path)} bytes)")


daily_split = load("daily_aggregates_split")
product_master_full = load("product_master_full")

with open(os.path.join(STATE_DIR, "incremental_daily_split_0710_0713.json"), "r", encoding="utf-8") as f:
    incremental = json.load(f)

print(f"Existing daily_split rows: {len(daily_split)}")
print(f"Incremental rows to add: {len(incremental)}")

existing_keys = set((r["calendar_date"], r["asin"], r["sku"]) for r in daily_split)
new_keys = set((r["calendar_date"], r["asin"], r["sku"]) for r in incremental)
overlap = existing_keys & new_keys
if overlap:
    raise RuntimeError(f"Refusing to merge: {len(overlap)} overlapping (date,asin,sku) keys found - would duplicate rows: {list(overlap)[:5]}")

max_existing_date = max(r["calendar_date"] for r in daily_split)
min_incremental_date = min(r["calendar_date"] for r in incremental)
print(f"Max existing date: {max_existing_date}, min incremental date: {min_incremental_date}")
if min_incremental_date <= max_existing_date:
    raise RuntimeError("Incremental data does not start strictly after existing data - refusing to merge blindly.")

merged_daily_split = daily_split + incremental
merged_daily_split.sort(key=lambda r: (r["calendar_date"], r["asin"], r["sku"]))
print(f"Merged daily_split rows: {len(merged_daily_split)}")

# Widen product master SKU lists for any newly-seen (asin, sku) pair.
asin_to_skus = {p["asin"]: set(p["skus"]) for p in product_master_full}
added_sku_pairs = 0
unknown_asins = []
for r in incremental:
    if r["asin"] not in asin_to_skus:
        unknown_asins.append(r["asin"])
        continue
    if r["sku"] not in asin_to_skus[r["asin"]]:
        asin_to_skus[r["asin"]].add(r["sku"])
        added_sku_pairs += 1

if unknown_asins:
    raise RuntimeError(f"Incremental data references ASIN(s) not in assigned product master - refusing to merge: {unknown_asins}")

print(f"New (asin, sku) pairs added to product master: {added_sku_pairs}")

updated_product_master = []
for p in product_master_full:
    updated_product_master.append({"asin": p["asin"], "skus": sorted(asin_to_skus[p["asin"]])})

no_sku_count = sum(1 for p in updated_product_master if not p["skus"])
with_sku_count = len(updated_product_master) - no_sku_count
print(f"Product master: {len(updated_product_master)} ASINs, {with_sku_count} with SKU, {no_sku_count} without (was widened by {added_sku_pairs} pairs)")

dump("daily_aggregates_split", merged_daily_split)
dump("product_master_full", updated_product_master)

print("DONE. Vendor periods and assigned_asins files are unchanged (not date-bounded, already current).")
