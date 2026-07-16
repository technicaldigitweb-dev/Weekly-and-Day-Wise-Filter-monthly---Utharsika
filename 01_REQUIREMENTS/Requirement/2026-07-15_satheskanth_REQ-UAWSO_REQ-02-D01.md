# **Daily Requirement Document**

## **1. Metadata Block**

| Field | Value |
| ----- | ----- |
| daily_requirement_submitted_date | 2026-07-15 |
| expected_deadline_date | 2026-07-15 (Target completion: **before 3:00 PM on 2026-07-15**) |
| end_user | Utharsika (`utharsika`) |
| expected_roi | Faster access to complete, correct ASIN-level Sales and Orders with product images, one row per ASIN, no SKU-level duplication or confusion (Quantity removed from scope — see Section 3.2, 2026-07-15 amendment) |
| developer | Satheskanth |
| project | Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report |
| project_code | UAWSO |
| phase | Phase-02 — ASIN-Level Report with Product Images |
| requirement_id | REQ-02 |
| deliverable_id | REQ-02-D01 |
| status | **IN-PROGRESS** |
| priority | **HIGH** |
| target_completion | **Before 3:00 PM on 2026-07-15** |
| blos_keys | One row = one ASIN (SKU removed from grain); Image sourced from `public.listing_data.main_image_url`; Orders = `COUNT(DISTINCT order_item_info)` grouped directly by (date, ASIN); Vendor counted once per ASIN |
| domain | Sales & Orders — Amazon — UK |
| planned_benefits | - Faster user access to complete real data<br>- One clear row per ASIN<br>- Easier product recognition through images<br>- Accurate ASIN-wise Orders<br>- Reduced duplicate-grain risk<br>- Simpler report reading<br>- Improved CSV usability<br>- Preserved historical outputs<br>- Safer future automation readiness |

---

## **2. Today Requirement Block**

### **2.1 Today Requirement**

#### **Task Name:**

Replace SKU-Based Report Layout with a True ASIN-Level Report (Image Column + ASIN-Wise Orders)

#### **Business Purpose / Today's Business Benefit:**

Before 3:00 PM, push the complete real Utharsika report data with the approved new report update so the user can view correct ASIN-level Sales and Orders with product images, without SKU-level duplication or confusion. This delivers:

- Faster user access to complete real data
- One clear row per ASIN
- Easier product recognition through images
- Accurate ASIN-wise Orders
- Reduced duplicate-grain risk
- Simpler report reading
- Improved CSV usability
- Preserved historical outputs
- Safer future automation readiness

---

### **Source Information**

Source System:

PostgreSQL (`order_management_copy`)

Tables:

```
public.order_transaction
public.vendor_sales
public.user
public.ph_categories
public.ph_cate_products
public.listing_data          -- NEW: approved image source
tech_team_outputs.ph_task
```

Requirement evidence sources read for this document:

```
01_REQUIREMENTS\requirement_template\Daily Requirement Document.md
01_REQUIREMENTS\daily_requirements\2026-07-10_satheskanth_REQ-UAWSO_REQ-01-D01.md
01_REQUIREMENTS\source_requirements\2026-07-15_utharsika_uawso_requirement_update_v002.xlsx
03_DISCOVERY\2026-07-15_uawso_REQ-01-D03_image_and_asin_orders_discovery.md
```

---

### **Filter Conditions**

```
source_name = 'AMAZON'
market_place = 'UK'
order_status = dynamic non-null/non-blank rule, excluding Cancelled/Canceled only (not a fixed allow-list)
Assigned scope: Utharsika only (public.user -> public.ph_categories -> public.ph_cate_products, DISTINCT applied)
Image source scope: public.listing_data, which_channel = 1, market_place = 'UK', wrong_sku = 0
```

---

### **Required Data Output**

