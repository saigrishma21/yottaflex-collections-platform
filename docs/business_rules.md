# Business Rules & Logic Specifications

This document defines the mathematical models, lifecycle states, regulatory constraints, and anomaly detection rules governing the YottaFlex Delinquency & Collections System.

---

## 1. Delinquency & Arrears Calculation Engine

### 1.1 Days Past Due (DPD)
DPD measures the number of days that have elapsed since the oldest unpaid, due installment.

$$\text{DPD} = \begin{cases} 
0, & \text{if all due installments are fully settled} \\
(\text{Snapshot Date} - \min(\text{due\_date}))_{\text{overdue}}, & \text{where } \text{due\_amount} > \text{paid\_amount} \land \text{due\_date} \le \text{Snapshot Date}
\end{cases}$$

### 1.2 Total Arrears
Total arrears is the arithmetic sum of the remaining unpaid balances of all installments whose due date has passed.

$$\text{Total Arrears} = \sum_{i \in \text{Overdue Installments}} \left(\text{due\_amount}_i - \text{paid\_amount}_i\right)$$

*Installments with due dates in the future ($\text{due\_date} > \text{Snapshot Date}$) are excluded from current arrears.*

### 1.3 Delinquency Bucketing
Accounts are categorized into regulatory aging tiers:
* **Current**: $\text{DPD} = 0$
* **Bucket 1 (1–30 DPD)**: Early delinquency (soft collections / automated reminder)
* **Bucket 2 (31–60 DPD)**: Mid delinquency (outreach & payment plan negotiation)
* **Bucket 3 (61–90 DPD)**: Severe delinquency (intensified collections / hardship review)
* **Default (90+ DPD)**: Default / legal escalation

---

## 2. Explainable Prioritization & Scoring Engine

### 2.1 Pre-Scoring Eligibility Filters (Statutory Guards)
Prior to calculating priority scores, the system applies non-negotiable eligibility checks:
1. **Paid Account Exclusion**: If $\text{Total Arrears} = 0$ or $\text{loan\_status} = \text{PAID\_OFF}$, the case is marked $\text{EXCLUDED\_PAID}$ with $\text{Score} = 0.0$.
2. **Dispute Review Routing**: If $\text{dispute\_status} = \text{OPEN}$, collection outreach is legally suspended. The case is routed to `ROUTED_DISPUTE_REVIEW` with $\text{Score} = 0.0$.
3. **Hardship Arrangement**: If $\text{is\_hardship} = \text{True}$, standard aggressive outreach is replaced with hardship counseling workflows.

### 2.2 Composite Priority Score Formula
Eligible accounts are ranked on a 0–100 scale using an explainable multi-factor formula:

$$\text{Priority Score} = \left(S_{\text{balance}} \times 0.40\right) + \left(S_{\text{DPD}} \times 0.35\right) + \left(S_{\text{risk}} \times 0.25\right)$$

Where:
* **Balance Component ($S_{\text{balance}}$)**:
  $$S_{\text{balance}} = \min\left(100.0, \frac{\text{Total Arrears}}{50,000} \times 100.0\right)$$
* **DPD Component ($S_{\text{DPD}}$)**:
  $$S_{\text{DPD}} = \min\left(100.0, \frac{\text{DPD}}{90} \times 100.0\right)$$
* **Customer Underwriting Risk Component ($S_{\text{risk}}$)**:
  $$S_{\text{risk}} = \begin{cases} 90.0, & \text{risk\_segment} = \text{HIGH} \\ 50.0, & \text{risk\_segment} = \text{MEDIUM} \\ 20.0, & \text{risk\_segment} = \text{LOW} \end{cases}$$

### 2.3 Priority Level Mapping
* **Critical**: $80.0 \le \text{Score} \le 100.0$
* **High**: $60.0 \le \text{Score} < 80.0$
* **Medium**: $40.0 \le \text{Score} < 60.0$
* **Low**: $0.0 \le \text{Score} < 40.0$

