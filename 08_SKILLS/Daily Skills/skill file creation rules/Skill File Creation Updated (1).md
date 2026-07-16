# **Skill File Creation** 

## **Objective**

The objective of the Skill File system is to extract reusable company intelligence from development work before that knowledge disappears into implementation activities.

The system transforms temporary development discoveries into permanent, reusable company memory.

---

# **Company Knowledge Goals**

The company is building a centralized knowledge ecosystem that contains:

* Reusable operational intelligence  
* LLM-queryable company context  
* Reusable business logic  
* Reusable validation rules  
* Reusable operational patterns  
* Reusable failure knowledge  
* Long-term company memory

This ensures that development knowledge is preserved, searchable, reusable, and continuously expandable across projects and departments.

---

# **Daily Skill File Rules**

1. ## **File Naming Standard**

Every skill file must follow the standardized naming convention below:

YYYY-MM-DD\_\_\[developer\]\_\_\[project-code\]\_\_\[requirement\_id\]-\[deliverable-id\].md

### **Example**

2026-07-03\_\_priya\_\_cfis\_\_REQ-08-D03.md

---

2. # **Mandatory Metadata Block**

Every skill file must contain a metadata section with the following mandatory fields:

* date  
* developer  
* project  
* project\_code  
* phase  
* requirement\_id  
* deliverable\_id  
* status  
* evidence\_location  
* blos\_keys\_used  
* hardcoded\_thresholds  
* three\_am\_standard  
* llm\_queryable  
* company\_knowledge\_candidate  
* Domain  
* User  
* Benefit Status

---

# **Why Metadata is Important**

The metadata structure enables:

* LLM-based grouping  
* Sequencing of development history  
* Knowledge compilation  
* Advanced filtering  
* Future retrieval and reuse  
* Cross-project intelligence mapping  
* Long-term organizational memory

Without standardized metadata, valuable operational knowledge becomes difficult to retrieve, validate, or reuse in future implementations.

---

# 

# **Sample Metadata Block**

date: 2026-05-21

developer: Priya

project: Customer Fulfillment Intelligence System

project\_code: CFIS

phase: Development \- phase 02

requirement\_id: REQ-08

deliverable\_id: D03

status: Inprogress

evidence\_location: /projects/cfis/evidence/REQ-08-D03/

blos\_keys\_used:

  \- postage\_validation\_enabled

  \- referral\_fee\_threshold

  \- category\_risk\_check

hardcoded\_thresholds:

  \- local\_postage\_min \= 2.44

  \- local\_postage\_max \= 5.80

  \- referral\_fee\_limit \= 15%

three\_am\_standard: TRUE

llm\_queryable: TRUE

company\_knowledge\_candidate: TRUE

domain: Ecommerce Operations

User: Vithushini

Benefit status: Pass / Not

---

# 

| Field | Description |
| ----- | ----- |
| `date` | Date the skill file was created. |
| `developer` | Name of the developer or analyst responsible for the work. |
| `project` | Full project name related to the skill file. |
| `project_code` | Short internal code used to identify the project. |
| `phase` | Current work stage such as Requirement, Development (phase 01 ,phase 02……..), Validation, Testing, or Production. |
| `requirement_id` | User requirement or business requirement identifier (task requirement number). Defines what business problem or operational need must be implemented. |
| `deliverable_id` | Specific deliverable or task identifier linked to the requirement (deliverable number under the requirement). Defines the exact implementation, document, logic, or output completed under the requirement. |
| `status` | Current progress state such as Draft, In Progress, Completed, Validated, or Rejected. |
| `evidence_location` | Folder path, URL, or storage location containing    screenshots, SQL queries, logs, documents, API responses, or validation proof files, n8n workflows names and path. |
| `blos_keys_used` | List of BLOS configuration keys, operational keys, or business logic keys used during implementation. Purpose: helps centralize configurable operational logic into BLOS tables for future reuse and maintenance. |
| `hardcoded_thresholds` | Fixed threshold values, percentages, or constants used in the implementation logic. Purpose: identify temporary hardcoded values because operational thresholds may change in the future and should ideally be managed through BLOS tables instead of hardcoding. |
| `three_am_standard` | Indicates whether the documentation is clear enough for someone to understand, troubleshoot, and continue work at 3 AM without additional explanation or developer dependency. |
| `llm_queryable` | Indicates whether the file is structured properly for future LLM retrieval, grouping, querying, and knowledge extraction. |
| `company_knowledge_candidate` | Indicates whether the content contains reusable company intelligence, operational knowledge, business rules, or implementation patterns worth preserving long term. |
| `domain` | Business or operational domain related to the work such as Ecommerce, Finance, Inventory, Logistics, Customer Service, Advertising, or Marketplace Operations. |
| `User` | Identifies the business requester, product owner, or end user for traceability and future knowledge compilation.  |
| `Benefit status` | Records whether the planned business benefits were actually achieved, providing measurable business value and implementation outcome.  |

# ---

