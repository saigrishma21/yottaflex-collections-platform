"""Prioritization Engine: Computes explainable multi-factor collection priority scores.
"""

from decimal import Decimal
from typing import Dict, Any


def score_collection_account(
    total_arrears: Decimal,
    days_past_due: int,
    risk_segment: str = "MEDIUM",
    loan_status: str = "ACTIVE",
    dispute_status: str = "NONE",
    is_hardship: bool = False,
) -> Dict[str, Any]:
    """Calculate an explainable collection priority score and tier with full factor attribution.

    Formula:
      Priority Score = (Balance_Score * 0.40) + (DPD_Score * 0.35) + (Risk_Score * 0.25)
    """
    # 1. Statutory Exclusions
    if total_arrears <= Decimal("0.00") or loan_status == "PAID_OFF":
        return {
            "priority_score": Decimal("0.00"),
            "priority_level": "LOW",
            "eligible": False,
            "exclusion_reason": "PAID_OFF_ZERO_ARREARS",
            "action": "EXCLUDE_FROM_COLLECTIONS",
            "factors": [],
            "decision_summary": "Account has zero overdue arrears or is marked paid off.",
        }

    if dispute_status == "OPEN":
        return {
            "priority_score": Decimal("0.00"),
            "priority_level": "LOW",
            "eligible": False,
            "exclusion_reason": "DISPUTED_DEBT",
            "action": "ROUTE_DISPUTE_REVIEW",
            "factors": [],
            "decision_summary": "Active consumer dispute pending. Collection outreach is legally stayed.",
        }

    # 2. Factor Normalization
    bal_float = float(total_arrears)
    s_balance = min(100.0, (bal_float / 50000.0) * 100.0)
    s_dpd = min(100.0, (days_past_due / 90.0) * 100.0)
    s_risk = 90.0 if risk_segment == "HIGH" else (50.0 if risk_segment == "MEDIUM" else 20.0)

    # 3. Weighted Composite Calculation
    c_balance = s_balance * 0.40
    c_dpd = s_dpd * 0.35
    c_risk = s_risk * 0.25
    raw_score = c_balance + c_dpd + c_risk

    # Hardship adjustment if applicable
    if is_hardship:
        raw_score = min(raw_score, 45.0)

    priority_score = Decimal(str(round(raw_score, 2)))

    # 4. Tier Mapping
    if priority_score >= 80.0:
        priority_level = "CRITICAL"
    elif priority_score >= 60.0:
        priority_level = "HIGH"
    elif priority_score >= 40.0:
        priority_level = "MEDIUM"
    else:
        priority_level = "LOW"

    factors = [
        {
            "factor_name": "Outstanding Balance Arrears",
            "raw_value": f"₹{bal_float:,.2f}",
            "normalized_score": round(s_balance, 1),
            "weight": 0.40,
            "weighted_contribution": round(c_balance, 2),
        },
        {
            "factor_name": "Days Past Due (Delinquency Age)",
            "raw_value": f"{days_past_due} Days",
            "normalized_score": round(s_dpd, 1),
            "weight": 0.35,
            "weighted_contribution": round(c_dpd, 2),
        },
        {
            "factor_name": "Customer Risk Profile",
            "raw_value": risk_segment,
            "normalized_score": round(s_risk, 1),
            "weight": 0.25,
            "weighted_contribution": round(c_risk, 2),
        },
    ]

    summary = (
        f"{priority_level} priority: Arrears of ₹{bal_float:,.2f} at {days_past_due} DPD "
        f"with {risk_segment} risk borrower."
    )

    return {
        "priority_score": priority_score,
        "priority_level": priority_level,
        "eligible": True,
        "exclusion_reason": None,
        "action": "SCHEDULE_OUTREACH",
        "factors": factors,
        "decision_summary": summary,
    }

