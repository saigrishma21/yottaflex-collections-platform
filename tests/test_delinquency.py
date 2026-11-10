"""Unit tests for Delinquency calculation engine."""

import pytest
from datetime import date
from decimal import Decimal
from backend.app.models.entities import Installment
from backend.app.services.delinquency import calculate_delinquency


def test_no_overdue_installments():
    """Verify DPD is 0 and bucket is CURRENT when all due installments are paid."""
    inst1 = Installment(
        installment_id="INS-001",
        loan_id="LOAN-001",
        installment_number=1,
        due_date=date(2026, 9, 1),
        principal_component=Decimal("1000.00"),
        interest_component=Decimal("100.00"),
        due_amount=Decimal("1100.00"),
        paid_amount=Decimal("1100.00"),
        status="PAID",
    )
    result = calculate_delinquency([inst1], as_of_date=date(2026, 10, 31))
    assert result["days_past_due"] == 0
    assert result["total_arrears"] == Decimal("0.00")
    assert result["delinquency_bucket"] == "CURRENT"


def test_overdue_installment_dpd_and_arrears():
    """Verify exact DPD calculation and arrears accumulation."""
    as_of = date(2026, 10, 31)
    # Oldest overdue: due 2026-09-01 -> 60 days overdue
    inst1 = Installment(
        installment_id="INS-001",
        loan_id="LOAN-001",
        installment_number=1,
        due_date=date(2026, 9, 1),
        principal_component=Decimal("2000.00"),
        interest_component=Decimal("200.00"),
        due_amount=Decimal("2200.00"),
        paid_amount=Decimal("200.00"),  # 2000 remaining
        status="PARTIALLY_PAID",
    )
    # Second overdue: due 2026-10-01 -> 30 days overdue
    inst2 = Installment(
        installment_id="INS-002",
        loan_id="LOAN-001",
        installment_number=2,
        due_date=date(2026, 10, 1),
        principal_component=Decimal("2000.00"),
        interest_component=Decimal("200.00"),
        due_amount=Decimal("2200.00"),
        paid_amount=Decimal("0.00"),  # 2200 remaining
        status="OVERDUE",
    )
    result = calculate_delinquency([inst1, inst2], as_of_date=as_of)
    assert result["days_past_due"] == 60
    assert result["total_arrears"] == Decimal("4200.00")
    assert result["delinquency_bucket"] == "BUCKET_31_60"
    assert result["overdue_installments_count"] == 2
