# UAWSO — REQ-01-D03 Discovery: Image Column and ASIN-Wise Orders

**Project:** UAWSO (Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report)
**Date:** 2026-07-15
**Developer:** Satheskanth
**Type:** Discovery only. No code, HTML, or database data was modified while producing this report.

---

## 1. Written requirement

Source: `01_REQUIREMENTS\source_requirements\2026-07-15_utharsika_uawso_requirement_update_v002.xlsx`, worksheet `PH-2026-07-UTHAR03 - Satheshkan`, cells A44–A45 (verbatim):

> A44: Replace the SKU column with the Image column
> A45: Calculate orders ASIN-wise

The same worksheet's row-2 header for column B has already been changed from `SKU` to `Image` directly in the workbook (confirmed by re-parsing the file cell-by-cell), consistent with A44. No sample `Image` value is populated anywhere in the illustrative rows (B3/B4/B5 are all empty) — the workbook does not suggest or imply any specific image source; one had to be discovered independently (see Section 3).

## 2. Source workbook path

`01_REQUIREMENTS\source_requirements\2026-07-15_utharsika_uawso_requirement_update_v002.xlsx` — single worksheet `PH-2026-07-UTHAR03 - Satheshkan`, populated range A1:K45. Read via `openpyxl`, cell-by-cell, all 45 rows.

## 3. Business question

Two changes to the shipped UAWSO dashboard:
1. Replace the currently-visible **SKU** column with an **Image** column.
2. Change **Total Orders** from being computed and displayed at the ASIN+SKU row grain to being computed **ASIN-wise** (`COUNT(DISTINCT order_item_info)` grouped by ASIN only, not by ASIN+SKU).

---

## 4. Current report grain

**Row grain today: one row = one ASIN + one SKU**, with two structural exceptions, both gated by explicit flags in `buildCanonicalRows()` (`05_IMPLEMENTATION\src\uawso_client_engine.js:327-355`):
- An ASIN with **zero** mapped SKUs gets exactly one row with a blank SKU (`rowType: "NO_SKU_MAPPING"`).
- An ASIN with **Vendor** data gets exactly **one additional**, dedicated blank-SKU row (`rowType: "VENDOR_ASIN_LEVEL"`), separate from its SKU rows — Vendor figures are never attached to a SKU-specific row and never duplicated across an ASIN's SKUs.

Row identity is **static** — it does not change as filters/date-range change; only the metric *values* on each row change (`buildCanonicalRows` comment, line 322–326).

