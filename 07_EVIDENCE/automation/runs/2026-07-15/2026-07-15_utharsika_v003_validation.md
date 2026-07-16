# UAWSO Automated Run Validation — 2026-07-15_utharsika_v003.html

**Mode:** dry-run
**Result:** DRY_RUN_PASS
**Run started:** 2026-07-15T10:38:26.510899
**Data range:** 2025-01-01 to 2026-07-14
**Assigned ASIN count:** 1723 (previous: None)

## Status rule (dynamic, exclusion-based)

Included: ['Completed', 'Deleted', 'Hold', 'Inprogress', 'New', 'Pending', 'Refunded']
Excluded: ['Canceled', 'Cancelled']
Null: 0
Blank: 0
Newly discovered since last run: ['Completed', 'Deleted', 'Hold', 'Inprogress', 'New', 'Pending', 'Refunded']

## Validation gates

- `all_asins_in_master`: PASS (1723)
- `no_credential_in_html`: PASS (checked)
- `no_pg_host_in_html`: PASS (checked)
- `no_connection_string`: PASS (checked)
- `no_order_item_info_field`: PASS (checked)
- `has_one_table`: PASS (1)
- `has_csv_buttons`: PASS (checked)
- `has_asin_sku_dropdowns`: PASS (checked)
- `no_duplicate_asin_sku_pairs`: PASS (0)
- `no_concatenated_skus`: PASS (0)
- `no_duplicate_daily_rows`: PASS (0)

## Historical Output Protection

- Previous HTML files changed: n/a (dry-run)
- New HTML files created: n/a (dry-run)
- Previous ph_task rows changed: n/a (dry-run)
- Stored/local hash match: n/a (dry-run)
