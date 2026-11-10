"""Unified Command-Line Interface for YottaFlex Collections Platform.

Usage:
    python cli.py generate --scale full --seed 20261022
    python cli.py validate
    python cli.py reproducibility
    python cli.py compliance
    python cli.py benchmark
    python cli.py top-priorities --limit 10
    python cli.py run-server --port 8000
"""

import sys
import argparse
from backend.app.database import SessionLocal
from backend.app.routes.collections import get_priority_worklist
from backend.app.services.compliance import scan_compliance_violations
from backend.app.routes.compliance import evaluate_ground_truth_benchmark
from data_generator.run_generator import run_pipeline
from validation.validator import run_full_validation
from validation.reproducibility import verify_seed_reproducibility


def main():
    parser = argparse.ArgumentParser(
        description="YottaFlex AI Loan Collections Platform CLI",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: generate
    p_gen = subparsers.add_parser("generate", help="Generate synthetic loan dataset")
    p_gen.add_argument("--scale", choices=["starter", "full"], default="starter", help="Dataset scale")
    p_gen.add_argument("--seed", type=int, default=20261022, help="Deterministic random seed")

    # Command: validate
    subparsers.add_parser("validate", help="Run comprehensive data integrity validation")

    # Command: reproducibility
    subparsers.add_parser("reproducibility", help="Run dual-pass seed reproducibility test")

    # Command: compliance
    subparsers.add_parser("compliance", help="Scan database for statutory & policy breaches")

    # Command: benchmark
    subparsers.add_parser("benchmark", help="Evaluate detection against isolated ground truth")

    # Command: top-priorities
    p_prio = subparsers.add_parser("top-priorities", help="Print top prioritized overdue accounts")
    p_prio.add_argument("--limit", type=int, default=10, help="Number of records to show")

    # Command: run-server
    p_srv = subparsers.add_parser("run-server", help="Launch FastAPI web server")
    p_srv.add_argument("--host", default="127.0.0.1", help="Host interface")
    p_srv.add_argument("--port", type=int, default=8000, help="Listening port")
    p_srv.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    if args.command == "generate":
        run_pipeline(scale=args.scale, seed=args.seed)

    elif args.command == "validate":
        res = run_full_validation()
        sys.exit(0 if res["passed"] else 1)

    elif args.command == "reproducibility":
        passed = verify_seed_reproducibility(seed=20261022, scale="starter")
        sys.exit(0 if passed else 1)

    elif args.command == "compliance":
        db = SessionLocal()
        try:
            violations = scan_compliance_violations(db)
            print(f"\nDetected {len(violations)} Compliance Exceptions:")
            for v in violations:
                print(f"  [{v['severity']:<8}] {v['violation_code']:<30} | Record: {v['record_id']:<24}")
                print(f"            Description: {v['description']}")
                print(f"            Remedial:    {v['recommended_action']}\n")
        finally:
            db.close()

    elif args.command == "benchmark":
        db = SessionLocal()
        try:
            bm = evaluate_ground_truth_benchmark(db)
            print("\nGround Truth Evaluation Benchmark:")
            print(f"  Ground Truth Anomalies: {bm['ground_truth_total']}")
            print(f"  Detected Anomalies:     {bm['detected_total']}")
            print(f"  Precision:              {bm['precision'] * 100:.1f}%")
            print(f"  Recall:                 {bm['recall'] * 100:.1f}%")
            print(f"  F1-Score:               {bm['f1_score']:.4f}")
        finally:
            db.close()

    elif args.command == "top-priorities":
        db = SessionLocal()
        try:
            items = get_priority_worklist(limit=args.limit, db=db)
            print(f"\nTop {len(items)} Prioritized Delinquent Accounts:")
            print(f"  {'Case ID':<18} {'Borrower':<24} {'Arrears':<15} {'DPD':<6} {'Score':<8} {'Tier':<10}")
            print("  " + "-" * 85)
            for it in items:
                print(
                    f"  {it.case_id:<18} {it.customer_name or it.customer_id:<24} "
                    f"₹{Number(it.outstanding_amount):>12,.2f}  {it.days_past_due:>4}d  "
                    f"{Number(it.priority_score):>6.1f}  {it.priority_level:<10}"
                )
        finally:
            db.close()

    elif args.command == "run-server":
        import uvicorn
        print(f"Starting YottaFlex Server on http://{args.host}:{args.port}")
        uvicorn.run("backend.app.main:app", host=args.host, port=args.port, reload=args.reload)

    else:
        parser.print_help()


if __name__ == "__main__":
    from decimal import Decimal
    Number = float
    main()
