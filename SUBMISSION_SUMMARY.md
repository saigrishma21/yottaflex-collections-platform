# YottaFlex.ai Hackathon — Final Submission Summary

**Role:** Associate AI Forward Deployed Engineer  
**Candidate Application:** [Application 6429](https://recruitment.yottaflex.ai/careers/my/application/6429)  
**Project:** Intelligent Loan Delinquency & Compliant Collections Management Platform  
**Target Seed:** `20261022` | **Simulation Window:** 12 Months  

---

## 1. Problem Statement & Scope Coverage

The objective was to build an end-to-end collections intelligence platform that prioritizes overdue loan accounts, schedules customer contact tasks in compliance with statutory windows (TCPA/FDCPA), monitors and reconciles borrower commitments (Promises-to-Pay), exposes transparent decision explainability, and preserves an immutable audit trail (`case_events`).

### Architecture & Tech Stack
- **Backend**: FastAPI, SQLAlchemy, Pydantic v2, Uvicorn, Python 3.13+
- **Database**: SQLite with foreign key enforcement (`PRAGMA foreign_keys=ON;`), indexed foreign keys, and bridge tables
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons, Recharts
- **Data Generator**: Deterministic relational synthetic generator parameterized for scale (`starter` vs `full`) with fixed seed `20261022`
- **Validation**: Schema integrity validator, dual-pass seed reproducibility auditor, and ground truth benchmark evaluator

---

## 2. Core Entities & Cardinality

The system strictly implements the 10 required domain entities, 1 many-to-many bridge table, and 1 immutable audit log:

| Entity Name | Primary Key Format | Foreign Keys | Relationship / Cardinality |
| :--- | :--- | :--- | :--- |
| `Customer` | `CUST-2026-XXXXXX` | - | $1 \leftrightarrow N$ with Account & Loan |
| `Account` | `ACC-2026-XXXXXX` | `customer_id` | $N \leftrightarrow 1$ with Customer, $1 \leftrightarrow N$ with Loan |
| `Loan` | `LOAN-2026-XXXXXX` | `customer_id`, `account_id` | $1 \leftrightarrow N$ with Installment & Payment |
| `Installment` | `INS-<loan_id>-XXX` | `loan_id` | Scheduled monthly repayment obligations |
| `Payment` | `PMT-2026-XXXXXX` | `loan_id` | Transaction receipts credited to loans |
| `PaymentAllocation` | `ALC-2026-XXXXXX` | `payment_id`, `installment_id` | Bridge resolving $M \leftrightarrow N$ payment allocations |
| `DelinquencySnapshot`| `SNP-<loan_id>-XXX` | `loan_id` | Calculated DPD, arrears, and regulatory aging bucket |
| `ContactPreference` | `PREF-<customer_id>-XXX`| `customer_id` | Permissible contact window, DNC flag, timezone |
| `CollectionCase` | `COL-2026-XXXXXX` | `loan_id` (Unique), `customer_id` | Prioritized queue and workflow states |
| `ContactAttempt` | `CTP-<case_id>-XXX` | `case_id` | Outreach execution history and compliance status |
| `PromiseToPay` | `PRM-<case_id>-XXX` | `case_id` | Borrower payment commitment and grace period |
| `CaseEvent` | `EVT-<case_id>-XXX` | `case_id` | Immutable state transition audit trail |

Detailed field definitions and constraints are documented in [`docs/data_dictionary.md`](docs/data_dictionary.md) and [`docs/database_schema.md`](docs/database_schema.md).

---

## 3. Scale & Integrity Verification

All data volumes strictly meet or exceed the granular hackathon instructions:

- **Loans**: Exactly **10,000 loans** generated across **8,000 unique customers**.
- **Installments**: Exactly **30,000 scheduled installments** across the 10,000 loans over a 12-month horizon.
- **Payments & Allocations**: **22,585 payments** and **22,605 payment allocations**.
- **Delinquency Snapshots**: **10,000 snapshots** tracking real-time DPD and arrears.
- **Contact Preferences**: **8,000 borrower preference records** governing permissible windows and DNC flags.
- **Collection Workflow**: **3,113 collection cases**, **2,060 contact attempts**, **919 promises to pay**, and **6,032 audit events**.
- **Integrity**: 100% unique primary keys, 0 orphaned foreign keys, 100% valid enum states, 100% payment allocation arithmetic reconciliation.

---

## 4. Business Logic & Mathematical Models

### 4.1 Continuous Explainable Prioritization Algorithm
Overdue accounts are scored on a continuous 0–100 scale:
$$\text{Priority Score} = (S_{\text{DPD}} \times 0.40) + (S_{\text{balance}} \times 0.35) + (S_{\text{risk}} \times 0.25)$$

- **Continuous DPD Normalization ($S_{\text{DPD}}$, 40%)**: Smooth piecewise function preventing saturation across early (1–30d), mid (31–90d), and extended (90–270d+) delinquency buckets.
- **Continuous Balance Normalization ($S_{\text{balance}}$, 35%)**: Smooth curve scaling across retail micro-loans (₹5k) to high-exposure facilities (₹10L+).
- **Continuous Risk Component ($S_{\text{risk}}$, 25%)**: Credit segment baseline augmented by the borrower's balance-to-principal exposure ratio.
- **Statutory Pre-Filters**: Zero arrears accounts receive $\text{Score} = 0.0$ (`PAID_OFF_ZERO_ARREARS`); active disputes receive $\text{Score} = 0.0$ (`ROUTED_DISPUTE_REVIEW`).
- **Score Distribution**: Generates **1,557 distinct continuous score values** (min `0.00`, max `98.61`, mean `58.24`).

### 4.2 Fair Contact Scheduling (FDCPA / TCPA)
- Enforces customer permissible contact windows (default 09:00:00 to 18:00:00 local time).
- Blocks outreach if `do_not_call = True` or `contact_allowed = False` (`BLOCKED_DNC`).
- Enforces a rolling 7-day voice contact frequency cap ($\le 3$ calls).

### 4.3 Commitment Reconciliation State Machine
- Staggers payment promises across the 12-month simulation window with a 3-day grace period.
- Automatically reconciles incoming payments:
  - `FULFILLED`: 269 records (linked to payment IDs)
  - `PARTIALLY_FULFILLED`: 85 records
  - `BROKEN`: 131 records
  - `PENDING`: 434 records
  - Overall Fulfillment Rate: **29.3%**

---

## 5. Ground Truth Benchmark Evaluation

The generator injects 5 labeled negative edge cases into an isolated dataset ([`data/ground_truth/ground_truth.csv`](data/ground_truth/ground_truth.csv)) without feature leakage:

| Scenario # | Injected Anomaly Scenario | Target Entity | Injected | Detected | Precision | Recall | F1-Score |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **Paid account remains in collection** | `CollectionCase` | 20 | 20 | 100.0% | 100.0% | 1.0000 |
| 2 | **Contact outside allowed window** | `ContactAttempt` | 20 | 20 | 100.0% | 100.0% | 1.0000 |
| 3 | **Payment allocated to wrong installment** | `PaymentAllocation` | 20 | 20 | 100.0% | 100.0% | 1.0000 |
| 4 | **Promise amount exceeds arrears** | `PromiseToPay` | 20 | 20 | 100.0% | 100.0% | 1.0000 |
| 5 | **Disputed debt treated as confirmed** | `CollectionCase` | 20 | 20 | 100.0% | 100.0% | 1.0000 |
| **Total** | **All Injected Edge Cases** | - | **100** | **100** | **100.0%** | **100.0%** | **1.0000** |

---

## 6. Deterministic Seed Reproducibility (Seed `20261022`)

Generating the dataset in dual independent runs from seed `20261022` produces bit-for-bit identical SHA-256 checksums across all 12 generated tables:
- `accounts.csv`: SHA-256 MATCH
- `case_events.csv`: SHA-256 MATCH
- `collection_cases.csv`: SHA-256 MATCH
- `contact_attempts.csv`: SHA-256 MATCH
- `contact_preferences.csv`: SHA-256 MATCH
- `customers.csv`: SHA-256 MATCH
- `delinquency_snapshots.csv`: SHA-256 MATCH
- `installments.csv`: SHA-256 MATCH
- `loans.csv`: SHA-256 MATCH
- `payment_allocations.csv`: SHA-256 MATCH
- `payments.csv`: SHA-256 MATCH
- `promises_to_pay.csv`: SHA-256 MATCH

---

## 7. Automated Test Suite

- **Unit & Integration Tests**: 25/25 passing in pytest (`tests/test_api.py`, `tests/test_compliance.py`, `tests/test_database.py`, `tests/test_delinquency.py`, `tests/test_payments.py`, `tests/test_prioritization.py`, `tests/test_reproducibility.py`).
- **Execution Time**: ~1.8 seconds.

---

## 8. Export Deliverables Manifest

All exported datasets and SQL seed scripts are packaged in the repository:
- `data/generated/*.csv` (12 tabular CSV files)
- `data/exports/seed_data.sql` (43 MB SQL dump)
- `data/exports/dataset.json` (52 MB nested JSON)
- `data/exports/source_manifest.json` (Record counts and SHA-256 checksums)
- `data/ground_truth/ground_truth.csv` & `ground_truth.json` (100 labeled anomaly records)

---

## 9. Quick Start Commands

```powershell
# 1. Start Web Server & UI (Port 8000)
.\.venv\Scripts\python cli.py run-server --port 8000

# 2. Run Comprehensive Schema & Integrity Validation
.\.venv\Scripts\python -m validation.validator

# 3. Evaluate Ground Truth Anomaly Benchmark
.\.venv\Scripts\python cli.py benchmark

# 4. Verify Dual-Pass Seed Reproducibility
.\.venv\Scripts\python cli.py reproducibility

# 5. Run Full Test Suite
.\.venv\Scripts\pytest -v
```
