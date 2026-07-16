"""
v3 generation driver: regenerates the SAME v001 identity/path with the
CORRECTED ASIN+SKU row grain (one row = one ASIN + one SKU; Vendor never
duplicated across SKU rows). Does NOT create v002.

*** PERMANENTLY DISABLED as of 2026-07-15 - DO NOT RUN. ***
This script is NOT reproducible: it embeds the entire CURRENT content of
src/uawso_client_engine.js verbatim (not a historical snapshot), and that
file has been additively edited many times since v001 was first
generated (v4 functions, dynamic-status functions). Running this script
does NOT reproduce the original 09_OUTPUTS\\2026-07-10_utharsika_v001.html
byte-for-byte - it silently overwrites it with different content. This
exact mistake happened on 2026-07-15 during automation-build validation
(see 07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md).
Per the mandatory HISTORICAL OUTPUT PROTECTION policy adopted the same
day, existing HTML outputs must never be regenerated in place. This
script is kept only for historical reference of the v3 grain-fix logic
and is archived, not deleted. The hard exit below prevents accidental
re-execution.

Run: python tests/generate_final_dashboard_v3.py
"""
import sys

print("REFUSED: this script is permanently disabled - it is not reproducible and would "
      "overwrite 09_OUTPUTS\\2026-07-10_utharsika_v001.html with non-original content. "
      "See the module docstring and "
      "07_EVIDENCE\\automation\\incidents\\2026-07-15_v001_accidental_overwrite.md. "
      "Do not remove this guard without an explicit, separately-approved decision.")
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
    sku_row_count = sum(len(p["skus"]) for p in product_master_full)
    vendor_asins = set(v["asin"] for v in vendor_periods)
    vendor_row_count = len(vendor_asins)
    total_row_count = sku_row_count + no_sku_count + sum(
        1 for p in product_master_full if p["skus"] and p["asin"] in vendor_asins
    )

    html = dashboard_renderer.render_dashboard(
        project_name="Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report",
        project_code="UAWSO",
        assigned_user="utharsika",
        version="v001",
        template_version="3.0.0",
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
        total_row_count=total_row_count,
        sku_row_count=sku_row_count,
        vendor_row_count=vendor_row_count,
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
        "has_row_type_column": 'Row Type' in html,
        "all_1723_in_product_master": len(product_master_full) == 1723,
        "expected_total_row_count_2388": total_row_count == 2388,
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
    print(f"Total row count: {total_row_count} (sku_rows={sku_row_count}, no_sku_rows={no_sku_count}, vendor_only_rows={total_row_count - sku_row_count - no_sku_count})")


if __name__ == "__main__":
    main()
