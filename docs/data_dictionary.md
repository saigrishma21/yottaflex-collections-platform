# Data Dictionary: YottaFlex AI Collections Management System

This document specifies the schema, constraints, data types, nullability, allowed values, uniqueness, and validation rules for all 10 core entities, the payment allocation bridge table, and the case event audit table.

---

## 1. Customer (`customers`)
Represents the individual borrower / legal entity holding loan obligations.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_id` | String(32) | Yes | Regex `^CUST-2026-\d{6}$` | Primary Key | Immutable customer identifier (e.g., `CUST-2026-000001`). |
| `first_name` | String(64) | Yes | Non-empty string | No | Legal first name. |
| `last_name` | String(64) | Yes | Non-empty string | No | Legal surname. |
| `email` | String(128) | Yes | Valid RFC 5322 email | Unique | Primary electronic contact email. |
| `phone` | String(32) | Yes | E.164 format `^\+\d{10,15}$` | No | Primary mobile/phone number. |
| `address` | String(255) | No | Free text | No | Street address. |
| `city` | String(64) | Yes | Non-empty string | No | Residential city. |
| `state` | String(64) | Yes | Non-empty string | No | State or province. |
| `postal_code` | String(16) | Yes | Postal/PIN format | No | Postal code. |
| `risk_segment` | String(16) | Yes | `LOW`, `MEDIUM`, `HIGH` | No | Initial underwriting risk tier. |
| `created_at` | DateTime | Yes | UTC timestamp | No | System registration timestamp. |
| `updated_at` | DateTime | Yes | UTC timestamp | No | Last record update timestamp. |

---

## 2. Account (`accounts`)
Represents the financial deposit or credit facility account under a customer.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `account_id` | String(32) | Yes | Regex `^ACC-2026-\d{6}$` | Primary Key | Account identifier (e.g., `ACC-2026-000001`). |
| `customer_id` | String(32) | Yes | FK -> `customers.customer_id` | No | Parent customer. Cascades on customer deletion. |
| `account_number` | String(32) | Yes | Alphanumeric (10-16 chars) | Unique | Banking account number. |
| `account_type` | String(32) | Yes | `SAVINGS`, `CURRENT`, `SALARY` | No | Type of banking account. |
| `account_status` | String(32) | Yes | `ACTIVE`, `DORMANT`, `FROZEN`, `CLOSED` | No | Operational status of the account. |
| `opened_date` | Date | Yes | `YYYY-MM-DD` | No | Account opening date. Must be $\le$ loan date. |
| `created_at` | DateTime | Yes | UTC timestamp | No | System creation timestamp. |

---

## 3. Loan (`loans`)
Represents the credit contract disbursed to the customer.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `loan_id` | String(32) | Yes | Regex `^LOAN-2026-\d{6}$` | Primary Key | Loan contract identifier (e.g., `LOAN-2026-000001`). |
| `account_id` | String(32) | Yes | FK -> `accounts.account_id` | No | Linked disbursement/servicing account. |
| `customer_id` | String(32) | Yes | FK -> `customers.customer_id` | No | Borrower reference. |
| `loan_type` | String(32) | Yes | `PERSONAL`, `AUTO`, `HOME`, `BUSINESS` | No | Asset/loan category. |
| `principal_amount` | Numeric(12,2) | Yes | Currency ($> 0.00$) | No | Disbursed principal sum. |
| `interest_rate` | Numeric(5,2) | Yes | Percentage ($0.01$ to $40.00$) | No | Annual percentage interest rate. |
| `tenure_months` | Integer | Yes | $1 \le \text{tenure} \le 360$ | No | Amortization period in months. |
| `loan_date` | Date | Yes | `YYYY-MM-DD` | No | Disbursed start date. |
| `maturity_date` | Date | Yes | `YYYY-MM-DD` | No | Final scheduled installment date. $\text{maturity\_date} > \text{loan\_date}$. |
| `loan_status` | String(32) | Yes | `ACTIVE`, `PAID_OFF`, `DEFAULTED`, `IN_COLLECTION`, `DISPUTED`, `HARDSHIP` | No | Lifecycle status of loan. |
| `dispute_status` | String(32) | Yes | `NONE`, `OPEN`, `RESOLVED_UPHELD`, `RESOLVED_DISMISSED` | No | Legal dispute flag. If `OPEN`, debt collection is restricted. |
| `is_hardship` | Boolean | Yes | `True`, `False` | No | Flag indicating borrower is on financial hardship restructuring. |
| `created_at` | DateTime | Yes | UTC timestamp | No | Record creation timestamp. |
| `updated_at` | DateTime | Yes | UTC timestamp | No | Record modification timestamp. |

---

## 4. Installment (`installments`)
Represents scheduled monthly repayment obligations.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `installment_id` | String(48) | Yes | Regex `^INS-LOAN-2026-\d{6}-\d{3}$` | Primary Key | Deterministic format (e.g., `INS-LOAN-2026-000001-001`). |
| `loan_id` | String(32) | Yes | FK -> `loans.loan_id` | No | Parent loan contract. |
| `installment_number` | Integer | Yes | $1 \le n \le \text{tenure}$ | Composite Unique (`loan_id`, `installment_number`) | Sequence number of the installment. |
| `due_date` | Date | Yes | `YYYY-MM-DD` | No | Payment deadline. |
| `principal_component` | Numeric(12,2) | Yes | $\ge 0.00$ | No | Principal portion of amortization. |
| `interest_component` | Numeric(12,2) | Yes | $\ge 0.00$ | No | Interest portion of amortization. |
| `due_amount` | Numeric(12,2) | Yes | $\text{principal} + \text{interest}$ | No | Total due for this schedule installment. |
| `paid_amount` | Numeric(12,2) | Yes | $0.00 \le \text{paid} \le \text{due}$ | No | Accumulated amount credited through allocations. |
| `status` | String(32) | Yes | `PENDING`, `PAID`, `PARTIALLY_PAID`, `OVERDUE` | No | Lifecycle state derived from payments and dates. |
| `paid_date` | Date | No | `YYYY-MM-DD` | No | Date when `paid_amount == due_amount`. |
| `created_at` | DateTime | Yes | UTC timestamp | No | Record creation timestamp. |

---

## 5. Payment (`payments`)
Represents an incoming transaction credited towards loan repayment.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `payment_id` | String(32) | Yes | Regex `^PMT-2026-\d{6}$` | Primary Key | Payment identifier (e.g., `PMT-2026-000001`). |
| `loan_id` | String(32) | Yes | FK -> `loans.loan_id` | No | Destination loan account. |
| `payment_date` | Date | Yes | `YYYY-MM-DD` | No | Date funds were received. |
| `payment_amount` | Numeric(12,2) | Yes | $> 0.00$ | No | Total transaction amount. |
| `payment_method` | String(32) | Yes | `UPI`, `NET_BANKING`, `DEBIT_CARD`, `AUTO_DEBIT`, `WIRE_TRANSFER`, `CASH` | No | Payment instrument. |
| `payment_status` | String(32) | Yes | `SUCCESS`, `PENDING`, `FAILED`, `REVERSED` | No | Payment execution status. |
| `reference_number` | String(64) | Yes | Gateway transaction ID | Unique | External transaction reference. |
| `created_at` | DateTime | Yes | UTC timestamp | No | Record creation timestamp. |

---

## 6. Payment Allocation Bridge (`payment_allocations`)
Bridge table resolving Many-to-Many ($M \leftrightarrow N$) relationship between Payments and Installments.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `allocation_id` | String(32) | Yes | Regex `^ALC-2026-\d{6}$` | Primary Key | Allocation identifier. |
| `payment_id` | String(32) | Yes | FK -> `payments.payment_id` | No | Source payment. |
| `installment_id` | String(48) | Yes | FK -> `installments.installment_id` | No | Destination installment. |
| `allocated_amount` | Numeric(12,2) | Yes | $> 0.00$ | No | Amount allocated to installment. $\sum \text{allocated} \le \text{payment\_amount}$. |
| `allocation_date` | Date | Yes | `YYYY-MM-DD` | No | Date allocation was applied. |
| `created_at` | DateTime | Yes | UTC timestamp | No | Record creation timestamp. |

---

## 7. Delinquency Snapshot (`delinquency_snapshots`)
Point-in-time calculation of account arrears, days past due, and risk classification.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `snapshot_id` | String(48) | Yes | Regex `^SNP-LOAN-2026-\d{6}-\d{3}$` | Primary Key | Snapshot record ID. |
| `loan_id` | String(32) | Yes | FK -> `loans.loan_id` | No | Target loan. |
| `snapshot_date` | Date | Yes | `YYYY-MM-DD` | No | As-of calculation date. |
| `days_past_due` | Integer | Yes | $\ge 0$ | No | Days elapsed since oldest overdue installment. |
| `total_arrears` | Numeric(12,2) | Yes | $\ge 0.00$ | No | Sum of due minus paid for all overdue installments. |
| `overdue_installments`| Integer | Yes | $\ge 0$ | No | Count of overdue unpaid installments. |
| `delinquency_bucket` | String(32) | Yes | `CURRENT`, `BUCKET_1_30`, `BUCKET_31_60`, `BUCKET_61_90`, `DEFAULT_90_PLUS` | No | Basel / regulatory arrears bucket. |
| `risk_level` | String(16) | Yes | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | No | Composite risk assessment. |
| `created_at` | DateTime | Yes | UTC timestamp | No | Calculation timestamp. |

---

## 8. Contact Preference (`contact_preferences`)
Borrower communication windows and statutory consent settings.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `preference_id` | String(48) | Yes | Regex `^PREF-CUST-2026-\d{6}-\d{3}$` | Primary Key | Preference identifier. |
| `customer_id` | String(32) | Yes | FK -> `customers.customer_id` | No | Target customer. |
| `preferred_channel` | String(32) | Yes | `PHONE`, `SMS`, `EMAIL`, `WHATSAPP` | No | Primary approved communication channel. |
| `contact_start_time` | String(8) | Yes | `HH:MM:SS` (e.g. `09:00:00`) | No | Earliest permissible local contact time. |
| `contact_end_time` | String(8) | Yes | `HH:MM:SS` (e.g. `18:00:00`) | No | Latest permissible local contact time. |
| `timezone` | String(32) | Yes | IANA format (e.g. `Asia/Kolkata`) | No | Customer's local timezone. |
| `contact_allowed` | Boolean | Yes | `True`, `False` | No | Whether contact is legally permitted. |
| `do_not_call` | Boolean | Yes | `True`, `False` | No | Statutory DNC register flag. |
| `effective_from` | Date | Yes | `YYYY-MM-DD` | No | Validity start date. |
| `effective_to` | Date | No | `YYYY-MM-DD` | No | Validity expiration date. |
| `created_at` | DateTime | Yes | UTC timestamp | No | Creation timestamp. |

---

## 9. Collection Case (`collection_cases`)
Operational entity tracking collection workflow, prioritized ranking, and agent assignment.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `case_id` | String(32) | Yes | Regex `^COL-2026-\d{6}$` | Primary Key | Case identifier (e.g., `COL-2026-000001`). |
| `loan_id` | String(32) | Yes | FK -> `loans.loan_id` | Unique | One active collection case per loan. |
| `customer_id` | String(32) | Yes | FK -> `customers.customer_id` | No | Borrower reference. |
| `outstanding_amount`| Numeric(12,2) | Yes | $\ge 0.00$ | No | Current delinquent arrears. |
| `days_past_due` | Integer | Yes | $\ge 0$ | No | Current days past due. |
| `priority_score` | Numeric(5,2) | Yes | $0.00 \le \text{score} \le 100.00$ | No | Explainable composite priority score. |
| `priority_level` | String(16) | Yes | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | No | Categorical tier based on score. |
| `case_status` | String(32) | Yes | `OPEN`, `CONTACT_SCHEDULED`, `PROMISE_ACTIVE`, `DISPUTED`, `HARDSHIP_HOLD`, `RESOLVED`, `CLOSED` | No | Current workflow state. |
| `score_explanation` | Text | No | JSON / structured string | No | Breakdown of score factors for audit. |
| `assigned_to` | String(64) | Yes | Agent ID / `Unassigned` | No | Assigned collector. |
| `created_at` | DateTime | Yes | UTC timestamp | No | Case inception timestamp. |
| `updated_at` | DateTime | Yes | UTC timestamp | No | Last update timestamp. |

---

## 10. Contact Attempt (`contact_attempts`)
Log of outreach attempts with compliance tracking.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `contact_id` | String(48) | Yes | Regex `^CTP-COL-2026-\d{6}-\d{3}$` | Primary Key | Contact attempt identifier. |
| `case_id` | String(32) | Yes | FK -> `collection_cases.case_id`| No | Target case. |
| `contact_channel` | String(32) | Yes | `PHONE`, `SMS`, `EMAIL`, `WHATSAPP` | No | Channel used. |
| `contact_time` | DateTime | Yes | UTC timestamp | No | Exact time contact was executed. |
| `outcome` | String(64) | Yes | `ANSWERED_PROMISED`, `ANSWERED_REFUSED`, `ANSWERED_DISPUTED`, `ANSWERED_CALLBACK_REQUESTED`, `NO_ANSWER`, `BUSY`, `INVALID_NUMBER`, `WRONG_PERSON` | No | Result of outreach attempt. |
| `notes` | Text | No | Free text | No | Collector conversation notes. |
| `compliance_status` | String(32) | Yes | `COMPLIANT`, `VIOLATION_WINDOW`, `VIOLATION_DNC`, `VIOLATION_FREQUENCY` | No | Compliance rule audit outcome. |
| `agent_id` | String(64) | Yes | Agent ID | No | Agent who conducted outreach. |
| `created_at` | DateTime | Yes | UTC timestamp | No | Record creation timestamp. |

---

## 11. Promise to Pay (`promises_to_pay`)
Commitment made by borrower to settle arrears by a target date.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `promise_id` | String(48) | Yes | Regex `^PRM-COL-2026-\d{6}-\d{3}$` | Primary Key | Promise commitment identifier. |
| `case_id` | String(32) | Yes | FK -> `collection_cases.case_id`| No | Target case. |
| `promised_amount` | Numeric(12,2) | Yes | $> 0.00$ | No | Amount borrower committed to pay. |
| `promised_date` | Date | Yes | `YYYY-MM-DD` | No | Due date for commitment. |
| `grace_period_days` | Integer | Yes | Default: 3 | No | Grace period in days before marking broken. |
| `status` | String(32) | Yes | `PENDING`, `FULFILLED`, `PARTIALLY_FULFILLED`, `BROKEN`, `CANCELLED` | No | State machine tracking actual receipt of payment. |
| `actual_paid_amount`| Numeric(12,2) | Yes | $\ge 0.00$ | No | Amount paid against this promise. |
| `reconciled_payment_id` | String(32) | No | FK -> `payments.payment_id` | No | Payment transaction that satisfied commitment. |
| `reconciled_at` | DateTime | No | UTC timestamp | No | Timestamp when reconciliation ran. |
| `created_at` | DateTime | Yes | UTC timestamp | No | Promise creation timestamp. |
| `updated_at` | DateTime | Yes | UTC timestamp | No | Last status update timestamp. |

---

## 12. Case Event Audit Trail (`case_events`)
Immutable event store preserving complete history of state changes and decisions.

| Field Name | Type | Required | Allowed Values / Format | Uniqueness | Validation Rule / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `event_id` | String(48) | Yes | Regex `^EVT-COL-2026-\d{6}-\d{3}$` | Primary Key | Event identifier. |
| `case_id` | String(32) | Yes | FK -> `collection_cases.case_id`| No | Collection case reference. |
| `event_type` | String(64) | Yes | `CASE_CREATED`, `STATUS_CHANGED`, `SCORE_UPDATED`, `CONTACT_LOGGED`, `PROMISE_CREATED`, `PAYMENT_RECONCILED`, `DISPUTE_FLAGGED`, `COMPLIANCE_FLAGGED` | No | Event taxonomy category. |
| `previous_state` | String(64) | No | Previous status / score | No | State before transition. |
| `new_state` | String(64) | Yes | New status / score | No | State after transition. |
| `reason` | Text | Yes | Non-empty text | No | Business reason or policy rule triggering the change. |
| `metadata_json` | Text | No | Valid JSON string | No | Additional context / factor details. |
| `created_by` | String(64) | Yes | User / `SYSTEM` | No | Actor responsible for trigger. |
| `created_at` | DateTime | Yes | UTC timestamp | No | Immutable timestamp of event. |

