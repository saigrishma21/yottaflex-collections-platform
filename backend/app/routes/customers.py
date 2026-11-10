"""Customer API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.entities import Customer
from backend.app.schemas.schemas import CustomerDetail

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("", response_model=List[CustomerDetail])
def list_customers(
    skip: int = 0,
    limit: int = 50,
    risk: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve paginated list of customers with optional risk filter."""
    query = db.query(Customer)
    if risk and isinstance(risk, str):
        query = query.filter(Customer.risk_segment == risk.upper())
    return query.offset(skip).limit(limit).all()


@router.get("/{customer_id}", response_model=CustomerDetail)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Retrieve customer details by ID."""
    cust = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")
    return cust
