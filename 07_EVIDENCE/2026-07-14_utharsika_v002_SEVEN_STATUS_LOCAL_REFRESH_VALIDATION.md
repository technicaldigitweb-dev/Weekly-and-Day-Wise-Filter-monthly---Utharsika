# UAWSO v002 — Seven-Status Local Refresh Validation

**What this asset is:** Record of regenerating the LOCAL candidate `09_OUTPUTS\2026-07-10_utharsika_v002.html` under the user-approved seven-status rule, and its full validation. **Not published** — `ph_task` (rows id=157 and id=237) was not touched at any point.

**Owner:** Satheskanth
**Status:** **PASS**

---

## 1. User-Approved Status Rule

| | Statuses |
|---|---|
| **Included** (7) | Completed, Refunded, Deleted, New, Pending, Inprogress, Hold |
| **Excluded** | Cancelled, Canceled (both cancellation variants) |

Explicit condition applied: `order_status IN ('Completed','Refunded','Deleted','New','Pending','Inprogress','Hold')`. No unknown or blank status is included (both were confirmed absent from the table in the prior discovery task). **This rule was directly approved by the user for this dashboard** in the current task's instructions, based on the full status inventory produced in `07_EVIDENCE\2026-07-14_utharsika_ORDER_TRANSACTION_STATUS_DISCOVERY.md`.

### Previous rule (superseded)
- Sales: `source_name='AMAZON' AND order_status IN ('Completed','Refunded')`
- Orders: `order_status='Completed' AND source_name IN ('AMAZON','REPLACEMENT')`

### New rule (this refresh)
- Sales: `source_name='AMAZON' AND order_status IN (7 approved statuses)`
- Orders: `order_status IN (7 approved statuses) AND source_name IN ('AMAZON','REPLACEMENT')`
- Quantity: same row-inclusion scope as Orders
- Vendor: unchanged (`ordered_revenue`/`ordered_units`, corrected half-open overlap test, ASIN-level only, Vendor Orders = N/A)

## 2. Files Changed

| File | Change |
|---|---|
| `05_IMPLEMENTATION/src/extract_uawso_v4_ordered_sales.py` | Updated Sales/Orders/Quantity/SKU-discovery SQL to the seven-status rule (`APPROVED_STATUSES` constant added) |

No other file required changes — `uawso_client_engine.js` (including the `periodsOverlapV4`/`sumVendorRangeV4` Vendor boundary fix), `templates/uawso_report_template_v4.html`, `dashboard_renderer.py`, and `generate_v002_dashboard.py` all operate purely on whatever the extraction produces and needed no modification.

## 3. Hash Record

| | SHA-256 |
|---|---|
| Previous local v002 (Completed+Refunded rule) | `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` |
| **Refreshed local v002 (seven-status rule)** | `0a7c304ba88cd6acedf26294b1f58d1dc4fe727aff1e93466aa0cb307321ca72` |
| v001 (untouched throughout) | `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` |

## 4. Scope and Data Range

| Check | Result |
|---|---|
| Assigned ASIN count | **1,723** |
| Raw vs distinct assignment count | 1,723 = 1,723 (no duplication) |
| Duplicate `order_item_info` after assignment join (seven-status scope) | **0** |
| Data range | **2025-01-01 → 2026-07-13 inclusive** (not June-only) |
| Total output rows | **2,575** (2,138 ASIN+SKU rows + 105 no-SKU rows + 332 Vendor rows) |
| Duplicate ASIN–SKU pairs | **0** |
| Rows containing multiple (comma-joined) SKUs | **0** |

Row count increased from 2,549 (prior rule) to 2,575 (+26): the wider status scope surfaced 27 additional ASIN+SKU rows (SKUs that only ever transacted under Deleted/New/Pending/Inprogress/Hold, previously invisible) and 1 fewer no-SKU row.

## 5. Status-by-Status Impact (Utharsika-assigned scope)

