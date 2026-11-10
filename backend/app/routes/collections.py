"""Collection Cases & Operations Workflow API Endpoints."""

import json
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models.entities import (
    CollectionCase,
    Customer,
    Loan,
    Installment,
    ContactAttempt,
    ContactPreference,
    PromiseToPay,
    CaseEvent,
)
from backend.app.schemas.schemas import (
    CollectionCaseListItem,
    CollectionCaseDetail,
    ContactAttemptCreate,
    ContactAttemptSchema,
    PromiseToPayCreate,
    PromiseToPaySchema,
)
from backend.app.services.contact_scheduler import validate_contact_schedule

router = APIRouter(prefix="/api/collections", tags=["Collections"])


@router.get("", response_model=List[CollectionCaseListItem])
def list_cases(
    skip: int = 0,
    limit: int = 50,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve collection cases with optional priority, status, and search filters."""
    query = (
        db.query(
            CollectionCase,
            Customer.first_name,
            Customer.last_name,
        )
        .join(Customer, CollectionCase.customer_id == Customer.customer_id)
    )

    if priority and isinstance(priority, str) and priority.strip().upper() != "ALL":
        query = query.filter(CollectionCase.priority_level == priority.strip().upper())
    
    # Status filtering: Default to active collection pipeline (exclude settled/resolved/closed)
    if status and isinstance(status, str):
        if status.strip().upper() != "ALL":
            query = query.filter(CollectionCase.case_status == status.strip().upper())
    else:
        query = query.filter(CollectionCase.case_status.notin_(["RESOLVED", "CLOSED"]))

    if search and isinstance(search, str):
        query = query.filter(
            (CollectionCase.case_id.ilike(f"%{search}%"))
            | (CollectionCase.loan_id.ilike(f"%{search}%"))
            | (Customer.first_name.ilike(f"%{search}%"))
            | (Customer.last_name.ilike(f"%{search}%"))
        )

    results = (
        query.order_by(desc(CollectionCase.priority_score))
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = []
    for case, first, last in results:
        item = CollectionCaseListItem.model_validate(case)
        item.customer_name = f"{first} {last}"
        items.append(item)
    return items


@router.get("/priority", response_model=List[CollectionCaseListItem])
def get_priority_worklist(
    limit: int = 25,
    db: Session = Depends(get_db),
):
    """Retrieve top-ranked collection accounts prioritized for collector outreach."""
    query = (
        db.query(
            CollectionCase,
            Customer.first_name,
            Customer.last_name,
        )
        .join(Customer, CollectionCase.customer_id == Customer.customer_id)
        .filter(CollectionCase.case_status.in_(["OPEN", "CONTACT_SCHEDULED"]))
    )
    results = (
        query.order_by(desc(CollectionCase.priority_score))
        .limit(limit)
        .all()
    )

    items = []
    for case, first, last in results:
        item = CollectionCaseListItem.model_validate(case)
        item.customer_name = f"{first} {last}"
        items.append(item)
    return items


@router.get("/{case_id}", response_model=CollectionCaseDetail)
def get_case_detail(case_id: str, db: Session = Depends(get_db)):
    """Retrieve full 360-degree case dossier including borrower, loan, contact history, and audit log."""
    case = db.query(CollectionCase).filter(CollectionCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Collection case not found")

    customer = db.query(Customer).filter(Customer.customer_id == case.customer_id).first()
    loan = db.query(Loan).filter(Loan.loan_id == case.loan_id).first()
    installments = db.query(Installment).filter(Installment.loan_id == case.loan_id).order_by(Installment.installment_number).all()
    attempts = db.query(ContactAttempt).filter(ContactAttempt.case_id == case_id).order_by(desc(ContactAttempt.contact_time)).all()
    promises = db.query(PromiseToPay).filter(PromiseToPay.case_id == case_id).order_by(desc(PromiseToPay.created_at)).all()
    events = db.query(CaseEvent).filter(CaseEvent.case_id == case_id).order_by(desc(CaseEvent.created_at)).all()

    explanation = None
    if case.score_explanation:
        try:
            explanation = json.loads(case.score_explanation)
        except Exception:
            explanation = {"raw": case.score_explanation}

    case_item = CollectionCaseListItem.model_validate(case)
    if customer:
        case_item.customer_name = f"{customer.first_name} {customer.last_name}"

    return {
        "case": case_item,
        "score_explanation": explanation,
        "customer": customer,
        "loan": loan,
        "installments": installments,
        "contact_attempts": attempts,
        "promises_to_pay": promises,
        "events": events,
    }


@router.post("/{case_id}/contact", response_model=ContactAttemptSchema)
def record_contact_attempt(
    case_id: str,
    payload: ContactAttemptCreate,
    db: Session = Depends(get_db),
):
    """Log an outreach attempt with statutory contact window and consent verification."""
    case = db.query(CollectionCase).filter(CollectionCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Collection case not found")

    # Check preferences
    pref = db.query(ContactPreference).filter(ContactPreference.customer_id == case.customer_id).first()
    contact_dt = payload.contact_time or datetime.now()

    compliance_status = "COMPLIANT"
    if pref:
        recent_atts = db.query(ContactAttempt).filter(ContactAttempt.case_id == case_id).all()
        check = validate_contact_schedule(pref, contact_dt, recent_attempts=recent_atts)
        if not check["allowed"]:
            compliance_status = check["status"]

    ctp_count = db.query(ContactAttempt).filter(ContactAttempt.case_id == case_id).count()
    ctp_id = f"CTP-{case_id}-{ctp_count + 1:03d}"

    attempt = ContactAttempt(
        contact_id=ctp_id,
        case_id=case_id,
        contact_channel=payload.contact_channel,
        contact_time=contact_dt,
        outcome=payload.outcome,
        notes=payload.notes,
        compliance_status=compliance_status,
        agent_id=payload.agent_id,
        created_at=datetime.utcnow(),
    )
    db.add(attempt)

    # Log immutable audit event
    evt_count = db.query(CaseEvent).filter(CaseEvent.case_id == case_id).count()
    evt = CaseEvent(
        event_id=f"EVT-{case_id}-{evt_count + 1:03d}",
        case_id=case_id,
        event_type="CONTACT_LOGGED",
        previous_state=case.case_status,
        new_state=case.case_status,
        reason=f"Contact attempt logged via {payload.contact_channel}. Outcome: {payload.outcome} (Compliance: {compliance_status})",
        metadata_json=json.dumps({"compliance_status": compliance_status, "outcome": payload.outcome}),
        created_by=payload.agent_id,
        created_at=datetime.utcnow(),
    )
    db.add(evt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.post("/{case_id}/promise", response_model=PromiseToPaySchema)
def record_promise_to_pay(
    case_id: str,
    payload: PromiseToPayCreate,
    db: Session = Depends(get_db),
):
    """Record borrower promise to pay with predatory commitment ceiling validation."""
    case = db.query(CollectionCase).filter(CollectionCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Collection case not found")

    # Guard: Promise amount cannot exceed 200% of outstanding arrears
    if case.outstanding_amount > Decimal("0.00") and payload.promised_amount > (case.outstanding_amount * Decimal("2.0")):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid commitment amount: Promised ₹{payload.promised_amount:,.2f} exceeds reasonable arrears ceiling (Max ₹{(case.outstanding_amount * Decimal('2.0')):,.2f}).",
        )

    prm_count = db.query(PromiseToPay).filter(PromiseToPay.case_id == case_id).count()
    prm_id = f"PRM-{case_id}-{prm_count + 1:03d}"

    promise = PromiseToPay(
        promise_id=prm_id,
        case_id=case_id,
        promised_amount=payload.promised_amount,
        promised_date=payload.promised_date,
        grace_period_days=payload.grace_period_days,
        status="PENDING",
        actual_paid_amount=Decimal("0.00"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(promise)

    # Transition case state to PROMISE_ACTIVE
    prev_status = case.case_status
    case.case_status = "PROMISE_ACTIVE"
    case.updated_at = datetime.utcnow()

    # Log immutable audit event
    evt_count = db.query(CaseEvent).filter(CaseEvent.case_id == case_id).count()
    evt = CaseEvent(
        event_id=f"EVT-{case_id}-{evt_count + 1:03d}",
        case_id=case_id,
        event_type="PROMISE_CREATED",
        previous_state=prev_status,
        new_state="PROMISE_ACTIVE",
        reason=f"Borrower committed to pay ₹{payload.promised_amount:,.2f} by {payload.promised_date}",
        metadata_json=json.dumps({"promise_id": prm_id, "amount": float(payload.promised_amount)}),
        created_by="Agent_Alpha",
        created_at=datetime.utcnow(),
    )
    db.add(evt)
    db.commit()
    db.refresh(promise)
    return promise
