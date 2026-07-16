# UAWSO v004 — 15-Row Table Viewport Correction and ph_task Row 256 Replacement

**Target (approved replacement, not a new version):** `09_OUTPUTS\2026-07-15_utharsika_v004.html`
**Target database row (approved replacement, not a new row):** `tech_team_outputs.ph_task.id = 256`
**Execution date:** 2026-07-15
**User approval:** Explicit — user approved correcting the existing v004 output and replacing the HTML stored in the existing ph_task row 256, with an explicit list of prohibitions (no v005, no new row, no changes to rows 157/237, no other HTML output changes, no data/KPI logic changes, no automation).

---

## 1. Baseline Verification (before any change)

| Item | Value |
| ----- | ----- |
| Local v004.html size | 5,123,369 bytes |
| Local v004.html SHA-256 | `8751b4d373772d4bc38c5e424000f846b842b61b73a9bb40368ba71df57d6f1e` |
| Row 256 stored SHA-256 (read-only) | `8751b4d373772d4bc38c5e424000f846b842b61b73a9bb40368ba71df57d6f1e` |
| Local/stored match before correction | YES, exact |

Both sides matched the expected pre-correction hash exactly — no `BASELINE_HASH_MISMATCH`.

## 2. Reversible Backups

| Backup | Path | Verified |
| ----- | ----- | ----- |
| Local HTML backup | `09_OUTPUTS\staging\2026-07-15_utharsika_v004_before_15_row_view_update.html` | Byte-identical to pre-correction v004.html (SHA-256 matches exactly) |
| Database content backup | `07_EVIDENCE\ph_task_backups\2026-07-15_utharsika_v004_row_256_before_15_row_view_update.html` | SHA-256 of the backup file matches the DB-computed `html_sha256` for row 256 exactly |
| Backup metadata | `07_EVIDENCE\ph_task_backups\2026-07-15_utharsika_v004_row_256_before_15_row_view_update.meta.json` | Records row ID, task ID, version, stored byte size/SHA-256, backup path |

No credential value was displayed or logged during either backup.

## 3. Viewport Issue — Measured, Not Guessed

A headless Chromium browser (Python `playwright` package, previously undetected in this session but confirmed present and fully functional) was used to genuinely render and measure the **actual current v004.html** before any change:

