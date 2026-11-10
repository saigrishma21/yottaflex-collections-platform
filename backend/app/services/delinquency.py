"""Delinquency calculation engine: Computes DPD, total arrears, and delinquency aging buckets.
"""

from datetime import date
from decimal import Decimal
from typing import List, Dict, Any
from backend.app.models.entities import Installment


def calculate_delinquency(
    installments: List[Installment],
    as_of_date: date = None,
) -> Dict[str, Any]:
    """Calculate Days Past Due (DPD), Total Arrears, and Delinquency Bucket.

    Mathematical Definition:
      DPD = (as_of_date - oldest_unpaid_due_date) for installments where due_date <= as_of_date
      Arrears = sum(due_amount - paid_amount) for installments where due_date <= as_of_date and due > paid
    """
    if as_of_date is None:
        as_of_date = date(2026, 10, 31)

    overdue_unpaid = [
        inst for inst in installments
        if inst.due_date <= as_of_date and inst.due_amount > inst.paid_amount
    ]

    if not overdue_unpaid:
        return {
            "days_past_due": 0,
            "total_arrears": Decimal("0.00"),
            "overdue_installments_count": 0,
            "delinquency_bucket": "CURRENT",
            "oldest_unpaid_due_date": None,
        }

    overdue_unpaid.sort(key=lambda x: x.due_date)
    oldest_due = overdue_unpaid[0].due_date
    dpd = max(0, (as_of_date - oldest_due).days)
    total_arrears = sum((inst.due_amount - inst.paid_amount) for inst in overdue_unpaid)

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

    return {
        "days_past_due": dpd,
        "total_arrears": total_arrears,
        "overdue_installments_count": len(overdue_unpaid),
        "delinquency_bucket": bucket,
        "oldest_unpaid_due_date": oldest_due,
    }
