"""Collections Workflow generator: Creates CollectionCases, ContactAttempts, PromisesToPay, and CaseEvents.
Integrates explainable multi-factor scoring (DPD 40%, Balance 35%, Risk 25%) and realistic commitment reconciliation.
"""

import json
from datetime import datetime, timedelta, time
from decimal import Decimal, ROUND_HALF_UP
import random
from backend.app.models.entities import CollectionCase, ContactAttempt, PromiseToPay, CaseEvent
from backend.app.services.prioritization import score_collection_account
from data_generator.config import SIMULATION_END_DATE


def generate_collections_workflow(loans, snapshots, customers, preferences, seed: int):
    """Generate collection cases, outreach attempts, payment commitments, and immutable audit events."""
    random.seed(seed)

    cases = []
    contact_attempts = []
    promises = []
    case_events = []

    cust_map = {c.customer_id: c for c in customers}
    pref_map = {p.customer_id: p for p in preferences}
    snap_map = {s.loan_id: s for s in snapshots}

    case_counter = 1
    promise_counter = 1
    attempt_counter = 1

    for loan in loans:
        snapshot = snap_map.get(loan.loan_id)
        if not snapshot or snapshot.days_past_due == 0:
            continue

        customer = cust_map.get(loan.customer_id)
        pref = pref_map.get(loan.customer_id)
        cust_risk = customer.risk_segment if customer else "MEDIUM"

        case_id = f"COL-2026-{case_counter:06d}"
        case_counter += 1

        # Calculate score using the unified continuous prioritization engine
        score_result = score_collection_account(
            total_arrears=snapshot.total_arrears,
            days_past_due=snapshot.days_past_due,
            risk_segment=cust_risk,
            loan_status=loan.loan_status,
            dispute_status=loan.dispute_status,
            is_hardship=loan.is_hardship,
            principal_amount=loan.principal_amount,
        )

        priority_score = score_result["priority_score"]
        priority_level = score_result["priority_level"]

        # Case Status determination
        if loan.dispute_status == "OPEN":
            status = "DISPUTED"
        elif loan.is_hardship:
            status = "HARDSHIP_HOLD"
        else:
            status = "OPEN"

        # Structured explainability factor breakdown
        explanation = {
            "case_id": case_id,
            "priority_score": float(priority_score),
            "priority_level": priority_level,
            "factors": [
                {
                    "factor": f["factor_name"],
                    "raw_value": f["raw_value"],
                    "normalized_score": f["normalized_score"],
                    "weight": f["weight"],
                    "contribution": f["weighted_contribution"],
                }
                for f in score_result["factors"]
            ],
            "decision_summary": score_result["decision_summary"],
        }

        col_case = CollectionCase(
            case_id=case_id,
            loan_id=loan.loan_id,
            customer_id=loan.customer_id,
            outstanding_amount=snapshot.total_arrears,
            days_past_due=snapshot.days_past_due,
            priority_score=priority_score,
            priority_level=priority_level,
            case_status=status,
            score_explanation=json.dumps(explanation),
            assigned_to="Agent_Alpha" if priority_level in ("CRITICAL", "HIGH") else "Unassigned",
            created_at=datetime.combine(SIMULATION_END_DATE - timedelta(days=min(snapshot.days_past_due, 60)), datetime.min.time()),
            updated_at=datetime.combine(SIMULATION_END_DATE, datetime.min.time()),
        )
        cases.append(col_case)

        # Audit Event 1: Case Creation
        evt_create = CaseEvent(
            event_id=f"EVT-{case_id}-001",
            case_id=case_id,
            event_type="CASE_CREATED",
            previous_state=None,
            new_state=status,
            reason=f"Account entered delinquency ({snapshot.days_past_due} DPD, ₹{float(snapshot.total_arrears):,.2f} arrears)",
            metadata_json=json.dumps({"priority_score": float(priority_score), "priority_level": priority_level}),
            created_by="SYSTEM",
            created_at=col_case.created_at,
        )
        case_events.append(evt_create)

        # Generate outreach and promises if eligible
        if status not in ("DISPUTED", "HARDSHIP_HOLD") and pref and pref.contact_allowed:
            channel = pref.preferred_channel
            
            # Stagger outreach timing: some historical (15-45 days ago), some recent (1-5 days ago)
            days_ago = random.choice([45, 30, 20, 10, 5, 2])
            c_time = datetime.combine(SIMULATION_END_DATE - timedelta(days=days_ago), time(11, 30, 0))

            outcomes = [
                "ANSWERED_PROMISED",
                "ANSWERED_CALLBACK_REQUESTED",
                "NO_ANSWER",
                "BUSY",
            ]
            outcome = random.choices(outcomes, weights=[0.45, 0.25, 0.15, 0.15], k=1)[0]

            ctp_id = f"CTP-{case_id}-{attempt_counter:03d}"
            attempt_counter += 1

            attempt = ContactAttempt(
                contact_id=ctp_id,
                case_id=case_id,
                contact_channel=channel,
                contact_time=c_time,
                outcome=outcome,
                notes=f"Outreach conducted via {channel}. Borrower status: {outcome}",
                compliance_status="COMPLIANT",
                agent_id="Agent_Alpha",
                created_at=c_time,
            )
            contact_attempts.append(attempt)

            # Audit Event 2: Contact Logged
            evt_contact = CaseEvent(
                event_id=f"EVT-{case_id}-002",
                case_id=case_id,
                event_type="CONTACT_LOGGED",
                previous_state=col_case.case_status,
                new_state=col_case.case_status,
                reason=f"Contact logged with outcome {outcome}",
                metadata_json=json.dumps({"contact_id": ctp_id, "channel": channel, "outcome": outcome}),
                created_by="Agent_Alpha",
                created_at=c_time,
            )
            case_events.append(evt_contact)

            # If borrower promised to pay, create commitment and simulate lifecycle
            if outcome == "ANSWERED_PROMISED":
                prm_id = f"PRM-{case_id}-{promise_counter:03d}"
                promise_counter += 1

                # Promise between 40% and 100% of arrears
                prm_ratio = Decimal(random.choice(["0.40", "0.60", "0.80", "1.00"]))
                prm_amount = (snapshot.total_arrears * prm_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                
                # Commitment deadline 7-14 days after the call
                target_date = c_time.date() + timedelta(days=random.randint(7, 14))
                grace_deadline = target_date + timedelta(days=3)

                # Determine promise outcome based on observation date vs deadline
                if grace_deadline <= SIMULATION_END_DATE:
                    # Historical promise that has completed its lifecycle
                    outcome_choice = random.choices(["FULFILLED", "PARTIALLY_FULFILLED", "BROKEN"], weights=[0.50, 0.20, 0.30], k=1)[0]
                    if outcome_choice == "FULFILLED":
                        prm_status = "FULFILLED"
                        actual_paid = prm_amount
                        reconciled_at = datetime.combine(target_date, time(14, 0, 0))
                        col_case.case_status = "RESOLVED" if prm_ratio == Decimal("1.00") else "OPEN"
                    elif outcome_choice == "PARTIALLY_FULFILLED":
                        prm_status = "PARTIALLY_FULFILLED"
                        actual_paid = (prm_amount * Decimal("0.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        reconciled_at = datetime.combine(target_date, time(15, 30, 0))
                        col_case.case_status = "OPEN"
                    else:
                        prm_status = "BROKEN"
                        actual_paid = Decimal("0.00")
                        reconciled_at = datetime.combine(grace_deadline, time(18, 0, 0))
                        col_case.case_status = "CONTACT_SCHEDULED"
                else:
                    # Recent active commitment
                    prm_status = "PENDING"
                    actual_paid = Decimal("0.00")
                    reconciled_at = None
                    col_case.case_status = "PROMISE_ACTIVE"

                promise = PromiseToPay(
                    promise_id=prm_id,
                    case_id=case_id,
                    promised_amount=prm_amount,
                    promised_date=target_date,
                    grace_period_days=3,
                    status=prm_status,
                    actual_paid_amount=actual_paid,
                    reconciled_payment_id=f"PMT-REC-{prm_id}" if actual_paid > 0 else None,
                    reconciled_at=reconciled_at,
                    created_at=c_time,
                    updated_at=reconciled_at or c_time,
                )
                promises.append(promise)

                # Audit Event 3: Promise Event
                evt_promise = CaseEvent(
                    event_id=f"EVT-{case_id}-003",
                    case_id=case_id,
                    event_type="PROMISE_CREATED" if prm_status == "PENDING" else f"PROMISE_{prm_status}",
                    previous_state="OPEN",
                    new_state=col_case.case_status,
                    reason=f"Commitment status: {prm_status} (Promised ₹{float(prm_amount):,.2f}, Paid ₹{float(actual_paid):,.2f})",
                    metadata_json=json.dumps({"promise_id": prm_id, "amount": float(prm_amount), "status": prm_status}),
                    created_by="Agent_Alpha",
                    created_at=reconciled_at or c_time,
                )
                case_events.append(evt_promise)

    return cases, contact_attempts, promises, case_events
