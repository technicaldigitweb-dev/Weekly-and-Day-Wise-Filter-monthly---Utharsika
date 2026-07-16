"""
One-off generation script for REQ-02-D01: builds the ASIN-level v5 staging
HTML from the already-extracted JSON evidence files (see
extract_uawso_v5_asin_level.py for the extraction logic/query these files
correspond to). Pure rendering - no database connection is made here.

Reads:
    07_EVIDENCE\\generated_data\\2026-07-15_utharsika_v004_product_master_asin_level.json
    07_EVIDENCE\\generated_data\\2026-07-15_utharsika_v004_daily_aggregates_asin.json
    07_EVIDENCE\\generated_data\\2026-07-15_utharsika_v004_vendor_periods.json

Writes:
    09_OUTPUTS\\staging\\2026-07-15_utharsika_v004.staging.html

Does not write to 09_OUTPUTS\\ (final), does not touch ph_task, does not
touch any existing file.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dashboard_renderer  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
EVIDENCE_DIR = os.path.join(ROOT, "07_EVIDENCE", "generated_data")
STAGING_DIR = os.path.join(ROOT, "09_OUTPUTS", "staging")

IDENTITY = "2026-07-15_utharsika_v004"
VERSION = "v004"
RUN_DATE = "2026-07-15"
LATEST_COMPLETED_DATE = "2026-07-14"
HISTORY_START = "2025-01-01"
GENERATED_TS_COLOMBO = "2026-07-15 14:09:59 (Asia/Colombo)"

# Multi-image count sourced from the same-session, same-scope database query
# already recorded in this task's evidence (07_EVIDENCE\generated_data\
# 2026-07-15_uawso_v004_image_coverage.csv) - not re-derivable from the
# product_master_asin_level.json alone, since that file only carries the
# SELECTED image per ASIN, not the full candidate-row count.
MULTI_IMAGE_COUNT = 227


def load(name):
    path = os.path.join(EVIDENCE_DIR, f"{IDENTITY}_{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    product_master = load("product_master_asin_level")
    daily_asin = load("daily_aggregates_asin")
    vendor_periods = load("vendor_periods")
    assigned_asins = load("assigned_asins")

    assigned_count = len(assigned_asins)
    image_covered = sum(1 for p in product_master if p["image_url"])
    no_image = assigned_count - image_covered

    if len(product_master) != assigned_count:
        raise RuntimeError(f"STOP: product master row count ({len(product_master)}) != assigned ASIN count ({assigned_count})")

    html = dashboard_renderer.render_dashboard_v5(
        project_name="Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report",
        project_code="UAWSO", assigned_user="utharsika",
        version=VERSION, template_version="5.0.0-asin-level",
        generated_timestamp=GENERATED_TS_COLOMBO,
        latest_completed_date=LATEST_COMPLETED_DATE,
        history_start=HISTORY_START, history_end=LATEST_COMPLETED_DATE,
        selectable_start=f"{LATEST_COMPLETED_DATE[:4]}-01-01", selectable_end=LATEST_COMPLETED_DATE,
        assigned_asin_count=assigned_count,
        product_master_asin_level=product_master,
        daily_aggregates_asin=daily_asin,
        vendor_periods=vendor_periods,
        image_covered_count=image_covered,
        no_image_count=no_image,
        multi_image_count=MULTI_IMAGE_COUNT,
    )

    unresolved = dashboard_renderer.verify_no_placeholders(html)
    if unresolved:
        raise RuntimeError(f"STOP: unresolved placeholders: {unresolved}")

    os.makedirs(STAGING_DIR, exist_ok=True)
    staging_path = os.path.join(STAGING_DIR, f"{RUN_DATE}_utharsika_{VERSION}.staging.html")
    if os.path.exists(staging_path):
        raise RuntimeError(f"STOP: staging path already exists, refusing to overwrite: {staging_path}")

    with open(staging_path, "wb") as f:
        f.write(html.encode("utf-8"))

    import hashlib
    sha256 = hashlib.sha256(html.encode("utf-8")).hexdigest()
    print(f"Wrote {staging_path}")
    print(f"Bytes: {os.path.getsize(staging_path)}")
    print(f"SHA-256: {sha256}")
    print(f"Assigned ASINs: {assigned_count}, image-covered: {image_covered}, no-image: {no_image}, multi-image: {MULTI_IMAGE_COUNT}")


if __name__ == "__main__":
    main()
