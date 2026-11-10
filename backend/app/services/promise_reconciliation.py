"""Promise-to-Pay Reconciliation Engine: Automates commitment lifecycle state machine.
"""

from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from backend.app.models.entities import PromiseToPay, Payment


def reconcile_promise_commitment(
    promise: PromiseToPay,
    received_payments: List[Payment],
    as_of_date: date = None,
) -> Dict[str, Any]:
    """Reconcile a PromiseToPay record against incoming payments.

    State Machine:
      - FULFILLED: paid >= promised within grace window
      - PARTIALLY_FULFILLED: 0 < paid < promised within grace window
      - BROKEN: paid == 0 and as_of_date > promised_date + grace_period
      - PENDING: window has not yet lapsed and payment pending
    """
    if as_of_date is None:
        as_of_date = date.today()

    # Grace window deadline
    grace_deadline = promise.promised_date + timedelta(days=promise.grace_period_days)
    creation_date = promise.created_at.date() if isinstance(promise.created_at, datetime) else promise.created_at

    # Filter qualifying payments received between commitment date and deadline
    qualifying_payments = [
        p for p in received_payments
        if creation_date <= p.payment_date <= grace_deadline and p.payment_status == "SUCCESS"
    ]

    total_paid = sum((p.payment_amount for p in qualifying_payments), Decimal("0.00"))
    last_payment = qualifying_payments[-1] if qualifying_payments else None

    prev_status = promise.status

    if total_paid >= promise.promised_amount:
        new_status = "FULFILLED"
    elif total_paid > Decimal("0.00"):
        if as_of_date > grace_deadline:
            new_status = "PARTIALLY_FULFILLED"
        else:
            new_status = "PARTIALLY_FULFILLED"
    else:
        if as_of_date > grace_deadline:
            new_status = "BROKEN"
        else:
            new_status = "PENDING"

    return {
        "promise_id": promise.promise_id,
        "previous_status": prev_status,
        "new_status": new_status,
        "promised_amount": promise.promised_amount,
        "actual_paid_amount": total_paid,
        "remaining_amount": max(Decimal("0.00"), promise.promised_amount - total_paid),
        "qualifying_payments_count": len(qualifying_payments),
        "reconciled_payment_id": last_payment.payment_id if last_payment else None,
        "deadline": grace_deadline,
        "status_changed": (prev_status != new_status),
    }

