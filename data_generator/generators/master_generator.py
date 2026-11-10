"""Master entity generator: Customers, Accounts, Loans, and ContactPreferences.
Uses seeded random and Faker generators to guarantee 100% deterministic reproducibility.
"""

from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
import random
from faker import Faker
from backend.app.models.entities import Customer, Account, Loan, ContactPreference
from data_generator.config import (
    SIMULATION_START_DATE,
    SIMULATION_END_DATE,
    LOAN_STATUS_WEIGHTS,
    LOAN_TYPE_WEIGHTS,
)


def generate_master_records(scale_config, seed: int):
    """Generate master records: Customers, Accounts, Loans, and Contact Preferences."""
    fake = Faker("en_IN")
    Faker.seed(seed)
    random.seed(seed)

    num_customers = scale_config["num_customers"]
    num_accounts = scale_config["num_accounts"]
    num_loans = scale_config["num_loans"]

    customers = []
    accounts = []
    loans = []
    contact_preferences = []

    # 1. GENERATE CUSTOMERS
    risk_segments = ["LOW", "MEDIUM", "HIGH"]
    risk_weights = [0.50, 0.35, 0.15]

    for i in range(1, num_customers + 1):
        cust_id = f"CUST-2026-{i:06d}"
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}.{i}@example.com"
        phone = f"+919{random.randint(100000000, 999999999)}"
        city = fake.city()
        state = fake.state()
        postal_code = fake.postcode()
        risk_segment = random.choices(risk_segments, weights=risk_weights, k=1)[0]

        customer = Customer(
            customer_id=cust_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=fake.street_address(),
            city=city,
            state=state,
            postal_code=postal_code,
            risk_segment=risk_segment,
            created_at=datetime(2025, 10, 1, 10, 0, 0),
            updated_at=datetime(2025, 10, 1, 10, 0, 0),
        )
        customers.append(customer)

        # Generate 1 ContactPreference per Customer
        channels = ["PHONE", "SMS", "EMAIL", "WHATSAPP"]
        pref_channel = random.choices(channels, weights=[0.50, 0.25, 0.15, 0.10], k=1)[0]
        # Standard fair contact windows (e.g. 09:00 - 18:00, or 10:00 - 17:00)
        window_options = [
            ("09:00:00", "18:00:00"),
            ("10:00:00", "19:00:00"),
            ("09:30:00", "17:30:00"),
        ]
        start_time, end_time = random.choice(window_options)
        # ~2% DNC borrowers
        do_not_call = random.random() < 0.02
        contact_allowed = not do_not_call

        preference = ContactPreference(
            preference_id=f"PREF-{cust_id}-001",
            customer_id=cust_id,
            preferred_channel=pref_channel,
            contact_start_time=start_time,
            contact_end_time=end_time,
            timezone="Asia/Kolkata",
            contact_allowed=contact_allowed,
            do_not_call=do_not_call,
            effective_from=date(2025, 10, 1),
            effective_to=None,
            created_at=datetime(2025, 10, 1, 10, 0, 0),
        )
        contact_preferences.append(preference)

    # 2. GENERATE ACCOUNTS (1 to N per customer)
    account_types = ["SAVINGS", "CURRENT", "SALARY"]
    for i in range(1, num_accounts + 1):
        acc_id = f"ACC-2026-{i:06d}"
        cust_index = (i - 1) % num_customers
        owner_cust = customers[cust_index]
        acc_type = random.choices(account_types, weights=[0.70, 0.20, 0.10], k=1)[0]
        acc_number = f"ACC{2026000000 + i}"

        account = Account(
            account_id=acc_id,
            customer_id=owner_cust.customer_id,
            account_number=acc_number,
            account_type=acc_type,
            account_status="ACTIVE",
            opened_date=date(2025, 10, 15),
            created_at=datetime(2025, 10, 15, 12, 0, 0),
        )
        accounts.append(account)

    # 3. GENERATE LOANS
    loan_types = list(LOAN_TYPE_WEIGHTS.keys())
    loan_type_w = list(LOAN_TYPE_WEIGHTS.values())

    loan_statuses = list(LOAN_STATUS_WEIGHTS.keys())
    loan_status_w = list(LOAN_STATUS_WEIGHTS.values())

    # Pre-calculated dates across the 12-month simulation
    sim_days = (SIMULATION_END_DATE - SIMULATION_START_DATE).days

    for i in range(1, num_loans + 1):
        loan_id = f"LOAN-2026-{i:06d}"
        acc = accounts[(i - 1) % len(accounts)]
        cust_id = acc.customer_id

        l_type = random.choices(loan_types, weights=loan_type_w, k=1)[0]
        l_status = random.choices(loan_statuses, weights=loan_status_w, k=1)[0]

        # Loan principal tiers based on loan type
        if l_type == "PERSONAL":
            principal = Decimal(random.choice([25000, 50000, 75000, 100000, 150000]))
            rate = Decimal(random.choice(["11.50", "12.00", "13.50", "14.00"]))
        elif l_type == "AUTO":
            principal = Decimal(random.choice([150000, 250000, 400000, 600000]))
            rate = Decimal(random.choice(["9.00", "9.50", "10.00", "10.50"]))
        elif l_type == "HOME":
            principal = Decimal(random.choice([1000000, 1500000, 2500000]))
            rate = Decimal(random.choice(["8.25", "8.50", "8.75"]))
        else:  # BUSINESS
            principal = Decimal(random.choice([200000, 500000, 800000, 1200000]))
            rate = Decimal(random.choice(["12.50", "14.00", "15.00"]))

        # Stagger loan origination dates across simulation
        days_offset = (i * 7) % (sim_days - 120)
        origination_date = SIMULATION_START_DATE + timedelta(days=days_offset)

        # Tenure: 3 to 12 months (averaging ~3 installments active in window)
        tenure_months = 3 if scale_config["num_installments"] // num_loans == 3 else random.choice([3, 4, 6])
        maturity_date = origination_date + timedelta(days=tenure_months * 30)

        dispute_status = "OPEN" if l_status == "DISPUTED" else "NONE"
        is_hardship = (l_status == "HARDSHIP")

        loan = Loan(
            loan_id=loan_id,
            account_id=acc.account_id,
            customer_id=cust_id,
            loan_type=l_type,
            principal_amount=principal,
            interest_rate=rate,
            tenure_months=tenure_months,
            loan_date=origination_date,
            maturity_date=maturity_date,
            loan_status=l_status,
            dispute_status=dispute_status,
            is_hardship=is_hardship,
            created_at=datetime.combine(origination_date, datetime.min.time()),
            updated_at=datetime.combine(origination_date, datetime.min.time()),
        )
        loans.append(loan)

    return customers, accounts, loans, contact_preferences

