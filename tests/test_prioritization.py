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
    """Verify severe balance, extended DPD, high risk produces critical tier (>=80.0) with explainability."""
    result = score_collection_account(
        total_arrears=Decimal("350000.00"),
        days_past_due=180,
        risk_segment="HIGH",
    )
    assert result["priority_score"] >= Decimal("80.00")
    assert result["priority_level"] == "CRITICAL"
    assert result["eligible"] is True
    assert len(result["factors"]) == 3
    assert result["factors"][0]["factor_name"] == "Days Past Due (Delinquency Age)"
    assert result["factors"][1]["factor_name"] == "Outstanding Balance Arrears"
    assert result["factors"][2]["factor_name"] == "Customer Risk Profile"

