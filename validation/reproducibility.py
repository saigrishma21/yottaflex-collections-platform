"""Reproducibility Test: Generates datasets twice with identical seed and verifies exact checksums.

Hackathon Acceptance Criterion:
"Regenerate twice with the same seed and compare row counts/checksums to demonstrate reproducibility."
"""

import sys
import os
import shutil
import hashlib

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_generator.config import DEFAULT_RANDOM_SEED
from data_generator.run_generator import run_pipeline


def get_dir_checksums(dir_path: str):
    """Compute SHA-256 for all CSV files in generated directory."""
    csv_dir = os.path.join(dir_path, "generated")
    checksums = {}
    row_counts = {}

    if not os.path.exists(csv_dir):
        return checksums, row_counts

    for fname in sorted(os.listdir(csv_dir)):
        if fname.endswith(".csv"):
            fpath = os.path.join(csv_dir, fname)
            with open(fpath, "rb") as f:
                checksums[fname] = hashlib.sha256(f.read()).hexdigest()
            with open(fpath, "r", encoding="utf-8") as f:
                # Exclude header
                row_counts[fname] = max(0, sum(1 for _ in f) - 1)

    return checksums, row_counts


def verify_seed_reproducibility(seed: int = DEFAULT_RANDOM_SEED, scale: str = "starter"):
    """Run dual generation passes and compare byte-for-byte reproducibility."""
    base_tmp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_reproducibility")
    run1_dir = os.path.join(base_tmp, "run_1")
    run2_dir = os.path.join(base_tmp, "run_2")

    try:
        if os.path.exists(base_tmp):
            shutil.rmtree(base_tmp)

        print("=" * 70)
        print("          DETERMINISTIC SEED REPRODUCIBILITY VERIFICATION")
        print("=" * 70)
        print(f"Target Seed: {seed}")
        print(f"Scale: {scale.upper()}")
        print("-" * 70)

        print("\n--> [Pass 1/2] Generating initial dataset...")
        run_pipeline(scale=scale, seed=seed, output_dir=run1_dir, populate_db=False)
        checks_1, counts_1 = get_dir_checksums(run1_dir)

        print("\n--> [Pass 2/2] Regenerating dataset from identical seed...")
        run_pipeline(scale=scale, seed=seed, output_dir=run2_dir, populate_db=False)
        checks_2, counts_2 = get_dir_checksums(run2_dir)

        print("\n" + "=" * 70)
        print("          REPRODUCIBILITY COMPARISON RESULTS")
        print("=" * 70)

        all_files = sorted(set(checks_1.keys()) | set(checks_2.keys()))
        all_match = True

        for fname in all_files:
            c1 = checks_1.get(fname, "N/A")
            c2 = checks_2.get(fname, "N/A")
            cnt1 = counts_1.get(fname, 0)
            cnt2 = counts_2.get(fname, 0)

            match = (c1 == c2) and (cnt1 == cnt2)
            if not match:
                all_match = False

            status = "[MATCH]" if match else "[MISMATCH]"
            print(f"  {status} {fname:<28} | Rows: {cnt1:>6} vs {cnt2:>6} | SHA256 Match: {c1 == c2}")

        print("=" * 70)
        if all_match:
            print("REPRODUCIBILITY TEST RESULT: 100% IDENTICAL CHECKSUMS (PASSED)")
        else:
            print("REPRODUCIBILITY TEST RESULT: MISMATCH DETECTED (FAILED)")
        print("=" * 70)

        return all_match

    finally:
        if os.path.exists(base_tmp):
            shutil.rmtree(base_tmp)


if __name__ == "__main__":
    success = verify_seed_reproducibility(scale="starter")
    sys.exit(0 if success else 1)

