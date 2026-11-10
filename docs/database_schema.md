# Database Schema & Entity Relationships

This document outlines the relational architecture, cardinalities, cascade constraints, and indices for the YottaFlex Delinquency & Collections Management System.

---

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    CUSTOMERS ||--o{ ACCOUNTS : "has (1:N)"
    CUSTOMERS ||--o{ CONTACT_PREFERENCES : "defines (1:N)"
    CUSTOMERS ||--o{ LOANS : "borrows (1:N)"
    CUSTOMERS ||--o{ COLLECTION_CASES : "subject_to (1:N)"
    
    ACCOUNTS ||--o{ LOANS : "services (1:N)"
    
    LOANS ||--|{ INSTALLMENTS : "schedules (1:N)"
    LOANS ||--o{ PAYMENTS : "receives (1:N)"
    LOANS ||--o{ DELINQUENCY_SNAPSHOTS : "evaluates (1:N)"
    LOANS ||--o| COLLECTION_CASES : "originates (1:1)"
    
    PAYMENTS ||--|{ PAYMENT_ALLOCATIONS : "allocates (1:N)"
    INSTALLMENTS ||--o{ PAYMENT_ALLOCATIONS : "covered_by (1:N)"
    
    COLLECTION_CASES ||--o{ CONTACT_ATTEMPTS : "records (1:N)"
    COLLECTION_CASES ||--o{ PROMISES_TO_PAY : "tracks (1:N)"
    COLLECTION_CASES ||--o{ CASE_EVENTS : "logs (1:N)"

    CUSTOMERS {
        string customer_id PK
        string first_name
        string last_name
        string email UK
        string phone
        string risk_segment
    }

    ACCOUNTS {
        string account_id PK
        string customer_id FK
        string account_number UK
        string account_type
        string account_status
    }

    LOANS {
        string loan_id PK
        string account_id FK
        string customer_id FK
        numeric principal_amount
        numeric interest_rate
        integer tenure_months
        string loan_status
        string dispute_status
        boolean is_hardship
    }

    INSTALLMENTS {
        string installment_id PK
        string loan_id FK
        integer installment_number
        date due_date
        numeric due_amount
        numeric paid_amount
        string status
    }

    PAYMENTS {
        string payment_id PK
        string loan_id FK
        date payment_date
        numeric payment_amount
        string payment_method
        string payment_status
        string reference_number UK
    }

    PAYMENT_ALLOCATIONS {
        string allocation_id PK
        string payment_id FK
        string installment_id FK
        numeric allocated_amount
        date allocation_date
    }

    DELINQUENCY_SNAPSHOTS {
        string snapshot_id PK
        string loan_id FK
        date snapshot_date
        integer days_past_due
        numeric total_arrears
        string delinquency_bucket
        string risk_level
    }

    CONTACT_PREFERENCES {
        string preference_id PK
        string customer_id FK
        string preferred_channel
        string contact_start_time
        string contact_end_time
        string timezone
        boolean contact_allowed
        boolean do_not_call
    }

    COLLECTION_CASES {
        string case_id PK
        string loan_id FK, UK
        string customer_id FK
        numeric outstanding_amount
        integer days_past_due
        numeric priority_score
        string priority_level
        string case_status
        string score_explanation
    }

    CONTACT_ATTEMPTS {
        string contact_id PK
        string case_id FK
        string contact_channel
        datetime contact_time
        string outcome
        string compliance_status
    }

    PROMISES_TO_PAY {
        string promise_id PK
        string case_id FK
        numeric promised_amount
        date promised_date
        string status
        numeric actual_paid_amount
    }

    CASE_EVENTS {
        string event_id PK
        string case_id FK
        string event_type
        string previous_state
        string new_state
        string reason
        datetime created_at
    }
```

---

## 2. Cardinalities & Relationship Mechanics

| Parent Entity | Child Entity | Cardinality | Join Keys | Delete / Update Action |
| :--- | :--- | :--- | :--- | :--- |
| `Customer` | `Account` | $1 : N$ | `customer_id` | `ON DELETE CASCADE` |
| `Customer` | `ContactPreference` | $1 : N$ | `customer_id` | `ON DELETE CASCADE` |
| `Customer` | `Loan` | $1 : N$ | `customer_id` | `ON DELETE RESTRICT` |
| `Account` | `Loan` | $1 : N$ | `account_id` | `ON DELETE RESTRICT` |
| `Loan` | `Installment` | $1 : N$ | `loan_id` | `ON DELETE CASCADE` |
| `Loan` | `Payment` | $1 : N$ | `loan_id` | `ON DELETE RESTRICT` |
| `Loan` | `DelinquencySnapshot` | $1 : N$ | `loan_id` | `ON DELETE CASCADE` |
| `Loan` | `CollectionCase` | $1 : 1$ | `loan_id` | `ON DELETE RESTRICT` (Unique) |
| `Payment` | `PaymentAllocation` | $1 : N$ | `payment_id` | `ON DELETE CASCADE` |
| `Installment` | `PaymentAllocation` | $1 : N$ | `installment_id` | `ON DELETE RESTRICT` |
| `CollectionCase` | `ContactAttempt` | $1 : N$ | `case_id` | `ON DELETE CASCADE` |
| `CollectionCase` | `PromiseToPay` | $1 : N$ | `case_id` | `ON DELETE CASCADE` |
| `CollectionCase` | `CaseEvent` | $1 : N$ | `case_id` | `ON DELETE CASCADE` |

---

## 3. Database Indices for Performance Optimization

1. **`customers`**: `email` (Unique), `phone`
2. **`accounts`**: `customer_id`, `account_number` (Unique)
3. **`loans`**: `customer_id`, `account_id`, `loan_status`
4. **`installments`**: `loan_id`, `due_date`, `status`, Composite `(loan_id, installment_number)` (Unique)
5. **`payments`**: `loan_id`, `payment_date`, `reference_number` (Unique)
6. **`payment_allocations`**: `payment_id`, `installment_id`, Composite `(payment_id, installment_id)`
7. **`delinquency_snapshots`**: `loan_id`, `snapshot_date`, Composite `(loan_id, snapshot_date)`
8. **`contact_preferences`**: `customer_id`
9. **`collection_cases`**: `loan_id` (Unique), `customer_id`, `priority_score`, `case_status`
10. **`contact_attempts`**: `case_id`, `contact_time`, `compliance_status`
11. **`promises_to_pay`**: `case_id`, `promised_date`, `status`
12. **`case_events`**: `case_id`, `created_at`, `event_type`
