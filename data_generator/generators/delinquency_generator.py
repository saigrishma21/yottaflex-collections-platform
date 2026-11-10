"""Delinquency Snapshot generator: Mathematically derives DPD, arrears, and risk tiers from installment schedules.
"""

from datetime import datetime
from decimal import Decimal
from backend.app.models.entities import DelinquencySnapshot
from data_generator.config import SIMULATION_END_DATE


def generate_delinquency_snapshots(loans, installments, customers):
    """Derive delinquency snapshots directly from source installment records."""
    snapshots = []

    # Map customers by customer_id
    customer_map = {c.customer_id: c for c in customers}

    # Group installments by loan_id
    installments_by_loan = {}
    for inst in installments:
        installments_by_loan.setdefault(inst.loan_id, []).append(inst)

    for loan in loans:
        loan_insts = installments_by_loan.get(loan.loan_id, [])
        customer = customer_map.get(loan.customer_id)

        # Filter overdue unpaid installments as of SIMULATION_END_DATE
        overdue_unpaid = [
            i for i in loan_insts
            if i.due_date <= SIMULATION_END_DATE and i.due_amount > i.paid_amount
        ]

        if overdue_unpaid:
            # Sort chronologically to find oldest unpaid installment
            overdue_unpaid.sort(key=lambda x: x.due_date)
            oldest_due_date = overdue_unpaid[0].due_date
            dpd = (SIMULATION_END_DATE - oldest_due_date).days
            total_arrears = sum(i.due_amount - i.paid_amount for i in overdue_unpaid)
            overdue_count = len(overdue_unpaid)
        else:
            dpd = 0
            total_arrears = Decimal("0.00")
            overdue_count = 0

        # Classify regulatory delinquency bucket
        if dpd == 0:
            bucket = "CURRENT"
        elif 1 <= dpd <= 30:
            bucket = "BUCKET_1_30"
        elif 31 <= dpd <= 60:
            bucket = "BUCKET_31_60"
        elif 61 <= dpd <= 90:
            bucket = "BUCKET_61_90"
        else:
            bucket = "DEFAULT_90_PLUS"

        # Determine composite risk level
        cust_risk = customer.risk_segment if customer else "MEDIUM"
        if dpd > 90 or (dpd > 60 and cust_risk == "HIGH"):
            risk_level = "CRITICAL"
        elif dpd > 30 or (dpd > 0 and cust_risk == "HIGH"):
            risk_level = "HIGH"
        elif dpd > 0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        snapshot = DelinquencySnapshot(
            snapshot_id=f"SNP-{loan.loan_id}-001",
            loan_id=loan.loan_id,
            snapshot_date=SIMULATION_END_DATE,
            days_past_due=dpd,
            total_arrears=total_arrears,
            overdue_installments=overdue_count,
            delinquency_bucket=bucket,
            risk_level=risk_level,
            created_at=datetime.combine(SIMULATION_END_DATE, datetime.min.time()),
        )
        snapshots.append(snapshot)

    return snapshots
