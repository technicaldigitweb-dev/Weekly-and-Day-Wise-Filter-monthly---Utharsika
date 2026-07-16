# **Daily Requirement Document**

## **1. Metadata Block**

| Field | Value |
| ----- | ----- |
| daily_requirement_submitted_date | 2026-07-10 |
| expected_deadline_date | 2026-07-10 |
| end_user | Utharsika (`utharsika`) |
| expected_roi | Complete, trustworthy daily/weekly/MTD Amazon UK performance visibility across all 1,723 assigned ASINs (up from 1,610 previously visible), combining FBM, FBA, and Vendor revenue in one place — removing the need to manually cross-reference missing products or separate fulfilment-channel reports |
| developer | Satheskanth |
| project | Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report |
| project_code | UAWSO |
| phase | Phase-01 — Full Assigned-ASIN Coverage with FBM/FBA/Vendor Integration |
| requirement_id | REQ-01 |
| deliverable_id | REQ-01-D01 |
| blos_keys | Amazon UK, Completed orders only; 130% year-over-year achievement target; one table row = one ASIN + one SKU; Vendor Sales attributed once per ASIN (never duplicated across SKU rows) |
| domain | Sales & Orders — Amazon — UK |
| planned_benefits | - All 1,723 Utharsika-assigned ASINs visible, not just the 1,610 with transaction history<br>- Combined FBM + FBA + Vendor revenue in one dashboard, closing a previously-unreported ~£46.6K Vendor revenue gap<br>- Correct one-ASIN-one-SKU row grain removes ambiguous multi-SKU comma-joined rows<br>- Filterable, exportable (CSV) dashboard replacing a fixed, non-interactive report |

---

## **2. Today Requirement Block**

### **2.1 Today Requirement**

#### **Task Name:**

Correct ASIN–SKU Row Grain, Integrate FBM/FBA/Vendor Sales Coverage, and Publish the Updated UAWSO Dashboard

#### **Business Purpose:**

Allow Utharsika to review Amazon UK performance using complete assigned-product coverage and correct row-level product mapping — every one of her 1,723 assigned ASINs must be visible in the dashboard (not only the subset with existing transactions), each ASIN/SKU combination must be its own row (not merged into a comma-joined SKU list), and Sales must reflect all three fulfilment sources she can be paid through (FBM, FBA, Vendor), not FBM/FBA alone.

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
tech_team_outputs.ph_task
```

---

### **Filter Conditions**

```
source_name = 'AMAZON'
market_place = 'UK'
order_status = 'Completed'
Assigned scope: Utharsika only (public.user -> public.ph_categories -> public.ph_cate_products, DISTINCT applied)
Embedded history: 2025-01-01 to 2026-07-09
Selectable current-period range: 2026-01-01 to 2026-07-09
Reporting timezone: Asia/Colombo
Current (incomplete) day excluded
```

---

### **Required Data Output**

| Field | Purpose |
| ----- | ----- |
| ASIN | Product identification |
| SKU | Sellable-variant identification (blank when no SKU mapping exists for the ASIN) |
| Row Type | Distinguishes ASIN+SKU rows from no-SKU-mapping and Vendor-only rows |
| FBM Sales / FBM Orders | Fulfilled-by-Merchant revenue and order count |
| FBA Sales / FBA Orders | Fulfilled-by-Amazon revenue and order count |
| Vendor Sales / Vendor Units | Amazon Vendor revenue and unit count (no order-level key exists for Vendor data) |
| PY Sales / CY Sales | Previous-year and current-year Sales for the selected comparison period (FBM+FBA+Vendor) |
| Sales Change | (CY − PY) ÷ PY, undefined when PY = 0 |
| Trend | UP / DOWN / NO CHANGE, Sales-based only |
| Achievement % | CY Sales ÷ (PY Sales × 130%) × 100, undefined when PY = 0 |

---

## **3. Business Logic Block**

**Purpose:** Defines how the collected data must be evaluated and represented.

### **Row Grain Rule**

```
IF an assigned ASIN has one or more matching SKUs (from Completed Amazon UK transaction history)
THEN create one row per (ASIN, SKU) pair
ELSE create exactly one row for that ASIN with SKU = blank, mapping_status = NO_SKU_MAPPING

