"""Anomaly Injector: Injects the 5 required negative edge cases and produces isolated ground truth files.
"""

from datetime import datetime, date, time, timedelta
from decimal import Decimal
import json
import csv
import os
from backend.app.models.entities import (
    CollectionCase,
    ContactAttempt,
    PaymentAllocation,
    PromiseToPay,
    CaseEvent,
)


def inject_required_anomalies(
    loans,
    installments,
    payments,
    allocations,
    snapshots,
    cases,
    contact_attempts,
    promises,
    case_events,
    customers,
    preferences,
    anomalies_per_type: int = 5,
):
    """Inject 5 required negative scenarios into generated records and populate isolated ground truth."""
    ground_truth_records = []
    pref_map = {p.customer_id: p for p in preferences}
    loan_map = {l.loan_id: l for l in loans}

    # =========================================================================
    # 1. ANOMALY: Paid account remains in collection
    # =========================================================================
    # Find paid-off loans and erroneously attach an OPEN collection case
    paid_loans = [l for l in loans if l.loan_status == "PAID_OFF"]
    count_1 = 0
    for loan in paid_loans:
        if count_1 >= anomalies_per_type:
            break
        # Check if case already exists for this loan
        if not any(c.loan_id == loan.loan_id for c in cases):
            case_id = f"COL-2026-ANOM1-{count_1 + 1:04d}"
            case = CollectionCase(
                case_id=case_id,
                loan_id=loan.loan_id,
                customer_id=loan.customer_id,
                outstanding_amount=Decimal("0.00"),
                days_past_due=0,
                priority_score=Decimal("45.00"),  # Erroneous non-zero score
                priority_level="MEDIUM",
                case_status="OPEN",  # Invalid active status
                score_explanation=json.dumps({"error": "Erroneous case assigned to settled debt"}),
                assigned_to="Agent_Alpha",
                created_at=datetime(2026, 10, 25, 10, 0, 0),
                updated_at=datetime(2026, 10, 25, 10, 0, 0),
            )
            cases.append(case)

            ground_truth_records.append({
                "record_id": case_id,
                "entity_type": "CollectionCase",
                "issue_type": "PAID_ACCOUNT_IN_COLLECTION",
                "description": f"Loan {loan.loan_id} is paid off (0 arrears), but collection case remains OPEN.",
                "expected_action": "EXCLUDE_AND_CLOSE",
            })
            count_1 += 1

    # =========================================================================
    # 2. ANOMALY: Contact outside allowed window
    # =========================================================================
    count_2 = 0
    for case in cases:
        if count_2 >= anomalies_per_type:
            break
        if case.case_status not in ("DISPUTED", "HARDSHIP_HOLD"):
            pref = pref_map.get(case.customer_id)
            ctp_id = f"CTP-{case.case_id}-ANOM2"
            # Injected outreach at 22:45:00 (late night, statutory violation)
            bad_time = datetime(2026, 10, 28, 22, 45, 0)
            attempt = ContactAttempt(
                contact_id=ctp_id,
                case_id=case.case_id,
                contact_channel="PHONE",
                contact_time=bad_time,
                outcome="ANSWERED_REFUSED",
                notes="Collector initiated call at 22:45 PM.",
                compliance_status="VIOLATION_WINDOW",  # Injected violation
                agent_id="Agent_Beta",
                created_at=bad_time,
            )
            contact_attempts.append(attempt)

            ground_truth_records.append({
                "record_id": ctp_id,
                "entity_type": "ContactAttempt",
                "issue_type": "OUTSIDE_CONTACT_WINDOW",
                "description": f"Contact attempt occurred at 22:45, violating permissible window 09:00-18:00.",
                "expected_action": "FLAG_COMPLIANCE_VIOLATION",
            })
            count_2 += 1

    # =========================================================================
    # 3. ANOMALY: Payment allocated to wrong installment (Cross-loan allocation)
    # =========================================================================
    count_3 = 0
    # Swap allocation of a payment to an installment belonging to a completely different loan
    if len(payments) > 5 and len(installments) > 10:
        for pmt in payments[:anomalies_per_type]:
            # Find an installment belonging to a different loan
            other_inst = next((i for i in installments if i.loan_id != pmt.loan_id), None)
            if other_inst:
                alc_id = f"ALC-ANOM3-{count_3 + 1:04d}"
                bad_alloc = PaymentAllocation(
                    allocation_id=alc_id,
                    payment_id=pmt.payment_id,
                    installment_id=other_inst.installment_id,
                    allocated_amount=Decimal("1500.00"),
                    allocation_date=pmt.payment_date,
                    created_at=datetime.combine(pmt.payment_date, datetime.min.time()),
                )
                allocations.append(bad_alloc)

                ground_truth_records.append({
                    "record_id": alc_id,
                    "entity_type": "PaymentAllocation",
                    "issue_type": "WRONG_INSTALLMENT_ALLOCATION",
                    "description": f"Payment {pmt.payment_id} for Loan {pmt.loan_id} allocated to Installment {other_inst.installment_id} belonging to Loan {other_inst.loan_id}.",
                    "expected_action": "REJECT_ALLOCATION_MISMATCH",
                })
                count_3 += 1

    # =========================================================================
    # 4. ANOMALY: Promise amount exceeds arrears
    # =========================================================================
    count_4 = 0
    for case in cases:
        if count_4 >= anomalies_per_type:
            break
        if case.outstanding_amount > Decimal("0.00"):
            prm_id = f"PRM-{case.case_id}-ANOM4"
            # Promise amount 3x larger than total arrears
            excessive_amount = (case.outstanding_amount * Decimal("3.5")).quantize(Decimal("0.01"))
            p_date = date(2026, 11, 10)
            bad_promise = PromiseToPay(
                promise_id=prm_id,
                case_id=case.case_id,
                promised_amount=excessive_amount,
                promised_date=p_date,
                grace_period_days=3,
                status="PENDING",
                actual_paid_amount=Decimal("0.00"),
                reconciled_payment_id=None,
                reconciled_at=None,
                created_at=datetime(2026, 10, 29, 14, 0, 0),
                updated_at=datetime(2026, 10, 29, 14, 0, 0),
            )
            promises.append(bad_promise)

            ground_truth_records.append({
                "record_id": prm_id,
                "entity_type": "PromiseToPay",
                "issue_type": "PROMISE_EXCEEDS_ARREARS",
                "description": f"Promised amount ₹{excessive_amount:,.2f} exceeds outstanding arrears ₹{case.outstanding_amount:,.2f} by >250%.",
                "expected_action": "FLAG_INVALID_COMMITMENT",
            })
            count_4 += 1

    # =========================================================================
    # 5. ANOMALY: Disputed debt treated as confirmed
    # =========================================================================
    count_5 = 0
    disputed_loans = [l for l in loans if l.dispute_status == "OPEN"]
    existing_case_by_loan = {c.loan_id: c for c in cases}

    for loan in disputed_loans:
        if count_5 >= anomalies_per_type:
            break
        
        # Check if case already exists for this loan
        if loan.loan_id in existing_case_by_loan:
            existing_case = existing_case_by_loan[loan.loan_id]
            # Erroneously change state to active contact collection
            existing_case.case_status = "CONTACT_SCHEDULED"
            existing_case.priority_score = Decimal("85.00")
            existing_case.priority_level = "CRITICAL"
            target_case_id = existing_case.case_id
        else:
            case_id = f"COL-2026-ANOM5-{count_5 + 1:04d}"
            bad_case = CollectionCase(
                case_id=case_id,
                loan_id=loan.loan_id,
                customer_id=loan.customer_id,
                outstanding_amount=loan.principal_amount,
                days_past_due=45,
                priority_score=Decimal("82.00"),
                priority_level="CRITICAL",
                case_status="CONTACT_SCHEDULED",  # Unlawful active collection on disputed debt
                score_explanation=json.dumps({"error": "Disputed debt actively pushed for outreach"}),
                assigned_to="Agent_Gamma",
                created_at=datetime(2026, 10, 26, 9, 0, 0),
                updated_at=datetime(2026, 10, 26, 9, 0, 0),
            )
            cases.append(bad_case)
            existing_case_by_loan[loan.loan_id] = bad_case
            target_case_id = case_id

        ground_truth_records.append({
            "record_id": target_case_id,
            "entity_type": "CollectionCase",
            "issue_type": "DISPUTED_DEBT_TREATED_CONFIRMED",
            "description": f"Loan {loan.loan_id} has OPEN dispute, but case is marked CONTACT_SCHEDULED instead of DISPUTE_HOLD.",
            "expected_action": "ROUTE_DISPUTE_REVIEW",
        })
        count_5 += 1

    return ground_truth_records


def export_ground_truth(ground_truth_records, output_dir: str):
    """Write ground truth to CSV and JSON files in data/ground_truth/."""
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "ground_truth.csv")
    json_path = os.path.join(output_dir, "ground_truth.json")

    # Write CSV
    if ground_truth_records:
        keys = list(ground_truth_records[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(ground_truth_records)

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth_records, f, indent=2)

    print(f"Exported {len(ground_truth_records)} ground truth labeled records to:")
    print(f"  - {csv_path}")
    print(f"  - {json_path}")
