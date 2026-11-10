"""Test deterministic reproducibility with fixed seed 20261022."""

import pytest
from validation.reproducibility import verify_seed_reproducibility


def test_seed_reproducibility():
    """Verify dual generation runs produce identical files and SHA-256 hashes."""
    is_reproducible = verify_seed_reproducibility(seed=20261022, scale="starter")
    assert is_reproducible is True, "Seed reproducibility check failed: generated files diverged."
