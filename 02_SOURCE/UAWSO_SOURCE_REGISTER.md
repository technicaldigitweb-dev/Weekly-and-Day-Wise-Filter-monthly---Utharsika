# UAWSO Source Register

**What this asset is:** The canonical list of every source file this project depends on, and its current location, after migration.

**Why it exists:** So no one has to search the filesystem to find a source — this is the index.

**Business question supported:** "Where is the file that defines X?"

**Source or evidence used:** `02_SOURCE\UAWSO_SOURCE_MIGRATION_MANIFEST.md` and `07_EVIDENCE\source_migration\UAWSO_SOURCE_MIGRATION_VALIDATION.md`.

**Owner:** Satheskanth
**Reviewer:** Satheesvaran
**Current status:** Current as of 2026-07-10, post-migration.
**Known limits:** If any of these files are edited in place after this date, this register's descriptions may drift from the live content — re-verify before relying on it for a new implementation pass.
**Pass/fail rule:** N/A (index asset).
**Next action:** Keep this register updated if any source file is superseded or a new one is added.

---

## Governance & Architecture

| File | Canonical path | Purpose |
|---|---|---|
| AIOS GPT Project instructions/prompts/skills pack | `00_PROJECT_CONTROL\governance_sources\AIOS GPT Project intructions, prompts and skill files-20260619T091849Z-3-001.zip` | General AIOS operating model (GPT=brain, Claude=worker); not project-specific |
| AIOS architecture doc | `00_PROJECT_CONTROL\governance_sources\aios_architecture.md` | 6-tier MySQL→PostgreSQL→Intelligence architecture governing all AIOS projects |

## Requirement (canonical)

| File | Canonical path | Purpose |
|---|---|---|
| Live requirement workbook | `01_REQUIREMENTS\source_requirements\PHs Daily works - Dev_Automation.xlsx` | **Canonical, live source of truth.** Only worksheet `PH-2026-07-UTHAR03 - Satheshkan…` is in scope. Multi-project shared tracker — all other tabs are out of scope for this project. |
| Requirement screenshot | `01_REQUIREMENTS\source_requirements\PH-2026-07-UTHAR03 - Satheshkanth - 09-07.PNG` | Point-in-time visual evidence only, not canonical — confirmed identical to the live worksheet on 2026-07-10 |

## Database Skills (reusable schema/business-rule references)

| File | Canonical path | Status |
|---|---|---|
| `skills_minimal_pack 2 (2).zip` | `08_SKILLS\database_skills\skills_minimal_pack 2 (2).zip` | **Canonical.** Contains `skills/TABLE_order_transaction.md` dated 2026-06-12 — the current reference for `public.order_transaction` / `public.order_shipping_billing_detail`. |
| `skills 3 (1) (3).zip` | `08_SKILLS\database_skills\skills 3 (1) (3).zip` | Historical/superseded. Its `TABLE_order_transaction.md` (2026-05-26) is missing the B&Q and FBA/FBM sections present in the canonical version. No rule conflict found — retained for history only. |

## `ph_task` Rules (generic, user-independent)

| File | Canonical path | Purpose |
|---|---|---|
| `ph_task_schema 5.md` | `08_SKILLS\ph_task_rules\ph_task_schema 5.md` | Full column/DDL reference for `tech_team_outputs.ph_task` |
| `New column - assigned_user_team.md` | `08_SKILLS\ph_task_rules\New column - assigned_user_team.md` | Defines `assigned_user_team` board-routing values (`ph_priors` / `ebay_priors`) |
| `Versioning - phase_level and version_level.md` | `08_SKILLS\ph_task_rules\Versioning - phase_level and version_level.md` | Defines the new-row-per-version + `version_status='rejected'` correction pattern |
| `PH_assigned_user_Standard (1) (1).docx` | `08_SKILLS\ph_task_rules\PH_assigned_user_Standard (1) (1).docx` | Defines how `assigned_user` values must be sourced and copied verbatim |

## Database Access Templates (reference patterns only — no credentials reproduced here)

| File | Canonical path | Purpose |
|---|---|---|
| `temp_user.py` | `02_SOURCE\db_access_templates\temp_user.py` | Generic connect/create/insert template |
| `update_table.py` | `02_SOURCE\db_access_templates\update_table.py` | Generic `ph_task.html_content` update template |
| `temp_user_access_report.pdf` | `02_SOURCE\db_access_templates\temp_user_access_report.pdf` | Access-report reference document |

**Credential handling note:** these templates contain a working (non-production, `temp_user`) credential set embedded as example values. No credential value from these files is reproduced anywhere else in this project's documentation, SQL design, or evidence files.

## Live Database Objects Consulted (read-only, this stage)

These are not files but are recorded here for traceability — schemas were inspected read-only via the connected PostgreSQL tool on 2026-07-10, no writes:

| Object | Purpose confirmed |
|---|---|
| `public.user` | Columns: `user` (id), `user_firstname`, `user_name`, `user_status`, `created_at`. Confirmed `user=109, user_firstname='Utharsika', user_name='utharsika', user_status='Active'`. |
| `public.ph_categories` | Columns: `id`, `category_name`, `user_id`, `assign_date`. Confirmed Utharsika (`user_id=109`) owns 2 categories: `Lampshade` (id 66) and `Wall plug` (id 67). |
| `public.ph_cate_products` | Columns: `id`, `ass_cate_id`, `ref_id`, `which_channel`. Confirmed `ref_id` holds ASIN values when `which_channel=1` (Amazon). Confirmed 0 duplicate ASINs across Utharsika's own two categories. |
| `tech_team_outputs.ph_task` | Confirmed live constraint `ph_task_task_id_unique` (UNIQUE on `task_id`, table-wide) — this drives the same-date-correction `task_id` design in `04_DESIGN\UAWSO_PH_TASK_PUBLICATION_PLAN.md`. |

**Other users' `ph_task` report content inspected or reused: NO.**