3. # **Daily Skill File Content**

## **1\. SYSTEM STATE**

Describe the current operational or technical state before today’s work began.

Include:

* existing implementation status  
* known limitations  
* current validation logic  
* current database structure  
* existing operational behavior

### **Example**

Postage validation logic existed only for LOCAL shipping.

INTERNATIONAL postage validation was missing.

Referral fee validation logic was partially implemented.

---

## **2\. WHAT CHANGED TODAY**

Explain the changes implemented during the day.

Include:

* new logic added  
* modified queries  
* updated workflows  
* configuration changes  
* new validations

### **Example**

Added INTERNATIONAL postage validation logic .explain about that logic dont add summary

---

## **3\. POSTGRESQL / MCP FINDING**

Document important technical findings discovered during database analysis, MCP investigation, or implementation research.

Include:

* schema findings  
* relationship discoveries  
* missing indexes  
* hidden assumptions  
* operational mappings

### **Example**

ph\_cate\_products.ass\_cate\_id maps to ph\_categories.id.

Relationship type identified as Many-to-One.

---

## **4\. GAP FOUND**

Document missing logic, incomplete requirements, unclear behavior, or operational gaps identified during implementation.

Include:

* missing thresholds  
* undefined business rules  
* unclear requirements  
* missing mappings  
* unsupported edge cases

### **Example**

No threshold exists for INTERNATIONAL economy shipping service type.

Requirement document does not define fallback behavior.

---

## **5\. VALIDATION RULE ADDED OR CHANGED**

Document any validation logic created or modified.

Include:

* business rules  
* threshold validations  
* operational conditions  
* logic assumptions

### **Good Example**

Validation Rule:

IF postage\_service\_type \= 'LOCAL'

THEN validate local\_postage\_expense\_per\_order using local\_postage\_min and local\_postage\_max thresholds.

IF validation fails

THEN mark order as postage validation failure.

### **Bad Example**

Postage logic added.

---

## **6\. FAILURE MODE OR EDGE CASE**

Document possible failures, exceptions, abnormal conditions, or operational risks.

Include:

* system failures  
* invalid data scenarios  
* null handling  
* threshold conflicts  
* operational anomalies

### **Example**

Orders containing multiple products from different categories may produce incorrect referral fee calculations if category mapping is missing.

---

## **7\. DECISIONS MADE TODAY**

Record important implementation or operational decisions.

Include:

* architectural decisions  
* temporary assumptions  
* threshold handling decisions  
* fallback logic decisions

### **Example**

Decided to retrieve all operational thresholds from BLOS tables instead of hardcoding values in SQL logic.

---

## **8\. COMPANY KNOWLEDGE EXTRACT**

Capture reusable company intelligence discovered during implementation.

Include:

* reusable patterns  
* operational insights  
* business rules  
* reusable validation logic  
* reusable schema understanding

### **Example**

Marketplace validation rules should always support future marketplace expansion using configuration-driven thresholds.

---

## **9\. LLM STANDARD CHECK**

Verify whether the file meets long-term AI and operational usability standards.

Checklist:

* Is terminology consistent?  
* Are business rules clearly explained?  
* Are assumptions documented?  
* Are edge cases included?  
* Is evidence referenced?  
* Can another developer continue the work independently?  
* Is the file queryable by LLM systems?

### **Example**

LLM Queryable: TRUE

Operational reasoning documented: TRUE

Edge cases documented: TRUE

Evidence linked: TRUE

---

4. # **BLOS GOVERNANCE**

Business thresholds must not silently live inside code.

 Hidden business logic is prohibited.

 Thresholds must be visible, governed, reviewable, and reusable.

 Examples requiring BLOS governance:  
 • thresholds  
 • score cutoffs  
 • percentages  
 • marketplace mappings  
 • workflow limits  
 • approval gates  
 • fee assumptions  
 • scoring formulas  
 • timing windows  
 • retry limits

5. # **WHAT A GOOD SKILL FILE LOOKS LIKE**

A good SKILL file:  
 • captures reusable business logic  
 • explains schema meaning and operational assumptions  
 • identifies gaps and edge cases  
 • references evidence  
 • uses canonical project vocabulary  
 • allows another developer or LLM to continue the work  
 • explains operational reasoning  
 • extracts company intelligence from implementation

6. # **REJECTION CONDITIONS**

A SKILL file may be rejected if:  
 • it is an activity log instead of knowledge extraction  
 • metadata is missing  
 • naming convention is incorrect  
 • reusable business logic is missing  
 • hidden thresholds exist without BLOS reference  
 • GAP discipline is missing  
 • evidence is absent  
 • the file is not LLM-queryable  
 • the file cannot satisfy the 3AM Standard

Immediate escalation conditions:  
 • credential exposed in file  
 • hidden hardcoded business thresholds  
 • business logic hidden in implementation  
 • developer misattribution  
 • scope violation  
 • architecture violation  
 • repeated logic leakage  
 • repeated missing extraction

