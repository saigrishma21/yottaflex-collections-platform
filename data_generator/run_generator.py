"""Synthetic Data Generator CLI entry point for YottaFlex Hackathon.

Usage:
    python -m data_generator.run_generator --scale starter
    python -m data_generator.run_generator --scale full --seed 20261022
"""

import sys
import os
import argparse
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_generator.config import DEFAULT_RANDOM_SEED, SCALE_CONFIGS
from data_generator.generators.master_generator import generate_master_records
from data_generator.generators.schedule_generator import generate_installments
from data_generator.generators.transaction_generator import generate_transactions
from data_generator.generators.delinquency_generator import generate_delinquency_snapshots
from data_generator.generators.collections_generator import generate_collections_workflow
from data_generator.anomaly_injector import inject_required_anomalies, export_ground_truth
from data_generator.exporter import export_all


def run_pipeline(scale: str = "starter", seed: int = DEFAULT_RANDOM_SEED, output_dir: str = "data", populate_db: bool = True):
    """Execute complete end-to-end data generation pipeline."""
    start_time = datetime.now()
    scale_cfg = SCALE_CONFIGS.get(scale, SCALE_CONFIGS["starter"])

    print("=" * 70)
    print(" YOTTAFLEX DELINQUENCY & COLLECTIONS SYNTHETIC DATA GENERATOR")
    print("=" * 70)
    print(f"Scale: {scale.upper()}")
    print(f"Random Seed: {seed}")
    print(f"Target Loans: {scale_cfg['num_loans']:,}")
    print(f"Target Installments: {scale_cfg['num_installments']:,}")
    print("-" * 70)

    # 1. Master Records
    print("[1/6] Generating Master Entities (Customers, Accounts, Loans, Preferences)...")
    customers, accounts, loans, preferences = generate_master_records(scale_cfg, seed)
    print(f"      Created {len(customers):,} Customers, {len(accounts):,} Accounts, {len(loans):,} Loans, {len(preferences):,} Preferences")

    # 2. Installment Schedule
    print("[2/6] Generating Amortization Schedules (Installments)...")
    installments = generate_installments(loans, scale_cfg["num_installments"])
    print(f"      Created {len(installments):,} Installments across {len(loans):,} Loans")

    # 3. Transactions & Allocations
    print("[3/6] Simulating Repayment Transactions & Allocations...")
    payments, allocations = generate_transactions(loans, installments, seed)
    print(f"      Created {len(payments):,} Payments and {len(allocations):,} Payment Allocations")

    # 4. Delinquency Snapshots
    print("[4/6] Deriving Delinquency Snapshots (DPD & Arrears)...")
    snapshots = generate_delinquency_snapshots(loans, installments, customers)
    print(f"      Derived {len(snapshots):,} Delinquency Snapshots")

    # 5. Collections Workflow
    print("[5/6] Building Collections Workflow (Cases, Outreach, Promises, Audit Events)...")
    cases, contact_attempts, promises, case_events = generate_collections_workflow(
        loans, snapshots, customers, preferences, seed
    )
    print(f"      Generated {len(cases):,} Cases, {len(contact_attempts):,} Contacts, {len(promises):,} Promises, {len(case_events):,} Events")

    # 6. Inject Anomaly Negative Scenarios
    print("[6/6] Injecting 5 Labeled Negative Edge Cases & Exporting Ground Truth...")
    ground_truth = inject_required_anomalies(
        loans,
        installments,
        payments,
        allocations,
        snapshots,
        cases,
        contact_attempts,
        promises,
        case_events,
        customers,
        preferences,
        anomalies_per_type=scale_cfg["anomalies_per_type"],
    )
    export_ground_truth(ground_truth, os.path.join(output_dir, "ground_truth"))

    # Bundle all data into dictionary
    data_dict = {
        "customers": customers,
        "accounts": accounts,
        "loans": loans,
        "installments": installments,
        "payments": payments,
        "payment_allocations": allocations,
        "delinquency_snapshots": snapshots,
        "contact_preferences": preferences,
        "collection_cases": cases,
        "contact_attempts": contact_attempts,
        "promises_to_pay": promises,
        "case_events": case_events,
    }

    # Export everything
    manifest = export_all(data_dict, ground_truth, output_dir, seed, scale, populate_db=populate_db)

    duration = (datetime.now() - start_time).total_seconds()
    print("=" * 70)
    print(f"GENERATION PIPELINE COMPLETED SUCCESSFULLY IN {duration:.2f}s")
    print("=" * 70)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic Data Generator")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter", help="Dataset scale preset")
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED, help="Deterministic random seed")
    parser.add_argument("--output-dir", default="data", help="Output directory path")
    args = parser.parse_args()

    run_pipeline(scale=args.scale, seed=args.seed, output_dir=args.output_dir)

