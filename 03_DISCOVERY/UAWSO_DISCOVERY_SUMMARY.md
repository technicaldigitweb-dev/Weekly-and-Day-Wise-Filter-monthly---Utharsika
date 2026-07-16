# UAWSO Discovery Summary

**What this asset is:** A record of what already existed before this design stage, so no work is duplicated.

**Why it exists:** AIOS's existing-asset-first rule requires proof that a search happened before new assets were created.

**Business question supported:** "Was anything reusable already built, and did we check before building new?"

**Source or evidence used:** Full inspection of the project root (this stage) and the temporary `Sources` folder (prior discovery stage, both now folded into `02_SOURCE\UAWSO_SOURCE_REGISTER.md`).

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Complete for this stage.
**Known limits:** Discovery was scoped to the approved project root and read-only database schema lookups; no other project folders or other users' data were inspected.
**Pass/fail rule:** N/A (descriptive asset).
**Next action:** None — proceed to design, which is already built on these findings.

---

## What existed before this stage

- No prior AIOS folder structure existed under the project root — only a flat `Sources` folder with 13 files.
- No prior SQL, HTML template, `ph_task` publishing script, scheduler, validation evidence, generated report, or handover record existed anywhere in the project.
- A canonical, reusable schema/business-rule reference for `public.order_transaction` already existed (`TABLE_order_transaction.md`, newest copy in `skills_minimal_pack 2 (2).zip`) — reused, not rebuilt.
- Canonical `tech_team_outputs.ph_task` schema, versioning, and `assigned_user_team` routing rules already existed in `ph_task_rules\` — reused, not rebuilt.
- The requirement itself (`PH-2026-07-UTHAR03`) already existed as a live worksheet inside the shared `PHs Daily works - Dev_Automation.xlsx` tracker — treated as canonical input, not rebuilt.
- Generic DB connection/update Python templates existed — reused as reference patterns, not rewritten.

## What did not exist and was newly resolved this stage (via read-only DB inspection)

- The exact assignment chain (`public.user` → `public.ph_categories` → `public.ph_cate_products`) was documented only in prose (`PH_assigned_user_Standard...docx`) without column names. This stage confirmed the real column names and resolved Utharsika's actual assignment: `user=109`, 2 categories, 1723 assigned Amazon ASINs (`ref_id` where `which_channel=1`), 0 internal duplicates.
- The live `ph_task_task_id_unique` constraint was confirmed to exist in production — this was previously only known from a template-script comment (drift risk flagged in prior discovery), now confirmed authoritative and directly shapes the same-date-correction `task_id` design.
- The `Sales Change` / `Order Change` formula was not stated as text anywhere — derived and confirmed this stage from the worksheet's own illustrative sample numbers (percentage growth, `(Current−Previous)÷Previous`), matching two independent sample rows exactly.

## Duplicate-truth risks found and resolved

- Two copies of `TABLE_order_transaction.md` existed (older/newer). Resolved: newer designated canonical, older retained as historical only, no rule conflict found between them.
- `ph_task_schema 5.md` and the DDL comment embedded in `update_table.py` disagreed on whether `task_id` is unique. Resolved via live schema check: `task_id` **is** unique — the schema doc undercounted a constraint; the template comment was correct. This is documented as a doc-drift note in `02_SOURCE\UAWSO_SOURCE_REGISTER.md`, not silently ignored.

## Isolation confirmation

No other PH user's `ph_task` rows, `html_content`, or report data were inspected, copied, or used as a template at any point during discovery or this design stage. **Other users' ph_task report content inspected or reused = NO.**
