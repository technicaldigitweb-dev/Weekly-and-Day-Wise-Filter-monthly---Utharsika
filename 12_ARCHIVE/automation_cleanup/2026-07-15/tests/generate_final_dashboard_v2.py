"""
v2 generation driver: regenerates the SAME v001 identity/path with the
updated full-ASIN-coverage + FBM/FBA/Vendor + CSV/dropdown template.
Does NOT create v002 - overwrites the same staging/final file per the
explicit "update the existing v001 output" instruction.

*** PERMANENTLY DISABLED as of 2026-07-15 - DO NOT RUN. ***
Superseded predecessor of generate_final_dashboard_v3.py (also
disabled - see that file's docstring and
07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md).
This script targets the SAME protected file
(09_OUTPUTS\\2026-07-10_utharsika_v001.html) and embeds the CURRENT
uawso_client_engine.js, not a historical snapshot, so re-running it
would silently overwrite the protected file with non-original bytes.
Archived under the mandatory Historical Output Protection policy
adopted 2026-07-15; kept for historical reference only.

Run: python tests/generate_final_dashboard_v2.py
"""
import sys

print("REFUSED: this script is permanently disabled - it targets a Historical-Output-"
      "Protection-covered file. See the module docstring and "
      "07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md.")
sys.exit(1)

import json  # noqa: E402  (unreachable - kept only so the rest of the file still parses)
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import dashboard_renderer
from src.html_renderer import write_html_and_hash

IDENTITY = "2026-07-10_utharsika_v001"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "07_EVIDENCE", "generated_data")
STAGING_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "09_OUTPUTS", "staging", f"{IDENTITY}.staging.html")
FINAL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "09_OUTPUTS", f"{IDENTITY}.html")


def load(name):
    path = os.path.join(DATA_DIR, f"{IDENTITY}_{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), os.path.getsize(path)


def main():
    product_master_full, pmf_size = load("product_master_full")
    daily_split, ds_size = load("daily_aggregates_split")
    vendor_periods, vp_size = load("vendor_periods")
    assigned_asins, _ = load("assigned_asins")

    no_sku_count = sum(1 for p in product_master_full if not p["skus"])
    with_sku_count = len(product_master_full) - no_sku_count

    html = dashboard_renderer.render_dashboard(
        project_name="Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report",
        project_code="UAWSO",
        assigned_user="utharsika",
        version="v001",
        template_version="2.0.0",
        generated_timestamp="2026-07-10 (Asia/Colombo, generation time not individually re-captured for this run)",
        latest_completed_date="2026-07-09",
        history_start="2025-01-01",
        history_end="2026-07-09",
        selectable_start="2026-01-01",
        selectable_end="2026-07-09",
        assigned_asin_count=len(assigned_asins),
        assigned_sku_count=with_sku_count,
        product_master_full=product_master_full,
        daily_aggregates_split=daily_split,
        vendor_periods=vendor_periods,
        no_sku_count=no_sku_count,
    )

    unresolved = dashboard_renderer.verify_no_placeholders(html)
    print(f"Unresolved placeholders: {len(unresolved)} {unresolved}")
    if unresolved:
        print("ABORT: unresolved placeholders present.")
        sys.exit(1)

    staging_sha = write_html_and_hash(STAGING_PATH, html)
    staging_size = os.path.getsize(STAGING_PATH)
    print(f"Staging written: {STAGING_PATH}")
    print(f"Staging SHA-256: {staging_sha}")
    print(f"Staging size: {staging_size} bytes ({staging_size/1024/1024:.2f} MB)")

    _pg_password = os.environ.get("PGPASSWORD", "")
    _pg_host = os.environ.get("PGHOST", "")
    checks = {
        "has_one_table": html.count('id="uawso-table"') == 1,
        "no_script_src": '<script src=' not in html,
        "no_credential_value": (not _pg_password) or (_pg_password not in html),
        "no_pg_host_literal": (not _pg_host) or (_pg_host not in html),
        "no_connection_string": 'postgresql://' not in html and 'psycopg2.connect' not in html,
        "no_order_id_field": '"order_id"' not in html and '"order_item_info"' not in html,
        "no_customer_fields": 'customer_email' not in html and 'tracking_number' not in html and 'customer_first_name' not in html,
        "has_csv_button": 'btn-csv' in html,
        "has_asin_dropdown": 'asin-dropdown' in html,
        "has_sku_dropdown": 'sku-dropdown' in html,
        "has_coverage_notes": 'Data Coverage Notes' in html,
        "all_1723_in_product_master": len(product_master_full) == 1723,
    }
    print(f"Structural checks: {checks}")
    if not all(checks.values()):
        print("ABORT: structural/security check failed.")
        sys.exit(1)

    final_sha = write_html_and_hash(FINAL_PATH, html)
    final_size = os.path.getsize(FINAL_PATH)
    print(f"\nFinal written: {FINAL_PATH}")
    print(f"Final SHA-256: {final_sha}")
    print(f"Final size: {final_size} bytes ({final_size/1024/1024:.2f} MB)")
    print(f"Product master (full): {len(product_master_full)} ASINs ({with_sku_count} with SKU, {no_sku_count} without) ({pmf_size} bytes)")
    print(f"Daily split aggregate rows: {len(daily_split)} ({ds_size} bytes)")
    print(f"Vendor period rows: {len(vendor_periods)} ({vp_size} bytes)")


if __name__ == "__main__":
    main()
