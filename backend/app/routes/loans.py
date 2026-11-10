"""Loans & Installments API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.entities import Loan, Installment, Payment
from backend.app.schemas.schemas import LoanSchema, InstallmentSchema

router = APIRouter(prefix="/api/loans", tags=["Loans"])


@router.get("", response_model=List[LoanSchema])
def list_loans(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    loan_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve paginated list of loans with optional status filter."""
    query = db.query(Loan)
    if status and isinstance(status, str):
        query = query.filter(Loan.loan_status == status.upper())
    if loan_type and isinstance(loan_type, str):
        query = query.filter(Loan.loan_type == loan_type.upper())
    return query.offset(skip).limit(limit).all()


@router.get("/{loan_id}", response_model=LoanSchema)
def get_loan(loan_id: str, db: Session = Depends(get_db)):
    """Retrieve loan by ID."""
    loan = db.query(Loan).filter(Loan.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@router.get("/{loan_id}/installments", response_model=List[InstallmentSchema])
def get_loan_installments(loan_id: str, db: Session = Depends(get_db)):
    """Retrieve repayment schedule for a loan."""
    return db.query(Installment).filter(Installment.loan_id == loan_id).order_by(Installment.installment_number).all()