| Aspect | Current state |
|---|---|
| Visible columns | ASIN, SKU, Row Type, FBM Sales/Orders/Quantity, FBA Sales/Orders/Quantity, Vendor Sales/Units, Total Sales/Orders/Quantity, PY/CY Sales/Orders/Quantity, Sales/Order/Quantity Change %, Trend, Achievement % (25 columns — `uawso_report_template.html:224-249`) |
| Hidden keys | `asin\|sku` composite key used internally for joining daily aggregates to rows (`uawso_client_engine.js:365,381,541`) |
| Grouping logic | `buildCanonicalRows()` builds the static row list from `product_master_full` (one entry per assigned ASIN, each carrying its full SKU array) |
| Sorting logic | Client-side, any of 14 fields incl. `sku` (`f-sort-field` dropdown, `uawso_report_template.html:172-187`); default sort is `totalSales` desc |
| Filtering logic | ASIN multi-select, **SKU multi-select** (searchable dropdown, cross-filters with ASIN selection), free-text search across `asin + sku`, Trend filter |
| CSV export grain | **Identical to the visible table grain** — same `sortRows()` output, same one-row-per-ASIN+SKU shape, `SKU` is CSV column 2 (`downloadCsv()`, `uawso_report_template.html:697-735`) |
| KPI-card grain | Grand total across all *currently visible/filtered* rows (`computeTotalV4`, sums every row's metrics regardless of SKU) — not a separate aggregation path from the table |
| Monthly aggregation grain | No stored monthly bucket; periods (Daily/Weekly/Month/MTD/Custom) are resolved dynamically client-side over a `(date → [asin,sku] rows)` index (`buildDailyIndexSplit`, `sumRangeSplitByAsinSkuV4`) |

### Where SKU is produced, layer by layer

| Layer | Exact location |
|---|---|
| SQL / extraction | `05_IMPLEMENTATION\src\extract_uawso_v4_ordered_sales.py:128-141` (`array_agg(DISTINCT ot.sku)` per ASIN, product master) and `:154-189` (`GROUP BY ot.order_date::date, ot.asin, ot.sku`, daily aggregates) |
| Python data model | `product_master_full[i]["skus"]` (list per ASIN) and `daily_split[j]["sku"]` (one field per daily row) — both plain JSON-serializable dicts, no further transformation |
| Renderer | `05_IMPLEMENTATION\src\dashboard_renderer.py` does **not** compute or touch SKU at all — it only serializes `product_master_full`/`daily_aggregates_split` verbatim into `__UAWSO_PRODUCT_MASTER_FULL_JSON__` / `__UAWSO_DAILY_AGGREGATES_SPLIT_JSON__` script tags |
| HTML template | `<th data-field="sku">SKU</th>` (line 225), SKU multi-select dropdown (lines 142–155), Data Coverage Notes text (lines 261–269 reference "one ASIN + one SKU") |
| JS client engine | `buildCanonicalRows()` (one row per `p.skus[j]`), `sumRangeSplitByAsinSkuV4()` (keyed by `asin+"\|"+sku`), `computeRowsV4()` (`sku: c.sku` on every output row) |
| CSV export | `downloadCsv()` header array `["ASIN","SKU","Row Type", ...]` and `r.sku` in the row-mapping (lines 698, 709) |

---

## 5. Image source findings

**No image field exists anywhere in the tables already used by this report.** `public.ph_cate_products` (the assigned-scope table) has exactly 4 columns (`id, ass_cate_id, ref_id, which_channel`) — no image. `public.order_transaction` (26 columns) has no image field either. This was verified by an `information_schema.columns` search across **all** schemas for any column matching `%image%`, `%img%`, `%photo%`, `%thumbnail%`, `%picture%`, `%media%`.

Candidates found, and why each was accepted or rejected:

| Table | Field | Verdict | Reason |
|---|---|---|---|
| `public.listing_data` | `main_image_url` | **Accepted — recommended source** | Same `ref_id`/`which_channel` join pattern already used for the assigned-ASIN scope (`which_channel=1` confirmed = `amazon` by direct value lookup, matching `ph_cate_products.which_channel=1`); 100% of assigned ASINs have a matching row; public Amazon CDN URLs |
| `public.google_merchant_products` | `image_link` | Rejected | Keyed by `product_id`, not `ref_id`/ASIN; no `which_channel`/`market_place='UK'` scoping consistent with the assigned-ASIN join; not evidently the same catalog as the Amazon UK listing data this report already trusts |
| `public.variation_product` | `variant_images` | Rejected | Keyed by `parent_sku`/`parent_id`/`child_id`, a different join shape; not evaluated further since `listing_data` already gives full coverage |
| `public.ebay_returns` | `img` | Rejected | eBay-specific (channel 2), not Amazon UK |
| `staging_ai.*` (4 tables) | `image_url` | Rejected outright | `staging_ai` is explicitly a non-trusted LLM sandbox schema per `00_PROJECT_CONTROL\governance_sources\aios_architecture.md` ("Data here is not trusted for production decisions") — disqualified by governance, not evaluated further |

### Exact field

`public.listing_data.main_image_url` (type `text`), joined via `listing_data.ref_id = <assigned ASIN>` AND `listing_data.which_channel = 1` AND `listing_data.market_place = 'UK'` — the identical join shape (`ref_id`, `which_channel`) already used for `public.ph_cate_products` in the assigned-scope CTE, plus a `market_place = 'UK'` filter matching the report's existing UK-only scope (`config.py::MARKET_PLACE_FILTER`).

### Completeness statistics (assigned scope, 1,723 ASINs, read-only queries against live data on 2026-07-15)

| Check | Result |
|---|---|
| Assigned ASINs with ≥1 `listing_data` row, `which_channel=1`, `market_place='UK'` | 1,723 / 1,723 (100%) |
| Assigned ASINs with a non-blank `main_image_url`, restricted to `market_place='UK'` | 1,715 / 1,723 (99.5%) |
| Assigned ASINs with a non-blank `main_image_url` across **any** market/row (channel=1, any country) | 1,722 / 1,723 (99.9%) |
| Assigned ASINs with **zero** non-blank image anywhere, any market | 1 (`B0GTY7S581`) |
| Max `listing_data` rows for one assigned ASIN (channel=1, UK) | 7 |
| Max **distinct** image URLs for one assigned ASIN (channel=1, UK) | 4 |
| Assigned ASINs with **more than one distinct** image URL across their rows | 280 / 1,723 (16.3%) |

### Duplicate-image / grain findings

**The image is SKU-level, not ASIN-level.** Confirmed directly: ASIN `B08DKQP89H` has two distinct SKUs (`LSCY290GR+RPR44WH R` and `LSCY290GR+RPR44WH_AMD3`), each with a genuinely different `main_image_url`. This is not duplicate ingestion — it is real per-SKU-variant product photography (e.g. different colour/size variants of the same parent ASIN). One exact duplicate-ingestion row pair was also found (`B0BWS7JGH9`, one SKU, 2 identical rows) — a minor, unrelated data-quality note.

### External hosting

All sampled URLs are `https://m.media-amazon.com/images/I/....jpg` — Amazon's own public product-image CDN. **Publicly accessible over plain HTTPS, no credentials or signed URLs required.** Safe to reference directly from a self-contained static HTML file (no secret leakage risk, unlike the DB connection string, which is already excluded from the HTML by an existing validation gate).

### Recommended image behaviour (design proposal only — not implemented)

- **Width/height:** small fixed thumbnail, e.g. 48×48px in the table cell, to keep row height and page weight reasonable across ~1,700+ rows.
- **Lazy loading:** `loading="lazy"` attribute on every `<img>` — the table can render hundreds of rows per page; eager-loading all images would be wasteful.
- **Alt text:** `alt="<ASIN>"` (never the SKU or any free-text title, to keep the attribute short and stable).
- **Fallback placeholder:** an inline, credential-free placeholder (e.g. a small embedded SVG/data-URI "no image" icon) shown when `main_image_url` is null/blank — never an external "loading" service, never a broken-image icon left unstyled.
- **Broken-image behaviour:** an `onerror` handler swapping the `<img>` to the same local placeholder, so a since-removed/expired Amazon CDN URL degrades gracefully instead of showing a broken-image glyph.
- **CSV export:** export the **image URL as plain text** (not an embedded image — CSV cannot embed images), in the same cell position the visible column occupies. This preserves "CSV export grain matches table grain" without inventing binary-in-CSV behaviour.

Fallback behaviour above matches the instruction's own stated preference (local/inline placeholder, never expose credentials/private URLs) — nothing here was invented beyond what was explicitly requested.

---

## 6. ASIN/SKU relationship statistics

Recomputed fresh, read-only, against the same widened SKU-discovery scope `extract_uawso_v4_ordered_sales.py` already uses (`market_place='UK'`, `source_name IN ('AMAZON','REPLACEMENT')`, dynamic status-inclusion rule):

| Metric | Value |
|---|---|
| Total distinct assigned ASINs | 1,723 |
| ASINs with zero SKUs (no qualifying transaction ever) | 105 |
| ASINs with exactly one SKU | 1,266 |
| ASINs with multiple SKUs | 352 |
| Maximum SKU count under one ASIN | 9 |

---

## 7. Current Orders logic

Confirmed directly from the active implementation, both server- and client-side:

- **Extraction SQL** (`extract_uawso_v4_ordered_sales.py:159-172`): `COUNT(DISTINCT ot.order_item_info)`, split by `fba_sales` flag into `fbm_orders`/`fba_orders`, **`GROUP BY ot.order_date::date, ot.asin, ot.sku`** — i.e. distinct-order counting happens *within* each (date, ASIN, SKU) partition, not at the ASIN level.
- **Client engine** (`computeRowsV4`, `uawso_client_engine.js:547-548`): `cyOrders = cs.fbmOrders + cs.fbaOrders` per (asin,sku) row; the **Total row / KPI card** then sums `r.currentYearOrders` across **every row**, including every SKU row of the same ASIN (`computeTotalV4`, lines 589-596).

This matches the requirement's own expected definition (`COUNT(DISTINCT order_item_info)`) — the formula itself is correct. The open question is only the **grain** it is grouped by: today it is grouped by (date, ASIN, **SKU**), then summed up to the ASIN/grand total; it is not grouped by (date, ASIN) directly.

### Duplicate-order-count risk assessment (measured, not assumed)

Two ways this SKU-then-sum approach could silently over-count an ASIN's true Orders:
1. The same `order_item_info` recorded under **two different SKU strings** for the same ASIN (e.g. a "supplied SKU" and its "mapped SKU" both appearing as distinct `sku` values in `order_transaction` for the same underlying order — a scenario proven to be structurally *possible* in this catalog: `listing_data.sku` vs `listing_data.mapped_sku` are frequently different strings for the same listing).
2. The same `order_item_info` recorded under **two different ASINs** (an unrelated but related sanity check).

Both were checked directly, full history (2025-01-01 → 2026-07-14), assigned scope, current dynamic status rule:

| Check | Result |
|---|---|
| `order_item_info` values spanning >1 distinct SKU under the same ASIN | **0** |
| `order_item_info` values spanning >1 distinct ASIN | **0** |

**Conclusion: no duplication currently exists in the data.** The SKU-summed method and a true ASIN-wise `COUNT(DISTINCT order_item_info)` produce the **exact same number today** — verified directly (see Section 8). The risk named in the requirement (SKU-level double counting) is real in *principle* (the `sku`/`mapped_sku` divergence proves the catalog can produce it) but has not *manifested* in `order_transaction` as of this discovery. This is exactly why the business wants the computation made **structurally** ASIN-wise rather than relying on today's coincidental equality holding forever.

---

## 8. Proposed ASIN-wise Orders logic

For each ASIN and reporting period: `COUNT(DISTINCT order_item_info)`, computed by grouping **directly by (date, ASIN)** — never by (date, ASIN, SKU) and then summed. An order item counts once for the ASIN regardless of how many SKUs are mapped to it, whether a supplied SKU and mapped SKU both match, or how many assignment rows exist. Never `COUNT(*)`, never a SKU row count, never Vendor Units.

### Recalculation (full history, 2025-01-01 → 2026-07-14, assigned scope, dynamic status rule)

| Method | Total Orders |
|---|---|
| Current (SKU-summed): `SUM` of per-(date,asin,sku) `COUNT(DISTINCT order_item_info)`, matching the exact daily-split grain the shipped HTML uses | **34,454** |
| Proposed (ASIN-wise): `COUNT(DISTINCT order_item_info)` grouped directly by (date, asin) | **34,454** |
| **Difference** | **0** |

The two methods are provably identical today (Section 7's duplication checks explain why: zero qualifying `order_item_info` values span multiple SKUs). Implementing the ASIN-wise grouping therefore changes **no current figure** — it only removes the latent risk of future silent divergence, and removes the SKU-summing step as an unnecessary intermediate that could mask a future data-quality issue.

---

## 9. Option A vs Option B

### Option A — One row per ASIN

Visible columns: Image, ASIN, Product Name (not currently in the report — would be a new addition, or omitted), Sales, Orders, Quantity, PY/CY figures, Change %, Trend, Achievement %. SKU is removed from the visible **and internal row** grain.

| | Assessment |
|---|---|
| Advantages | Matches the requirement literally (SKU column replaced, not merely relabelled); one row = one product = one image, no ambiguity about which figure applies to which image; simpler mental model for the assigned user; Orders becomes trivially, unambiguously ASIN-wise since there is no SKU dimension left to sum across |
| Risks | **280 assigned ASINs have more than one distinct SKU-level image** — collapsing to one row per ASIN requires a new, currently-undefined tie-break rule for which image is shown (see unresolved questions); loses the ability to filter/sort by SKU (a currently-used feature — SKU multi-select dropdown); CSV export loses SKU-level detail entirely, which may or may not be acceptable to the business |
| Effect on Sales | Straightforward: sum FBM+FBA Sales (+ Vendor, already ASIN-level) across all of an ASIN's SKUs per period — arithmetically identical to today's Total-row Sales figure, just computed one grain earlier |
| Effect on Quantity | Same as Sales — straightforward sum, no behavioural change to the *total*, only to *where* the summing happens |
| Effect on Orders | **Requires a genuinely new extraction query** grouped by (date, ASIN) directly — see Section 8. Not just "sum the existing SKU rows," since that would still be the SKU-summed method wearing an ASIN-level costume; the whole point of the requirement is to group correctly at the source, not visually hide the grouping |
| Effect on CSV export | SKU column disappears entirely from CSV; Image column becomes a URL text column (see Section 5) |
| Effect on filters | SKU multi-select filter must be removed or repurposed (e.g. kept as an internal-only filter that still narrows which ASINs are shown, without ever being a visible column) |
| Effect on totals | No double-counting risk at all — one row per ASIN structurally cannot double-sum an ASIN's own Orders |
| Duplicate-risk | **None** — eliminated by construction |
| Queryability | High — a developer can look at one table and understand "Orders" without needing to know an ASIN might appear on multiple rows |

### Option B — Keep SKU-level rows, show ASIN-wise Orders

Visible SKU column becomes Image; rows remain internally ASIN+SKU; ASIN Orders must not repeat across every SKU row of the same ASIN, and totals must not double count.

| | Assessment |
|---|---|
| Advantages | Preserves today's SKU-level Sales/Quantity detail and SKU filter/sort/CSV granularity; smaller code change to the row-building logic itself (rows keep their current shape) |
| Risks | **Directly creates the "misleading row" problem the requirement itself warns about** (Section 6): each SKU row of a multi-SKU ASIN would need to show the *same* ASIN-wide Orders number, which is confusing next to genuinely SKU-specific Sales/Quantity on the same row, and is easy to summed-in-error by anyone consuming the CSV without reading a footnote; the Total-row/KPI-card sum would have to special-case Orders (sum once per unique ASIN, not once per row) while Sales/Quantity sum per row as today — two different summation rules on one table is a real complexity and correctness-risk source |
| Effect on Sales | No change — remains SKU-level, as today |
| Effect on Quantity | No change — remains SKU-level, as today |
| Effect on Orders | Shown ASIN-wide but *displayed* on a SKU-grain row — a genuine grain mismatch within a single row |
| Effect on CSV export | A multi-SKU ASIN's Orders value would appear identically on 2+ CSV rows; a naive `SUM(Orders column)` in a spreadsheet would over-count by exactly the number of extra SKU rows — the exact failure mode the requirement is trying to eliminate, just moved into the CSV instead of the HTML table |
| Effect on filters | SKU filter/search remains fully intact (advantage) |
| Effect on totals | Requires a **non-uniform** total rule (Sales/Quantity summed per row, Orders summed per unique ASIN) — more code, more test surface, more chance of a future regression re-introducing double counting |
| Duplicate-risk | **Real and structural** — inherent to showing an ASIN-level number on a SKU-level row, not eliminated, only carefully managed |
| Queryability | Lower — a reader must understand "this Orders number is not this row's own number, it's the ASIN's number, shown here for convenience" without that being visually obvious |

### Recommendation

**Option A.** The requirement's own two changes are mutually reinforcing evidence for it: replacing the visible SKU column with an Image column already breaks the "one row = one identifiable SKU" mental model, and Section 5's finding that images are themselves SKU-level (280 ASINs have more than one distinct image) means Option B would show a SKU-specific image next to an ASIN-wide Orders figure on the same row — a direct grain contradiction on a single row, which is precisely the "misleading rows" failure mode the requirement explicitly asks to avoid (Section 6). Option A additionally eliminates the duplicate-order-count risk **by construction**, rather than by careful, ongoing code discipline (Option B's non-uniform total rule). The tradeoff — losing the visible SKU-level filter/sort/CSV detail — is an accepted, direct consequence of the requirement's own instruction to replace the SKU column, not a side effect introduced by this recommendation.

---

## 10. Sales and Quantity impact

| | Current grain | Proposed grain (Option A) |
|---|---|---|
| Sales | ASIN + SKU (summed to ASIN/grand total in the footer today) | ASIN (summed directly at extraction; arithmetically identical result) |
| Quantity | ASIN + SKU (same summing pattern) | ASIN (same — arithmetically identical result) |
| Orders | ASIN + SKU, `COUNT(DISTINCT order_item_info)` **within** each (date,asin,sku) partition, then summed | ASIN, `COUNT(DISTINCT order_item_info)` **directly** grouped by (date,asin) — structurally correct, not just today-equal |

Only **Orders** needs a genuinely new computation grain (grouping directly by ASIN in the extraction query). Sales and Quantity do not need a new *formula* — they only need to be aggregated one level higher (ASIN instead of ASIN+SKU), which is arithmetically identical to today's own Total-row figures, already proven correct by the existing v002 validation evidence. **Recommendation: make the entire visible table ASIN-wise (Option A), not just the Orders column** — a table with ASIN-wide Orders sitting beside SKU-level Sales/Quantity on the same row (i.e. Option B) would create exactly the misleading-row risk described in Section 9.

---

## 11. CSV export impact

- Current CSV header row: `ASIN, SKU, Row Type, FBM Sales, FBM Orders, FBM Quantity, FBA Sales, FBA Orders, FBA Quantity, Vendor Sales, Vendor Units, Total Sales, Total Orders, Total Quantity, PY Sales, CY Sales, PY Orders, CY Orders, PY Quantity, CY Quantity, Sales Change %, Order Change %, Quantity Change %, Trend, Achievement %` (25 columns, `downloadCsv()`).
- Under Option A: `SKU` column removed; `Image` column added holding the plain-text image URL (not an embedded image — CSV cannot embed images); `Row Type` likely simplifies (fewer distinct row types once SKU-level/no-mapping/Vendor-only distinctions collapse into a single ASIN-level row, though a "has Vendor data" indicator may still be worth keeping as a boolean/flag column). `Total Orders` becomes the genuinely-ASIN-wise figure.
- Under Option B: `SKU` retained, `Image` added as an *additional* column (not a replacement, contradicting the literal instruction) or SKU is dropped from display but kept in an internal-only field feeding the CSV in a different way — either reading is awkward, reinforcing the Option A recommendation.

---

## 12. Required file changes (impact map — not implemented, discovery only)

| File | Classification | Why |
|---|---|---|
| `05_IMPLEMENTATION\templates\uawso_report_template.html` (common template) | **MUST_CHANGE** | Replace SKU `<th>`/`<td>` with Image `<th>`/`<td>` (`<img>` + fallback + lazy-load); remove/repurpose SKU multi-select dropdown; update CSV header array in `downloadCsv()`; update Data Coverage Notes text describing row grain |
| `05_IMPLEMENTATION\src\uawso_client_engine.js` (client engine) | **MUST_CHANGE** | New ASIN-grain row-building function (analogous to `computeRowsV2`'s ASIN collapse, but carrying v4's Quantity fields and the corrected Vendor overlap logic); Orders must be sourced from a new ASIN-grouped daily index, not `sumRangeSplitByAsinSkuV4`; `computeTotalV4`-equivalent needs no special-casing under Option A (uniform per-row summing is safe again) |
| `05_IMPLEMENTATION\src\extract_uawso_v4_ordered_sales.py` (data extraction / generator) | **MUST_CHANGE** | New query: `main_image_url` per ASIN (with an explicit, approved tie-break rule for the 280 ASINs with multiple distinct images) from `public.listing_data` (`which_channel=1`, `market_place='UK'`); new/modified daily-aggregate query grouping Orders by (date, asin) directly, not (date, asin, sku) |
| `05_IMPLEMENTATION\src\dashboard_renderer.py` (renderer) | **MAY_CHANGE** | Only if the JSON payload shape changes (e.g. a new `image_url` field on each product-master entry) — the renderer itself does no calculation, so a shape-compatible change may need no code edit here at all |
| CSV export logic (inside the template's `downloadCsv()`) | **MUST_CHANGE** | Header array and row-mapping array both change (see Section 11) |
| Tests (`05_IMPLEMENTATION\tests\*`) | **MUST_CHANGE** | New unit tests for ASIN-wise Orders correctness and image-field/fallback behaviour; existing SKU-grain assumptions (e.g. any "duplicate ASIN+SKU pair" gate) need review — some may become structurally impossible (and thus removable) under Option A |
| `05_IMPLEMENTATION\automation\uawso_daily_runner.py` (automation runner) | **MUST_CHANGE (future, not now)** | Validation gates `no_duplicate_asin_sku_pairs` / `no_concatenated_skus` are SKU-grain-specific and would need ASIN-grain replacements; **not touched during this discovery**, and per the active pause instruction, automation implementation remains paused regardless of this requirement update |
| `05_IMPLEMENTATION\automation\run_uawso_daily.ps1` (scheduler wrapper) | **NO_CHANGE** | Thin wrapper, has no knowledge of row grain |
| `07_EVIDENCE\...` evidence/manifest writers | **MAY_CHANGE** | Would benefit from new fields (image completeness, ASIN-wise Orders reconciliation) but not required for correctness |
| `01_REQUIREMENTS\UAWSO_REQUIREMENT_RECORD.md` | **MUST_CHANGE (documentation, not code)** | Needs the new workbook's A44/A45 instructions folded in, per the project's own "single source of truth" documentation practice — not done as part of this discovery pass |
| `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md` | **MUST_CHANGE (documentation, not code)** | Needs the new Image and ASIN-wise-Orders rules documented once an option is approved |
| `05_IMPLEMENTATION\config\config.py` | **NO_CHANGE** | `AMAZON_CHANNEL_CODE = 1` already matches `listing_data.which_channel = 1` — no new constant needed |
| `09_OUTPUTS\*.html` (existing outputs) | **DO_NOT_TOUCH** | Historical Output Protection — explicit |
| `tech_team_outputs.ph_task` (existing rows) | **DO_NOT_TOUCH** | Historical Output Protection — explicit |
| `12_ARCHIVE\...` (archived files) | **DO_NOT_TOUCH** | Unrelated to this requirement |
| PostgreSQL production data (`public.*`) | **DO_NOT_TOUCH** | Read-only discovery only — no writes were made or are proposed |

No file listed above was edited during this discovery task.

---

## 13. Risks

- **Multi-image ASIN tie-break is undefined.** 280 assigned ASINs (16.3%) have more than one distinct `main_image_url` across their SKU-level listing rows. Option A requires picking exactly one image per ASIN with a deterministic rule (candidates: prefer the `is_parent=1` row's image; prefer the first non-blank image by SKU alphabetical order; prefer the image from the ASIN's SKU with the most historical Sales) — **no rule has been approved**.
- **1 assigned ASIN (`B0GTY7S581`) has zero image anywhere** — the fallback placeholder is not optional, it will be exercised in production from day one.
- **8 assigned ASINs have a UK-market row but no UK-specific image** (1,715 vs 1,723) — falling back to a non-UK market's image for those 8 is a policy decision, not yet approved (vs. showing the placeholder for those 8 specifically).
- **Losing the visible SKU column removes an actively-used filter** (the SKU multi-select dropdown) — no replacement filter has been requested or designed.
- **The "ASIN-wise Orders equals SKU-summed Orders today" finding could regress silently** if a future SKU-remapping event (the `sku` vs `mapped_sku` divergence already proven to exist in `listing_data`) ever causes the same `order_item_info` to appear under two SKUs in `order_transaction` — this is exactly the scenario the requirement is pre-emptively guarding against, and is the core justification for implementing genuine ASIN-grain grouping now rather than deferring it.

## 14. Duplicate-truth risk

None found in the *current* Orders figures (Section 7/8 — 0 difference, proven). The duplicate-truth risk is **structural and latent**, not manifested: today's SKU-summed method happens to equal the true ASIN-wise method only because no `order_item_info` currently spans multiple SKUs under the same ASIN. Nothing in the current schema or extraction code *prevents* that from happening in the future — it is observed to be absent, not guaranteed to be absent. Implementing genuine (date, ASIN)-grouped Orders removes this latent risk permanently.

## 15. Unresolved questions

1. Which image wins when an ASIN has multiple distinct SKU-level images (280 ASINs affected)? No rule proposed by the business yet.
2. What should the report show for the 1 ASIN with no image anywhere, and the 8 ASINs with no UK-specific image (fall back to a non-UK image, or always use the placeholder)?
3. Is the SKU multi-select filter meant to be removed entirely under Option A, or preserved as a non-visible/internal-only filter?
4. Should "Row Type" (currently distinguishing ASIN+SKU / Vendor-only / No-SKU-mapping rows) be simplified or removed once rows collapse to one-per-ASIN?
5. Final confirmation of Option A vs Option B is still required from the business before any implementation begins.

## 16. Evidence paths

- New requirement workbook: `01_REQUIREMENTS\source_requirements\2026-07-15_utharsika_uawso_requirement_update_v002.xlsx`
- This discovery report: `03_DISCOVERY\2026-07-15_uawso_REQ-01-D03_image_and_asin_orders_discovery.md`
- Prior pause evidence (context, unmodified): `07_EVIDENCE\automation\2026-07-15_uawso_automation_paused_for_user_updates.md`, `10_HANDOVER\2026-07-15_uawso_automation_pause_handover.md`
- All statistics in this report came from ad-hoc, read-only SQL queries executed directly against the live database during this discovery session (no query results were persisted to a separate evidence file beyond this report — no discovery script was written to disk, per the "discovery only" instruction to avoid creating new implementation artifacts).

## 17. Pass/fail rule

This discovery is current as of 2026-07-15. Re-run the image-completeness and ASIN/SKU-relationship queries before implementation begins if any meaningful time has passed, since both `order_transaction` and `listing_data` are live, continuously-updated tables.

## 18. Reviewer requirements

Satheesvaran (business validator) must confirm: (a) Option A vs Option B, (b) the multi-image tie-break rule, (c) the no-image/no-UK-image fallback policy, (d) whether the SKU filter should be preserved in any form.

## 19. One next step

Present this discovery report's Option A recommendation and the five unresolved questions (Section 15) to the business for explicit approval before writing any implementation code.

---

## Historical Output Protection re-verification (performed immediately before writing this report)

| File | SHA-256 | Status |
|---|---|---|
| `09_OUTPUTS\2026-07-09_utharsika_v001.html` | `52667eebadb04234f098af67d48d6005402f36e9f4e7b9e7ecdeb0cdc736aa9b` | Unchanged |
| `09_OUTPUTS\2026-07-10_utharsika_v001.html` | `335e65f8e922a052a7cb96def3f63172e21d8b8cb39f4c2a85abdf43a3c4e1c4` | Unchanged (pre-existing incident state, see prior evidence) |
| `09_OUTPUTS\2026-07-10_utharsika_v002.html` | `0a7c304ba88cd6acedf26294b1f58d1dc4fe727aff1e93466aa0cb307321ca72` | Unchanged |
| `09_OUTPUTS\2026-07-14_utharsika_v002.html` | `16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684` | Unchanged |
| `ph_task` id=157 | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` | Unchanged |
| `ph_task` id=237 | `16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684` | Unchanged |

No historical generator was run. No new HTML was created. No `ph_task` row was created, updated, or deleted.