| Field | Purpose |
| ----- | ----- |
| ASIN | Product identification (row key — one row per ASIN) |
| Image | Product visual identification, replaces the visible SKU column |
| FBM Sales / FBM Orders | Fulfilled-by-Merchant revenue and order count, aggregated at ASIN level |
| FBA Sales / FBA Orders | Fulfilled-by-Amazon revenue and order count, aggregated at ASIN level |
| Vendor Sales / Vendor Orders | Amazon Vendor revenue and order count, counted once per ASIN. **Vendor Orders = `ordered_units`** (one Vendor Unit = one Vendor Order — see Section 3.2, 2026-07-15 amendment) |
| PY Sales / CY Sales | Previous-year and current-year Sales for the selected comparison period (FBM+FBA+Vendor), ASIN level |
| FBM Orders / FBA Orders (ASIN-wise) | `COUNT(DISTINCT order_item_info)` grouped directly by (date, ASIN), split by fulfilment channel |
| Total Orders | **FBM Orders + FBA Orders + Vendor Orders** (see Section 3.2, 2026-07-15 amendment) |
| PY Orders / CY Orders | Previous-year and current-year Total Orders for the selected comparison period |
| Sales Change | (CY − PY) ÷ PY, undefined when PY = 0 |
| Trend | UP / DOWN / NO CHANGE, Sales-based only |
| Achievement % | CY Sales ÷ (PY Sales × 130%) × 100, undefined when PY = 0 |

**Removed from this deliverable:** the visible SKU column and the SKU column in CSV export; **and, as of the 2026-07-15 same-day amendment (Section 3.2), all Quantity fields** (FBM Quantity, FBA Quantity, Vendor Quantity, Total Quantity, PY/CY Quantity, Quantity Change %).

---

## **3. Written Requirement**

Replace the SKU-based report layout with a true ASIN-level report.

The new report must:

1. Use one row per ASIN.
2. Remove SKU from the visible report and CSV export.
3. Replace the SKU column with an Image column.
4. Use one valid product image for each ASIN.
5. Use `public.listing_data` as the approved image source.
6. Match `listing_data.ref_id` to ASIN — **proven and corrected, see Section 3.1.**
7. Apply:
   - `which_channel = 1`
   - `market_place = 'UK'`
   - `wrong_sku = 0`
8. Select one image deterministically when multiple image rows exist.
9. Show "No image available" when no image exists.
10. Show "Image loading issue" when a valid URL exists but the browser cannot load it.
11. Calculate FBM/FBA Orders ASIN-wise using:
    `COUNT(DISTINCT order_item_info)`
12. Aggregate Sales at ASIN level. **Quantity is no longer part of this deliverable — see Section 3.2.**
13. Keep Vendor data counted once per ASIN. **Vendor Orders = `ordered_units` and are included in Total Orders — see Section 3.2.**
14. Export one CSV row per ASIN.
15. Export the selected image URL as text.
16. Create a new versioned HTML output.
17. Insert a new versioned `ph_task` row only after validation and approval.
18. Never overwrite any previous HTML output.
19. Never modify or replace any previous `ph_task` row.

### **3.1 Join Column — Corrected and Proven**

An earlier draft of this requirement referenced *"Match `listing_data.maid` to ASIN."* This has been corrected following read-only clarification work (`03_DISCOVERY\2026-07-15_uawso_REQ-02-D01_blocker_clarification.md`), which directly queried `information_schema.columns` against the live database, database-wide, case-insensitively.

**Proven result: `maid` does not exist anywhere in the database.** It is removed from this requirement. The proven join is:

```
public.listing_data.ref_id = <assigned ASIN>
AND public.listing_data.which_channel = 1
AND public.listing_data.market_place = 'UK'
AND public.listing_data.wrong_sku = 0
```

`wrong_sku = 0` is a mandatory filter per `public.listing_data`'s own governance documentation ("Always filter `wrong_sku = 0` — bad/duplicate rows exist and will corrupt results") and must never be omitted. The image field is `public.listing_data.main_image_url`. Zero trim/case mismatches were found between `ref_id` and the assigned ASIN — no normalization is required.

**Status: RESOLVED.** No open discrepancy remains on the join column.

### **3.2 Scope Amendment — Sales and Orders Only, Vendor Orders Rule (2026-07-15, Same-Day Amendment)**

