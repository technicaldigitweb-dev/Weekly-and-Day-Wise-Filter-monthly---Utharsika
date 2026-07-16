# UAWSO Business-Rule Update — AMAZON-Only Orders

| Field | Value |
| ----- | ----- |
| Date | 2026-07-16 |
| Author | Satheskanth |
| Project code | UAWSO |
| Parent requirement | REQ-02 |
| Deliverable | REQ-02-D01 |
| Change type | Business-rule update |
| Status | APPROVED |

**Parent requirement (unchanged, historical, not modified by this file):** `01_REQUIREMENTS\Requirement\2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md`

---

## Reason for Change

A read-only diagnosis (`07_EVIDENCE\2026-07-16_B0FX2XDLT5_june_cancelled_order_diagnosis.md`) of a real ASIN-level discrepancy found that FBM/FBA Orders were counting `REPLACEMENT`-source rows as valid Orders alongside `AMAZON`-source rows. For ASIN `B0FX2XDLT5` in June 2026, this produced 17 Orders where the business-confirmed correct figure is 16 — 17 raw `AMAZON`-source distinct order items, 1 correctly excluded for cancellation, 16 valid. The diagnosis proved the cancellation-exclusion filter itself has no defect (it correctly excludes the one `Canceled` row under either source scope); the defect is the Order *source* scope including `REPLACEMENT` rows, which do not represent genuine Seller Central Amazon orders.

## Prior Rule

FBM/FBA Orders (and every figure derived from them — PY/CY Orders, Order Change %, Total Amazon Orders, report Total Orders) used:

```sql
source_name IN ('AMAZON', 'REPLACEMENT')
```

## New Rule (Approved)

1. **Amazon Orders must use `source_name = 'AMAZON'` only** — FBM Orders, FBA Orders, PY Orders, CY Orders, Order Change %, Total Amazon Orders, and report Total Orders.
2. **`REPLACEMENT`-source rows must not contribute to any Order count.**
3. **Cancellation exclusion is unchanged**, applied to the AMAZON-only Order scope:
   ```sql
   source_name = 'AMAZON'
   AND order_status IS NOT NULL
   AND BTRIM(order_status) <> ''
   AND BTRIM(order_status) NOT IN ('Cancelled', 'Canceled')
   ```
4. **Vendor Orders** (unaffected by this update, carried forward from the 2026-07-15 amendment):
   ```
   Vendor Orders = public.vendor_sales.ordered_units
   One Vendor Unit = one Vendor Order
   ```
5. **Total Orders = FBM Orders + FBA Orders + Vendor Orders** (now computed from the corrected AMAZON-only FBM/FBA Orders).
6. **Sales logic is unchanged** — FBM/FBA Sales already used `source_name='AMAZON'` only; this update affects Orders only.
7. **The report requires Sales and Orders only. Quantity output fields are not required** (carried forward, unaffected by this update).

## Evidence Path

- Diagnosis: `07_EVIDENCE\2026-07-16_B0FX2XDLT5_june_cancelled_order_diagnosis.md`
- Reconciliation CSV: `07_EVIDENCE\generated_data\2026-07-16_B0FX2XDLT5_june_order_item_reconciliation.csv`

## Impacted Files

To be updated under this business-rule change (active implementation only, not archived/historical scripts):

- `05_IMPLEMENTATION\src\extract_uawso_v5_asin_level.py` — Orders source scope
- `05_IMPLEMENTATION\src\uawso_client_engine.js` — any client-side mirror of the Orders source scope, if present
- Associated active tests under `05_IMPLEMENTATION\tests\`

Sales logic in these same files is **not** to be changed by this update.

## Validation Rule (Regression Check)

Required for this update and every future refresh: ASIN `B0FX2XDLT5`, June 2026 (`order_date >= '2026-06-01' AND order_date < '2026-07-01'`) must reconcile to:

| Metric | Required value |
| ----- | ----- |
| Raw AMAZON-source distinct order items | 17 |
| Cancelled (excluded) | 1 |
| Valid Amazon Orders | 16 (14 FBM + 2 FBA) |
| REPLACEMENT-source rows contributing to the count | 0 |

The specific `REPLACEMENT` row `order_item_info = 1177733` must not appear in any Order count.

## Known Limits

- This update does not change how Sales is calculated — Sales was already `source_name='AMAZON'`-only.
- This update does not re-evaluate whether `REPLACEMENT` rows should count toward some other future metric (e.g. a distinct "Replacements" KPI) — that is out of scope here; `REPLACEMENT` rows are simply excluded from Orders.
- The parent requirement document (`2026-07-15_satheskanth_REQ-UAWSO_REQ-02-D01.md`) is treated as an immutable historical asset and is intentionally **not** edited by this update — this file is the authoritative record of the change instead.

## Next Step

Update the active extraction script and client engine to apply the AMAZON-only Orders rule, fetch fresh data, generate and validate a new `09_OUTPUTS\2026-07-16_utharsika_v001.html`, and hold publication to `ph_task` for a separate, later approval.