Never merge multiple SKUs into one comma-joined value.
Never omit an assigned ASIN from the output.
```

### **Vendor Non-Duplication Rule**

```
Vendor Sales/Units (public.vendor_sales, ASIN-only, no SKU) attach to exactly ONE row per ASIN:
  - the ASIN's existing blank no-SKU row, if it has one, OR
  - one additional blank "Vendor" row, if the ASIN already has SKU rows.
Vendor values are NEVER attached to a SKU-specific row.
```

### **Trend and Achievement Rule**

```
Sales Target = Previous Year Sales x 1.30
Achieve % = (Current Year Sales / Sales Target) x 100   [undefined, not fabricated, when Sales Target = 0]

Current Sales > Previous Sales -> UP
Current Sales < Previous Sales -> DOWN
Current Sales = Previous Sales -> NO CHANGE   (includes Previous = 0 AND Current = 0)
Previous = 0 AND Current > 0 -> UP
```

### **KPI / Filter Rule**

```
KPI cards and CSV export are always computed from the currently filtered row set,
calculated BEFORE pagination is applied — pagination must never change a total.
```

---

## **4. Data Enrichment Block**

**Purpose:** Collect additional product information after identifying candidates.

**Not applicable for this deliverable.** UAWSO's required output (ASIN, SKU, Sales, Orders, Trend, Achievement %) is fully satisfied by `order_transaction` and `vendor_sales`; no secondary enrichment source (e.g. a product-catalog system for titles/images/specifications) was required or used for this cycle. This section is retained per the template structure and marked not applicable rather than removed.

---

## **5. Business Benefit Delivered**

The updated dashboard allows Utharsika to:

- View all 1,723 assigned ASINs without products disappearing because of missing transactions.
- See each ASIN/SKU mapping independently, as its own row.
- Identify products with no SKU mapping or no sales activity (Row Type / Data Coverage Notes).
- Compare previous-year and current-year performance across Daily, Weekly, Month, and Month-to-Date views.
- View combined FBM, FBA, and Vendor revenue coverage in one place.
- Filter the dashboard to specific ASINs, SKUs, and periods using searchable multi-select dropdowns.
- See KPI cards recalculate live based on the selected filters.
- Download the exact selected/filtered data as CSV for further operational review.
- Access the corrected dashboard from the existing company dashboard record (no new task row, no new link to learn).

---

## **6. Completed Output**

| Field | Value |
| ----- | ----- |
| Output file | `09_OUTPUTS\2026-07-10_utharsika_v001.html` |
| Version | v001 (the existing v001 was updated in place — this is **not** v002) |
| Final SHA-256 | `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` |

---

## **7. Database Publication**

```
Database table:
tech_team_outputs.ph_task

Target row:
id = 157

Task ID:
UAWSO-2026-07-10-utharsika-v001

Assigned user:
utharsika

Assigned user team:
ph_priors

Version:
v001

Update type:
Existing HTML content replaced (UPDATE, not INSERT)

Columns updated:
html_content, updated_at only

Rows affected:
1

Duplicate row created:
NO

Other user data changed:
NO
```

---

## **8. Validation Results**

```
Distinct assigned ASINs represented:     1,723
Total output rows:                       2,388
Distinct populated ASIN-SKU pairs:       1,947
Rows containing multiple SKUs:           0
Duplicate ASIN-SKU pairs:                0
ASINs without SKU mapping:               113

FBM Sales:    £507,631.04
FBM Orders:   25,448

FBA Sales:    £170,330.29
FBA Orders:   7,886