**User-confirmed change, same day as this requirement's original approval.** The following supersedes every earlier statement in this document about Quantity and about Vendor Units/Vendor Orders. Where an earlier section conflicts with this amendment, this amendment is authoritative and the earlier section has been updated in place — no dual/conflicting rule remains active anywhere in this document.

**New approved rules:**

1. The report contains **Sales and Orders only**. Quantity is no longer a required output.
2. **Vendor Orders = `public.vendor_sales.ordered_units`.**
3. **One Vendor Unit equals one Vendor Order** (a direct 1:1 mapping — not derived from a Seller-Central-style distinct order-item count, since Vendor has no order-item key).
4. **Total Orders = FBM Orders + FBA Orders + Vendor Orders.**
5. Quantity fields (FBM Quantity, FBA Quantity, Vendor Quantity/Units-as-quantity, Total Quantity, PY Quantity, CY Quantity, Quantity Change %) are removed from the canonical data model, the visible table, KPI cards, CSV export, and Column Definitions.
6. Sales logic is unchanged by this amendment: FBM Sales, FBA Sales, Vendor Sales, Total Sales, Sales Change %, Trend, and Achievement % all remain exactly as defined elsewhere in this document.

**Superseded statements (no longer active — replaced by the rules above):**

- Section 4's prior "Quantity | FBM Quantity + FBA Quantity + Vendor Units" row — **removed**.
- Section 4's prior "Vendor Orders | N/A" row — **replaced**: Vendor Orders now exist and equal `ordered_units`.
- Section 5's prior "Vendor Non-Duplication Rule" statement "Vendor Orders do not exist (N/A) — Vendor has no order-level key" — **replaced**: Vendor Orders are now defined directly as `ordered_units` (a per-ASIN count, not an order-item-key-based count), and are included in Total Orders.
- Section 5's prior "ASIN-Wise Orders Rule" statement "never Vendor Units" — **narrowed**: this still correctly describes how **FBM/FBA Orders** are calculated (`COUNT(DISTINCT order_item_info)`, never Vendor Units mixed into that specific count), but **Total Orders** now separately adds Vendor Orders (`ordered_units`) on top of FBM+FBA Orders. FBM/FBA Orders and Vendor Orders remain two structurally different calculations that are summed together only at the Total Orders level, never blended into one `COUNT(DISTINCT order_item_info)` query.

**Reason for change:** Business decision — Utharsika confirmed Order Count (not unit volume) is the metric of interest across all three channels, and that Vendor's `ordered_units` figure should be treated as Vendor's order-count equivalent, consistent with how FBM/FBA Orders represent order counts for those channels.

**Who approved:** User, same session, 2026-07-15.

---

## **4. Current Approved Business Rules**

| Rule | Value |
| ----- | ----- |
| Row grain | One row per ASIN |
| SKU | Removed completely from visible report and CSV |
| Image | One image per ASIN |
| Missing image | "No image available" |
| Image load failure | "Image loading issue" |
| FBM/FBA Orders | `COUNT(DISTINCT order_item_info)` grouped directly at ASIN level |
| Sales | `item_price × quantity`, aggregated at ASIN level |
| Vendor Orders | `= ordered_units` (one Vendor Unit = one Vendor Order — 2026-07-15 amendment, Section 3.2) |
| Total Orders | FBM Orders + FBA Orders + Vendor Orders (2026-07-15 amendment, Section 3.2) |
| Quantity | **Removed from scope (2026-07-15 amendment, Section 3.2).** No Quantity field of any kind is part of this deliverable. |
| Status rule | Include every non-null and non-blank status except Cancelled / Canceled. Do not convert this into a fixed allow-list. |

---

## **5. Business Logic Block**

### **Row Grain Rule**

```
ONE row per assigned ASIN (SKU is no longer part of the row key).
Never omit an assigned ASIN from the output.
```

### **Image Selection Rule**

```
IF one or more public.listing_data rows exist for the ASIN
   (which_channel=1, market_place='UK', wrong_sku=0)
  AND at least one has a non-blank main_image_url
THEN select the row with the LOWEST listing_data.id among the non-blank-image rows
     (deterministic — never an unordered LIMIT 1)
ELSE IF listing_data rows exist (wrong_sku=0) but main_image_url is blank/null for all of them
THEN display "No image available"
ELSE IF no listing_data row exists for the ASIN under this scope (wrong_sku=0)
THEN display "No image available"

At render time, IF the selected image URL fails to load in the browser
THEN display "Image loading issue" (onerror fallback, not a blank image)
```

