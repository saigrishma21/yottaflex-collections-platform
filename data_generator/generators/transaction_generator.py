"""Transaction generator: Generates realistic payments, payment allocations, and reconciles installment balances.
"""

from datetime import timedelta, datetime
from decimal import Decimal, ROUND_HALF_UP
import random
from backend.app.models.entities import Payment, PaymentAllocation
from data_generator.config import SIMULATION_END_DATE, PAYMENT_METHOD_WEIGHTS


def generate_transactions(loans, installments, seed: int):
    """Simulate payments and bridge table allocations matching loan statuses."""
    random.seed(seed)
    payments = []
    allocations = []

    # Map installments by loan_id
    installments_by_loan = {}
    for inst in installments:
        installments_by_loan.setdefault(inst.loan_id, []).append(inst)

    # Sort each loan's installments by installment_number
    for l_id in installments_by_loan:
        installments_by_loan[l_id].sort(key=lambda x: x.installment_number)

    payment_counter = 1
    allocation_counter = 1

    methods = list(PAYMENT_METHOD_WEIGHTS.keys())
    method_w = list(PAYMENT_METHOD_WEIGHTS.values())

    for loan in loans:
        loan_insts = installments_by_loan.get(loan.loan_id, [])

        for inst in loan_insts:
            is_past_due = inst.due_date <= SIMULATION_END_DATE

            if not is_past_due:
                inst.status = "PENDING"
                continue

            # Determine payment behavior by loan status
            if loan.loan_status == "PAID_OFF":
                # Paid in full on or slightly before due date
                pmt_date = inst.due_date - timedelta(days=random.randint(0, 5))
                pmt_amount = inst.due_amount
                should_pay = True
                is_partial = False
            elif loan.loan_status == "ACTIVE":
                # Current on payments
                pmt_date = inst.due_date - timedelta(days=random.randint(0, 3))
                pmt_amount = inst.due_amount
                should_pay = True
                is_partial = False
            elif loan.loan_status == "HARDSHIP":
                # Partial payment on some installments
                if random.random() < 0.60:
                    pmt_date = inst.due_date + timedelta(days=random.randint(2, 15))
                    pmt_amount = (inst.due_amount * Decimal("0.40")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    should_pay = True
                    is_partial = True
                else:
                    should_pay = False
            elif loan.loan_status in ("IN_COLLECTION", "DEFAULTED", "DISPUTED"):
                # Either missed entirely or small partial payment on earlier installments
                if inst.installment_number == 1 and random.random() < 0.40:
                    pmt_date = inst.due_date + timedelta(days=random.randint(5, 20))
                    pmt_amount = (inst.due_amount * Decimal("0.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    should_pay = True
                    is_partial = True
                else:
                    should_pay = False
            else:
                should_pay = False

            if should_pay and pmt_amount > Decimal("0.00"):
                pmt_id = f"PMT-2026-{payment_counter:06d}"
                payment_counter += 1
                method = random.choices(methods, weights=method_w, k=1)[0]
                ref_num = f"TXN{202600000000 + payment_counter}"

                payment = Payment(
                    payment_id=pmt_id,
                    loan_id=loan.loan_id,
                    payment_date=pmt_date,
                    payment_amount=pmt_amount,
                    payment_method=method,
                    payment_status="SUCCESS",
                    reference_number=ref_num,
                    created_at=datetime.combine(pmt_date, datetime.min.time()),
                )
                payments.append(payment)

                # Create allocation bridge entry
                alc_id = f"ALC-2026-{allocation_counter:06d}"
                allocation_counter += 1

                allocation = PaymentAllocation(
                    allocation_id=alc_id,
                    payment_id=pmt_id,
                    installment_id=inst.installment_id,
                    allocated_amount=pmt_amount,
                    allocation_date=pmt_date,
                    created_at=datetime.combine(pmt_date, datetime.min.time()),
                )
                allocations.append(allocation)

                # Reconcile installment
                inst.paid_amount += pmt_amount
                if inst.paid_amount >= inst.due_amount:
                    inst.status = "PAID"
                    inst.paid_date = pmt_date
                else:
                    inst.status = "PARTIALLY_PAID"
            else:
                # No payment made
                if inst.paid_amount == Decimal("0.00"):
                    inst.status = "OVERDUE"
                elif inst.paid_amount < inst.due_amount:
                    inst.status = "PARTIALLY_PAID"

    return payments, allocations
