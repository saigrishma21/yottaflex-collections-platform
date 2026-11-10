"""SQLAlchemy ORM models for YottaFlex Delinquency & Collections System.

Implements all 10 core entities + PaymentAllocation bridge table + CaseEvent audit trail.
Enforces strict primary keys, foreign keys, lifecycle states, indexes, and relationships.
"""

from datetime import datetime, date, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Date,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


def utc_now():
    """Return timezone-aware or naive UTC datetime for database column defaults."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ============================================================================
# 1. CUSTOMER ENTITY
# ============================================================================
class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(32), primary_key=True)  # Format: CUST-2026-000001
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    email = Column(String(128), unique=True, nullable=False, index=True)
    phone = Column(String(32), nullable=False, index=True)
    address = Column(String(255), nullable=True)
    city = Column(String(64), nullable=False)
    state = Column(String(64), nullable=False)
    postal_code = Column(String(16), nullable=False)
    risk_segment = Column(String(16), nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    contact_preferences = relationship("ContactPreference", back_populates="customer", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="customer")
    collection_cases = relationship("CollectionCase", back_populates="customer")

    __table_args__ = (
        CheckConstraint("risk_segment IN ('LOW', 'MEDIUM', 'HIGH')", name="chk_customer_risk_segment"),
    )

    def __repr__(self):
        return f"<Customer {self.customer_id}: {self.first_name} {self.last_name}>"


# ============================================================================
# 2. ACCOUNT ENTITY
# ============================================================================
class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(String(32), primary_key=True)  # Format: ACC-2026-000001
    customer_id = Column(String(32), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    account_number = Column(String(32), unique=True, nullable=False, index=True)
    account_type = Column(String(32), nullable=False, default="SAVINGS")  # SAVINGS, CURRENT, SALARY
    account_status = Column(String(32), nullable=False, default="ACTIVE")  # ACTIVE, DORMANT, FROZEN, CLOSED
    opened_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    loans = relationship("Loan", back_populates="account")

    __table_args__ = (
        CheckConstraint("account_type IN ('SAVINGS', 'CURRENT', 'SALARY')", name="chk_account_type"),
        CheckConstraint("account_status IN ('ACTIVE', 'DORMANT', 'FROZEN', 'CLOSED')", name="chk_account_status"),
    )

    def __repr__(self):
        return f"<Account {self.account_id}: {self.account_number} ({self.account_status})>"


# ============================================================================
# 3. LOAN ENTITY
# ============================================================================
class Loan(Base):
    __tablename__ = "loans"

    loan_id = Column(String(32), primary_key=True)  # Format: LOAN-2026-000001
    account_id = Column(String(32), ForeignKey("accounts.account_id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id = Column(String(32), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False, index=True)
    loan_type = Column(String(32), nullable=False)  # PERSONAL, AUTO, HOME, BUSINESS
    principal_amount = Column(Numeric(12, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)  # e.g., 10.50%
    tenure_months = Column(Integer, nullable=False)
    loan_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    loan_status = Column(String(32), nullable=False, default="ACTIVE")  # ACTIVE, PAID_OFF, DEFAULTED, IN_COLLECTION, DISPUTED, HARDSHIP
    dispute_status = Column(String(32), nullable=False, default="NONE")  # NONE, OPEN, RESOLVED_UPHELD, RESOLVED_DISMISSED
    is_hardship = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    account = relationship("Account", back_populates="loans")
    customer = relationship("Customer", back_populates="loans")
    installments = relationship("Installment", back_populates="loan", cascade="all, delete-orphan", order_by="Installment.installment_number")
    payments = relationship("Payment", back_populates="loan", cascade="all, delete-orphan")
    delinquency_snapshots = relationship("DelinquencySnapshot", back_populates="loan", cascade="all, delete-orphan")
    collection_case = relationship("CollectionCase", back_populates="loan", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("principal_amount > 0", name="chk_loan_principal_positive"),
        CheckConstraint("tenure_months > 0", name="chk_loan_tenure_positive"),
        CheckConstraint("loan_status IN ('ACTIVE', 'PAID_OFF', 'DEFAULTED', 'IN_COLLECTION', 'DISPUTED', 'HARDSHIP')", name="chk_loan_status"),
        CheckConstraint("dispute_status IN ('NONE', 'OPEN', 'RESOLVED_UPHELD', 'RESOLVED_DISMISSED')", name="chk_loan_dispute_status"),
    )

    def __repr__(self):
        return f"<Loan {self.loan_id}: {self.loan_status} Principal={self.principal_amount}>"


# ============================================================================
# 4. INSTALLMENT ENTITY
# ============================================================================
class Installment(Base):
    __tablename__ = "installments"

    installment_id = Column(String(48), primary_key=True)  # Format: INS-LOAN-2026-000001-001
    loan_id = Column(String(32), ForeignKey("loans.loan_id", ondelete="CASCADE"), nullable=False, index=True)
    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    principal_component = Column(Numeric(12, 2), nullable=False)
    interest_component = Column(Numeric(12, 2), nullable=False)
    due_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    status = Column(String(32), nullable=False, default="PENDING")  # PENDING, PAID, PARTIALLY_PAID, OVERDUE
    paid_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    loan = relationship("Loan", back_populates="installments")
    allocations = relationship("PaymentAllocation", back_populates="installment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_installment_loan_num", "loan_id", "installment_number", unique=True),
        CheckConstraint("due_amount >= 0", name="chk_installment_due_nonnegative"),
        CheckConstraint("paid_amount >= 0", name="chk_installment_paid_nonnegative"),
        CheckConstraint("status IN ('PENDING', 'PAID', 'PARTIALLY_PAID', 'OVERDUE')", name="chk_installment_status"),
    )

    def __repr__(self):
        return f"<Installment {self.installment_id}: Due={self.due_date} Status={self.status} Balance={float(self.due_amount) - float(self.paid_amount)}>"


# ============================================================================
# 5. PAYMENT ENTITY
# ============================================================================
class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String(32), primary_key=True)  # Format: PMT-2026-000001
    loan_id = Column(String(32), ForeignKey("loans.loan_id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_date = Column(Date, nullable=False, index=True)
    payment_amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(32), nullable=False)  # UPI, NET_BANKING, DEBIT_CARD, AUTO_DEBIT, WIRE_TRANSFER, CASH
    payment_status = Column(String(32), nullable=False, default="SUCCESS")  # SUCCESS, PENDING, FAILED, REVERSED
    reference_number = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    loan = relationship("Loan", back_populates="payments")
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("payment_amount > 0", name="chk_payment_amount_positive"),
        CheckConstraint("payment_status IN ('SUCCESS', 'PENDING', 'FAILED', 'REVERSED')", name="chk_payment_status"),
    )

    def __repr__(self):
        return f"<Payment {self.payment_id}: Date={self.payment_date} Amount={self.payment_amount}>"


# ============================================================================
# 6. PAYMENT ALLOCATION (BRIDGE TABLE: Payment N <-> M Installment)
# ============================================================================
class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    allocation_id = Column(String(32), primary_key=True)  # Format: ALC-2026-000001
    payment_id = Column(String(32), ForeignKey("payments.payment_id", ondelete="CASCADE"), nullable=False, index=True)
    installment_id = Column(String(48), ForeignKey("installments.installment_id", ondelete="RESTRICT"), nullable=False, index=True)
    allocated_amount = Column(Numeric(12, 2), nullable=False)
    allocation_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    payment = relationship("Payment", back_populates="allocations")
    installment = relationship("Installment", back_populates="allocations")

    __table_args__ = (
        CheckConstraint("allocated_amount > 0", name="chk_alloc_amount_positive"),
        Index("idx_alloc_payment_installment", "payment_id", "installment_id"),
    )

    def __repr__(self):
        return f"<Allocation {self.allocation_id}: Payment={self.payment_id} -> Installment={self.installment_id} Amount={self.allocated_amount}>"


# ============================================================================
# 7. DELINQUENCY SNAPSHOT ENTITY
# ============================================================================
class DelinquencySnapshot(Base):
    __tablename__ = "delinquency_snapshots"

    snapshot_id = Column(String(48), primary_key=True)  # Format: SNP-LOAN-2026-000001-001
    loan_id = Column(String(32), ForeignKey("loans.loan_id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    days_past_due = Column(Integer, nullable=False, default=0)
    total_arrears = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    overdue_installments = Column(Integer, nullable=False, default=0)
    delinquency_bucket = Column(String(32), nullable=False, default="CURRENT")  # CURRENT, BUCKET_1_30, BUCKET_31_60, BUCKET_61_90, DEFAULT_90_PLUS
    risk_level = Column(String(16), nullable=False, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    loan = relationship("Loan", back_populates="delinquency_snapshots")

    __table_args__ = (
        Index("idx_snapshot_loan_date", "loan_id", "snapshot_date"),
        CheckConstraint("days_past_due >= 0", name="chk_snapshot_dpd_nonnegative"),
        CheckConstraint("total_arrears >= 0", name="chk_snapshot_arrears_nonnegative"),
        CheckConstraint("delinquency_bucket IN ('CURRENT', 'BUCKET_1_30', 'BUCKET_31_60', 'BUCKET_61_90', 'DEFAULT_90_PLUS')", name="chk_snapshot_bucket"),
        CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name="chk_snapshot_risk"),
    )

    def __repr__(self):
        return f"<DelinquencySnapshot {self.snapshot_id}: DPD={self.days_past_due} Arrears={self.total_arrears} Bucket={self.delinquency_bucket}>"


# ============================================================================
# 8. CONTACT PREFERENCE ENTITY
# ============================================================================
class ContactPreference(Base):
    __tablename__ = "contact_preferences"

    preference_id = Column(String(48), primary_key=True)  # Format: PREF-CUST-2026-000001-001
    customer_id = Column(String(32), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    preferred_channel = Column(String(32), nullable=False, default="PHONE")  # PHONE, SMS, EMAIL, WHATSAPP
    contact_start_time = Column(String(8), nullable=False, default="09:00:00")  # Permissible contact window start
    contact_end_time = Column(String(8), nullable=False, default="18:00:00")    # Permissible contact window end
    timezone = Column(String(32), nullable=False, default="Asia/Kolkata")
    contact_allowed = Column(Boolean, nullable=False, default=True)
    do_not_call = Column(Boolean, nullable=False, default=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="contact_preferences")

    __table_args__ = (
        CheckConstraint("preferred_channel IN ('PHONE', 'SMS', 'EMAIL', 'WHATSAPP')", name="chk_pref_channel"),
    )

    def __repr__(self):
        return f"<ContactPreference {self.preference_id}: Channel={self.preferred_channel} Window={self.contact_start_time}-{self.contact_end_time} Allowed={self.contact_allowed}>"


# ============================================================================
# 9. COLLECTION CASE ENTITY
# ============================================================================
class CollectionCase(Base):
    __tablename__ = "collection_cases"

    case_id = Column(String(32), primary_key=True)  # Format: COL-2026-000001
    loan_id = Column(String(32), ForeignKey("loans.loan_id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    customer_id = Column(String(32), ForeignKey("customers.customer_id", ondelete="RESTRICT"), nullable=False, index=True)
    outstanding_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    days_past_due = Column(Integer, nullable=False, default=0)
    priority_score = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))  # 0.00 to 100.00
    priority_level = Column(String(16), nullable=False, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    case_status = Column(String(32), nullable=False, default="OPEN")  # OPEN, CONTACT_SCHEDULED, PROMISE_ACTIVE, DISPUTED, HARDSHIP_HOLD, RESOLVED, CLOSED
    score_explanation = Column(Text, nullable=True)  # JSON or text breakdown of score factors
    assigned_to = Column(String(64), nullable=False, default="Unassigned")
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    loan = relationship("Loan", back_populates="collection_case")
    customer = relationship("Customer", back_populates="collection_cases")
    contact_attempts = relationship("ContactAttempt", back_populates="collection_case", cascade="all, delete-orphan", order_by="desc(ContactAttempt.contact_time)")
    promises_to_pay = relationship("PromiseToPay", back_populates="collection_case", cascade="all, delete-orphan", order_by="desc(PromiseToPay.created_at)")
    events = relationship("CaseEvent", back_populates="collection_case", cascade="all, delete-orphan", order_by="desc(CaseEvent.created_at)")

    __table_args__ = (
        CheckConstraint("priority_score >= 0.0 AND priority_score <= 100.0", name="chk_case_priority_score_range"),
        CheckConstraint("priority_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name="chk_case_priority_level"),
        CheckConstraint("case_status IN ('OPEN', 'CONTACT_SCHEDULED', 'PROMISE_ACTIVE', 'DISPUTED', 'HARDSHIP_HOLD', 'RESOLVED', 'CLOSED')", name="chk_case_status"),
    )

    def __repr__(self):
        return f"<CollectionCase {self.case_id}: Loan={self.loan_id} Score={self.priority_score} Level={self.priority_level} Status={self.case_status}>"


# ============================================================================
# 10. CONTACT ATTEMPT ENTITY
# ============================================================================
class ContactAttempt(Base):
    __tablename__ = "contact_attempts"

    contact_id = Column(String(48), primary_key=True)  # Format: CTP-COL-2026-000001-001
    case_id = Column(String(32), ForeignKey("collection_cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    contact_channel = Column(String(32), nullable=False)  # PHONE, SMS, EMAIL, WHATSAPP
    contact_time = Column(DateTime, nullable=False, index=True)
    outcome = Column(String(64), nullable=False)  # ANSWERED_PROMISED, ANSWERED_REFUSED, ANSWERED_DISPUTED, ANSWERED_CALLBACK_REQUESTED, NO_ANSWER, BUSY, INVALID_NUMBER, WRONG_PERSON
    notes = Column(Text, nullable=True)
    compliance_status = Column(String(32), nullable=False, default="COMPLIANT")  # COMPLIANT, VIOLATION_WINDOW, VIOLATION_DNC, VIOLATION_FREQUENCY
    agent_id = Column(String(64), nullable=False, default="SYSTEM")
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    collection_case = relationship("CollectionCase", back_populates="contact_attempts")

    __table_args__ = (
        CheckConstraint("contact_channel IN ('PHONE', 'SMS', 'EMAIL', 'WHATSAPP')", name="chk_contact_channel"),
        CheckConstraint("compliance_status IN ('COMPLIANT', 'VIOLATION_WINDOW', 'VIOLATION_DNC', 'VIOLATION_FREQUENCY')", name="chk_contact_compliance"),
    )

    def __repr__(self):
        return f"<ContactAttempt {self.contact_id}: Case={self.case_id} Outcome={self.outcome} Compliance={self.compliance_status}>"


# ============================================================================
# 11. PROMISE TO PAY ENTITY
# ============================================================================
class PromiseToPay(Base):
    __tablename__ = "promises_to_pay"

    promise_id = Column(String(48), primary_key=True)  # Format: PRM-COL-2026-000001-001
    case_id = Column(String(32), ForeignKey("collection_cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    promised_amount = Column(Numeric(12, 2), nullable=False)
    promised_date = Column(Date, nullable=False, index=True)
    grace_period_days = Column(Integer, nullable=False, default=3)
    status = Column(String(32), nullable=False, default="PENDING")  # PENDING, FULFILLED, PARTIALLY_FULFILLED, BROKEN, CANCELLED
    actual_paid_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    reconciled_payment_id = Column(String(32), nullable=True)
    reconciled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    collection_case = relationship("CollectionCase", back_populates="promises_to_pay")

    __table_args__ = (
        CheckConstraint("promised_amount > 0", name="chk_promise_amount_positive"),
        CheckConstraint("actual_paid_amount >= 0", name="chk_promise_actual_paid_nonnegative"),
        CheckConstraint("status IN ('PENDING', 'FULFILLED', 'PARTIALLY_FULFILLED', 'BROKEN', 'CANCELLED')", name="chk_promise_status"),
    )

    def __repr__(self):
        return f"<PromiseToPay {self.promise_id}: Amount={self.promised_amount} By={self.promised_date} Status={self.status} Paid={self.actual_paid_amount}>"


# ============================================================================
# 12. CASE EVENT (AUDIT TRAIL & STATE TRANSITION HISTORY)
# ============================================================================
class CaseEvent(Base):
    __tablename__ = "case_events"

    event_id = Column(String(48), primary_key=True)  # Format: EVT-COL-2026-000001-001
    case_id = Column(String(32), ForeignKey("collection_cases.case_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # CASE_CREATED, STATUS_CHANGED, SCORE_UPDATED, CONTACT_LOGGED, PROMISE_CREATED, PAYMENT_RECONCILED, DISPUTE_FLAGGED, COMPLIANCE_FLAGGED
    previous_state = Column(String(64), nullable=True)
    new_state = Column(String(64), nullable=False)
    reason = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)  # JSON payload with contextual details
    created_by = Column(String(64), nullable=False, default="SYSTEM")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    collection_case = relationship("CollectionCase", back_populates="events")

    def __repr__(self):
        return f"<CaseEvent {self.event_id}: Case={self.case_id} Type={self.event_type} {self.previous_state}->{self.new_state}>"