Vendor Sales: £46,642.46
Vendor Units: 4,738
```

Vendor values are stored once at ASIN level (one dedicated row per ASIN with Vendor data) and are **not** duplicated across that ASIN's SKU rows — verified programmatically (0 Vendor Sales leaked onto any ASIN+SKU row; 0 ASINs with more than one Vendor-carrying row).

---

## **9. Evidence References**

- `07_EVIDENCE\2026-07-10_utharsika_v001_PH_TASK_REPLACEMENT.md`
- `07_EVIDENCE\2026-07-10_utharsika_v001_ASIN_SKU_GRAIN_AND_JUNE_RECONCILIATION.md`
- `07_EVIDENCE\2026-07-10_utharsika_VENDOR_SALES_VALIDATION.md`
- `07_EVIDENCE\2026-07-10_utharsika_ASIN_SCOPE_VALIDATION.md`

No credentials or full HTML content are reproduced in this requirement document.

---

## **10. Known Limitation**

```
June 2025 source-backed Sales:  £41,146.84
User-provided reference:        £42,086.96
Difference:                     £940.12

Status: The source of the user-provided reference has not yet been identified.
Eight reconciliation variants were tested (full month vs. partial-day range,
FBM+FBA-only vs. +Vendor, Vendor overlap vs. strict-containment allocation,
a timezone-shift hypothesis, live-vs-cached data) and none reproduced the
reference figure. The dashboard retains the database-reconciled value and
does not hardcode the reference value.
```

This limitation does not invalidate the ASIN/SKU row correction or the dashboard publication, but it remains **open for business clarification**.

---

## **11. Reusable Asset**

- Corrected UAWSO v001 HTML (self-contained, filterable dashboard)
- ASIN–SKU row-grain generation logic (`Engine.buildCanonicalRows`, `computeRowsV3`)
- Full assigned-ASIN master logic (`extract_uawso_full_coverage.py`)
- FBM/FBA/Vendor integration logic (`sumRangeSplitByAsinSku`, `sumVendorRange`)
- Filter-responsive KPI logic (cards computed pre-pagination from the filtered row set)
- Filtered CSV export logic (exports `state.lastFilteredRows`, full set, not the visible page)
- Validation and publication evidence (see Section 9)

---

## **12. Pass/Fail Rule**

```
PASS when:

- all 1,723 assigned ASINs are represented;
- each table row contains one ASIN and zero or one SKU;
- no row contains multiple SKUs;
- duplicate ASIN-SKU pairs = 0;
- FBM, FBA and Vendor totals reconcile to source;
- Vendor values are not duplicated;
- KPI cards respond to active filters;
- CSV export follows active filters;
- updated HTML is stored in the existing ph_task row;
- no duplicate ph_task row is created;
- other users' data is not modified;
- evidence paths are recorded.
```

**Final requirement status:** `PASS`

**Known business clarification:** June PY reference difference (£940.12) remains open.

---

## **13. Review Requirements**

| Role | Reviewer |
| ----- | ----- |
| Coordinator | Sathees or assigned coordinator |
| Technical reviewer | Sajeesan or assigned senior developer |
| Queryability reviewer | Tamil Selvan or assigned reviewer |
| Business validator | PH domain owner / Utharsika report owner |

---

## **14. Queryability Self-Check**

| Question | Answered in |
| ----- | ----- |
| What was requested | Section 2 (Today Requirement) |
| Why the dashboard was needed | Section 2 (Business Purpose), Section 5 |
| Who uses it | Section 1 (`end_user`), Section 1 metadata |
| What was updated | Section 2, Section 3 (Business Logic Block) |
| What data sources were included | Section 2 (Source Information) |
| How ASIN and SKU rows are represented | Section 3 (Row Grain Rule) |
| What evidence proves completion | Section 9 |
| Where the final HTML is stored | Section 6 |
| Where the dashboard record is stored | Section 7 |
| What limitation remains | Section 10 |
| What should happen next | Section 10 (route the June reference question), Section 13 (review roles) |

**Result: every question is answerable from this file alone. Queryability: PASS.**
