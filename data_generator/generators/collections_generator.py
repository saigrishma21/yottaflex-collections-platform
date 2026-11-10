"""Collections Workflow generator: Creates CollectionCases, ContactAttempts, PromisesToPay, and CaseEvents.
"""

import json
from datetime import datetime, timedelta, time
from decimal import Decimal, ROUND_HALF_UP
import random
from backend.app.models.entities import CollectionCase, ContactAttempt, PromiseToPay, CaseEvent
from data_generator.config import SIMULATION_END_DATE


def generate_collections_workflow(loans, snapshots, customers, preferences, seed: int):
    """Generate collection cases, contact attempts, commitments, and immutable audit events."""
    random.seed(seed)

    cases = []
    contact_attempts = []
    promises = []
    case_events = []

    cust_map = {c.customer_id: c for c in customers}
    pref_map = {p.customer_id: p for p in preferences}
    snap_map = {s.loan_id: s for s in snapshots}

    case_counter = 1

    for loan in loans:
        snapshot = snap_map.get(loan.loan_id)
        if not snapshot or snapshot.days_past_due == 0:
            continue

        customer = cust_map.get(loan.customer_id)
        pref = pref_map.get(loan.customer_id)
        cust_risk = customer.risk_segment if customer else "MEDIUM"

        case_id = f"COL-2026-{case_counter:06d}"
        case_counter += 1

        # Calculate explainable priority score
        bal_float = float(snapshot.total_arrears)
        s_balance = min(100.0, (bal_float / 50000.0) * 100.0)
        s_dpd = min(100.0, (snapshot.days_past_due / 90.0) * 100.0)
        s_risk = 90.0 if cust_risk == "HIGH" else (50.0 if cust_risk == "MEDIUM" else 20.0)

        raw_score = (s_balance * 0.40) + (s_dpd * 0.35) + (s_risk * 0.25)
        priority_score = Decimal(str(round(raw_score, 2)))

        if priority_score >= 80.0:
            priority_level = "CRITICAL"
        elif priority_score >= 60.0:
            priority_level = "HIGH"
        elif priority_score >= 40.0:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"

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
                    "factor": "Outstanding Arrears",
                    "raw_value": f"₹{bal_float:,.2f}",
                    "normalized_score": round(s_balance, 1),
                    "weight": 0.40,
                    "contribution": round(s_balance * 0.40, 2),
                },
                {
                    "factor": "Days Past Due",
                    "raw_value": f"{snapshot.days_past_due} Days",
                    "normalized_score": round(s_dpd, 1),
                    "weight": 0.35,
                    "contribution": round(s_dpd * 0.35, 2),
                },
                {
                    "factor": "Customer Risk Segment",
                    "raw_value": cust_risk,
                    "normalized_score": round(s_risk, 1),
                    "weight": 0.25,
                    "contribution": round(s_risk * 0.25, 2),
                },
            ],
            "decision_summary": f"{priority_level} priority case with ₹{bal_float:,.0f} arrears at {snapshot.days_past_due} DPD.",
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
            created_at=datetime.combine(SIMULATION_END_DATE - timedelta(days=min(snapshot.days_past_due, 30)), datetime.min.time()),
            updated_at=datetime.combine(SIMULATION_END_DATE, datetime.min.time()),
        )
        cases.append(col_case)

        # Audit Event 1: Case Creation
        evt_create = CaseEvent(
            event_id=f"EVT-{case_id}-001",
            case_id=case_id,
            event_type="CASE_CREATED",
            previous_state=None,
            new_state="OPEN",
            reason=f"Account entered delinquency ({snapshot.days_past_due} DPD, ₹{bal_float:,.2f} arrears)",
            metadata_json=json.dumps({"priority_score": float(priority_score), "priority_level": priority_level}),
            created_by="SYSTEM",
            created_at=col_case.created_at,
        )
        case_events.append(evt_create)

        # Generate contact attempt and promise if eligible (not disputed and contact allowed)
        if status not in ("DISPUTED", "HARDSHIP_HOLD") and pref and pref.contact_allowed:
            channel = pref.preferred_channel
            # Compliant contact time within window (e.g. 11:30 AM)
            c_time = datetime.combine(SIMULATION_END_DATE - timedelta(days=2), time(11, 30, 0))

            outcomes = [
                "ANSWERED_PROMISED",
                "ANSWERED_CALLBACK_REQUESTED",
                "NO_ANSWER",
                "BUSY",
            ]
            outcome = random.choices(outcomes, weights=[0.40, 0.25, 0.20, 0.15], k=1)[0]

            ctp_id = f"CTP-{case_id}-001"
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

            # If borrower promised to pay, create commitment
            if outcome == "ANSWERED_PROMISED":
                prm_id = f"PRM-{case_id}-001"
                # Promise 60% to 100% of arrears
                prm_amount = (snapshot.total_arrears * Decimal(random.choice(["0.60", "0.80", "1.00"]))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                target_date = SIMULATION_END_DATE + timedelta(days=random.randint(5, 14))

                promise = PromiseToPay(
                    promise_id=prm_id,
                    case_id=case_id,
                    promised_amount=prm_amount,
                    promised_date=target_date,
                    grace_period_days=3,
                    status="PENDING",
                    actual_paid_amount=Decimal("0.00"),
                    reconciled_payment_id=None,
                    reconciled_at=None,
                    created_at=c_time,
                    updated_at=c_time,
                )
                promises.append(promise)
                col_case.case_status = "PROMISE_ACTIVE"

                # Audit Event 3: Promise Created
                evt_promise = CaseEvent(
                    event_id=f"EVT-{case_id}-003",
                    case_id=case_id,
                    event_type="PROMISE_CREATED",
                    previous_state="OPEN",
                    new_state="PROMISE_ACTIVE",
                    reason=f"Borrower committed to pay ₹{float(prm_amount):,.2f} by {target_date}",
                    metadata_json=json.dumps({"promise_id": prm_id, "amount": float(prm_amount)}),
                    created_by="Agent_Alpha",
                    created_at=c_time,
                )
                case_events.append(evt_promise)

    return cases, contact_attempts, promises, case_events