**Business confirmation from Utharsika:**

> An ASIN may have one SKU or multiple SKUs. All SKUs under the same ASIN represent the same product for this report. Therefore, when multiple valid product images exist for one ASIN, the system may display any one valid image.
>
> The report must still use:
> - one row per ASIN;
> - one selected image per ASIN;
> - no visible SKU column;
> - ASIN-wise Sales, Orders and Quantity.

*(Quoted verbatim as originally recorded. Quantity was subsequently removed from scope by the 2026-07-15 same-day amendment in Section 3.2 — this quote is preserved unedited as the historical record of the original business confirmation, not as a currently-active requirement for Quantity.)*

**Tie-break status: BUSINESS-CONFIRMED — deterministic technical selection required.** The business does not require a specific SKU's image to be shown — any valid image under the ASIN is acceptable, since all SKUs under one ASIN represent the same product for this report. Deterministic selection is still required regardless, purely so that repeated runs of the report produce the same image for the same ASIN each time (run-to-run stability). This is a **technical consistency mechanism, not a business preference** — the business confirmation does not endorse "lowest id" as the "best" image, only as an acceptable, stable way to pick one of the valid images.

**Technical selection rule:** When more than one valid filtered image row exists for an ASIN, select one row deterministically using the lowest `public.listing_data.id`.

- `listing_data.id` is the database row identifier (bigint primary key) — nothing more.
- Lowest `id` is used only to keep image selection stable across repeated runs.
- It does **not** mean the selected image is better, newer, or preferred over the others.
- Any selected valid image is acceptable per the business confirmation above.
- Implementation must not use an unordered `LIMIT 1` — the ordering by `id` is mandatory so the same ASIN always resolves to the same image.

### **Image Coverage — Proven (2026-07-15)**

| Metric | Count |
| ----- | ----- |
| Assigned ASINs | 1,723 |
| ASINs with at least one valid `listing_data` row (`which_channel=1`, `market_place='UK'`, `wrong_sku=0`) | 1,706 |
| ASINs with a usable (non-blank) image | 1,699 |
| **No-image ASINs (total)** | **24** |
| — of which: no valid filtered listing row at all | 17 |
| — of which: has listing row(s), but every `main_image_url` is blank | 7 |
| Multi-image ASINs (more than one distinct non-blank image) | 227 |
| Maximum distinct images for one ASIN | 3 |
| Maximum valid listing rows for one ASIN | 6 |

Source: `03_DISCOVERY\2026-07-15_uawso_REQ-02-D01_blocker_clarification.md`; full ASIN lists in `07_EVIDENCE\generated_data\2026-07-15_uawso_image_field_coverage.csv`.

### **ASIN-Wise Orders Rule**

```
FBM Orders / FBA Orders = COUNT(DISTINCT order_item_info), grouped directly
by (date, ASIN), split by fulfilment channel. Never COUNT(*), never a SKU
row count. Grouping must occur at the extraction/SQL layer by (date, ASIN)
directly — summing SKU-level counts up to the ASIN level is NOT equivalent
and does not satisfy this rule (see discovery report Section 8 for why).

Vendor Orders are a SEPARATE, differently-calculated figure (see Vendor
Non-Duplication Rule below) — never blended into the COUNT(DISTINCT
order_item_info) query above. FBM/FBA Orders and Vendor Orders are summed
together only at the Total Orders level.

Total Orders = FBM Orders + FBA Orders + Vendor Orders
  (2026-07-15 amendment, Section 3.2 — supersedes any earlier statement
  that Total Orders excluded Vendor).
```

### **Vendor Non-Duplication Rule**

