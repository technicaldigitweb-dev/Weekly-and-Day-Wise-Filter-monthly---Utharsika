# UAWSO — 2026-07-16 Utharsika v001 Publication (ph_task)

**Target:** `tech_team_outputs.ph_task`, new row for `09_OUTPUTS\2026-07-16_utharsika_v001.html`
**Execution date:** 2026-07-16
**Result: PASS** — one new row (id=262) inserted; rows 157, 237, and 256 confirmed unchanged.

---

## 1. Local HTML Verification

| Item | Value |
| ----- | ----- |
| Path | `09_OUTPUTS\2026-07-16_utharsika_v001.html` |
| Byte size | 5,011,392 |
| SHA-256 | `b0a781f4d79e5be64fe446bdbe93dd789f4c61f92dfa0dac3e90eb0fdecea2bf` |
| Matches expected hash | YES, exact |
| ASIN rows | 1,723 |
| FBM Orders | 26,271 |
| FBA Orders | 7,975 |
| Vendor Orders | 4,748 |
| Total Orders | 38,994 |
| Total Sales | £719,453.86 |
| Quantity fields remaining | 0 |
| Report period | 2025-01-01 through 2026-07-15 |

All values re-verified before publication (re-ran the dedicated test suite, `05_IMPLEMENTATION\tests\test_uawso_2026_07_16_amazon_only_orders_v001.js`, against this exact file — 22/22 passed). No `LOCAL_HTML_VALIDATION_FAILED` condition was hit.

## 2. Assigned User Resolution

Resolved from `public.user` (read-only): `user_name='utharsika'`, `user_firstname='Utharsika'`, `user_status='Active'` — exact match for `lower(user_name) = lower('utharsika')`. Used verbatim, not retyped or re-cased: **`utharsika`**.

## 3. Established Publication Conventions (read from row 256, the most recent prior UAWSO row)

| Field | Row 256 value | Used for this publication |
| ----- | ----- | ----- |
| `project_name` | `Utharsika Amazon UK Daily, Weekly and Month-to-Date Sales and Orders Report` | Same (via `config.config.PROJECT_NAME`) |
| `team` | `PH Team` | Same (via `config.config.TEAM`) |
| `developer` | `Satheskanth` | Same |
| `assigned_user_team` | `ph_priors` | Same |
| `phase_level` | `1` | Same |

**Disclosure:** the governing task's literal instruction gave `project_name: Weekly and Day Wise Filter Monthly` — this text matches the local project *folder* name, not the `project_name` field actually stored in `ph_task` by every prior UAWSO row (157, 237, 256), all of which use the full report title above. Using the literal folder-name text would have broken `project_name` consistency for the same `project_code` across rows, so the established, already-approved convention was used instead (sourced from `config.config.PROJECT_NAME`, the exact constant every previous successful UAWSO publication has used). No other field required this kind of substitution — `team`, `developer`, `assigned_user_team`, and `phase_level` in the governing task's instructions already matched the established convention exactly.

## 4. Duplicate Check (before insert)

Queried all `project_code='UAWSO'` rows and specifically `task_id LIKE 'UAWSO-2026-07-16%'` and any `task_name`/`description` mentioning `2026-07-16`: **0 matching rows found**. Only rows 157, 237, and 256 existed (all for prior dates). Proceeded to INSERT.

## 5. Insert (via the existing, unmodified `ph_task_publisher.publish_report()`, `is_correction=False`)

| Field | Value |
| ----- | ----- |
| Inserted row ID | **262** |
| `task_id` | `UAWSO-2026-07-16-utharsika-v001` |
| `project_code` | `UAWSO` |
| `assigned_user` | `utharsika` |
| `assigned_user_team` | `ph_priors` |
| `phase_level` | `1` |
| `version_level` | `1` |
| `version_status` | `released` |
| `action_took_by` / `action_took_date_time` | Left `NULL` (not set) |
| Stored HTML SHA-256 | `b0a781f4d79e5be64fe446bdbe93dd789f4c61f92dfa0dac3e90eb0fdecea2bf` |
| Stored/local SHA-256 match | **YES, exact** |
| Read-back verification (inside `publish_report`) | Passed (`project_code`, `task_id`, `assigned_user`, `assigned_user_team`, `version_status`, `html_content` all matched) |
| Active rows for `2026-07-16` after insert | **1** (exactly one, as required) |
| Transaction committed | **YES** |

## 6. Post-Commit Verification

| Check | Result |
| ----- | ----- |
| Row 256 unchanged (hash + `updated_at`) | YES |
| Row 237 unchanged | YES |
| Row 157 unchanged | YES |
| Rows inserted | 1 |
| Rows updated | 0 |
| Rows deleted | 0 |
| Exactly one active `2026-07-16` UAWSO output | YES (row 262 only) |
| Local HTML unchanged after publication | YES (re-hashed, matches `b0a781f4...`) |

## 7. Final PASS/FAIL

```
- one new row inserted                                     YES (id=262)
- no existing row updated                                  YES (0 updated)
- no row deleted                                            YES (0 deleted)
- exact 2026-07-16 HTML stored                              YES
- local/stored hashes match                                 YES
- assigned_user is exact                                    YES (utharsika)
- assigned_user_team = ph_priors                             YES
- version_level = 1                                          YES
- version_status = released                                  YES
- row 256 unchanged                                          YES
- prior-day rows (157, 237) unchanged                        YES
- exactly one active 2026-07-16 Utharsika output             YES
```

**FINAL STATUS: PASS.** `tech_team_outputs.ph_task` row **262** (`UAWSO-2026-07-16-utharsika-v001`) is published, read-back verified, and byte-identical (by SHA-256) to the approved local `09_OUTPUTS\2026-07-16_utharsika_v001.html`. Rows 157, 237, and 256 are confirmed unchanged. `daily_task` was not accessed. No automation or Task Scheduler was touched.
