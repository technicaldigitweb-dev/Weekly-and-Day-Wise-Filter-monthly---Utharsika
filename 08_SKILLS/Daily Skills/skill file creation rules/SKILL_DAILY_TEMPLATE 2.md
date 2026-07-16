# SKILL FILE — DAILY KNOWLEDGE EXTRACTION TEMPLATE
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## ── METADATA BLOCK ──────────────────────────────────────────────────────────
# MANDATORY — Every field required. Missing fields = REJECTION.

date:                   # DD-MM-YYYY
developer:              # firstname or alias (lowercase)
project:                # Full project name
project_code:           # e.g. CFIS, KMS, PPC
phase:                  # DISCOVERY | BUILD | TEST | REVIEW | DEPLOY
requirement_id:         # e.g. REQ-08
deliverable_id:         # e.g. REQ-08-D03
status:                 # IN-PROGRESS | COMPLETE | BLOCKED | PENDING-REVIEW
evidence_location:      # Git commit hash / n8n workflow ID / Notion URL / file path
blos_keys_used:         # List all business logic constants used — e.g. BLOS-FEE-001, BLOS-SCORE-003 | NONE
hardcoded_thresholds:   # Describe any magic numbers or thresholds in implementation | NONE
three_am_standard:      # PASS | FAIL — Could an unknown developer continue from this file alone?
llm_queryable:          # YES | NO — Is this file structured for LLM compilation?
company_knowledge_candidate: # YES | NO — Does this contain reusable company logic?
domain:                 # e.g. AMAZON-LISTINGS | PPC | INFRASTRUCTURE | N8N | DATABASE | FINANCE

## File path (fill after saving):
# DD-MM-YYYY__[developer]__[project-code]__[deliverable-id].md

---

## 1. SYSTEM STATE
# What is the system state at the START of today's session?
# What existed before you touched it? What was broken, incomplete, or unknown?

- Current system state:
- What was working:
- What was broken / missing:
- Your starting point:

---

## 2. WHAT CHANGED TODAY
# What did you build, fix, or change today?
# Be specific. Reference files, tables, workflow nodes, functions.
# NOT: "worked on the workflow" — YES: "added HTTP node to WF-042 that calls /api/postage"

- Change 1:
- Change 2:
- Change 3:
# Add more as needed

Evidence reference (Git SHA / workflow export / file path):

---

## 3. POSTGRESQL / MCP / DATABASE FINDING
# Any schema discoveries, query logic, data anomalies, or MCP findings today.
# If none: write NONE — do not skip.

Table(s) involved:
Finding:
SQL logic or pattern discovered:
Operational meaning (why does this schema exist?):

> If NONE: `DATABASE FINDING: None today.`

---

## 4. GAP FOUND
# What is missing, undocumented, or unclear in the system?
# Gaps are valuable. Report them honestly.

Gap description:
Impact if unresolved:
Recommended action:
Owner (if known):

> If NONE: `GAP: None identified today.`

---

## 5. VALIDATION RULE ADDED OR CHANGED
# Any data validation, input check, guard clause, or business rule enforced in code today.
# These MUST be extracted here — they cannot remain trapped inside source code.

Rule name / ID:
Condition checked:
What it prevents:
Where implemented (file / node / function):
BLOS reference (if applicable):

> If NONE: `VALIDATION RULE: None added or changed today.`

---

## 6. FAILURE MODE OR EDGE CASE
# What can go wrong? What did go wrong? What unexpected behaviour was discovered?
# How is the failure detected? How is it recovered?

Failure scenario:
How it is triggered:
How it is detected:
Recovery procedure:
Risk level: LOW | MEDIUM | HIGH | CRITICAL

> If NONE: `FAILURE MODE: None identified today.`

---

## 7. DECISIONS MADE TODAY
# Architectural, business logic, or operational decisions made during today's session.
# Why was option A chosen over option B? What was the reasoning?
# Future developers must understand the WHY, not just the WHAT.

Decision:
Alternatives considered:
Reason for choice:
Trade-off accepted:
Who approved (if applicable):

> If NONE: `DECISIONS: No significant decisions today.`

---

## 8. COMPANY KNOWLEDGE EXTRACT
# The most important section.
# Extract reusable business logic, operational rules, or domain knowledge discovered today.
# This is what future developers and LLMs will query.

### Business Rule:
[Describe the rule in plain English. Why does it exist?]

### Operational Assumption:
[What does the system assume about the business, the data, or the user?]

### Reusable Logic / Formula:
[Any scoring formula, threshold, mapping, or calculation that must be visible to future developers]

### Canonical Vocabulary:
[Any project-specific terms, abbreviations, or naming conventions used]

### Cross-Project Applicability:
[Can this logic be reused in other projects? If yes, describe.]

---

## 9. LLM STANDARD CHECK
# Final self-review before submission.
# Answer honestly. Do not submit if any answer is NO without explanation.

| Check | YES / NO |
|---|---|
| Could an unknown developer continue from this file without reading source code? | |
| Is every business threshold visible (not buried in code)? | |
| Is the GAP section completed or marked NONE? | |
| Is the COMPANY KNOWLEDGE EXTRACT section substantive? | |
| Are evidence locations referenced? | |
| Is metadata complete? | |
| Is this extracting knowledge — not just logging activity? | |

**Three-AM Standard self-assessment:**
> Write one sentence: "A developer with no context could ________ using this file."

---

## ── SUBMISSION CHECKLIST ─────────────────────────────────────────────────────

- [ ] File named correctly: `DD-MM-YYYY__[developer]__[project-code]__[deliverable-id].md`
- [ ] All metadata fields filled
- [ ] Sections 1–9 completed (or explicitly marked NONE)
- [ ] No credentials, passwords, or API keys included
- [ ] LLM Standard Check table completed
- [ ] Three-Am Standard self-assessment written
- [ ] Evidence location referenced

---
*DIGITWEB LK LTD — Daily Skill Increment System — v3.0 — May 2026*
*Issued to: Developers · Joshna · Vithusali · Mayurika · Sajeesan · Management Team*
