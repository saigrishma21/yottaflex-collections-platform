"""Compliance & Regulatory Audit Engine: Detects unfair practices and policy exceptions.
"""

from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.entities import (
    CollectionCase,
    Loan,
    ContactAttempt,
    ContactPreference,
    PaymentAllocation,
    Payment,
    Installment,
    PromiseToPay,
)
from backend.app.services.contact_scheduler import parse_time_str


def scan_compliance_violations(db: Session) -> List[Dict[str, Any]]:
    """Scan database to identify statutory, policy, and data integrity violations."""
    violations = []

    # 1. PAID ACCOUNT IN COLLECTION
    paid_cases = (
        db.query(CollectionCase, Loan)
        .join(Loan, CollectionCase.loan_id == Loan.loan_id)
        .filter(
            (Loan.loan_status == "PAID_OFF") | (CollectionCase.outstanding_amount <= Decimal("0.00")),
            CollectionCase.case_status.in_(["OPEN", "CONTACT_SCHEDULED", "PROMISE_ACTIVE"]),
        )
        .all()
    )
    for case, loan in paid_cases:
        violations.append({
            "violation_code": "ERR_PAID_IN_COLLECTION",
            "category": "UNLAWFUL_COLLECTION",
            "severity": "CRITICAL",
            "record_id": case.case_id,
            "entity_type": "CollectionCase",
            "description": f"Collection case {case.case_id} is active on fully settled loan {loan.loan_id} (0 arrears).",
            "recommended_action": "Immediately close case and issue debt satisfaction notice.",
        })

    # 2. CONTACT OUTSIDE ALLOWED WINDOW
    # Query attempts joined with case and preference
    attempts = (
        db.query(ContactAttempt, ContactPreference)
        .join(CollectionCase, ContactAttempt.case_id == CollectionCase.case_id)
        .join(ContactPreference, CollectionCase.customer_id == ContactPreference.customer_id)
        .all()
    )
    for att, pref in attempts:
        start_t = parse_time_str(pref.contact_start_time)
        end_t = parse_time_str(pref.contact_end_time)
        att_time = att.contact_time.time()
        if att_time < start_t or att_time > end_t or att.compliance_status == "VIOLATION_WINDOW":
            violations.append({
                "violation_code": "ERR_OUTSIDE_CONTACT_WINDOW",
                "category": "FDCPA_STATUTORY_BREACH",
                "severity": "HIGH",
                "record_id": att.contact_id,
                "entity_type": "ContactAttempt",
                "description": f"Outreach at {att.contact_time.strftime('%H:%M:%S')} violated permissible window {start_t} - {end_t}.",
                "recommended_action": "Log statutory violation, flag collector, and restrict future outreach hours.",
            })

    # 3. WRONG PAYMENT ALLOCATION (CROSS-LOAN ALLOCATION)
    mismatched_allocs = (
        db.query(PaymentAllocation, Payment, Installment)
        .join(Payment, PaymentAllocation.payment_id == Payment.payment_id)
        .join(Installment, PaymentAllocation.installment_id == Installment.installment_id)
        .filter(Payment.loan_id != Installment.loan_id)
        .all()
    )
    for alloc, pmt, inst in mismatched_allocs:
        violations.append({
            "violation_code": "ERR_WRONG_PAYMENT_ALLOCATION",
            "category": "ACCOUNTING_MISALLOCATION",
            "severity": "HIGH",
            "record_id": alloc.allocation_id,
            "entity_type": "PaymentAllocation",
            "description": f"Payment {pmt.payment_id} for Loan {pmt.loan_id} allocated to Installment {inst.installment_id} on Loan {inst.loan_id}.",
            "recommended_action": "Reverse cross-loan allocation and re-credit correct debtor installment.",
        })

    # 4. PROMISE AMOUNT EXCEEDS ARREARS
    excessive_promises = (
        db.query(PromiseToPay, CollectionCase)
        .join(CollectionCase, PromiseToPay.case_id == CollectionCase.case_id)
        .filter(
            PromiseToPay.status == "PENDING",
            PromiseToPay.promised_amount > (CollectionCase.outstanding_amount * Decimal("2.0")),
            CollectionCase.outstanding_amount > Decimal("0.00"),
        )
        .all()
    )
    for prm, case in excessive_promises:
        violations.append({
            "violation_code": "ERR_PROMISE_EXCEEDS_ARREARS",
            "category": "PREDATORY_COMMITMENT",
            "severity": "MEDIUM",
            "record_id": prm.promise_id,
            "entity_type": "PromiseToPay",
            "description": f"Promised amount ₹{prm.promised_amount:,.2f} exceeds outstanding arrears ₹{case.outstanding_amount:,.2f} by >200%.",
            "recommended_action": "Void inflated promise commitment and restructure realistic payment plan.",
        })

    # 5. DISPUTED DEBT TREATED AS CONFIRMED
    disputed_violations = (
        db.query(CollectionCase, Loan)
        .join(Loan, CollectionCase.loan_id == Loan.loan_id)
        .filter(
            Loan.dispute_status == "OPEN",
            CollectionCase.case_status.in_(["CONTACT_SCHEDULED", "OPEN"]),
        )
        .all()
    )
    for case, loan in disputed_violations:
        violations.append({
            "violation_code": "ERR_DISPUTED_TREATED_CONFIRMED",
            "category": "DISPUTED_DEBT_VIOLATION",
            "severity": "CRITICAL",
            "record_id": case.case_id,
            "entity_type": "CollectionCase",
            "description": f"Loan {loan.loan_id} has an open dispute, but case is actively routed for collections.",
            "recommended_action": "Immediately freeze collection workflow and route to Dispute Investigation Unit.",
        })

    return violations