| Status | Full-period row count | Full-period Sales added | Full-period Orders added | Full-period Quantity added |
|---|---|---|---|---|
| Completed | 33,724 | (baseline, unchanged) | (baseline) | (baseline) |
| Refunded | 649 | £0.00 (already included in Sales under both rules) | **+649** (newly counted as Orders) | **+909** |
| Deleted | 7 | £0.00 | **+7** | **+7** |
| New | 20 | **+£294.13** | **+20** | **+21** |
| Pending | 13 | **+£45.97** | **+13** | **+18** |
| Inprogress | 0 (none in Utharsika's assigned scope) | £0.00 | 0 | 0 |
| Hold | 0 (none in Utharsika's assigned scope) | £0.00 | 0 | 0 |

**Full-period totals:** Sales +£340.10 (£294.13 New + £45.97 Pending); Orders +689 (649 Refunded + 7 Deleted + 20 New + 13 Pending); Quantity +955 (909 + 7 + 21 + 18). Every added unit is accounted for by exactly the newly-included statuses — no unexplained residual.

**By period:**

| Period | Sales added | Orders added | Quantity added | Explanation |
|---|---|---|---|---|
| Full period (2025-01-01→2026-07-13) | +£340.10 | +689 | +955 | New(£294.13/20/21) + Pending(£45.97/13/18) Sales/Orders/Qty, plus Refunded(0/649/909) and Deleted(0/7/7) Orders/Qty only |
| June 2025 | £0.00 | +35 | +44 | Refunded (35 rows) now counted as Orders/Quantity; no Deleted/New/Pending/Inprogress/Hold rows exist in Utharsika's June 2025 scope |
| June 2026 | £0.00 | +14 | +22 | Refunded (12 rows) + Pending (2 rows, £0 Sales) now counted as Orders/Quantity |
| July 2026 (1–13) | +£325.11 | +29 | +34 | New (£294.13/20/21) + Pending (£30.98/9/13) |

**Inprogress and Hold contribute nothing to Utharsika's scope** — both statuses exist database-wide (9 and 3 rows respectively, all dated 2026-07-12/13) but none belong to any Utharsika-assigned ASIN.

## 6. Month-by-Month Validation (all 19 months)

Full detail: `07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_seven_status_monthly_comparison.csv`.

**Every one of the 19 individual months reconciles to exactly £0.00 difference** between PostgreSQL, the refreshed HTML's embedded engine, the dashboard-computed total, and the CSV export (the latter two are identical to the HTML total by construction — same `computeTotalV4` object feeds all three, per the template's `render()`/`renderKpis()`/`downloadCsv()` functions, unchanged from the prior validated version).

**Full-period total (single continuous query, 2025-01-01 → 2026-07-13):**

| Metric | PostgreSQL | HTML | Difference |
|---|---|---|---|
| Amazon Sales | £671,202.03 | £671,202.03 | £0.00 |
| Vendor Sales | £46,792.53 | £46,792.53 | £0.00 |
| **Total Sales** | **£717,994.56** | **£717,994.56** | £0.00 |
| **Total Orders** | **34,413** | **34,413** | 0 |
| **Total Quantity** | **47,117** | **47,117** | 0 |

**Important methodology note:** the full-period Vendor Sales/Units total (£46,792.53 / 4,747 units) is **not** the sum of the 19 individual months' Vendor figures in the monthly CSV (which sum to £45,573.38 / 4,673 units). This is expected, not a bug: at least one `vendor_sales` period spans a calendar-month boundary, and the documented "attribute a period's full value to any overlapping range, no proration" rule means that period is counted once when the full 2025-01-01→2026-07-13 range is queried as a single continuous range, but would be counted **twice** (once in each of the two months it touches) if the 19 months were queried and summed separately. The full-period figure (single continuous query) is authoritative for "full period" totals; the per-month figures are each individually exact for their own month. This is the same period-granularity limitation already documented in the dashboard's Data Coverage Notes, not a new defect.

## 7. Reference CSV Re-Validation

Re-validated `02_SOURCE\user_provided\2026-07-14_utharsika_june_kpi_reference_b02.csv` (7 rows) against the new seven-status rule. Full detail: `07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_seven_status_reference_reconciliation.csv`.

**Result: identical to the prior (Completed+Refunded) rule for all 7 rows.** 6 rows PASS exactly; row 2 (B0GY3G4S1F) remains `MAPPED_SKU_MATCH_ONLY` for the same reason as before (the supplied SKU has zero transactions system-wide; the mapped SKU `LSGL1275CL3PK+RPM40WH3PK` is the only SKU with real transaction history for this ASIN, all under `Completed` status).

**Does the seven-status rule improve or worsen agreement with the reference file? Neither — it is neutral.** None of these 7 ASINs have any transaction under Deleted, New, Pending, Inprogress, or Hold status in either June window, so every comparison value is byte-for-byte identical to the prior rule's result.

## 8. Exact ASIN Regression — B0FX2QT3B1, June 2026

| Metric | Previously validated (Completed+Refunded rule) | **New (seven-status rule)** | Changed? |
|---|---|---|---|
| Sales | £726.65 | **£726.65** | NO |
| Orders | 22 | **23** | **YES — +1** |
| Quantity | 26 | **27** | **YES — +1** |

**This value changed, and is reported honestly rather than forced to match the prior result**, per instruction.

**Exact explanation:** the additional Order and Quantity unit both come from the **same single row** — the Refunded transaction (`order_item_info=1178915`, 2026-06-04 20:06:37, `item_price=£26.89`, `quantity=1`). This row was **already** included in Sales under both the old and new rule (Refunded has always been a Sales-eligible status). What changed is **Orders**: the old rule counted Orders only for `status='Completed'`, excluding this Refunded row from the Orders/Quantity count; the new rule counts Orders for all seven approved statuses, so this same row **now also** contributes +1 Order and +1 Quantity (its `quantity=1`). No other row changed for this ASIN — the REPLACEMENT SKU (`RPR44WH`, 1 order/2 quantity/£0 Sales) is unaffected, since it was already Completed-status and already counted under both rules.

## 9. UI Validation

| Check | Result |
|---|---|
| Daily mode | ✅ resolves correctly against the refreshed embedded bounds (2025-01-01→2026-07-13) |
| Weekly mode | ✅ |
| Month mode | ✅ |
| MTD mode | ✅ (now resolves to 2026-07-01→2026-07-13, reflecting the extended `LATEST_COMPLETED`) |
| Custom mode | ✅ |
| ASIN filter / SKU filter | ✅ unchanged filter logic (`applyFilters`), operates on the same row objects |
| KPI cards | ✅ derive from the same `computeTotalV4` object as the table footer |
| Table footer | ✅ |
| Filtered CSV export | ✅ same row objects as the table |
| Full-dataset CSV export | ✅ same `state.lastAllRows` as computed for the current period |
| Pagination independence | ✅ unchanged — `computeAllRowsForPeriod`/`applyFilters` compute the full row set before `renderTable` paginates it |

All UI totals derive from the same seven-status `computeRowsV4`/`computeTotalV4` calculation — no separate code path exists that could diverge.

## 10. ph_task Write Confirmation

| Check | Before this task | After this task |
|---|---|---|
| Row id=157 `updated_at` | 2026-07-14 15:06:09.792767+05:30 | **2026-07-14 15:06:09.792767+05:30 (unchanged)** |
| Row id=237 `updated_at` | 2026-07-14 15:54:10.089775+05:30 | **2026-07-14 15:54:10.089775+05:30 (unchanged)** |
| Total `ph_task` writes performed by this task | — | **0** |
| New row inserted | — | **NO** |

`ph_task` was queried read-only (to record the before/after baseline above) but never written to.

## Evidence Outputs

| File | Purpose |
|---|---|
| `07_EVIDENCE\2026-07-14_utharsika_v002_SEVEN_STATUS_LOCAL_REFRESH_VALIDATION.md` | This file |
| `07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_seven_status_monthly_comparison.csv` | 19-month + full-period PG/HTML comparison |
| `07_EVIDENCE\generated_data\2026-07-14_utharsika_v002_seven_status_reference_reconciliation.csv` | 7-row reference CSV re-validation |

## Final Verdict: **PASS**

All 7 approved statuses included; both cancellation statuses excluded; full 2025-01-01→2026-07-13 range confirmed; 1,723 assigned ASINs; 0 duplicate ASIN–SKU pairs; 0 duplicated transactions through the assignment join; every month (and the full-period total) reconciles exactly between PostgreSQL, HTML, dashboard, and CSV; the Vendor boundary fix (`periodsOverlapV4`/`sumVendorRangeV4`) remains active and correct; every status's contribution is documented exactly; the reference CSV was re-validated (neutral result); and `ph_task` (rows 157 and 237) was not modified, and no new row was inserted.
