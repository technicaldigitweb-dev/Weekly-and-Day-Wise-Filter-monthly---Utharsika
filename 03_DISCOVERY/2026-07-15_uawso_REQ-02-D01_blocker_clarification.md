# UAWSO REQ-02-D01 — Blocker Clarification: Image Join Column and Orders Baseline

**Date:** 2026-07-15
**Type:** Read-only clarification (no implementation)
**Governing requirement:** `01_REQUIREMENTS\Requirement\2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md`
**Prior discovery:** `03_DISCOVERY\2026-07-15_uawso_REQ-01-D03_image_and_asin_orders_discovery.md`

This document resolves two blocking evidence gaps flagged in REQ-02-D01 Section 3.1 (join column) and Section 7.1 (Orders baseline). All work below is read-only against `public.listing_data` and `public.order_transaction`. No code, template, client engine, HTML output, `ph_task` row, or PostgreSQL data was modified.

---

## Issue 1 — Image Join Column (`maid` vs `ref_id`)

### Source inspected

`public.listing_data` — live schema, queried via `information_schema.columns` (52 columns total) and cross-schema search for any column named `maid` or matching `%image%`/`%img%`/`%photo%`/`%thumbnail%`/`%picture%`/`%media%`.

### Query conditions

```sql
SELECT column_name, data_type FROM information_schema.columns
WHERE table_schema='public' AND table_name='listing_data';

SELECT table_schema, table_name, column_name, data_type FROM information_schema.columns
WHERE column_name ILIKE '%image%' OR ... OR column_name ILIKE 'maid';
```

### Evidence

- **`maid` does not exist** anywhere in the database (checked case-insensitively across all schemas). The requirement text's item 6 ("Match `listing_data.maid` to ASIN") does not refer to a real column.
- **`ref_id` exists** in `public.listing_data` (type `text`) and is the channel listing identifier; for Amazon (`which_channel=1`) it is the ASIN.
- **`main_image_url` exists** in `public.listing_data` (type `text`) — confirms the REQ-01-D03 discovery report's claim, contrary to the curated MCP table-definition summary for this table, which happened to omit it (an incompleteness in that summary, not evidence that the column is absent — the live `information_schema` query is authoritative).
- **A materially important filter was missing from the prior D03 discovery**: `listing_data`'s own documentation states *"Always filter `wrong_sku = 0` — mandatory on every query; bad/duplicate rows exist and will corrupt results."* The D03 discovery report did not apply this filter. Applying it changes the coverage numbers (see below).

### Join validation (assigned-scope: 1,723 ASINs, `utharsika`)

