"""Database table initialization script.
Creates all 12 tables (10 core entities + PaymentAllocation + CaseEvent) in hackathon.db.
"""

import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.database import engine, Base
from backend.app.models.entities import (
    Customer,
    Account,
    Loan,
    Installment,
    Payment,
    PaymentAllocation,
    DelinquencySnapshot,
    ContactPreference,
    CollectionCase,
    ContactAttempt,
    PromiseToPay,
    CaseEvent,
)


def create_all_tables():
    """Create all tables in the database."""
    print("Connecting to database and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Successfully created all tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")


def drop_all_tables():
    """Drop all tables in the database (used for clean resets/testing)."""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped successfully.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        drop_all_tables()
    create_all_tables()

