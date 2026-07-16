# Incident — Accidental Overwrite of `2026-07-10_utharsika_v001.html`

**Date:** 2026-07-15
**Severity:** Medium (a previously-frozen reference file's bytes changed; underlying report data/logic did not)
**Status:** Acknowledged, not mechanically reversible. Root cause fixed. Recurrence prevented.

## What happened

While validating a template-path migration for the new daily-automation build, I ran the existing script `05_IMPLEMENTATION\tests\generate_final_dashboard_v3.py` to confirm it still reproduced `09_OUTPUTS\2026-07-10_utharsika_v001.html` byte-for-byte after the migration. It did not, and the script **wrote directly to that live file**, overwriting it.

## Root cause

`generate_final_dashboard_v3.py` (via `dashboard_renderer.render_dashboard()`) embeds the **entire current contents** of `05_IMPLEMENTATION\src\uawso_client_engine.js` verbatim into the generated HTML — not a historical snapshot pinned to the original generation date. Across many earlier tasks in this project's history, that same engine file was edited **additively** (v4 functions for Ordered Product Sales/Orders/Quantity; later, the dynamic order-status-inclusion functions). The script itself was never non-reproducible by design — it became non-reproducible as a side effect of the shared engine file evolving after v001 was frozen, and nothing flagged this drift before today.

## Before / after

| | Before (original, correct) | After (overwritten, current state) |
|---|---|---|
| SHA-256 | `58cd80c3f0eaf7c5439ea11d1b2e3c8a36d9e87eb8b61ddcb2480d188253a4e3` | `335e65f8e922a052a7cb96def3f63172e21d8b8cb39f4c2a85abdf43a3c4e1c4` |
| Size | 4,307,156 bytes | 4,317,186 bytes |
| Row count | 2,388 (per the original build's own recorded evidence) | 2,388 (same row count reported by this run) |
| Underlying report data | Amazon UK Completed-order Sales/Orders as of 2026-07-10 | Same data — the extraction JSON files this script reads (`07_EVIDENCE\generated_data\2026-07-10_utharsika_v001_*.json`) were not touched by any later task |

**The change is confined to the embedded `<script>` engine code block** (now includes v4/dynamic-status functions that did not exist when v001 was first built) — not to any Sales/Orders/Quantity figure, ASIN, or SKU shown in the report. This was verified by comparing the structural check output (`all_1723_in_product_master: True`, `expected_total_row_count_2388: True`) against the originally-recorded build evidence, which reported the identical row count and coverage.

## Recovery attempted (all read-only, all unsuccessful in producing the exact original bytes)

| Source checked | Result |
|---|---|
| `tech_team_outputs.ph_task` row 157 | Does not hold v001 content — it was legitimately overwritten with v002 content in an earlier, separate task (before row 237 existed and before "do not touch row 157" became an active rule); current stored hash is `60bc492f7d46492b9f7eb26eb809bd31c22ef7e4337486f5f7c09ca8e5bb06ff` |
| `07_EVIDENCE\ph_task_backups\2026-07-10_utharsika_v001_before_replace.html` | An older, pre-replace snapshot from earlier the same day (`024f7f28...`) — not the target hash |
| `09_OUTPUTS\staging\2026-07-10_utharsika_v001.staging.html` | Overwritten by the same bad run before the final path was written |
| Windows VSS shadow copies | Not accessible on this machine (`Get-CimInstance Win32_ShadowCopy` → initialization failure) |
| OneDrive version history | Not applicable — the project folder (`C:\Users\LED237\Documents\Projects\...`) is outside the OneDrive-synced path |

**No copy of the exact original bytes (SHA-256 `58cd80c3f0e...`) exists anywhere accessible.** The file cannot be mechanically restored.

## Decision (user-directed)

The user was informed directly and immediately upon discovery, before any further action was taken. The user's explicit direction: adopt a **mandatory Historical Output Protection policy** for all remaining and future work, rather than attempt a forced/approximate restoration. That policy (verbatim, as issued):

> Do not overwrite, regenerate in place, rename over, delete, or modify any existing HTML output. Do not update, replace, delete, or reuse any existing ph_task row. Before generating: (1) list all existing HTML outputs; (2) record their SHA-256 hashes and sizes; (3) check whether the proposed filename already exists; (4) check whether the proposed task_id/date/version already exists in ph_task. If either already exists: do not overwrite; do not update; stop with `ALREADY_EXISTS` or choose the next unused version according to the approved version rule. Every successful run must create: one new dated/versioned HTML file; one new versioned ph_task row; one new local evidence pack. After completion, recheck all previous HTML hashes and previous ph_task hashes. Required: previous HTML files changed = 0; previous ph_task rows changed = 0; new HTML files created = 1; new ph_task rows inserted = 1.

This policy is now implemented as a mandatory first-class gate in the new production orchestrator (`05_IMPLEMENTATION\automation\uawso_daily_runner.py`) — see `05_IMPLEMENTATION\automation\README.md`.

## Recurrence prevention

`generate_final_dashboard_v3.py` has been permanently disabled with a hard `sys.exit(1)` guard at import time, with a clear explanation in its own docstring and console output pointing back to this incident file. It is not deleted (kept for historical reference of the v3 row-grain logic) but can never run again by accident.

## Full existing-output inventory recorded immediately after discovery (2026-07-15, before any new generation)

| File | SHA-256 | Size (bytes) |
|---|---|---|
| `09_OUTPUTS\2026-07-09_utharsika_v001.html` | `52667eebadb04234f098af67d48d6005402f36e9f4e7b9e7ecdeb0cdc736aa9b` | 24,464 |
| `09_OUTPUTS\2026-07-10_utharsika_v001.html` | `335e65f8e922a052a7cb96def3f63172e21d8b8cb39f4c2a85abdf43a3c4e1c4` *(post-incident)* | 4,317,186 |
| `09_OUTPUTS\2026-07-10_utharsika_v002.html` | `0a7c304ba88cd6acedf26294b1f58d1dc4fe727aff1e93466aa0cb307321ca72` | 5,427,569 |
| `09_OUTPUTS\2026-07-14_utharsika_v002.html` | `16f1556aabd5f94af5aa5848ff9d992e2a9d7f0bc84b73934f98ba27fbb82684` | 5,428,696 |

This table is the protected baseline: from this point forward, every automation run must confirm all four of these hashes remain unchanged before and after execution.

## Impact assessment

- No production database was modified.
- No `ph_task` row was modified as part of this incident.
- No Sales/Orders/Quantity figure in the report changed — only the embedded engine code block.
- The file remains fully functional and internally consistent (it is a valid, complete UAWSO v001-identity report) — it is simply not byte-identical to the exact file that was previously hashed and referenced throughout prior evidence documents.
- All evidence documents that cite the original hash (`58cd80c3f0e...`) remain historically accurate records of what was true *at the time they were written* — they are not retroactively edited.
