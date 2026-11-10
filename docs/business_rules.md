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
Eligible accounts are ranked on a continuous 0–100 scale using an explainable multi-factor formula:

$$\text{Priority Score} = \left(S_{\text{DPD}} \times 0.40\right) + \left(S_{\text{balance}} \times 0.35\right) + \left(S_{\text{risk}} \times 0.25\right)$$

Where:
* **DPD Component ($S_{\text{DPD}}$, 40% Weight)**:
  Continuous piecewise delinquency aging curve:
  - $\text{DPD} \le 30$: $S_{\text{DPD}} = (\text{DPD} / 30) \times 35.0$
  - $30 < \text{DPD} \le 90$: $S_{\text{DPD}} = 35.0 + ((\text{DPD} - 30) / 60) \times 35.0$
  - $90 < \text{DPD} \le 270$: $S_{\text{DPD}} = 70.0 + ((\text{DPD} - 90) / 180) \times 25.0$
  - $\text{DPD} > 270$: $S_{\text{DPD}} = 95.0 + \min(5.0, ((\text{DPD} - 270) / 90) \times 5.0)$
* **Balance Component ($S_{\text{balance}}$, 35% Weight)**:
  Continuous balance exposure curve spanning retail to high-ticket loans:
  - $\text{Arrears} \le ₹20\text{k}$: $S_{\text{balance}} = (\text{Arrears} / 20000) \times 30.0$
  - $₹20\text{k} < \text{Arrears} \le ₹80\text{k}$: $S_{\text{balance}} = 30.0 + ((\text{Arrears} - 20000) / 60000) \times 35.0$
  - $₹80\text{k} < \text{Arrears} \le ₹300\text{k}$: $S_{\text{balance}} = 65.0 + ((\text{Arrears} - 80000) / 220000) \times 25.0$
  - $\text{Arrears} > ₹300\text{k}$: $S_{\text{balance}} = 90.0 + \min(10.0, ((\text{Arrears} - 300000) / 700000) \times 10.0)$
* **Customer Risk Component ($S_{\text{risk}}$, 25% Weight)**:
  Incorporates base credit tier plus current balance-to-principal exposure ratio:
  - $\text{HIGH}$: $S_{\text{risk}} = 80.0 + (\text{exposure\_ratio} \times 18.0)$
  - $\text{MEDIUM}$: $S_{\text{risk}} = 45.0 + (\text{exposure\_ratio} \times 20.0)$
  - $\text{LOW}$: $S_{\text{risk}} = 15.0 + (\text{exposure\_ratio} \times 20.0)$

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
    {"factor": "Days Past Due (Delinquency Age)", "raw_value": "58 Days", "normalized_score": 51.3, "weight": 0.40, "contribution": 20.52},
    {"factor": "Outstanding Balance Arrears", "raw_value": "₹35,000.00", "normalized_score": 38.8, "weight": 0.35, "contribution": 13.58},
    {"factor": "Customer Risk Profile", "raw_value": "HIGH (Exposure: 45%)", "normalized_score": 88.1, "weight": 0.25, "contribution": 22.03}
  ],
  "decision_summary": "HIGH priority: 58 DPD with ₹35,000.00 arrears on HIGH risk profile."
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

