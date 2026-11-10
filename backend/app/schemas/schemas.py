"""Pydantic request and response schemas for REST APIs."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Customer Schemas
# ============================================================================
class CustomerBase(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    city: str
    state: str
    postal_code: str
    risk_segment: str


class CustomerDetail(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    address: Optional[str] = None
    created_at: datetime


# ============================================================================
# Loan & Installment Schemas
# ============================================================================
class InstallmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    installment_id: str
    loan_id: str
    installment_number: int
    due_date: date
    due_amount: Decimal
    paid_amount: Decimal
    status: str
    paid_date: Optional[date] = None


class LoanSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    loan_id: str
    account_id: str
    customer_id: str
    loan_type: str
    principal_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    loan_date: date
    maturity_date: date
    loan_status: str
    dispute_status: str
    is_hardship: bool


# ============================================================================
# Collection Case Schemas
# ============================================================================
class ContactAttemptCreate(BaseModel):
    contact_channel: str = Field(..., json_schema_extra={"example": "PHONE"})
    contact_time: Optional[datetime] = None
    outcome: str = Field(..., json_schema_extra={"example": "ANSWERED_PROMISED"})
    notes: Optional[str] = None
    agent_id: str = Field(default="Agent_Alpha")


class ContactAttemptSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    contact_id: str
    case_id: str
    contact_channel: str
    contact_time: datetime
    outcome: str
    notes: Optional[str] = None
    compliance_status: str
    agent_id: str


class PromiseToPayCreate(BaseModel):
    promised_amount: Decimal = Field(..., gt=0, json_schema_extra={"example": 5000.00})
    promised_date: date = Field(..., json_schema_extra={"example": "2026-11-15"})
    grace_period_days: int = Field(default=3)


class PromiseToPaySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    promise_id: str
    case_id: str
    promised_amount: Decimal
    promised_date: date
    grace_period_days: int
    status: str
    actual_paid_amount: Decimal
    reconciled_payment_id: Optional[str] = None
    reconciled_at: Optional[datetime] = None
    created_at: datetime


class CaseEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: str
    case_id: str
    event_type: str
    previous_state: Optional[str] = None
    new_state: str
    reason: str
    created_by: str
    created_at: datetime


class CollectionCaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    case_id: str
    loan_id: str
    customer_id: str
    customer_name: Optional[str] = None
    outstanding_amount: Decimal
    days_past_due: int
    priority_score: Decimal
    priority_level: str
    case_status: str
    assigned_to: str
    created_at: datetime


class CollectionCaseDetail(BaseModel):
    case: CollectionCaseListItem
    score_explanation: Optional[Dict[str, Any]] = None
    customer: CustomerDetail
    loan: LoanSchema
    installments: List[InstallmentSchema]
    contact_attempts: List[ContactAttemptSchema]
    promises_to_pay: List[PromiseToPaySchema]
    events: List[CaseEventSchema]


# ============================================================================
# Dashboard & Compliance Schemas
# ============================================================================
class DashboardSummary(BaseModel):
    total_customers: int
    total_loans: int
    total_outstanding_delinquent: Decimal
    active_cases_count: int
    critical_cases_count: int
    compliance_issues_count: int
    promises_fulfilled_rate: float


class ComplianceViolationItem(BaseModel):
    violation_code: str
    category: str
    severity: str
    record_id: str
    entity_type: str
    description: str
    recommended_action: str


class CreateCaseRequest(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = "9876543210"
    email: Optional[str] = None
    city: Optional[str] = "Mumbai"
    state: Optional[str] = "Maharashtra"
    postal_code: Optional[str] = "400001"
    risk_segment: str = "HIGH"
    loan_type: str = "PERSONAL"
    principal_amount: Decimal = Decimal("500000.00")
    total_arrears: Decimal = Decimal("150000.00")
    days_past_due: int = 120
    target_priority: Optional[str] = None  # None for auto-score, or 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'


class OverridePriorityRequest(BaseModel):
    priority_level: str
    reason: Optional[str] = "Manual tier override by operations analyst"
