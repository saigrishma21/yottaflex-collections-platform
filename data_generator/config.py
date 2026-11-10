"""Configuration presets for synthetic data generation."""

from datetime import date

# Fixed deterministic seed for exact reproducibility
DEFAULT_RANDOM_SEED = 20261022

# Simulation observation window (12 months: Nov 1, 2025 to Oct 31, 2026)
SIMULATION_START_DATE = date(2025, 11, 1)
SIMULATION_END_DATE = date(2026, 10, 31)

# Scale Presets
SCALE_CONFIGS = {
    # Lightweight preset for rapid testing, development, and unit test verification
    "starter": {
        "num_customers": 80,
        "num_accounts": 100,
        "num_loans": 100,
        "num_installments": 300,
        "anomalies_per_type": 5,
    },
    # Full hackathon benchmark volume: 10,000 loans, 30,000 installments over 12 months
    "full": {
        "num_customers": 8000,
        "num_accounts": 10000,
        "num_loans": 10000,
        "num_installments": 30000,
        "anomalies_per_type": 20,
    },
}

# Portfolio Distribution Targets
LOAN_STATUS_WEIGHTS = {
    "ACTIVE": 0.45,
    "PAID_OFF": 0.25,
    "IN_COLLECTION": 0.20,
    "DISPUTED": 0.05,
    "HARDSHIP": 0.05,
}

LOAN_TYPE_WEIGHTS = {
    "PERSONAL": 0.40,
    "AUTO": 0.25,
    "HOME": 0.20,
    "BUSINESS": 0.15,
}

PAYMENT_METHOD_WEIGHTS = {
    "UPI": 0.45,
    "NET_BANKING": 0.25,
    "DEBIT_CARD": 0.15,
    "AUTO_DEBIT": 0.10,
    "WIRE_TRANSFER": 0.03,
    "CASH": 0.02,
}