| Dimension | Measured value |
| ----- | ----- |
| `thead` row height | 28px |
| Body row height (uniform across sampled rows) | 59px (driven by the 48px `.uawso-product-image` + 5px/5px td padding + 1px collapsed border — the tallest cell in a row; the 24 no-image ASINs render a shorter row, which can only ever show *more* than the target row count, never fewer) |
| Pagination bar height | 53px |
| Previous `.uawso-table-wrap` sizing | `max-height: 70vh` (viewport-relative — at 900px window height this computed to 630px, enough for only ~9 rows in principle, and materially fewer on the user's actual, likely smaller, window) |

**Root cause:** the old `70vh` rule sized the table viewport as a fraction of whatever window height happened to be open, so the number of visible rows varied by device/window size rather than being a fixed, intentional count.

## 4. Fix Applied

Added four CSS custom properties to `:root` in `05_IMPLEMENTATION\templates\uawso_report_template_v5_asin_level.html`, all sourced from the real measurements above (not guesses):

```css
--uawso-header-height: 28px;
--uawso-row-height: 59px;
--uawso-pagination-height: 53px;
--uawso-visible-row-count: 15;
--uawso-viewport-buffer: 6px;   /* compensates for .uawso-table-wrap's own 1px top+bottom border under box-sizing:border-box, measured empirically to close a ~3.5px shortfall that left row 15 barely clipped */
```

Replaced the viewport-relative rule:

```css
.uawso-table-wrap { max-height: calc(var(--uawso-header-height) + (var(--uawso-row-height) * var(--uawso-visible-row-count)) + var(--uawso-pagination-height) + var(--uawso-viewport-buffer)); }
```

Result: an **absolute pixel height (972px)**, independent of the viewer's window size, computed directly from header + 15 rows + pagination (+ a small measured border-compensation buffer) — not a device-relative guess.

No extraction, KPI, image-selection, Vendor, or status logic was touched. Page size remains 50 (unchanged).

## 5. Actual Visible-Row Result (measured, real browser)

Re-rendered from the **same embedded data snapshot** (`07_EVIDENCE\generated_data\2026-07-15_utharsika_v004_*.json` — no new query) via `generate_uawso_v5_2026_07_15_15row_view_update_staging.py`, then measured with the same Playwright harness at three different window sizes:

| Viewport | Fully-visible body rows | Row 15 fully visible | Row 16 requires scroll |
| ----- | ----- | ----- | ----- |
| 1440×900 | 15 | YES | YES |
| 1366×768 | 15 | YES | YES |
| 1920×1080 | 15 | YES | YES |

Identical result at all three sizes — confirms the fix is genuinely device-independent, unlike the prior `70vh` rule.

## 6. Preserved UI Functions (functionally verified, real browser)

| Function | Result |
| ----- | ----- |
| Sticky header | YES (`position: sticky` confirmed via `getComputedStyle`) |
| Sticky ASIN column | YES |
| Sticky Image column | YES |
| Sticky pagination | YES |
| Pagination does not cover row 15 | YES (row 15 counted fully visible, above the pagination-covered band) |
| Previous button | YES (clicked; page changed 1→prev correctly after Next) |
| Next button | YES (clicked; "Page 1 of 35" → "Page 2 of 35") |
| Go-to-page input + Go button | YES (typed "10"; "Page 10 of 35") |
| Page/total-page display | YES ("Page N of 35" shown throughout) |
| Filtered-row range display | YES |
| Search | YES (searching a specific ASIN reduced visible rows from 1,723 to 1; reset restored 1,723) |
| Date filters / ASIN filter | Present and functioning (filter panel unchanged; search test above exercises the same filter pipeline) |
| One full-filtered-data download | YES — captured the **real download event** (not an internal state read, since `state` is module-scoped inside the template's IIFE and not exposed on `window`): CSV contained exactly 1 header line + 1,723 data rows = 1,724 lines |
| Column Definitions section | YES, present (`#uawso-column-definitions` found) |

## 7. Data and KPI Values (unchanged, verified against the real engine)

| Metric | Before | After | Difference |
| ----- | ----- | ----- | ----- |
| Data range | 2025-01-01 → 2026-07-14 | 2025-01-01 → 2026-07-14 | none |
| ASIN rows | 1,723 | 1,723 | 0 |
| Sales | £718,835.91 | £718,835.91 | £0.00 |
| Orders | 34,454 | 34,454 | 0 |
| Quantity | 47,166 | 47,166 | 0 |

Recomputed by extracting the actual embedded JSON from the corrected, promoted file and running the real, unmodified `uawso_client_engine.js` (`buildCanonicalRowsV5`/`sumRangeByAsinV5`/`sumVendorRangeV4`/`computeRowsV5`/`computeTotalV5`) in Node — not assumed unchanged.

## 8. Local File Update

| Item | Value |
| ----- | ----- |
| Staging path | `09_OUTPUTS\staging\2026-07-15_utharsika_v004_15row_view_update.staging.html` |
| Staging SHA-256 | `51865bbb45a5b49c15c74156723efa12d8ec6211f397487e9dec12f288587b24` |
| Atomic replace | `update_uawso_v004_15row_view.py` — asserted target filename, verified backup hash and current-file hash both equal the expected pre-update hash before replacing; temp-file write + hash-verify + `os.replace()`; re-verified final hash matches staging hash |
| Updated local file size | 5,124,804 bytes |
| Updated local file SHA-256 | `51865bbb45a5b49c15c74156723efa12d8ec6211f397487e9dec12f288587b24` |
| Other historical HTML files (v001 07-09, v001/v002 07-10, v002 07-14) | Re-hashed immediately after the replace: all 4 **UNCHANGED** |

## 9. Tests

New suite: `05_IMPLEMENTATION\tests\test_uawso_15row_viewport_v5.py` — genuine Playwright-driven functional tests (not static grep), covering all 19 required items from Section 9 of the governing task (visible-row target, row 15/16 boundary at 3 viewport sizes, page size, sticky header/columns/pagination, pagination-does-not-cover-row-15, Previous/Next/direct-navigation, real-download-capture row count, Sales/Orders/Quantity/ASIN-count unchanged via the real engine, and all 4 other historical HTML files unchanged). **28/28 checks passed**, run once against the staging file and once again against the final promoted file (identical result both times).

Full regression re-run: `test_uawso_client_engine.js` 42/42, `test_uawso_client_engine_v2.js` 19/19, `test_uawso_client_engine_v3.js` 21/21, `test_uawso_client_engine_v5.js` 23/23, `test_uawso_sticky_columns_and_export_v5.js` 21/21, `test_uawso_pagination_v5.js` 40/40 — all still passing (166/166), confirming the CSS-only change did not affect any prior functionality. **Total: 194/194 across all suites.**

## 10. Browser Validation

**Full browser validation was possible this time** — a headless Chromium browser (`playwright` Python package) was found to be genuinely available in this environment (previously disclosed as unavailable in the sticky-columns and pagination tasks). All Section 10 checks were performed with real rendering and real measurement, not static source inspection: 15 complete rows visible, header fully visible, pagination fully visible, row 15 not clipped, row 16 requires scrolling, no overlap, frozen ASIN/Image columns confirmed via `getComputedStyle`, horizontal scroll unaffected (no change made to that axis), vertical scroll confirmed programmatically. No pixel-level limitation remains to disclose for this task.

## 11. ph_task Row 256 Update

Reused the existing, approved credential mechanism (`config/.env` via `config.config.load_db_config()`, the same one used for the original v004 publication) and wrote a dedicated content-only UPDATE script, `update_ph_task_row_256_15row_view_2026_07_15.py` — no new publisher, no new credential mechanism.

| Field | Value |
| ----- | ----- |
| Target row | id = 256 |
| Operation | `UPDATE tech_team_outputs.ph_task SET html_content = ..., updated_at = now() WHERE id = 256` |
| task_id | Unchanged: `UAWSO-2026-07-15-utharsika-v004` |
| version_level | Unchanged: 4 |
| project_code / assigned_user / assigned_user_team | Unchanged: `UAWSO` / `utharsika` / `ph_priors` |
| description | Unchanged — already accurate, contained no obsolete UI details requiring correction |
| Rows inserted | 0 |
| Rows updated | 1 |
| Rows deleted | 0 |
| Stored HTML SHA-256 after commit | `51865bbb45a5b49c15c74156723efa12d8ec6211f397487e9dec12f288587b24` |
| Local/stored hash match | YES, exact |
| Row 157 unchanged (hash + updated_at) | YES |
| Row 237 unchanged (hash + updated_at) | YES |
| Total UAWSO rows after update | 3 (unchanged — 157, 237, 256; no new row) |
| Transaction committed | YES (pre-commit checks all passed first) |

## 12/13. Transaction Safety and Post-Commit Verification

Pre-commit checks (inside the same transaction, before COMMIT): target row ID = 256 ✓, exactly one row affected ✓, task_id unchanged ✓, version_level unchanged ✓, project_code/assigned_user/assigned_user_team unchanged ✓, stored HTML SHA-256 equals the corrected local SHA-256 ✓, row 157 unchanged ✓, row 237 unchanged ✓ — all passed, so the transaction proceeded to COMMIT (no rollback needed). Post-commit: row 256 re-read fresh, hash re-verified, rows 157/237 re-read and re-verified unchanged, other historical local HTML files re-hashed unchanged.

## 14. Final PASS/FAIL

```
- 15 complete rows visible (3 viewport sizes)                YES
- row 15 not clipped                                          YES
- pagination does not cover rows 1-15                         YES
- page size remains 50                                        YES
- sticky header works                                          YES
- sticky ASIN and Image columns work                           YES
- sticky pagination works                                      YES
- KPI values unchanged (Sales/Orders/Quantity/ASIN count)      YES (0 difference, verified via real engine)
- local v004 updated successfully                              YES
- ph_task row 256 updated successfully                         YES
- local/stored updated hashes match                            YES
- rows inserted                                                 0
- rows updated                                                  1
- rows deleted                                                  0
- rows 157/237 unchanged                                       YES
- other historical HTML files unchanged                        YES
- no v005 created                                               YES (confirmed - no new file)
- no new ph_task row created                                   YES (confirmed - total UAWSO rows still 3)
- automation/Task Scheduler touched                             NO
```

**FINAL STATUS: PASS.** The table viewport now shows exactly 15 complete rows at any window size (measured, not guessed), with row 16 reachable by scrolling, all sticky/pagination/filter/search/download functionality intact, and zero change to Sales/Orders/Quantity/ASIN count. `tech_team_outputs.ph_task` row 256 was updated in place (not replaced with a new row) and verified byte-identical to the corrected local file. Rows 157 and 237, and all other local HTML outputs, are confirmed unchanged.
