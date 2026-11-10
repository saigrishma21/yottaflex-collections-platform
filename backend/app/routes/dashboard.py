"""Dashboard Statistics & Analytics API Endpoints."""

from decimal import Decimal
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models.entities import (
    Customer,
    Loan,
    CollectionCase,
    DelinquencySnapshot,
    PromiseToPay,
)
from backend.app.schemas.schemas import DashboardSummary, PromiseToPaySchema
from backend.app.services.compliance import scan_compliance_violations

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Retrieve executive summary KPIs for top metrics bar."""
    total_cust = db.query(func.count(Customer.customer_id)).scalar() or 0
    total_loans = db.query(func.count(Loan.loan_id)).scalar() or 0
    total_arrears = db.query(func.sum(CollectionCase.outstanding_amount)).scalar() or Decimal("0.00")
    active_cases = db.query(func.count(CollectionCase.case_id)).filter(CollectionCase.case_status.in_(["OPEN", "CONTACT_SCHEDULED", "PROMISE_ACTIVE"])).scalar() or 0
    critical_cases = db.query(func.count(CollectionCase.case_id)).filter(
        CollectionCase.case_status.in_(["OPEN", "CONTACT_SCHEDULED", "PROMISE_ACTIVE"]),
        CollectionCase.priority_level == "CRITICAL"
    ).scalar() or 0

    # Promise fulfillment rate
    total_promises = db.query(func.count(PromiseToPay.promise_id)).scalar() or 0
    fulfilled_promises = db.query(func.count(PromiseToPay.promise_id)).filter(PromiseToPay.status == "FULFILLED").scalar() or 0
    fulfillment_rate = (fulfilled_promises / total_promises * 100.0) if total_promises > 0 else 0.0

    # Compliance issues
    violations = scan_compliance_violations(db)

    return {
        "total_customers": total_cust,
        "total_loans": total_loans,
        "total_outstanding_delinquent": total_arrears,
        "active_cases_count": active_cases,
        "critical_cases_count": critical_cases,
        "compliance_issues_count": len(violations),
        "promises_fulfilled_rate": round(fulfillment_rate, 1),
    }


@router.get("/dashboard/metrics")
def get_dashboard_chart_metrics(db: Session = Depends(get_db)):
    """Retrieve aggregations for dashboard charts (Delinquency Buckets, Priority, Loan Types)."""
    # 1. Delinquency Buckets
    bucket_counts = (
        db.query(DelinquencySnapshot.delinquency_bucket, func.count(DelinquencySnapshot.snapshot_id))
        .group_by(DelinquencySnapshot.delinquency_bucket)
        .all()
    )
    bucket_data = [{"bucket": b, "count": c} for b, c in bucket_counts]

    # 2. Priority Distribution
    priority_counts = (
        db.query(CollectionCase.priority_level, func.count(CollectionCase.case_id))
        .group_by(CollectionCase.priority_level)
        .all()
    )
    priority_data = [{"level": p, "count": c} for p, c in priority_counts]

    # 3. Loan Status Distribution
    status_counts = (
        db.query(Loan.loan_status, func.count(Loan.loan_id))
        .group_by(Loan.loan_status)
        .all()
    )
    status_data = [{"status": s, "count": c} for s, c in status_counts]

    return {
        "delinquency_buckets": bucket_data,
        "priority_distribution": priority_data,
        "loan_status_distribution": status_data,
    }


@router.get("/promises", response_model=List[PromiseToPaySchema])
def list_promises(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
):
    """Retrieve promises to pay commitments."""
    query = db.query(PromiseToPay)
    if status:
        query = query.filter(PromiseToPay.status == status.upper())
    return query.order_by(PromiseToPay.promised_date).offset(skip).limit(limit).all()