```
Vendor Sales (public.vendor_sales.ordered_revenue) and Vendor Orders
(public.vendor_sales.ordered_units) each attach to exactly ONE value per
ASIN — ASIN-only, no SKU, no duplication across SKU rows.

Vendor Orders = ordered_units (one Vendor Unit = one Vendor Order).
This is a direct 1:1 mapping, not a COUNT(DISTINCT order_item_info)-style
calculation — Vendor has no order-item key, so Vendor Orders cannot be
calculated the same way FBM/FBA Orders are.

Vendor Orders ARE included in Total Orders (2026-07-15 amendment,
Section 3.2). The earlier statement "Vendor Orders do not exist (N/A)" is
superseded and no longer applies.
```

### **Trend and Achievement Rule** (unchanged from REQ-01-D01)

```
Sales Target = Previous Year Sales x 1.30
Achieve % = (Current Year Sales / Sales Target) x 100   [undefined when Sales Target = 0]

Current Sales > Previous Sales -> UP
Current Sales < Previous Sales -> DOWN
Current Sales = Previous Sales -> NO CHANGE   (includes Previous = 0 AND Current = 0)
Previous = 0 AND Current > 0 -> UP
```

### **KPI / Filter Rule** (unchanged from REQ-01-D01)

```
KPI cards and CSV export are always computed from the currently filtered row set,
calculated BEFORE pagination is applied — pagination must never change a total.
```

---

## **6. Data Enrichment Block**

**Purpose:** Collect additional product information after identifying candidates.

Source:

`public.listing_data`

Required Data:

| Field | Reason |
| ----- | ----- |
| `main_image_url` | Product image display (replaces SKU column) |
| `which_channel` | Scope filter (=1, matches existing `AMAZON_CHANNEL_CODE`) |
| `market_place` | Scope filter (='UK') |
| `wrong_sku` | Scope filter (=0, mandatory per `listing_data` governance — excludes bad/duplicate rows) |
| Join column to ASIN | **Proven and corrected, see Section 3.1** (`ref_id`; `maid` does not exist and has been removed) |

---

## **7. Data and Validation Requirements**

The new report must use complete real source data.

Required validation:

```
- one output row per ASIN
- no visible SKU column
- no SKU column in CSV
- no duplicate ASIN rows
- no duplicate order_item_info
- FBM/FBA Orders reconcile to PostgreSQL
- Vendor Orders reconcile to PostgreSQL (= ordered_units)
- Total Orders (FBM + FBA + Vendor Orders) reconciles to PostgreSQL
- Sales reconcile to PostgreSQL
- No Quantity field is present anywhere in the output (2026-07-15 amendment, Section 3.2)
- Vendor values counted once
- one deterministic image selected per ASIN
- missing-image state validated
- broken-image state validated
- current source date range recorded
- all historical HTML hashes remain unchanged
- all historical ph_task rows remain unchanged
```

### **7.1 Orders Baseline — Traced and Classified (2026-07-15)**

| Item | Value |
| ----- | ----- |
| Historical validated v002 Orders | **34,413** |
| Historical range | 2025-01-01 through 2026-07-13 |
| Current discovery Orders | **34,454** |
| Current range | 2025-01-01 through 2026-07-14 |
| Mechanically explained difference | **28 orders**, from real 2026-07-14 order activity |
| Remaining difference | **13 orders** |
| Classification | **NOT_COMPARABLE_FROM_AVAILABLE_EVIDENCE** |

**Why the remaining 13 cannot be safely attributed to one cause:**

- The assigned-ASIN scope (`public.ph_cate_products` via `public.ph_categories`/`public.user`) is a live table and was never snapshotted as of the 2026-07-14 extraction — there is no record of the exact ASIN set used to produce 34,413, only its count (1,723).
- Re-running the **exact same** historical date range (2025-01-01 → 2026-07-13) today, with the same status rule, source filter, and scope logic, returns **34,426** — not 34,413.
- Two independent methods computed today (a flat `COUNT(DISTINCT order_item_info)` over the whole range, and the production grouped-by-`(date,asin,sku)`-then-summed method) **agree with each other at 34,426**, confirming today's data is internally consistent — the mismatch is against the *historical* figure, not a live calculation bug.
- With no snapshot to diff against, the 13-order gap could stem from live `order_transaction` backfill for dates ≤2026-07-13, from assigned-scope drift, or another cause — none of which is provable from currently available evidence.

