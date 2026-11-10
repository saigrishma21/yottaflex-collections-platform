"""Schedule generator: Generates exact loan repayment amortization schedules (Installments).
"""

from datetime import timedelta, datetime
from decimal import Decimal, ROUND_HALF_UP
from backend.app.models.entities import Installment


def generate_installments(loans, total_target_installments: int):
    """Generate installment schedule matching the exact required target volume."""
    installments = []
    installments_per_loan = total_target_installments // len(loans)

    for loan in loans:
        # Simple interest amortization per installment
        monthly_rate = (loan.interest_rate / Decimal("100")) / Decimal("12")
        principal_part = (loan.principal_amount / Decimal(loan.tenure_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        interest_part = (loan.principal_amount * monthly_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        due_amount = principal_part + interest_part

        for num in range(1, installments_per_loan + 1):
            inst_id = f"INS-{loan.loan_id}-{num:03d}"
            due_date = loan.loan_date + timedelta(days=num * 30)

            installment = Installment(
                installment_id=inst_id,
                loan_id=loan.loan_id,
                installment_number=num,
                due_date=due_date,
                principal_component=principal_part,
                interest_component=interest_part,
                due_amount=due_amount,
                paid_amount=Decimal("0.00"),
                status="PENDING",
                paid_date=None,
                created_at=datetime.combine(loan.loan_date, datetime.min.time()),
            )
            installments.append(installment)

    return installments

