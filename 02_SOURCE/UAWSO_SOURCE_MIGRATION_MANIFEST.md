# UAWSO Source Migration Manifest

**What this asset is:** Complete inventory of every file found under the temporary `Sources` folder, with size, SHA-256 hash, classification, and approved destination, captured before any file was moved.

**Why it exists:** AIOS governance requires a full pre-migration inventory so every file has exactly one canonical destination and migration can be verified byte-for-byte afterward.

**Business question supported:** "Where did every discovery-stage file end up, and can we prove nothing was lost or altered?"

**Source or evidence used:** Direct filesystem inspection (`find`, `sha256sum`) of `Sources\` under the approved project root, run 2026-07-10.

**Owner:** Satheskanth (developer)
**Reviewer:** Satheesvaran (business clarification / validation contact)
**Current status:** Migration manifest — pre-move state captured; see `07_EVIDENCE\source_migration\UAWSO_SOURCE_MIGRATION_VALIDATION.md` for post-move verification.
**Known limits:** Hashes were computed once, pre-move. Post-move hashes are recorded separately in the validation evidence file.
**Pass/fail rule:** Migration passes only if every row below reaches `PASS` status in the validation evidence file (destination exists, size matches, hash matches).
**Next action:** Execute the safe move procedure for each row, then produce the validation evidence file.

---

## Inventory and Destination Mapping

| # | Original relative path | Filename | Ext | Size (bytes) | SHA-256 | Classification | Proposed destination | Reason |
|---|---|---|---|---|---|---|---|---|
| 1 | `Sources\AIOS GPT Project intructions, prompts and skill files-20260619T091849Z-3-001.zip` | `AIOS GPT Project intructions, prompts and skill files-20260619T091849Z-3-001.zip` | .zip | 62575 | `75a122157b46856841e44af4e9f07eb9ef42dae071c71f115c23b0ebe110a47e` | AIOS governance/methodology archive | `00_PROJECT_CONTROL\governance_sources\` | General AIOS operating-model documentation (GPT-brain/Claude-worker), not project-specific |
| 2 | `Sources\aios_architecture.md` | `aios_architecture.md` | .md | 8590 | `41a9e418bfd2a7e0699cccf3cd5a60c9d8ce1ed43c0864027a401ff3d7fcac1a` | AIOS governance/architecture doc | `00_PROJECT_CONTROL\governance_sources\` | Describes the 6-tier MySQL→PostgreSQL→Intelligence architecture that governs this and all AIOS projects |
| 3 | `Sources\db credentials & scripts template\temp_user.py` | `temp_user.py` | .py | 1989 | `9814c1687c3b7f864aa5ba54a3bb7711bd92a186505179e9fb0da691c93550b4` | Generic DB connection/insert template (no project logic) | `02_SOURCE\db_access_templates\` | Reference connection pattern only |
| 4 | `Sources\db credentials & scripts template\temp_user_access_report.pdf` | `temp_user_access_report.pdf` | .pdf | 20830 | `b0c2641ae879e33e898df8b7d109d5a630510031aafd62b3de274babe175a5cd` | DB access reference document | `02_SOURCE\db_access_templates\` | Companion reference to the `temp_user` credential set |
| 5 | `Sources\db credentials & scripts template\update_table.py` | `update_table.py` | .py | 2588 | `9784d14ab8e0646e454a8effe9e049dfdd10a8fb32fe4fd63cfa29a1120ff5bc` | Generic `ph_task` update template (no project logic) | `02_SOURCE\db_access_templates\` | Reference HTML-push pattern only |
| 6 | `Sources\PH-2026-07-UTHAR03 - Satheshkanth - 09-07.PNG` | `PH-2026-07-UTHAR03 - Satheshkanth - 09-07.PNG` | .PNG | 180531 | `27f09ceb13781ae515e23d87372a19c8a84224a354fba72605e105c75c6d5369` | Point-in-time visual evidence of the requirement worksheet | `01_REQUIREMENTS\source_requirements\` | Supporting evidence for the UAWSO requirement; XLSX is canonical, this is the visual snapshot |
| 7 | `Sources\PHs Daily works - Dev_Automation.xlsx` | `PHs Daily works - Dev_Automation.xlsx` | .xlsx | 1512292 | `f44abded0ae320ce78fb3b4447efcaccaec4ece9d93e22798bbf187414c65220` | Canonical live requirement workbook (multi-project; only worksheet `PH-2026-07-UTHAR03 - Satheshkan…` is in scope for UAWSO) | `01_REQUIREMENTS\source_requirements\` | Business-requirement source of truth for `PH-2026-07-UTHAR03` |
| 8 | `Sources\ph_task_rules\New column - assigned_user_team.md` | `New column - assigned_user_team.md` | .md | 2111 | `82e6d4d8a5e9b841ce26cd74b8ff807d411f4d67f5dbbdb953e90a87ada19f3f` | `ph_task` schema rule (generic, user-independent) | `08_SKILLS\ph_task_rules\` | Defines `assigned_user_team` routing standard used by all PH projects |
| 9 | `Sources\ph_task_rules\PH_assigned_user_Standard (1) (1).docx` | `PH_assigned_user_Standard (1) (1).docx` | .docx | 9776 | `087fc8117924b62f48a8b6538b3f4caa9830a8a54d88b001107d03cf75f3b237` | Assigned-user resolution standard (generic) | `08_SKILLS\ph_task_rules\` | Defines the approved method for resolving `assigned_user` values |
| 10 | `Sources\ph_task_rules\ph_task_schema 5.md` | `ph_task_schema 5.md` | .md | 10188 | `718338bd8dd9809509b26c5b51fd668c8714ae3e2dfa433dca010920b82ab40b` | `ph_task` table schema documentation (generic) | `08_SKILLS\ph_task_rules\` | Canonical schema reference for `tech_team_outputs.ph_task` |
| 11 | `Sources\ph_task_rules\Versioning - phase_level and version_level.md` | `Versioning - phase_level and version_level.md` | .md | 3181 | `93f94c4486900475b3d18148cfaa6ef166132b6c0b3bb7ececd9f0579679cf71` | `ph_task` versioning rule (generic) | `08_SKILLS\ph_task_rules\` | Defines `phase_level`/`version_level`/`rejected` behaviour used by all PH projects |
| 12 | `Sources\skills 3 (1) (3).zip` | `skills 3 (1) (3).zip` | .zip | 63183 | `72810946557f288c2a4e0217bde70ee250f7906e6248b3522bc2a149d1d6dc82` | Database skill pack — **older** (`TABLE_order_transaction.md` dated 2026-05-26), historical | `08_SKILLS\database_skills\` | Retained as historical/superseded reference per Section 14.2; the minimal pack is canonical |
| 13 | `Sources\skills_minimal_pack 2 (2).zip` | `skills_minimal_pack 2 (2).zip` | .zip | 78984 | `068578f1b906b621938ee768a812863a4e02932ee3a39bb58355a7ad346ff6db` | Database skill pack — **newest** (`TABLE_order_transaction.md` dated 2026-06-12), canonical | `08_SKILLS\database_skills\` | Canonical reusable schema/business-rule reference for `public.order_transaction` |

**Files inventoried:** 13
**Unresolved files:** 0
**Duplicate name conflicts at destination:** 0 (all destination folders were empty before migration)

## Conflict Check: `TABLE_order_transaction.md` (older vs. newer)

Both zips contain a file of this name. Compared directly (extracted, not modified):

- **Newer** (`skills_minimal_pack 2 (2).zip`, 2026-06-12, 14509 bytes uncompressed): includes the B&Q platform section (`source = 16`), the full Sub-Source reference list, and the Amazon FBA/FBM filter rules.
- **Older** (`skills 3 (1) (3).zip`, 2026-05-26, 13584 bytes uncompressed): lacks the B&Q section and the FBA/FBM rules present in the newer version.
- **No conflicting rule found** — the newer file is a strict superset of confirmed rules, not a contradiction. The newer version is designated canonical per Section 14.2; the older is retained unmodified as historical inside its own zip, not deleted.

## AIOS-Created Documentation Files (not part of Sources migration — listed for completeness)

The following files are newly authored in this stage and are not migrated `Sources` content:

- `README.md`
- `00_PROJECT_CONTROL\UAWSO_PROJECT_OVERVIEW.md`
- `01_REQUIREMENTS\UAWSO_REQUIREMENT_RECORD.md`
- `02_SOURCE\UAWSO_SOURCE_REGISTER.md`
- `03_DISCOVERY\UAWSO_DISCOVERY_SUMMARY.md`
- `04_DESIGN\UAWSO_SOURCE_TO_TARGET_MAPPING.md`
- `04_DESIGN\UAWSO_BUSINESS_RULES_SPEC.md`
- `04_DESIGN\UAWSO_SQL_DESIGN.sql.md`
- `06_VALIDATION\UAWSO_VALIDATION_PLAN.md`
- `04_DESIGN\UAWSO_PH_TASK_PUBLICATION_PLAN.md`
- `04_DESIGN\UAWSO_DAILY_AUTOMATION_DESIGN.md`
- `10_HANDOVER\UAWSO_HANDOVER.md`
- `07_EVIDENCE\source_migration\UAWSO_SOURCE_MIGRATION_VALIDATION.md`
