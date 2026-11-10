"""Unit tests for Promise to Pay reconciliation state machine."""

import pytest
from datetime import date, datetime
from decimal import Decimal
from backend.app.models.entities import PromiseToPay, Payment
from backend.app.services.promise_reconciliation import reconcile_promise_commitment


def test_promise_fulfilled():
    """Verify promise is marked FULFILLED when full payment is received on time."""
    promise = PromiseToPay(
        promise_id="PRM-001",
        case_id="COL-001",
        promised_amount=Decimal("5000.00"),
        promised_date=date(2026, 11, 1),
        grace_period_days=3,
        status="PENDING",
        created_at=datetime(2026, 10, 25, 10, 0, 0),
    )
    pmt = Payment(
        payment_id="PMT-001",
        loan_id="LOAN-001",
        payment_date=date(2026, 10, 30),
        payment_amount=Decimal("5000.00"),
        payment_method="UPI",
        payment_status="SUCCESS",
        reference_number="REF-001",
    )
    res = reconcile_promise_commitment(promise, [pmt], as_of_date=date(2026, 11, 2))
    assert res["new_status"] == "FULFILLED"
    assert res["actual_paid_amount"] == Decimal("5000.00")
    assert res["remaining_amount"] == Decimal("0.00")


def test_promise_partially_fulfilled():
    """Verify promise is marked PARTIALLY_FULFILLED when partial payment is received."""
    promise = PromiseToPay(
        promise_id="PRM-002",
        case_id="COL-002",
        promised_amount=Decimal("10000.00"),
        promised_date=date(2026, 11, 1),
        grace_period_days=3,
        status="PENDING",
        created_at=datetime(2026, 10, 25, 10, 0, 0),
    )
    pmt = Payment(
        payment_id="PMT-002",
        loan_id="LOAN-002",
        payment_date=date(2026, 10, 31),
        payment_amount=Decimal("6000.00"),
        payment_method="NET_BANKING",
        payment_status="SUCCESS",
        reference_number="REF-002",
    )
    res = reconcile_promise_commitment(promise, [pmt], as_of_date=date(2026, 11, 5))
    assert res["new_status"] == "PARTIALLY_FULFILLED"
    assert res["actual_paid_amount"] == Decimal("6000.00")
    assert res["remaining_amount"] == Decimal("4000.00")


def test_promise_broken():
    """Verify promise is marked BROKEN when no payment is received past the grace period."""
    promise = PromiseToPay(
        promise_id="PRM-003",
        case_id="COL-003",
        promised_amount=Decimal("8000.00"),
        promised_date=date(2026, 11, 1),
        grace_period_days=3,  # Grace deadline: 2026-11-04
        status="PENDING",
        created_at=datetime(2026, 10, 25, 10, 0, 0),
    )
    # as_of_date is 2026-11-06 (past grace period)
    res = reconcile_promise_commitment(promise, [], as_of_date=date(2026, 11, 6))
    assert res["new_status"] == "BROKEN"
    assert res["actual_paid_amount"] == Decimal("0.00")