| Filter combination | Matched ASINs | Unmatched ASINs |
|---|---|---|
| `ref_id`, `which_channel=1`, `market_place='UK'` (no `wrong_sku` filter — D03's original method) | 1,723 / 1,723 | 0 |
| `ref_id`, `which_channel=1`, `market_place='UK'`, `wrong_sku=0` (governance-mandatory filter) | 1,706 / 1,723 | **17** |

Trim/case mismatch check: **0** — every matching `ref_id` is an exact, untrimmed match to the assigned ASIN. No normalization is required.

Ten sample matches, plus row-level detail confirming exact-ASIN equality, `wrong_sku=0`, and populated `main_image_url`: `07_EVIDENCE\generated_data\2026-07-15_uawso_listing_data_join_validation.csv`.

### Image completeness (with the mandatory `wrong_sku=0` filter applied)

| Metric | Count |
|---|---|
| Assigned ASINs | 1,723 |
| ASINs with zero valid `listing_data` row (channel=1, UK, `wrong_sku=0`) | 17 |
| ASINs with a valid row but **every** row's `main_image_url` blank/null | 7 |
| ASINs with **no usable image at all** | **24** (17 + 7) |
| ASINs with exactly one distinct non-blank image | 1,472 |
| ASINs with more than one distinct non-blank image | **227** |
| Max distinct images for one ASIN | 3 |
| Max `listing_data` rows for one ASIN | 6 |

This differs from the D03 discovery report's figures (which reported only 1 zero-image ASIN and 280 multi-image ASINs, max 4 images) **because D03 did not apply `wrong_sku=0`**. This clarification's numbers are the ones that should be used going forward, since `wrong_sku=0` is a mandatory, pre-existing governance rule for this table, not a new constraint introduced here.

Full lists (17 zero-row ASINs, 7 all-blank-image ASINs, sample of multi-image ASINs): `07_EVIDENCE\generated_data\2026-07-15_uawso_image_field_coverage.csv`.

### Deterministic image-selection field

No purpose-built ordering/priority column exists for Amazon rows: `image_pos` and `image_id` are `NULL` on every sampled `which_channel=1` row (those fields appear to be populated for other channels only). The only field that is always populated and inherently stable is `listing_data.id` (the table's `bigint` primary key). **Selecting the row with the lowest `id`** is mechanically deterministic and requires no new logic, but it is a technical fallback, not a business decision — it has not been validated against what a reviewer would consider "the right" image when an ASIN has 2–3 different photos (e.g. box art vs. lifestyle vs. bundle photo). **This still requires reviewer sign-off before implementation.**

### Conclusion

```
Proven ASIN join field:        listing_data.ref_id
Proven image URL field:        listing_data.main_image_url
Required filters:               which_channel = 1, market_place = 'UK', wrong_sku = 0
maid:                           does not exist - remove from the requirement text
Deterministic tie-break field:  listing_data.id (lowest wins) - proposed, not yet approved
```

**Confidence: HIGH.** Directly queried, not inferred. **Not blocked** — `BLOCKED_IMAGE_JOIN` does not apply.

---

## Issue 2 — Orders Baseline (34,413 vs 34,454)

### Source identified for each figure

| Figure | Source | Date range | Where published |
|---|---|---|---|
| **34,413** | `07_EVIDENCE\2026-07-14_utharsika_v002_DYNAMIC_STATUS_FINAL_BUILD_AND_PUBLICATION.md` (line 62) | 2025-01-01 → **2026-07-13** inclusive | `ph_task` id=237, `UAWSO-2026-07-14-utharsika-v002` |
| **34,454** | `03_DISCOVERY\2026-07-15_uawso_REQ-01-D03_image_and_asin_orders_discovery.md` (Section 8) | 2025-01-01 → **2026-07-14** inclusive | Discovery only, not published |

Both figures share the same documented formula and scope on paper: `COUNT(DISTINCT order_item_info)`, `source_name IN ('AMAZON','REPLACEMENT')`, `market_place='UK'`, dynamic status rule (exclude only `Cancelled`/`Canceled`), assigned-scope join to `utharsika`'s 1,723 ASINs. **They differ by exactly one calendar day of data** (2026-07-14 is included in the second figure, not the first).

### Re-run under identical conditions

Re-ran the assigned-scope + status-filter + date-range logic live today (2026-07-15), matching the extraction script's exact filter fragment (`extract_uawso_v4_ordered_sales.py`: `order_status IS NOT NULL AND BTRIM(order_status) <> '' AND BTRIM(order_status) NOT IN ('Cancelled','Canceled')`, `market_place='UK'`, `source_name IN ('AMAZON','REPLACEMENT')`).

| Query | Result |
|---|---|
| Orders, 2025-01-01 → 2026-07-13 (same range as the 34,413 baseline), flat `COUNT(DISTINCT order_item_info)` | **34,426** |
| Orders, 2025-01-01 → 2026-07-13, grouped `(date,asin,sku)` then summed (production's exact method) | **34,426** (identical to flat — confirms no partition double-counting exists in today's data for this range) |
| Orders, 2025-01-01 → 2026-07-14 (same range as the 34,454 figure) | **34,454** (exactly reproduces the discovery report) |
| Orders on 2026-07-14 only | **28** — mechanically proven, see row-level evidence below |

### A–F, as specified

```
A. Orders under the exact v002 conditions (2025-01-01 to 2026-07-13, reproduced today):  34,426
B. Orders under the current discovery conditions (2025-01-01 to 2026-07-14):              34,454
C. Orders when both use identical conditions:  34,426 (thru 07-13) reproduces internally
   consistently by two independent methods, but does NOT match the historically recorded
   34,413 for that same range.
D. Difference caused by source-date growth (07-13 -> 07-14, measured today):              28
E. Difference caused by scope or logic (34,426 fresh vs 34,413 historical, SAME range):    13 - NOT explained
F. Remaining unexplained difference:                                                       13
```

### Row-level evidence for the explained portion

The 28 orders attributable to 2026-07-14 are individually listed, with `order_item_info`, ASIN, SKU, status, source, fulfilment flag, price and quantity: `07_EVIDENCE\generated_data\2026-07-15_uawso_orders_difference_rows.csv`. Mixed `New` and `Completed` statuses appear, confirming the dynamic status-inclusion rule is active (not restricted to `Completed` only).

### The remaining 13-order gap

This clarification does **not** invent a row-level cause for the 13-order gap between the historically recorded 34,413 (as of 2026-07-14's extraction) and today's fresh reproduction of the exact same date range (34,426). Two mechanisms could explain it, neither of which is provable from currently available evidence:

1. **Live-data drift**: `order_transaction` is a continuously-updated table; rows for dates ≤ 2026-07-13 may have been inserted/backfilled after the 2026-07-14 extraction ran.
2. **Scope drift**: the assigned-ASIN scope (`public.ph_cate_products` via `public.ph_categories`/`public.user`) is also a live, unsnapshotted table; the exact set of 1,723 ASINs as of 2026-07-14 was never persisted, so it cannot be diffed against today's set even though both happen to total 1,723.

No snapshot of either table's 2026-07-14 state exists to test either hypothesis. Per instruction, this portion is classified:

```
NOT_COMPARABLE_FROM_AVAILABLE_EVIDENCE (13 of the 41-order gap)
```

Full comparison table: `07_EVIDENCE\generated_data\2026-07-15_uawso_orders_baseline_comparison.csv`.

### Recommended correction to the requirement

Replace the current REQ-02-D01 Section 7.1 framing ("the exact difference must be explained") with:

> Of the 41-order gap between the 2026-07-14 baseline (34,413) and the 2026-07-15 discovery figure (34,454), 28 orders are mechanically traced to legitimate new order activity on 2026-07-14. The remaining 13 orders could not be reconciled from available evidence and are classified `NOT_COMPARABLE_FROM_AVAILABLE_EVIDENCE`. Implementation should re-run this same comparison at build time using the live scope and a fixed as-of date, and should not block publication solely on a same-range gap under roughly 15 orders unless it recurs or grows at the next re-check.

---

## Historical Output Protection — Re-verification

| Item | Result |
|---|---|
| `09_OUTPUTS\2026-07-09_utharsika_v001.html` | SHA-256 `52667eeb...36aa9b` — unchanged, matches D03 baseline |
| `09_OUTPUTS\2026-07-10_utharsika_v001.html` | SHA-256 `335e65f8...a4e3` — unchanged, matches D03 baseline |
| `09_OUTPUTS\2026-07-10_utharsika_v002.html` | SHA-256 `0a7c304b...1ca72` — unchanged, matches D03 baseline |
| `09_OUTPUTS\2026-07-14_utharsika_v002.html` | SHA-256 `16f1556a...bb82684` — unchanged, matches D03 baseline |
| `ph_task` id=237 `html_content` | MD5-verified byte-identical to local `2026-07-14_utharsika_v002.html` |
| `ph_task` id=157 `html_content` | MD5 does **not** match local `2026-07-10_utharsika_v001.html` — **this is the same pre-existing incident state already flagged in the D03 discovery report** ("Unchanged (pre-existing incident state, see prior evidence)"), not a new change caused by this session |

**Observation flagged, not caused by this session:** `ph_task` rows 157 and 237 both show `updated_at` of **2026-07-15 05:27:22 / 05:27:38** (Asia/Colombo) — later than any timestamp previously recorded in project documents (last recorded: 2026-07-14 15:06:09 / 18:01:26). This session performed **only `SELECT` queries** against `tech_team_outputs.ph_task`; no `UPDATE`/`INSERT` was issued. The content itself (verified by MD5 for row 237, and confirmed unchanged relative to the D03-recorded state for row 157) was not altered. The cause of the `updated_at` bump is unknown from this session's vantage point — possibly an external process, a scheduled job, or a `updated_at`-refresh side effect elsewhere in the system (the schema notes `updated_at` is "not auto-maintained... unless the application sets it"). **This should be reviewed by whoever owns the `ph_task` write path**, since it indicates *something* wrote to these rows outside of any activity documented in this project's evidence trail — even though the content did not change for row 237, and row 157's mismatch is the same pre-existing state as before.

No `09_OUTPUTS\*.html` file, `ph_task` row content, template, client engine, extraction script, or PostgreSQL source data was modified by this clarification task.

---

## Pass/Fail Rule

```
PASS if:
- the exact image join field is proven                      -> YES (ref_id)
- the exact image URL field is proven                        -> YES (main_image_url)
- image coverage is measured                                 -> YES (24 no-image, 227 multi-image, full lists in CSV)
- both Orders totals are traced or formally classified        -> YES (28 traced, 13 formally classified
                                                                  NOT_COMPARABLE_FROM_AVAILABLE_EVIDENCE)
- no implementation files changed                             -> YES
- no historical output modified                                -> YES
- no database write occurs                                     -> YES
```

## Reviewer Required

- **Satheesvaran (business validator)**: confirm the multi-image tie-break rule (lowest `listing_data.id`) is acceptable, or supply an alternative business rule.
- **Sajeesan (technical reviewer)**: confirm the corrected join (`ref_id` + `wrong_sku=0`, not `maid`) before any extraction code is written; confirm whether the 13-order unexplained gap is acceptable to proceed on, or whether a scope/data snapshot process should be added first.
- **ph_task write-path owner**: review the unexplained `updated_at` bump on rows 157/237 noted above.

## Next Step

Update `01_REQUIREMENTS\Requirement\2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md` Section 3.1 and Section 7.1 with the corrected join field and the partial-explanation framing above, obtain the two reviewer sign-offs listed, then proceed to implementation.