**No cause is invented for the remaining 13.** The 28-order portion is fully evidenced at the row level in `07_EVIDENCE\generated_data\2026-07-15_uawso_orders_difference_rows.csv`. Full comparison detail: `07_EVIDENCE\generated_data\2026-07-15_uawso_orders_baseline_comparison.csv` and `03_DISCOVERY\2026-07-15_uawso_REQ-02-D01_blocker_clarification.md`.

---

## **8. Output and Evidence**

Expected new output format:

```
YYYY-MM-DD_utharsika_vNNN.html
```

The exact version must be selected from the next unused local and `ph_task` version.

Required output location:

```
09_OUTPUTS\
```

Required evidence locations:

```
07_EVIDENCE\
07_EVIDENCE\generated_data\
```

Required evidence content:

```
- ASIN-level reconciliation
- image coverage report
- multi-image selection report
- missing-image report
- Orders difference reconciliation (34,413 vs 34,454, 28 explained / 13 not-comparable — see Section 7.1)
- Sales/Orders reconciliation (Total Orders = FBM + FBA + Vendor Orders — Quantity removed from scope, Section 3.2)
- final HTML hash
- new ph_task row ID
- stored/local HTML hash comparison
```

**Status at time of this document: none of the above exist yet.** This deliverable (REQ-02-D01) is a requirement document only — no implementation, HTML, or evidence has been produced under this requirement as of 2026-07-15.

---

## **9. Historical Protection Rule**

```
- Previous HTML outputs are immutable.
- Previous ph_task rows are immutable.
- No historical generator may write into an existing output path.
- No existing ph_task row may be updated.
- Every approved successful publication must create a new versioned file and a new row.
```

Verified as of this document (read-only, no changes made): existing `09_OUTPUTS\*.html` files and `tech_team_outputs.ph_task` rows 157 and 237 remain unchanged (last confirmed during the REQ-01-D03 discovery pass, 2026-07-15).

### **9.1 Known Risk — `ph_task` Timestamp Observation (Non-Blocking)**

```
- ph_task rows 157 and 237 showed updated_at timestamps on 2026-07-15
  (05:27:22 and 05:27:38 Asia/Colombo) newer than any previously recorded value.
- The REQ-02-D01 blocker-clarification task performed read-only SELECT queries
  only against tech_team_outputs.ph_task — no write was issued.
- Row 237 content was verified unchanged (MD5-identical to the local
  2026-07-14_utharsika_v002.html file).
- Row 157 remains in its previously documented pre-existing incident state
  (its content does not match the local v001 file, a condition already
  flagged before this requirement existed — not a new change).
- The cause of the updated_at change is unknown from this project's vantage
  point and is NOT classified as caused by this requirement or its
  clarification task. The ph_task write-path owner should review it
  separately, outside this deliverable's scope.
```

Full detail: `03_DISCOVERY\2026-07-15_uawso_REQ-02-D01_blocker_clarification.md` ("Historical Output Protection — Re-verification"). Neither row was modified by this document or its supporting clarification work.

---

## **10. Scope Boundary**

**Allowed (future work, after this requirement is approved):**

```
- requirement documentation
- active report implementation
- ASIN-level extraction changes
- template changes
- image display changes
- tests
- validation evidence
- new versioned staging output
- new versioned final output after approval
- new ph_task insert after approval
```

