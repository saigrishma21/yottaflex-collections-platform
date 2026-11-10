"""Unit tests for explainable Prioritization & Scoring engine."""

import pytest
from decimal import Decimal
from backend.app.services.prioritization import score_collection_account


def test_paid_off_exclusion():
    """Verify paid-off accounts receive score 0 and are excluded."""
    result = score_collection_account(
        total_arrears=Decimal("0.00"),
        days_past_due=0,
        loan_status="PAID_OFF",
    )
    assert result["priority_score"] == Decimal("0.00")
    assert result["eligible"] is False
    assert result["exclusion_reason"] == "PAID_OFF_ZERO_ARREARS"


def test_disputed_debt_exclusion():
    """Verify open disputes are routed to review with score 0."""
    result = score_collection_account(
        total_arrears=Decimal("25000.00"),
        days_past_due=45,
        dispute_status="OPEN",
    )
    assert result["priority_score"] == Decimal("0.00")
    assert result["eligible"] is False
    assert result["action"] == "ROUTE_DISPUTE_REVIEW"


def test_critical_priority_scoring():
    """Verify high balance, high DPD, high risk produces critical tier with explainability."""
    result = score_collection_account(
        total_arrears=Decimal("60000.00"),  # max normalized score = 100 * 0.40 = 40.0
        days_past_due=95,                   # max normalized score = 100 * 0.35 = 35.0
        risk_segment="HIGH",                # 90 * 0.25 = 22.5
    )
    # Total = 40.0 + 35.0 + 22.5 = 97.5
    assert result["priority_score"] == Decimal("97.50")
    assert result["priority_level"] == "CRITICAL"
    assert result["eligible"] is True
    assert len(result["factors"]) == 3
    assert result["factors"][0]["factor_name"] == "Outstanding Balance Arrears"

