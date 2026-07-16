# UAWSO Daily Summary — 2026-07-10

**Project:** Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report (UAWSO)
**Developer:** Satheskanth
**Requirement:** REQ-01-D01
**Status:** COMPLETE

---

## What was done today

Fixed two problems in the UAWSO dashboard and published the corrected version.

**1. Missing products.**
Before today, the dashboard only showed 1,610 of Utharsika's 1,723 assigned products. 113 products were missing because they had never sold anything on Amazon UK, so the report had no way to display them. We rebuilt the dashboard to always start from the full list of 1,723 assigned products, then add sales data on top. Now all 1,723 products are always visible, even the ones with zero sales.

**2. Wrong table layout.**
Before today, if one product had several SKUs, all the SKUs were squeezed into one table cell, separated by commas. This made the data hard to read and impossible to filter properly. We fixed this so each product-SKU combination gets its own row. A product with 3 SKUs now shows as 3 clean rows instead of 1 messy row.

**3. Missing sales channel.**
The dashboard was only counting two of Amazon's three sales channels — FBM and FBA. It was missing Vendor sales completely, which is about £46,642 in real revenue. We added Vendor sales and Vendor units to the dashboard, and made sure this money is only counted once per product (not accidentally multiplied across multiple SKU rows).

**4. Published the update.**
The corrected dashboard replaced the old one in the company system (`ph_task`, row 157). We did not create a new version — the existing report record was updated in place, so nothing else needed to change on the business side.

---

## Key numbers after the fix

| Metric | Value |
|---|---|
| Total assigned products | 1,723 (all shown) |
| Total table rows | 2,388 |
| Products with multiple SKUs shown correctly | Yes, one row per SKU |
| FBM Sales | £507,631.04 |
| FBA Sales | £170,330.29 |
| Vendor Sales | £46,642.46 |
| Duplicate rows found | 0 |
| Vendor revenue counted twice anywhere | 0 (checked and confirmed) |

---

## One open question — not resolved yet

There is one number we could not match. Someone gave us a reference figure for June 2025 sales of £42,086.96. Our system calculates £41,146.84 for the same period — a difference of £940.12.

We checked this eight different ways (different date ranges, with and without Vendor sales, different time zone handling) and could not find a calculation that produces the reference figure. We did **not** force our dashboard to show the reference number, because we could not prove it was correct.

**Next step:** whoever gave us the £42,086.96 figure needs to explain exactly how they calculated it, so we can compare it properly.

---

## Where to find the details

- Full technical write-up: `08_SKILLS\Daily Skills\2026-07-10__satheskanth__uawso__REQ-01-D01.md`
- Requirement document: `01_REQUIREMENTS\daily_requirements\2026-07-10_satheskanth_REQ-UAWSO_REQ-01-D01.md`
- Proof of the fix: `07_EVIDENCE\2026-07-10_utharsika_v001_ASIN_SKU_GRAIN_AND_JUNE_RECONCILIATION.md`
- Proof of the database update: `07_EVIDENCE\2026-07-10_utharsika_v001_PH_TASK_REPLACEMENT.md`
- Final report file: `09_OUTPUTS\2026-07-10_utharsika_v001.html`