### 2.4 Explainability Output Contract
Every scored case exposes a factor attribution payload explaining why the score was assigned:
```json
{
  "case_id": "COL-2026-000001",
  "priority_score": 78.5,
  "priority_level": "HIGH",
  "factors": [
    {"name": "Outstanding Arrears", "raw_value": "₹35,000", "weight": 0.40, "contribution": 28.0},
    {"name": "Delinquency Duration", "raw_value": "58 Days (Bucket 2)", "weight": 0.35, "contribution": 22.5},
    {"name": "Customer Risk Segment", "raw_value": "HIGH", "weight": 0.25, "contribution": 22.5}
  ],
  "decision_summary": "High risk borrower with 58 DPD and substantial arrears requires high priority intervention."
}
```

---

## 3. Contact Scheduling & Fair Practice Rules

To protect consumers and comply with Fair Debt Collection Practices Act (FDCPA) and statutory guidelines:

1. **Permissible Contact Windows**:
   * Outreach is only permitted between customer's configured window (default 09:00:00 to 18:00:00 in customer local timezone).
   * Attempts outside this window are blocked with status `BLOCKED_OUTSIDE_WINDOW`.

2. **Do Not Call (DNC) / Cease Contact**:
   * If customer `do_not_call = True` or `contact_allowed = False`, direct phone contact is strictly prohibited (`BLOCKED_DNC`).

3. **Weekly Outreach Frequency Limits**:
   * Maximum 3 attempted voice contacts per 7-day rolling window per borrower. Subsequent attempts are blocked with `BLOCKED_FREQUENCY_LIMIT`.

4. **Preferred Channel Routing**:
   * Initial scheduled attempt defaults to customer's `preferred_channel` (`PHONE`, `SMS`, `EMAIL`, `WHATSAPP`).

---

## 4. Promise-to-Pay (PTP) Reconciliation Engine

Borrowers frequently commit to pay a specific amount by a scheduled future date.

### 4.1 Commitment Validation
* The promised amount cannot exceed total outstanding arrears by more than 10%. Commitments exceeding this threshold are flagged as invalid / predatory.

### 4.2 State Machine Transitions
When an active promise exists (`status = PENDING`), the reconciliation engine runs upon payment arrival or grace period expiry:
* **`FULFILLED`**: $\text{Actual Paid} \ge \text{Promised Amount}$ received on or before $\text{Promised Date} + \text{Grace Period}$.
* **`PARTIALLY_FULFILLED`**: $0 < \text{Actual Paid} < \text{Promised Amount}$ received on or before $\text{Promised Date} + \text{Grace Period}$.
* **`BROKEN`**: $\text{Actual Paid} = 0$ after $\text{Current Date} > \text{Promised Date} + \text{Grace Period}$.
* **`CANCELLED`**: Case marked disputed or settled through alternative restructure.

---

## 5. Injected Negative Scenarios & Labeled Ground Truth

The system includes 5 required edge cases to validate compliance monitoring. Each injected anomaly is recorded in `data/ground_truth/ground_truth.csv` and `.json`:

| Anomaly Code | Name | Injected State | Expected System Detection |
| :--- | :--- | :--- | :--- |
| `ERR_PAID_IN_COLLECTION` | Paid Account in Collection | Loan is fully paid off ($\text{Arrears} = 0$), but case status remains `OPEN`. | Compliance audit flags case as `INVALID_ACTIVE_COLLECTION` and triggers closure. |
| `ERR_OUTSIDE_CONTACT_WINDOW` | Outreach Outside Permitted Window | A contact attempt timestamp falls outside `contact_start_time` - `contact_end_time`. | Compliance engine flags `VIOLATION_WINDOW` and logs regulatory audit breach. |
| `ERR_WRONG_PAYMENT_ALLOCATION` | Payment Allocated to Wrong Installment | `PaymentAllocation` references an installment belonging to a different loan. | Cross-loan validation flags allocation mismatch. |
| `ERR_PROMISE_EXCEEDS_ARREARS` | Promise Exceeds Arrears | Promised amount is greater than twice the total arrears balance. | Commitment validation flags `INVALID_COMMITMENT_AMOUNT`. |
| `ERR_DISPUTED_TREATED_CONFIRMED` | Disputed Debt Treated as Confirmed | Loan has `dispute_status = 'OPEN'`, but case is subjected to active collection calls. | Compliance engine flags `VIOLATION_DISPUTED_COLLECTION`. |