**Not allowed (including during this document's creation):**

```
- modifying source PostgreSQL data
- overwriting historical HTML
- updating historical ph_task rows
- enabling the paused scheduler
- storing plaintext credentials
- deleting archived assets
- modifying parent AIOS truth
```

**This document itself performs none of the "Allowed — future work" items.** Only the requirement file was created.

---

## **11. Owner and Reviewers**

| Role | Reviewer |
| ----- | ----- |
| Owner | Satheskanth |
| Coordinator | Sathees or assigned coordinator |
| Business validator | Utharsika / domain owner |
| Technical reviewer | Sajeesan or assigned senior developer |
| Queryability reviewer | Tamil Selvan or assigned reviewer |

---

## **12. Pass/Fail Rule**

```
PASS when:

- requirement completed before 3:00 PM
- complete real data is used
- one row per ASIN is implemented
- SKU is removed
- Image column works
- missing and broken image messages work
- Orders are calculated ASIN-wise
- the current implementation reconciles to the current live source, under
  one documented date range, assignment scope, and status rule
- the 28 date-growth orders (2026-07-14 activity) are evidenced
- the remaining historical 13-order difference is documented as
  NOT_COMPARABLE_FROM_AVAILABLE_EVIDENCE, not silently dropped or invented
- no unsupported historical-equivalence claim is made (i.e. implementation
  does not claim 34,413 and 34,454 fully reconcile)
- a new versioned HTML is created
- no previous HTML is modified
- a new ph_task row is inserted only after approval
- no existing ph_task row is modified
- evidence is complete
- the result is LLM-queryable

FAIL when:

- current ASIN-level Orders do not reconcile to the current source
- unexplained differences exist within the same current source snapshot
  and query conditions (i.e. two queries against today's live data, using
  identical date range/scope/status rule, disagree with each other)
- any historical output is changed
```

**This section defines the pass/fail rule for the full deliverable (implementation), not for this requirement document alone.** For the requirement-document-only scope covered by this file, see Section 15 (Final Check).

---

## **13. Next Step**

Implement and validate the ASIN-level report update, then produce the new versioned HTML and submit it for publication approval before 3:00 PM. Sections 3.1 (join column), 5 (image tie-break — now `BUSINESS-CONFIRMED`), and 7.1 (Orders baseline) are all resolved with evidence. No open item remains blocking the start of implementation.

---

## **14. Queryability Self-Check**

| Question | Answered in |
| ----- | ----- |
| What was requested | Section 3 (Written Requirement) |
| Why this benefits the business before 3:00 PM | Section 2 (Business Purpose) |
| Who uses it | Section 1 (`end_user`) |
| What changes from the previous report | Section 3, Section 4 |
| What data sources were included | Section 2 (Source Information), Section 6 |
| How the image is selected/sourced | Section 5 (Image Selection Rule, Image Coverage), Section 3.1 (join column, resolved) |
| How Orders becomes ASIN-wise | Section 5 (ASIN-Wise Orders Rule), Section 7.1 (baseline, traced) |
| What evidence will prove completion | Section 8 |
| What business/technical confirmations exist | Section 5 (image tie-break — `BUSINESS-CONFIRMED`, deterministic technical selection required) |
| What non-blocking risk is being tracked | Section 9.1 (`ph_task` timestamp observation) |
| What should happen next | Section 13 |

**Result: every question is answerable from this file alone. Queryability: PASS.**

---

## **15. Final Check**

```
[x] Exact filename used: 2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md
[x] REQ-02-D01 used consistently throughout
[x] Previous requirement (REQ-01-D01) read-only, unchanged — verified, no write performed
[x] All mandatory template sections present (metadata, today requirement, business logic,
    data enrichment, business benefit/purpose, pass/fail rule, reviewers)
[x] Benefit before 3:00 PM stated explicitly (Section 1, Section 2)
[x] Sources and evidence listed (Section 2, Section 8)
[x] Owner and reviewers present (Section 11)
[x] Pass/fail rule is binary/numeric (Section 12)
[x] No unsupported claims added — the maid/ref_id join column and the 34,413/34,454 Orders
    gap were both resolved with direct database evidence (see Section 3.1, Section 7.1, and
    03_DISCOVERY\2026-07-15_uawso_REQ-02-D01_blocker_clarification.md), not silently assumed.
    The 13-order remainder is honestly classified NOT_COMPARABLE_FROM_AVAILABLE_EVIDENCE
    rather than forced to reconcile.
[x] Image tie-break rule is BUSINESS-CONFIRMED (Section 5) — Utharsika confirmed any valid
    image under an ASIN is acceptable; lowest listing_data.id remains documented purely as a
    deterministic technical consistency mechanism, not a business preference
[x] No open item remains blocking the start of implementation
```

**Document status: requirement corrected and business-confirmed. Implementation not started. No code, HTML, PostgreSQL data, or ph_task rows were modified in the creation or correction of this document.**
