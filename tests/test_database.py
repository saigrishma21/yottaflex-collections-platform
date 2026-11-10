"""Tests for database tables, foreign keys, and constraints."""

import pytest
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from backend.app.database import SessionLocal, Base, engine
from backend.app.models.entities import (
    Customer,
    Account,
    Loan,
    Installment,
    Payment,
    PaymentAllocation,
    DelinquencySnapshot,
    ContactPreference,
    CollectionCase,
    ContactAttempt,
    PromiseToPay,
    CaseEvent,
)


@pytest.fixture(scope="module")
def db():
    """Create fresh database session for testing."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_tables_created(db):
    """Verify all 12 tables exist in the metadata."""
    expected_tables = {
        "customers",
        "accounts",
        "loans",
        "installments",
        "payments",
        "payment_allocations",
        "delinquency_snapshots",
        "contact_preferences",
        "collection_cases",
        "contact_attempts",
        "promises_to_pay",
        "case_events",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


def test_customer_account_loan_relationship(db):
    """Verify relationship hierarchy: Customer -> Account -> Loan -> Installment."""
    # Clean up any previous test records
    cust_id = "CUST-TEST-000001"
    existing = db.query(Customer).filter_by(customer_id=cust_id).first()
    if existing:
        db.delete(existing)
        db.commit()

    customer = Customer(
        customer_id=cust_id,
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone="+919876543210",
        address="123 MG Road",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560001",
        risk_segment="LOW",
    )
    db.add(customer)
    db.commit()

    account = Account(
        account_id="ACC-TEST-000001",
        customer_id=customer.customer_id,
        account_number="ACC99990001",
        account_type="SAVINGS",
        account_status="ACTIVE",
        opened_date=date(2025, 1, 1),
    )
    db.add(account)
    db.commit()

    loan = Loan(
        loan_id="LOAN-TEST-000001",
        account_id=account.account_id,
        customer_id=customer.customer_id,
        loan_type="PERSONAL",
        principal_amount=Decimal("50000.00"),
        interest_rate=Decimal("12.00"),
        tenure_months=6,
        loan_date=date(2025, 6, 1),
        maturity_date=date(2025, 12, 1),
        loan_status="ACTIVE",
    )
    db.add(loan)
    db.commit()

    installment = Installment(
        installment_id="INS-LOAN-TEST-000001-001",
        loan_id=loan.loan_id,
        installment_number=1,
        due_date=date(2025, 7, 1),
        principal_component=Decimal("8000.00"),
        interest_component=Decimal("500.00"),
        due_amount=Decimal("8500.00"),
        paid_amount=Decimal("0.00"),
        status="OVERDUE",
    )
    db.add(installment)
    db.commit()

    # Query back and verify
    queried_cust = db.query(Customer).filter_by(customer_id=cust_id).first()
    assert queried_cust is not None
    assert len(queried_cust.accounts) == 1
    assert len(queried_cust.loans) == 1
    assert len(queried_cust.loans[0].installments) == 1
    assert queried_cust.loans[0].installments[0].due_amount == Decimal("8500.00")

    # Clean up
    db.delete(installment)
    db.delete(loan)
    db.delete(account)
    db.delete(customer)
    db.commit()


def test_foreign_key_violation(db):
    """Verify foreign key constraint blocks orphaned child insertion."""
    orphan_account = Account(
        account_id="ACC-NONEXISTENT",
        customer_id="CUST-DOES-NOT-EXIST",
        account_number="INVALID999",
        account_type="SAVINGS",
        account_status="ACTIVE",
        opened_date=date(2025, 1, 1),
    )
    db.add(orphan_account)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

