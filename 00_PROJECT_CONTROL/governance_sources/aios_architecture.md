# AIOS Complete Architecture with Capability Enhancement Loop

> **Summary:** Full architecture from Core MySQL through Mirror MySQL, PostgreSQL schemas, AIOS intelligence chain, execution loop, and an explicit capability enhancement loop that feeds back into the capability registry.

---

## TIER 1 — Core MySQL (Transaction Truth)

**Role:** Live production system. The single source of truth for all transactional data.

**Key rules:**
- All writes happen here and **only** here.
- No AI, reporting, or analytics load touches this layer.
- Syncs to Mirror MySQL within **≤10 minutes**, with timestamp proof.

**Tables in this layer:**
| Table | Purpose |
|---|---|
| Orders | Customer order records |
| Stock | Inventory levels |
| Purchase Orders | Supplier purchase records |
| Invoices | Billing and payment records |
| Workflow · Products | Operational workflow and product data |

---

↓ **sync ≤10 min · timestamp proof**

---

## TIER 2 — Mirror MySQL (Safety Copy)

**Role:** A read-only replica of Core MySQL that protects production from AI/analytics load.

**Key rules:**
- No humans write here.
- Owner: **Sajeesan** — sync evidence required.
- Feeds into PostgreSQL via **ETL / transformation**.

---

↓ **ETL / transformation**

---

## TIER 3 — PostgreSQL (AIOS Data Layer)

**Role:** The analytical and AI data layer. Contains **five schemas**, each with a defined purpose and strict write permissions.

### Schema 1 — `raw_data`
- Exact copy of all source data from Mirror MySQL.
- Covers all sources.
- **Write permission:** ETL process only.

### Schema 2 — `staging_ai`
- LLM sandbox environment for AI experimentation.
- Data expires after **14 days**.
- Data here is **not trusted** for production decisions.
- **Write permission:** Selected ETL processes only.

### Schema 3 — `human_input`
- Human-defined knowledge layer: classifications, mappings, rules.
- Written by staff and developers.
- Contains approved lists of business rules.
- **Write permission:** Approved staff / dev list only.

### Schema 4 — `validation`
- The **Sajeesan gate** — a human review checkpoint before data is promoted.
- **Pass** → data moves up to `business_intelligence`.
- **Fail** → data is returned for correction.
- **Write permission:** Sajeesan only.

### Schema 5 — `business_intelligence`
- The trusted truth layer. This is where LLMs query data.
- Populated only after passing validation.
- **Write permission:** ETL only (no direct human or AI writes).

### Schema 6 — `audit`
- Full audit trail of all operations and decisions.
- Immutable record for traceability.

---

↓ **data flows into AIOS Intelligence Chain**

---

## TIER 4 — AIOS Intelligence Chain

**Role:** Transforms raw data into organisational intelligence. Three first-class assets — all LLM-queryable.

### Asset 1 — Facts
- Verified statements derived from evidence.
- Example: *"SKU ABC lost £12,400. FBM stockout · 17 days."*

### Asset 2 — Decisions
- Structured outcomes: **ACT · FLAG · ESCALATE · KILL**
- Example: *"Reorder threshold was set too low."*

### Asset 3 — Capabilities
- Reusable, cross-domain logic packaged for re-use.
- Example: *"FBM stock leakage detection v1. Solve once. Reuse."*

---

↓ **capabilities dispatched to execution**

---

## TIER 5 — Execution Loop (Across All Domains)

**Role:** Capabilities are applied across all operational domains of the business.

**Domains covered:**
- Amazon
- eBay
- Shopify
- Vendor
- FBM (Fulfilled by Merchant)
- Warehouse
- PPC (Pay-Per-Click advertising)
- Customer Service

> **Core principle:** No domain rebuilds what another domain already solved.

---

↓ **execution results feed into enhancement loop**

---

## TIER 6 — Capability Enhancement Loop

**Role:** Ensures every execution improves the capability that was used. A capability that does not improve after use is **not an AIOS asset**.

### 6 Post-Execution Questions (mandatory after every run)
1. Did the capability work?
2. What failed?
3. What evidence was produced?
4. What learning was captured?
5. Should the capability be updated?
6. Can this learning improve another domain's capability?

### Enhancement Steps (sequential)

```
Verification       →   Learning         →   Capability      →   Registry
(pass / fail)          capture               update              update
                                                                 (v1 → v2)
```

### Concrete Example — FBM Stock Leakage Detection

| Step | What happened |
|---|---|
| v1 deployed | Capability runs in production |
| Validation | Wrong formula found during verification |
| Correction | Formula corrected |
| Learning captured | Root cause and fix recorded |
| v2 promoted | New version pushed to capability registry |
| Cross-domain reuse | Warehouse, eBay, Shopify all reuse v2 automatically |

> **Result:** No domain re-learns what the first domain already fixed.

---

## Feedback Arrow — Stronger Capability

A **feedback loop** runs from the Enhancement Loop back up to the **AIOS Intelligence Chain** (Capabilities asset), indicated as "stronger capability". This closes the loop:

```
Execution → Enhancement Loop → Updated Capability Registry → Intelligence Chain → Execution
```

Every cycle produces a more capable system.

---

## Foundational Rule

> **"A capability that does not improve after execution is a static file. Static files are not AIOS assets."**

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────┐
│  TIER 1: Core MySQL  (transaction truth)         │
│  Orders · Stock · POs · Invoices · Products      │
└──────────────────────┬──────────────────────────┘
          sync ≤10 min │ timestamp proof
┌──────────────────────▼──────────────────────────┐
│  TIER 2: Mirror MySQL  (safety copy)             │
│  Read-only. No humans write. Owner: Sajeesan     │
└──────────────────────┬──────────────────────────┘
           ETL / transformation
┌──────────────────────▼──────────────────────────┐
│  TIER 3: PostgreSQL  (AIOS data layer)           │
│  raw_data → staging_ai → human_input             │
│  validation (Sajeesan gate) → business_intel     │
│  + audit                                         │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  TIER 4: AIOS Intelligence Chain                 │
│  Facts · Decisions · Capabilities                │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  TIER 5: Execution Loop                          │
│  Amazon · eBay · Shopify · FBM · Warehouse       │
│  PPC · Vendor · Customer Service                 │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  TIER 6: Capability Enhancement Loop             │
│  Verify → Learn → Update → Registry (v1→v2)     │
└──────────────────────┬──────────────────────────┘
                       │  stronger capability
                       └──────────────────────────►
                            back to Tier 4
```
